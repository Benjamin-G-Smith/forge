import time

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from api.auth import require_admin
from api.db.database import get_session
from api.models.models import Metrics, MetricsUpdate, Milestone, MilestoneUpdate

router = APIRouter()


@router.patch("/api/metrics", dependencies=[Depends(require_admin)])
def update_metrics(payload: MetricsUpdate, session: Session = Depends(get_session)):
    metrics = session.get(Metrics, 1)
    if metrics is None:
        metrics = Metrics(id=1)
        session.add(metrics)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(metrics, field, value)
    metrics.updated_at = int(time.time() * 1000)

    session.add(metrics)
    session.commit()
    session.refresh(metrics)
    return metrics


@router.patch("/api/milestones/{key}", dependencies=[Depends(require_admin)])
def update_milestone(
    key: str, payload: MilestoneUpdate, session: Session = Depends(get_session)
):
    milestone = session.get(Milestone, key)
    if milestone is None:
        milestone = Milestone(key=key)

    milestone.completed = payload.completed
    milestone.completed_at = int(time.time() * 1000) if payload.completed else None

    session.add(milestone)
    session.commit()
    session.refresh(milestone)
    return milestone
