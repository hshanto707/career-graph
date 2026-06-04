"""
NormalizationAgent — Resolves skill synonyms and deduplicates skill names.

Uses a curated synonym map for exact/case-insensitive matches,
and rapidfuzz for fuzzy matching against a known skill vocabulary.
"""
from rapidfuzz import fuzz, process


DEFAULT_FUZZY_THRESHOLD = 85  # Score out of 100 required for fuzzy match


class NormalizationAgent:
    """
    Normalizes skill names to canonical forms.

    Steps for each skill:
    1. Lowercase lookup in synonym map (e.g., "reactjs" -> "React")
    2. If not found, fuzzy match against known_skills vocabulary
    3. If score >= threshold, return best match
    4. Otherwise return original skill name unchanged

    This prevents graph pollution from aliases like ReactJS, React.js, react.
    """

    def __init__(
        self,
        synonyms: dict[str, str] | None = None,
        known_skills: list[str] | None = None,
        fuzzy_threshold: int = DEFAULT_FUZZY_THRESHOLD,
    ):
        """
        Args:
            synonyms: Mapping of lowercase alias -> canonical name.
            known_skills: List of canonical skill names for fuzzy matching.
            fuzzy_threshold: Minimum rapidfuzz score (0-100) for fuzzy match.
        """
        self.synonyms = synonyms or {}
        self.known_skills = known_skills or []
        self.fuzzy_threshold = fuzzy_threshold

    def normalize(self, skill: str) -> str:
        """
        Normalize a single skill name.

        Args:
            skill: Raw skill name (may be an alias or misspelling).

        Returns:
            Canonical skill name.
        """
        lower = skill.lower().strip()

        # Step 1: Exact synonym lookup (case-insensitive)
        if lower in self.synonyms:
            return self.synonyms[lower]

        # Step 2: Fuzzy match against known skills vocabulary
        if self.known_skills:
            match = process.extractOne(skill, self.known_skills, scorer=fuzz.ratio)
            if match and match[1] >= self.fuzzy_threshold:
                return match[0]

        return skill  # Return original if no match found

    def normalize_list(self, skills: list[str]) -> list[str]:
        """
        Normalize and deduplicate a list of skill names.

        Args:
            skills: Raw list of skill names.

        Returns:
            List of canonical skill names with duplicates removed (preserving order).
        """
        seen: set[str] = set()
        result: list[str] = []
        for skill in skills:
            canonical = self.normalize(skill)
            if canonical not in seen:
                seen.add(canonical)
                result.append(canonical)
        return result

    def normalize_jobs(self, jobs: list[dict]) -> list[dict]:
        """
        Normalize skills_required for a list of job dicts.

        Modifies and returns the same list with normalized skill names.

        Args:
            jobs: List of job dicts with 'skills_required' list.

        Returns:
            The same list with skills_required normalized in-place.
        """
        for job in jobs:
            if "skills_required" in job:
                job["skills_required"] = self.normalize_list(job["skills_required"])
        return jobs

    @classmethod
    def from_files(cls, synonyms_path: str, onet_path: str | None = None) -> "NormalizationAgent":
        """
        Load synonym map from JSON and optional skill vocabulary from CSV.

        Args:
            synonyms_path: Path to synonyms.json file.
            onet_path: Optional path to onet_skills.csv.

        Returns:
            Configured NormalizationAgent instance.
        """
        import json
        import csv as csv_module

        with open(synonyms_path, "r") as f:
            synonyms = json.load(f)

        known_skills: list[str] = []
        if onet_path:
            with open(onet_path, "r") as f:
                reader = csv_module.DictReader(f)
                known_skills = [row["name"] for row in reader if row.get("name")]

        return cls(synonyms=synonyms, known_skills=known_skills)
