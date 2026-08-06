"""Save-for-later archive endpoints. Not currently wired into the UI (retired
along with the old single-goal Context Sync feature) but left in place since
the underlying data model still works standalone — see ArchivedContextItem.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from api.auth import require_admin
from api.db.database import get_session
from api.models.models import ArchivedContextItem, ArchiveItemCreate
from api.services.context_service import archive_item, list_archived_items, unarchive_item

router = APIRouter()


def _serialize_archived(a: ArchivedContextItem) -> dict:
    return {
        "id": a.id,
        "text": a.text,
        "source": a.source,
        "snapshot_id": a.snapshot_id,
        "archived_at": a.archived_at,
    }


@router.get("/api/context/archive")
def get_archived_items(session: Session = Depends(get_session)):
    return [_serialize_archived(a) for a in list_archived_items(session)]


@router.post("/api/context/archive", dependencies=[Depends(require_admin)])
def post_archive_item(payload: ArchiveItemCreate, session: Session = Depends(get_session)):
    item = archive_item(session, payload.text, payload.source, payload.snapshot_id)
    return _serialize_archived(item)


@router.delete("/api/context/archive/{item_id}", dependencies=[Depends(require_admin)])
def delete_archived_item(item_id: int, session: Session = Depends(get_session)):
    try:
        unarchive_item(session, item_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="archived item not found")
    return {"ok": True}
