from typing import Optional

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class Session(SQLModel, table=True):
    __tablename__ = "sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    date: str  # YYYY-MM-DD
    type: str  # JSON array string, e.g. '["python","project"]'
    notes: Optional[str] = None
    commits: int = 0
    level: int  # 1=light, 2=solid, 3=deep
    created_at: Optional[int] = None  # unix ms


class Metrics(SQLModel, table=True):
    __tablename__ = "metrics"

    id: Optional[int] = Field(default=1, primary_key=True)
    projects_shipped: int = 0
    applications_sent: int = 0
    stages_complete: int = 0
    updated_at: Optional[int] = None


class Milestone(SQLModel, table=True):
    __tablename__ = "milestones"

    key: str = Field(primary_key=True)
    completed: bool = False
    completed_at: Optional[int] = None


class Brief(SQLModel, table=True):
    __tablename__ = "briefs"

    id: Optional[int] = Field(default=None, primary_key=True)
    date: str  # YYYY-MM-DD
    summary: Optional[str] = None
    focus: Optional[str] = None
    research: Optional[str] = None  # JSON array string
    generated_at: Optional[int] = None


# --- Request/response schemas (not tables) ---


class SessionCreate(BaseModel):
    date: str
    type: list[str]
    notes: Optional[str] = None
    commits: int = 0
    level: int


class MetricsUpdate(BaseModel):
    projects_shipped: Optional[int] = None
    applications_sent: Optional[int] = None
    stages_complete: Optional[int] = None


class MilestoneUpdate(BaseModel):
    completed: bool
