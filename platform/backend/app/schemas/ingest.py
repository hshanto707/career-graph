from pydantic import BaseModel


class IngestStatusResponse(BaseModel):
    status: str   # "running" | "completed" | "failed"
    total_rows: int
    valid_rows: int
    failed_rows: int
    message: str
