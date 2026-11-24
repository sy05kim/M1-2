"""Initialize Firestore lazily, allowing Swagger/health before credentials are set."""
import json
import os
from functools import lru_cache
from pathlib import Path

from config import BASE_DIR  # Resolve backend/.env when scripts run from anywhere

import firebase_admin
from firebase_admin import credentials, firestore


@lru_cache(maxsize=1)
def get_db():
    if not firebase_admin._apps:
        key_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
        key_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "").strip()
        if key_json:
            try:
                info = json.loads(key_json)
            except json.JSONDecodeError as exc:
                raise RuntimeError("FIREBASE_SERVICE_ACCOUNT_JSON is not valid JSON") from exc
            cred = credentials.Certificate(info)
        elif key_path:
            path = Path(key_path).expanduser()
            if not path.is_absolute():
                path = BASE_DIR / path
            if not path.is_file():
                raise RuntimeError(f"Firebase key file not found: {path.name} in backend/")
            cred = credentials.Certificate(str(path))
        else:
            raise RuntimeError("Set FIREBASE_SERVICE_ACCOUNT_JSON or FIREBASE_SERVICE_ACCOUNT_PATH")
        firebase_admin.initialize_app(cred)
    return firestore.client()
