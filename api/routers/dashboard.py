import json

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from api.db.database import get_session
from api.models.models import Brief, ContextSnapshot, Metrics, Milestone, Session as SessionModel

router = APIRouter()


@router.get("/api/dashboard")
def get_dashboard(session: Session = Depends(get_session)):
    sessions = session.exec(
        select(SessionModel).order_by(SessionModel.date.desc()).limit(200)
    ).all()
    metrics = session.get(Metrics, 1) or Metrics(id=1)
    milestones = session.exec(select(Milestone)).all()
    latest_brief = session.exec(
        select(Brief).order_by(Brief.date.desc()).limit(1)
    ).first()
    latest_context = session.exec(
        select(ContextSnapshot).order_by(ContextSnapshot.created_at.desc()).limit(1)
    ).first()

    return {
        "log": [
            {
                "id": s.id,
                "date": s.date,
                "type": json.loads(s.type),
                "notes": s.notes,
                "commits": s.commits,
                "level": s.level,
            }
            for s in sessions
        ],
        "metrics": {
            "projects_shipped": metrics.projects_shipped,
            "applications_sent": metrics.applications_sent,
            "stages_complete": metrics.stages_complete,
        },
        "milestones": [
            {"key": m.key, "completed": m.completed, "completed_at": m.completed_at}
            for m in milestones
        ],
        "brief": (
            {
                "date": latest_brief.date,
                "summary": latest_brief.summary,
                "focus": latest_brief.focus,
                "research": json.loads(latest_brief.research or "[]"),
            }
            if latest_brief
            else None
        ),
        "context": (
            {
                "id": latest_context.id,
                "created_at": latest_context.created_at,
                "source": latest_context.source,
                "summary": latest_context.summary,
                "next_action": latest_context.next_action,
                "reasoning": latest_context.reasoning,
                "proposed_stage": latest_context.proposed_stage,
                "proposed_milestones": json.loads(latest_context.proposed_milestones),
                "applied": latest_context.applied,
                "applied_at": latest_context.applied_at,
            }
            if latest_context
            else None
        ),
    }
