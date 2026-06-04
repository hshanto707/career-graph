"""Tests for IngestionAgent — WRITTEN BEFORE IMPLEMENTATION (TDD)."""
import io
import pytest
from app.engine.ingestion.ingestion_agent import IngestionAgent, IngestionResult

VALID_CSV = """id,title,company,location,employment_type,salary_min,salary_max,skills_required,description,posted_date
JOB_001,Software Engineer,TechCorp,San Francisco CA,Full-time,80000,120000,"Python,FastAPI,PostgreSQL",Backend dev role,2024-01-15
JOB_002,Frontend Dev,WebCo,Remote,Full-time,70000,100000,"React,TypeScript,CSS",Frontend role,2024-02-01
JOB_003,Data Scientist,DataCo,New York NY,Full-time,90000,140000,"Python,Machine Learning,Pandas",DS role,2024-03-01
"""

INVALID_CSV_MISSING_COL = """id,title,company
JOB_001,Software Engineer,TechCorp
"""

MALFORMED_ROW_CSV = """id,title,company,location,employment_type,salary_min,salary_max,skills_required,description,posted_date
JOB_001,Software Engineer,TechCorp,San Francisco CA,Full-time,not_a_number,120000,"Python",Backend,2024-01-15
JOB_002,Frontend Dev,WebCo,Remote,Full-time,70000,100000,"React",Frontend,2024-02-01
"""

def test_valid_csv_parsed():
    """Valid CSV parses all rows correctly."""
    agent = IngestionAgent()
    result = agent.ingest_csv(VALID_CSV)
    assert isinstance(result, IngestionResult)
    assert result.total_rows == 3
    assert result.valid_rows == 3
    assert result.failed_rows == 0
    assert len(result.jobs) == 3

def test_job_has_required_fields():
    """Each parsed job has all required fields."""
    agent = IngestionAgent()
    result = agent.ingest_csv(VALID_CSV)
    job = result.jobs[0]
    assert job["id"] == "JOB_001"
    assert job["title"] == "Software Engineer"
    assert isinstance(job["skills_required"], list)
    assert "Python" in job["skills_required"]

def test_malformed_salary_row_is_dropped():
    """Row with non-numeric salary is dropped and counted as failed."""
    agent = IngestionAgent()
    result = agent.ingest_csv(MALFORMED_ROW_CSV)
    assert result.total_rows == 2
    assert result.failed_rows == 1
    assert result.valid_rows == 1

def test_invalid_schema_raises():
    """CSV missing required columns raises ValueError."""
    agent = IngestionAgent()
    with pytest.raises(ValueError, match="Missing required columns"):
        agent.ingest_csv(INVALID_CSV_MISSING_COL)

def test_skills_parsed_as_list():
    """Comma-separated skills_required is parsed into a Python list."""
    agent = IngestionAgent()
    result = agent.ingest_csv(VALID_CSV)
    skills = result.jobs[0]["skills_required"]
    assert isinstance(skills, list)
    assert len(skills) == 3

def test_empty_csv_body():
    """CSV with headers only (no data rows) returns zero jobs."""
    agent = IngestionAgent()
    empty_csv = "id,title,company,location,employment_type,salary_min,salary_max,skills_required,description,posted_date\n"
    result = agent.ingest_csv(empty_csv)
    assert result.total_rows == 0
    assert result.valid_rows == 0
