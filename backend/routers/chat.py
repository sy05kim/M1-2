"""Context injection from the same summarization service used by GET /api/data/summary."""
import logging
import os
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from openai import OpenAI
from config import MODEL
from models import ChatRequest
from security import require_token
from services.data_summary import get_summary
from services.research_prompt import system_context
from services.firestore_db import get_db

router = APIRouter(prefix="/api/chat", tags=["Chat"], dependencies=[Depends(require_token)])
logger = logging.getLogger(__name__)




@router.post("")
def chat(payload: ChatRequest):
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY is not configured")
    db = get_db()
    col = db.collection("conversations")
    ref = col.document(payload.conversation_id) if payload.conversation_id else col.document()
    existing = ref.get() if payload.conversation_id else None
    if payload.conversation_id and (existing is None or not existing.exists):
        raise HTTPException(status_code=404, detail="Conversation not found")
    previous = (existing.to_dict().get("messages") or []) if existing else []
    if len(previous) >= 100:
        raise HTTPException(status_code=422, detail="대화가 너무 길어졌습니다. 새 대화를 시작해 주세요.")
    previous = [{"role": m["role"], "content": m["content"]} for m in previous[-12:]
                if m.get("role") in ("user", "assistant") and isinstance(m.get("content"), str)]
    prompt_messages = previous + [{"role": "user", "content": payload.question}]
    data_summary = get_summary()
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=25.0, max_retries=1)
        response = client.responses.create(
            model=MODEL, instructions=system_context(data_summary), input=prompt_messages,
            max_output_tokens=400, store=False,
        )
        answer = response.output_text.strip()
        if not answer:
            raise ValueError("Empty model response")
    except Exception:
        logger.exception("OpenAI request failed")
        raise HTTPException(status_code=502, detail="AI response failed; check model/key/quota on the server")
    ts = datetime.now(timezone.utc).isoformat()
    saved_messages = (existing.to_dict().get("messages") or []) if existing else []
    saved_messages += [{"role": "user", "content": payload.question}, {"role": "assistant", "content": answer}]
    if existing:
        ref.update({"messages": saved_messages, "updated_at": ts})
    else:
        ref.set({"title": payload.question[:60], "messages": saved_messages,
                 "created_at": ts, "updated_at": ts})
    return {"answer": answer, "conversation_id": ref.id, "summary_used": data_summary,
            "message_count": len(saved_messages)}
