import time

from sqlmodel import Session, select

from api.models.models import ArchivedContextItem


def list_archived_items(session: Session) -> list[ArchivedContextItem]:
    return session.exec(
        select(ArchivedContextItem).order_by(ArchivedContextItem.archived_at.desc())
    ).all()


def archive_item(session: Session, text: str, source: str, snapshot_id: int | None) -> ArchivedContextItem:
    item = ArchivedContextItem(
        text=text,
        source=source,
        snapshot_id=snapshot_id,
        archived_at=int(time.time() * 1000),
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def unarchive_item(session: Session, item_id: int) -> None:
    item = session.get(ArchivedContextItem, item_id)
    if item is None:
        raise ValueError("archived item not found")
    session.delete(item)
    session.commit()
