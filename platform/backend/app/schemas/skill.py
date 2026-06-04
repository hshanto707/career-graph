from pydantic import BaseModel


class MarketSkillResponse(BaseModel):
    name: str
    demand_count: int
    demand_score: float  # 0-100
