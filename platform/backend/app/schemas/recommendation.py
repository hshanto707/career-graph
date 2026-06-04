from pydantic import BaseModel


class JobRecommendationResponse(BaseModel):
    job_id: str
    title: str
    company: str
    location: str
    employment_type: str
    salary_min: int | None
    salary_max: int | None
    score: float
    matched_skills: list[str]
    missing_skills: list[str]
    why_recommended: str | None = None
