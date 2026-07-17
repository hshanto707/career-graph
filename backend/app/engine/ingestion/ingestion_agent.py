"""IngestionAgent — module B4.

Reads raw job-posting CSV data (Kaggle-style export, or the Internshala
scraper's output once that lands), validates the schema, drops malformed
rows, and parses the `skills_required` field into a clean list per row.

This agent does zero graph/database work and zero synonym resolution — it
only turns "a CSV" into "a list of validated, structurally-clean Python
dicts". `NormalizationAgent` takes that output and resolves skill names /
writes to the graph.

Expected CSV columns (see `data/kaggle_jobs.csv` and docs/data-sources.md):
    title, company, location, type, skills_required, salary_min, salary_max
    category (optional — used for the Job -[:IN_CATEGORY]-> Category edge)
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from pathlib import Path

REQUIRED_COLUMNS = {"title", "company", "location", "type", "skills_required"}
VALID_JOB_TYPES = {"Full-time", "Part-time", "Internship", "Contract"}


@dataclass
class IngestionStats:
    rows_read: int = 0
    rows_dropped: int = 0
    drop_reasons: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "rows_read": self.rows_read,
            "rows_dropped": self.rows_dropped,
            "drop_reasons": list(self.drop_reasons),
        }


@dataclass
class IngestionResult:
    records: list[dict]
    stats: IngestionStats


class IngestionAgent:
    """Reads + validates a job-postings CSV into clean Python records."""

    def read_csv(self, source: str | Path | io.IOBase | bytes) -> IngestionResult:
        """Parse `source` (a file path, an open file-like object, or raw
        bytes/str content — e.g. an uploaded file) into validated records.

        Malformed rows are dropped, never raise: a single bad row must not
        abort the whole ingestion run.
        """
        text = self._read_text(source)
        stats = IngestionStats()
        records: list[dict] = []

        reader = csv.DictReader(io.StringIO(text))
        header = set(reader.fieldnames or [])
        if not REQUIRED_COLUMNS.issubset(header):
            missing = REQUIRED_COLUMNS - header
            raise ValueError(f"CSV is missing required columns: {sorted(missing)}")

        for row in reader:
            stats.rows_read += 1
            record, drop_reason = self._validate_row(row)
            if drop_reason is not None:
                stats.rows_dropped += 1
                stats.drop_reasons.append(drop_reason)
                continue
            records.append(record)

        return IngestionResult(records=records, stats=stats)

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    @staticmethod
    def _read_text(source: str | Path | io.IOBase | bytes) -> str:
        if isinstance(source, bytes):
            # Strip a UTF-8 BOM if present (common in Excel-exported CSVs);
            # normalize Windows line endings.
            return source.decode("utf-8-sig")
        if isinstance(source, (str, Path)) and not _looks_like_csv_content(source):
            with open(source, "r", encoding="utf-8-sig", newline="") as f:
                return f.read()
        if hasattr(source, "read"):
            content = source.read()
            if isinstance(content, bytes):
                return content.decode("utf-8-sig")
            return content
        # Raw CSV text passed directly.
        return str(source)

    def _validate_row(self, row: dict) -> tuple[dict | None, str | None]:
        title = (row.get("title") or "").strip()
        company = (row.get("company") or "").strip()
        location = (row.get("location") or "").strip()
        job_type = (row.get("type") or "").strip()
        skills_raw = (row.get("skills_required") or "").strip()

        if not title:
            return None, "missing title"
        if not company:
            return None, "missing company"
        if not skills_raw:
            return None, "missing skills_required"

        skills = self._parse_skills(skills_raw)
        if not skills:
            return None, "skills_required had no usable entries"

        salary_min = self._parse_int(row.get("salary_min"))
        salary_max = self._parse_int(row.get("salary_max"))
        if salary_min is not None and salary_max is not None and salary_min > salary_max:
            return None, "salary_min greater than salary_max"

        if job_type and job_type not in VALID_JOB_TYPES:
            # Unknown type isn't fatal — normalize to a sentinel rather than
            # dropping real postings over an unexpected label.
            job_type = job_type

        record = {
            "title": title,
            "company": company,
            "location": location or "Unspecified",
            "type": job_type or "Unspecified",
            "skills_required": skills,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "category": (row.get("category") or "").strip() or None,
        }
        return record, None

    @staticmethod
    def _parse_skills(raw: str) -> list[str]:
        """Split a comma-separated skills field, trimming whitespace,
        dropping empty entries, and de-duplicating (case-insensitive) while
        preserving first-seen order."""
        seen: set[str] = set()
        skills: list[str] = []
        for chunk in raw.split(","):
            name = chunk.strip()
            if not name:
                continue
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            skills.append(name)
        return skills

    @staticmethod
    def _parse_int(value) -> int | None:
        if value is None or str(value).strip() == "":
            return None
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None


def _looks_like_csv_content(value: str | Path) -> bool:
    """Heuristic: a genuine file path won't contain a newline; raw CSV text
    passed as a string for convenience (e.g. in tests) will."""
    return isinstance(value, str) and "\n" in value
