"""NormalizationAgent — module B4.

Takes the clean records produced by `IngestionAgent` and, per
system-design.md §9.2 / §11.4:

1. Loads `synonyms.json` (exact alias -> canonical name) and the O*NET/ESCO
   skill taxonomy (`onet_skills.csv`) once.
2. For every raw skill name on a job posting:
   a. Exact match against `synonyms.json` (case-insensitive) -> use the
      mapped canonical name.
   b. Else fuzzy match via `rapidfuzz` against the O*NET taxonomy. Score
      >= `fuzzy_threshold` (default 90) -> accept the canonical O*NET name.
      Ties at the top score are broken deterministically (alphabetically by
      canonical name), never by "whatever the library returns first".
   c. Else keep the raw name as-is and flag it for manual review.
3. Derives `importance` ("must"/"nice") from the skill's position in the
   posting: the first half of the (deduplicated) list are "must", the rest
   are "nice" — a simple, concrete, documented rule per the open decision in
   features-todo.md §B5.
4. Writes the job + its normalized skills into the graph via `GraphService`
   (or `FakeGraphService` in tests) using `GraphService.ingest_job_posting`,
   which is MERGE-based end to end and therefore idempotent: re-running the
   same input twice does not create duplicate Job/Skill nodes or REQUIRES
   edges.
"""
from __future__ import annotations

import csv
import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rapidfuzz import fuzz, process

DEFAULT_FUZZY_THRESHOLD = 90


@dataclass
class NormalizedSkill:
    raw_name: str
    normalized_name: str
    category: str | None
    flagged: bool
    match_type: str  # "exact_synonym" | "already_canonical" | "fuzzy" | "unmatched"
    importance: str = "nice"

    def as_dict(self) -> dict[str, Any]:
        return {
            "raw_name": self.raw_name,
            "normalized_name": self.normalized_name,
            "category": self.category,
            "flagged": self.flagged,
            "match_type": self.match_type,
            "importance": self.importance,
        }


@dataclass
class NormalizationStats:
    jobs_written: int = 0
    skills_flagged: int = 0
    skill_edges_written: int = 0
    flagged_skills: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "jobs_written": self.jobs_written,
            "skills_flagged": self.skills_flagged,
            "skill_edges_written": self.skill_edges_written,
            "flagged_skills": list(dict.fromkeys(self.flagged_skills)),
        }


