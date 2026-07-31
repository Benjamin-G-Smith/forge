import json

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from api.auth import require_admin
from api.db.database import get_session
from api.models.models import ContextSnapshot
from api.services.context_service import apply_snapshot, generate_and_save_snapshot

router = APIRouter()


def _serialize(s: ContextSnapshot) -> dict:
    return {
        "id": s.id,
        "created_at": s.created_at,
        "source": s.source,
        "summary": s.summary,
        "next_action": s.next_action,
        "reasoning": s.reasoning,
        "proposed_stage": s.proposed_stage,
        "proposed_milestones": json.loads(s.proposed_milestones),
        "applied": s.applied,
        "applied_at": s.applied_at,
    }


@router.get("/api/context")
def get_context(session: Session = Depends(get_session)):
    latest = session.exec(
        select(ContextSnapshot).order_by(ContextSnapshot.created_at.desc()).limit(1)
    ).first()
    return _serialize(latest) if latest else None


@router.post("/api/context/refresh", dependencies=[Depends(require_admin)])
def refresh_context(session: Session = Depends(get_session)):
    snapshot = generate_and_save_snapshot(session)
    return _serialize(snapshot)


@router.post("/api/context/{snapshot_id}/apply", dependencies=[Depends(require_admin)])
def apply_context(snapshot_id: int, session: Session = Depends(get_session)):
    try:
        snapshot = apply_snapshot(session, snapshot_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="snapshot not found or already applied")
    return _serialize(snapshot)
