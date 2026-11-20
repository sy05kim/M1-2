from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query, Depends
from firebase_admin import firestore
from models import DataPayload, DataUpdate
from security import require_token
from services.firestore_db import get_db
from services.data_summary import get_summary, invalidate_summary

router = APIRouter(prefix="/api/data", tags=["Data"], dependencies=[Depends(require_token)])


def as_row(snapshot):
    return {"id": snapshot.id, **snapshot.to_dict()}


@router.get("/summary")
def summary():
    return get_summary()


@router.get("")
def list_data(limit: int = Query(default=120, ge=1, le=2000)):
    docs = get_db().collection("data").order_by("recorded_at", direction=firestore.Query.DESCENDING).limit(limit).stream()
    return [as_row(d) for d in docs]


@router.post("", status_code=201)
def create_data(payload: DataPayload):
    now = datetime.now(timezone.utc).isoformat()
    row = payload.model_dump(mode="json")
    row.update({"recorded_at": f"{row['date']}T00:00:00", "created_at": now, "updated_at": now})
    ref = get_db().collection("data").document()
    ref.set(row)
    invalidate_summary()
    return {"id": ref.id, **row}


@router.put("/{item_id}")
def update_data(item_id: str, payload: DataUpdate):
    ref = get_db().collection("data").document(item_id)
    snap = ref.get()
    if not snap.exists:
        raise HTTPException(status_code=404, detail="Data not found")
    row = payload.model_dump(mode="json")
    # Preserve full SECOM timestamp if date wasn't changed.
    old = snap.to_dict()
    row["recorded_at"] = old.get("recorded_at") if old.get("date") == row["date"] else f"{row['date']}T00:00:00"
    row["updated_at"] = datetime.now(timezone.utc).isoformat()
    ref.update(row)
    invalidate_summary()
    return {"id": item_id, **old, **row}


@router.delete("/{item_id}")
def delete_data(item_id: str):
    ref = get_db().collection("data").document(item_id)
    if not ref.get().exists:
        raise HTTPException(status_code=404, detail="Data not found")
    ref.delete()
    invalidate_summary()
    return {"deleted": True, "id": item_id}
