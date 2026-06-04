from pydantic import BaseModel


class DashboardResponse(BaseModel):
    skills_count: int
    top_job_readiness: float   # 0-100
    total_jobs_in_market: int
    top_demanded_skill: str
