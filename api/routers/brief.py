import json

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from api.auth import require_admin
from api.db.database import get_session
from api.models.models import Brief
from api.services.brief_service import generate_and_save_brief

router = APIRouter()


@router.get("/api/brief")
def get_brief(session: Session = Depends(get_session)):
    latest = session.exec(select(Brief).order_by(Brief.date.desc()).limit(1)).first()
    if latest is None:
        return None
    return {
        "date": latest.date,
        "summary": latest.summary,
        "focus": latest.focus,
        "research": json.loads(latest.research or "[]"),
    }


@router.post("/api/brief/generate", dependencies=[Depends(require_admin)])
def generate(session: Session = Depends(get_session)):
    brief = generate_and_save_brief(session)
    return {
        "date": brief.date,
        "summary": brief.summary,
        "focus": brief.focus,
        "research": json.loads(brief.research or "[]"),
    }
