import json

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from api.auth import require_admin
from api.db.database import get_session
from api.models.models import (
    ApplySnapshotRequest,
    Brief,
    CompleteItemRequest,
    Metrics,
    Milestone,
    ProjectSnapshot,
    Session as SessionModel,
)
from api.services.project_service import (
    apply_project_snapshot,
    complete_up_next_item,
    get_latest_snapshot,
    refresh_project,
    vault_last_active_ms,
)
from chain.morning_brief import ROADMAP
from chain.projects import PROJECTS

router = APIRouter()


def _card(config: dict, snapshot: ProjectSnapshot | None, stages_complete: int | None = None) -> dict:
    card = {
        "id": config["id"],
        "name": config["name"],
        "subtitle": config["subtitle"],
        "icon": config["icon"],
        "accent": config["accent"],
        "flagship": config["flagship"],
        "status": snapshot.status if snapshot else "Warm",
        "focus_meta": snapshot.focus_meta if snapshot else "Not synced yet",
        "stats": json.loads(snapshot.stats) if snapshot else [],
        "last_active": vault_last_active_ms(config["id"]),
        "synced": snapshot is not None,
    }
    if config["flagship"] and stages_complete is not None:
        card["stage_progress"] = {"complete": stages_complete, "total": len(ROADMAP)}
    return card


def _roadmap(stages_complete: int) -> list[dict]:
    steps = []
    for r in ROADMAP:
        if r["stage"] <= stages_complete:
            state = "done"
        elif r["stage"] == stages_complete + 1:
            state = "current"
        else:
            state = "todo"
        steps.append({"label": r["title"], "date": r["target"], "state": state})
    return steps


@router.get("/api/projects")
def list_projects(session: Session = Depends(get_session)):
    metrics = session.get(Metrics, 1) or Metrics(id=1)
    return [
        _card(
            config,
            get_latest_snapshot(session, config["id"]),
            stages_complete=metrics.stages_complete if config["flagship"] else None,
        )
        for config in PROJECTS
    ]


@router.get("/api/projects/{project_id}")
def get_project(project_id: str, session: Session = Depends(get_session)):
    config = next((p for p in PROJECTS if p["id"] == project_id), None)
    if config is None:
        raise HTTPException(status_code=404, detail="project not found")

    snapshot = get_latest_snapshot(session, project_id)
    card = _card(config, snapshot)

    if snapshot is None:
        detail = {
            **card,
            "snapshot_id": None,
            "focus": "Not synced yet.",
            "focus_meta": "",
            "up_next": [],
            "progress": [],
            "proposed_stage": None,
            "proposed_milestones": None,
            "applied": True,
        }
    else:
        completed_up_next = json.loads(snapshot.completed_up_next)
        progress = [item["title"] for item in completed_up_next] + json.loads(snapshot.progress)
        detail = {
            **card,
            "snapshot_id": snapshot.id,
            "focus": snapshot.focus,
            "focus_meta": snapshot.focus_meta,
            "up_next": json.loads(snapshot.up_next),
            "progress": progress,
            "proposed_stage": snapshot.proposed_stage,
            "proposed_milestones": (
                json.loads(snapshot.proposed_milestones) if snapshot.proposed_milestones else None
            ),
            "applied": snapshot.applied,
        }

    if config["flagship"]:
        sessions = session.exec(
            select(SessionModel).order_by(SessionModel.date.desc()).limit(200)
        ).all()
        metrics = session.get(Metrics, 1) or Metrics(id=1)
        milestones = session.exec(select(Milestone)).all()
        latest_brief = session.exec(select(Brief).order_by(Brief.date.desc()).limit(1)).first()

        detail["roadmap"] = _roadmap(metrics.stages_complete)
        detail["log"] = [
            {
                "id": s.id,
                "date": s.date,
                "type": json.loads(s.type),
                "notes": s.notes,
                "commits": s.commits,
                "level": s.level,
            }
            for s in sessions
        ]
        detail["metrics"] = {
            "projects_shipped": metrics.projects_shipped,
            "applications_sent": metrics.applications_sent,
            "stages_complete": metrics.stages_complete,
        }
        detail["milestones"] = [
            {"key": m.key, "completed": m.completed, "completed_at": m.completed_at}
            for m in milestones
        ]
        detail["brief"] = (
            {
                "date": latest_brief.date,
                "summary": latest_brief.summary,
                "focus": latest_brief.focus,
                "research": json.loads(latest_brief.research or "[]"),
            }
            if latest_brief
            else None
        )

    return detail


@router.post("/api/projects/{project_id}/refresh", dependencies=[Depends(require_admin)])
def refresh(project_id: str, session: Session = Depends(get_session)):
    if project_id not in {p["id"] for p in PROJECTS}:
        raise HTTPException(status_code=404, detail="project not found")
    refresh_project(session, project_id)
    return get_project(project_id, session)


@router.post("/api/projects/{project_id}/apply", dependencies=[Depends(require_admin)])
def apply(project_id: str, payload: ApplySnapshotRequest, session: Session = Depends(get_session)):
    try:
        apply_project_snapshot(session, payload.snapshot_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return get_project(project_id, session)


@router.post("/api/projects/{project_id}/complete-item", dependencies=[Depends(require_admin)])
def complete_item(
    project_id: str, payload: CompleteItemRequest, session: Session = Depends(get_session)
):
    try:
        complete_up_next_item(session, project_id, payload.index)
    except (ValueError, IndexError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    return get_project(project_id, session)
