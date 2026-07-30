import json
import time

from fastapi import APIRouter, Depends
from sqlmodel import Session

from api.auth import require_admin
from api.db.database import get_session
from api.models.models import Session as SessionModel, SessionCreate

router = APIRouter()


@router.post("/api/log", dependencies=[Depends(require_admin)])
def create_log(payload: SessionCreate, session: Session = Depends(get_session)):
    entry = SessionModel(
        date=payload.date,
        type=json.dumps(payload.type),
        notes=payload.notes,
        commits=payload.commits,
        level=payload.level,
        created_at=int(time.time() * 1000),
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return {"id": entry.id, "date": entry.date}
