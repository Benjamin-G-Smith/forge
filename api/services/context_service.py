import json
import time

from sqlmodel import Session, select

from api.models.models import ContextSnapshot, Metrics, Milestone
from chain.context_sync import MILESTONE_LABELS, synthesize_context


def _current_milestones(session: Session) -> dict[str, bool]:
    existing = {m.key: m.completed for m in session.exec(select(Milestone)).all()}
    return {key: existing.get(key, False) for key in MILESTONE_LABELS}


def generate_and_save_snapshot(session: Session) -> ContextSnapshot:
    metrics = session.get(Metrics, 1) or Metrics(id=1)
    current_milestones = _current_milestones(session)

    result = synthesize_context(metrics.stages_complete, current_milestones)

    snapshot = ContextSnapshot(
        created_at=int(time.time() * 1000),
        source="career-pivot.md",
        summary=result["summary"],
        next_action=result["next_action"],
        reasoning=result.get("reasoning", ""),
        proposed_stage=result["proposed_stage"],
        proposed_milestones=json.dumps(result["proposed_milestones"]),
    )
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)
    return snapshot


def apply_snapshot(session: Session, snapshot_id: int) -> ContextSnapshot:
    snapshot = session.get(ContextSnapshot, snapshot_id)
    if snapshot is None or snapshot.applied:
        raise ValueError("snapshot not found or already applied")

    now = int(time.time() * 1000)

    metrics = session.get(Metrics, 1) or Metrics(id=1)
    metrics.stages_complete = snapshot.proposed_stage
    metrics.updated_at = now
    session.add(metrics)

    proposed = json.loads(snapshot.proposed_milestones)
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
