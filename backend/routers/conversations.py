from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from models import ConversationCreate
from security import require_token
from services.firestore_db import get_db

router = APIRouter(prefix="/api/conversations", tags=["Conversations"], dependencies=[Depends(require_token)])


def now():
    return datetime.now(timezone.utc).isoformat()


@router.post("", status_code=201)
def create_conversation(payload: ConversationCreate):
    timestamp = now()
    row = {"title": payload.title or "새 대화", "messages": [m.model_dump() for m in payload.messages],
           "created_at": timestamp, "updated_at": timestamp}
    ref = get_db().collection("conversations").document()
    ref.set(row)
    return {"id": ref.id, **row}


@router.get("")
def list_conversations():
    docs = get_db().collection("conversations").order_by("updated_at", direction="DESCENDING").limit(100).stream()
    return [{"id": d.id, "title": d.get("title"), "updated_at": d.get("updated_at"),
             "message_count": len(d.get("messages") or [])} for d in docs]


@router.get("/{conversation_id}")
def get_conversation(conversation_id: str):
    doc = get_db().collection("conversations").document(conversation_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"id": doc.id, **doc.to_dict()}


@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: str):
    ref = get_db().collection("conversations").document(conversation_id)
    if not ref.get().exists:
        raise HTTPException(status_code=404, detail="Conversation not found")
    ref.delete()
    return {"deleted": True, "id": conversation_id}
