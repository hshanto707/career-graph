from pydantic import BaseModel


class JobResponse(BaseModel):
    id: str
    title: str
    company: str
    location: str
    employment_type: str
    salary_min: int | None
    salary_max: int | None
    skills_required: list[str]
    description: str
    posted_date: str


class JobFilter(BaseModel):
    search: str | None = None
    location: str | None = None
    employment_type: str | None = None
    skill: str | None = None
    limit: int = 20
    offset: int = 0
