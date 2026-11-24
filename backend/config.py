"""Load server-side configuration. Never expose these values in frontend code."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(
    dotenv_path=Path(__file__).resolve().parent / ".env",
    override=False
)



def origins() -> list[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "http://127.0.0.1:5500,http://localhost:5500,http://localhost:8001,http://127.0.0.1:8001")
    return [item.strip().rstrip("/") for item in raw.split(",") if item.strip()]


MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
