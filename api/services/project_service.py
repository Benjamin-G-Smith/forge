import json
import os
import time

from sqlmodel import Session, select

from api.models.models import Metrics, Milestone, ProjectSnapshot
from chain.project_sync import MILESTONE_LABELS, VAULT_PROJECTS_DIR, synthesize_project
from chain.projects import PROJECTS_BY_ID


def vault_last_active_ms(project_id: str) -> int | None:
    vault_note_path = VAULT_PROJECTS_DIR / PROJECTS_BY_ID[project_id]["vault_note"]
    if not vault_note_path.exists():
        return None
    return int(os.path.getmtime(vault_note_path) * 1000)


def _current_milestones(session: Session) -> dict[str, bool]:
    existing = {m.key: m.completed for m in session.exec(select(Milestone)).all()}
    return {key: existing.get(key, False) for key in MILESTONE_LABELS}


def get_latest_snapshot(session: Session, project_id: str) -> ProjectSnapshot | None:
    return session.exec(
        select(ProjectSnapshot)
        .where(ProjectSnapshot.project_id == project_id)
        .order_by(ProjectSnapshot.created_at.desc())
        .limit(1)
    ).first()


def refresh_project(session: Session, project_id: str) -> ProjectSnapshot:
    config = PROJECTS_BY_ID[project_id]

    flagship_context = None
    if config["flagship"]:
        metrics = session.get(Metrics, 1) or Metrics(id=1)
        flagship_context = {
            "current_stage": metrics.stages_complete,
            "current_milestones": _current_milestones(session),
        }

    vault_note_path = VAULT_PROJECTS_DIR / config["vault_note"]
    result = synthesize_project(vault_note_path, flagship_context)

    previous = get_latest_snapshot(session, project_id)
    completed_up_next = previous.completed_up_next if previous else "[]"

    snapshot = ProjectSnapshot(
        project_id=project_id,
        created_at=int(time.time() * 1000),
        status=result["status"],
        focus=result["focus"],
        focus_meta=result["focus_meta"],
        stats=json.dumps(result["stats"]),
        up_next=json.dumps(result["up_next"]),
        progress=json.dumps(result["progress"]),
        completed_up_next=completed_up_next,
        proposed_stage=result.get("proposed_stage"),
        proposed_milestones=(
            json.dumps(result["proposed_milestones"]) if "proposed_milestones" in result else None
        ),
    )
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)
    return snapshot


def complete_up_next_item(session: Session, project_id: str, index: int) -> ProjectSnapshot:
    snapshot = get_latest_snapshot(session, project_id)
    if snapshot is None:
        raise ValueError("no snapshot for project")

    up_next = json.loads(snapshot.up_next)
    if index < 0 or index >= len(up_next):
        raise IndexError("up_next index out of range")

    item = up_next.pop(index)
    completed = json.loads(snapshot.completed_up_next)
    completed.insert(0, item)

    snapshot.up_next = json.dumps(up_next)
    snapshot.completed_up_next = json.dumps(completed)
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)
    return snapshot


def apply_project_snapshot(session: Session, snapshot_id: int) -> ProjectSnapshot:
    snapshot = session.get(ProjectSnapshot, snapshot_id)
    if snapshot is None or snapshot.applied or snapshot.proposed_stage is None:
        raise ValueError("snapshot not found, already applied, or has no proposed state")

    now = int(time.time() * 1000)

    metrics = session.get(Metrics, 1) or Metrics(id=1)
    metrics.stages_complete = snapshot.proposed_stage
    metrics.updated_at = now
    session.add(metrics)

    proposed = json.loads(snapshot.proposed_milestones or "{}")
    for key, completed in proposed.items():
        milestone = session.get(Milestone, key) or Milestone(key=key)
        if milestone.completed != completed:
            milestone.completed = completed
            milestone.completed_at = now if completed else None
        session.add(milestone)

    snapshot.applied = True
    snapshot.applied_at = now
    session.add(snapshot)

    session.commit()
    session.refresh(snapshot)
    return snapshot
