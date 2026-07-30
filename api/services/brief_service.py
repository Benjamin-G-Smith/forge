import json
import time
from datetime import date, timedelta

from sqlmodel import Session, select

from api.models.models import Brief, Session as SessionModel
from chain.morning_brief import generate_brief


def generate_and_save_brief(session: Session) -> Brief:
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    yesterday_session = session.exec(
        select(SessionModel).where(SessionModel.date == yesterday)
    ).first()

    session_dict = (
        {
            "date": yesterday_session.date,
            "type": json.loads(yesterday_session.type),
            "notes": yesterday_session.notes,
            "level": yesterday_session.level,
        }
        if yesterday_session
        else None
    )

    result = generate_brief(session_dict)

    brief = Brief(
        date=date.today().isoformat(),
        summary=result["summary"],
        focus=result["focus"],
        research=json.dumps(result["research"]),
        generated_at=int(time.time() * 1000),
    )
    session.add(brief)
    session.commit()
    session.refresh(brief)
    return brief
