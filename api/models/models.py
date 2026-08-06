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


class ProjectSnapshot(SQLModel, table=True):
    """A synced state for one project (see chain/projects.py), from its vault note.

    Insert-only from refresh, with one exception: complete_up_next_item mutates
    the latest row in place to move an item from up_next into completed_up_next,
    since that's a user action against "the current snapshot" rather than a new
    sync — see api/services/project_service.py.
    """

    __tablename__ = "project_snapshots"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: str
    created_at: int  # unix ms
    status: str
    focus: str
    focus_meta: str
    stats: str  # JSON [[label, value], ...]
    up_next: str  # JSON [{title, detail}, ...]
    progress: str  # JSON [str, ...]
    completed_up_next: str = "[]"  # JSON [{title, detail}, ...], carried forward on refresh
    proposed_stage: Optional[int] = None  # flagship project only
    proposed_milestones: Optional[str] = None  # JSON {key: bool}, flagship project only
    applied: bool = False
    applied_at: Optional[int] = None


class ArchivedContextItem(SQLModel, table=True):
    """A single bullet the user saved for later off a context_snapshots field.

    Decoupled from context_snapshots on purpose: snapshot text is regenerated
    fresh on every refresh, so an archived bullet has to stand on its own to
    survive future refreshes rather than pointing at text that may no longer
    exist verbatim.
    """

    __tablename__ = "archived_context_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    text: str
    source: str  # "summary" | "next_action" | "reasoning"
    snapshot_id: Optional[int] = None  # provenance only, not a live FK lookup
    archived_at: int  # unix ms


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


class ArchiveItemCreate(BaseModel):
    text: str
    source: str
    snapshot_id: Optional[int] = None


class ApplySnapshotRequest(BaseModel):
    snapshot_id: int


class CompleteItemRequest(BaseModel):
    index: int
