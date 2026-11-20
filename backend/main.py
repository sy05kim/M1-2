from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import origins
from routers import chat, conversations, data

app = FastAPI(title="SECOM Process R&D AI Assistant", version="1.0.0", description="Firestore 기반 반도체 공정 R&D 데이터 분석 AI 학습 서비스")
app.add_middleware(
    CORSMiddleware, allow_origins=origins(), allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Access-Token"],
)
app.include_router(data.router)
app.include_router(conversations.router)
app.include_router(chat.router)


@app.get("/api/health", tags=["Health"])
def health():
    return {"status": "ok", "message": "서버가 실행 중입니다. /docs에서 API 문서를 확인하세요."}