class NormalizationAgent:
    """Resolves raw skill names to canonical O*NET names and writes the
    normalized job posting into the knowledge graph."""

    def __init__(
        self,
        graph_service: Any,
        synonyms_path: str | Path,
        onet_skills_path: str | Path,
        fuzzy_threshold: int = DEFAULT_FUZZY_THRESHOLD,
    ):
        self._graph = graph_service
        self._fuzzy_threshold = fuzzy_threshold
        self._synonyms = self._load_synonyms(synonyms_path)
        self._onet_by_lower, self._onet_categories = self._load_onet(onet_skills_path)
        # Sorted once so any tie-break iteration order is deterministic.
        self._onet_canonical_names = sorted(self._onet_by_lower.values())

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def normalize_skill(self, raw_name: str) -> NormalizedSkill:
        """Resolve a single raw skill name. Never raises on unmatched input
        — worst case it is kept as-is and flagged."""
        cleaned = raw_name.strip()
        lower = cleaned.lower()

        # (a) exact synonym match
        mapped = self._synonyms.get(lower)
        if mapped is not None:
            category = self._onet_by_lower.get(mapped.lower())
            return NormalizedSkill(
                raw_name=cleaned,
                normalized_name=mapped,
                category=self._onet_categories.get(mapped.lower()) if category else None,
                flagged=False,
                match_type="exact_synonym",
            )

        # already an exact canonical O*NET name (case-insensitive)
        canonical = self._onet_by_lower.get(lower)
        if canonical is not None:
            return NormalizedSkill(
                raw_name=cleaned,
                normalized_name=canonical,
                category=self._onet_categories.get(lower),
                flagged=False,
                match_type="already_canonical",
            )

        # (b) fuzzy match against the O*NET taxonomy
        best = self._fuzzy_match(cleaned)
        if best is not None:
            return NormalizedSkill(
                raw_name=cleaned,
                normalized_name=best,
                category=self._onet_categories.get(best.lower()),
                flagged=False,
                match_type="fuzzy",
            )

        # (c) unmatched — keep raw, flag for manual review
        return NormalizedSkill(
            raw_name=cleaned,
            normalized_name=cleaned,
            category=None,
            flagged=True,
            match_type="unmatched",
        )

    def process_and_write(self, records: list[dict[str, Any]]) -> NormalizationStats:
        """Normalize every skill on every record and write the resulting
        job + REQUIRES edges into the graph. Safe to call twice on the same
        input — idempotent via `GraphService.ingest_job_posting`'s MERGE
        semantics."""
        stats = NormalizationStats()

        for record in records:
            raw_skills: list[str] = record.get("skills_required", [])
            normalized = [self.normalize_skill(name) for name in raw_skills]
            self._assign_importance(normalized)

            job_id = self._job_id(record["company"], record["title"])
            job = {
                "id": job_id,
                "title": record["title"],
                "company": record["company"],
                "location": record.get("location"),
                "type": record.get("type"),
                "salary_min": record.get("salary_min"),
                "salary_max": record.get("salary_max"),
                "category": record.get("category"),
                "source": record.get("source", "kaggle_csv"),
            }

            write_result = self._graph.ingest_job_posting(
                job, [skill.as_dict() for skill in normalized]
            )

            stats.jobs_written += write_result.get("jobs_written", 1)
            stats.skill_edges_written += write_result.get("skill_edges_written", len(normalized))
            for skill in normalized:
                if skill.flagged:
                    stats.skills_flagged += 1
                    stats.flagged_skills.append(skill.normalized_name)

        return stats

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    def _fuzzy_match(self, raw_name: str) -> str | None:
        if not self._onet_canonical_names:
            return None
        matches = process.extract(
            raw_name,
            self._onet_canonical_names,
            scorer=fuzz.WRatio,
            score_cutoff=self._fuzzy_threshold,
            limit=None,
        )
        if not matches:
            return None
        top_score = max(score for _, score, _ in matches)
        tied = sorted(name for name, score, _ in matches if score == top_score)
        # Deterministic tie-breaker: alphabetically first canonical name.
        return tied[0]

    @staticmethod
    def _assign_importance(skills: list[NormalizedSkill]) -> None:
        """First half of the (already-deduplicated) skill list on a posting
        is 'must', the rest is 'nice' — a simple, concrete, documented rule
        (see module docstring / docs/data-sources.md)."""
        must_count = max(1, math.ceil(len(skills) / 2)) if skills else 0
        for index, skill in enumerate(skills):
            skill.importance = "must" if index < must_count else "nice"

    @staticmethod
    def _job_id(company: str, title: str) -> str:
        """Deterministic MERGE key for a Job node: slug(company)::slug(title).

        Documented collision caveat (features-todo.md §B4): two distinct
        postings with the same company + title collide into a single Job
        node. Acceptable for capstone scope; a production ingestion of the
        full 10k+ Kaggle dataset would additionally key on a source row id.
        """
        return f"{_slug(company)}::{_slug(title)}"

    @staticmethod
    def _load_synonyms(path: str | Path) -> dict[str, str]:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return {alias.strip().lower(): canonical for alias, canonical in raw.items()}

    @staticmethod
    def _load_onet(path: str | Path) -> tuple[dict[str, str], dict[str, str]]:
        by_lower: dict[str, str] = {}
        categories: dict[str, str] = {}
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = (row.get("skill_name") or "").strip()
                if not name:
                    continue
                by_lower[name.lower()] = name
                categories[name.lower()] = (row.get("category") or "").strip() or None
        return by_lower, categories


def _slug(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "unknown"
