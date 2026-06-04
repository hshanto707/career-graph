from pydantic import BaseModel


class GapAnalysisRequest(BaseModel):
    target_job_id: str
    explain: bool = False  # If True, call LLM for explanation


class RoadmapMilestone(BaseModel):
    week: int
    skills: list[str]
    description: str


class Roadmap(BaseModel):
    milestones: list[RoadmapMilestone]
    weeks_estimate: int
    total_skills: int
    summary: str | None = None


class GapAnalysisResponse(BaseModel):
    target_job_id: str
    target_job_title: str
    readiness_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    must_matched: int
    must_total: int
    nice_matched: int
    nice_total: int
    roadmap: Roadmap | None = None
    explanation: str | None = None
    encouragement: str | None = None
    weeks_to_learn: int | None = None
