"""
IngestionAgent — Parses and validates job postings from CSV files.

Reads a CSV string (or file path), validates required columns,
parses each row, drops malformed rows, and returns structured job dicts.
"""
import io
import csv
from dataclasses import dataclass, field


REQUIRED_COLUMNS = {
    "id", "title", "company", "location", "employment_type",
    "salary_min", "salary_max", "skills_required", "description", "posted_date",
}


@dataclass
class IngestionResult:
    """Result of a CSV ingestion operation."""
    jobs: list[dict] = field(default_factory=list)
    total_rows: int = 0
    valid_rows: int = 0
    failed_rows: int = 0
    errors: list[str] = field(default_factory=list)


class IngestionAgent:
    """
    Parses job posting CSV data into structured Python dicts.

    Validates schema, drops malformed rows (e.g. non-numeric salary),
    and parses comma-separated skills_required into lists.
    """

    def ingest_csv(self, csv_content: str) -> IngestionResult:
        """
        Parse a CSV string of job postings.

        Args:
            csv_content: CSV data as a string.

        Returns:
            IngestionResult with validated jobs and error counts.

        Raises:
            ValueError: If required columns are missing from the CSV header.
        """
        reader = csv.DictReader(io.StringIO(csv_content.strip()))
        columns = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - columns
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        result = IngestionResult()
        for row in reader:
            result.total_rows += 1
            try:
                job = self._parse_row(row)
                result.jobs.append(job)
                result.valid_rows += 1
            except (ValueError, KeyError) as e:
                result.failed_rows += 1
                result.errors.append(f"Row {result.total_rows}: {e}")

        return result

    def _parse_row(self, row: dict) -> dict:
        """Parse and validate a single CSV row into a job dict."""
        salary_min = int(float(row["salary_min"]))  # Raises ValueError if not numeric
        salary_max = int(float(row["salary_max"]))

        skills_raw = row.get("skills_required", "")
        skills = [s.strip() for s in skills_raw.split(",") if s.strip()]

        return {
            "id": row["id"].strip(),
            "title": row["title"].strip(),
            "company": row["company"].strip(),
            "location": row["location"].strip(),
            "employment_type": row["employment_type"].strip(),
            "salary_min": salary_min,
            "salary_max": salary_max,
            "skills_required": skills,
            "description": row.get("description", "").strip(),
            "posted_date": row.get("posted_date", "").strip(),
        }

    def ingest_file(self, file_path: str) -> IngestionResult:
        """Parse a CSV file by path."""
        with open(file_path, "r", encoding="utf-8") as f:
            return self.ingest_csv(f.read())
