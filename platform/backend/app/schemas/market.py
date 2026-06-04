from pydantic import BaseModel


class MarketInsightsResponse(BaseModel):
    total_jobs: int
    top_skills: list[dict]    # [{"name": str, "demand_count": int, "demand_score": float}]
    top_categories: list[dict]  # [{"name": str, "job_count": int}]
