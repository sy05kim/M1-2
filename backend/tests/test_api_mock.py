"""FastAPI routing tests with mocked Firestore/OpenAI. No paid or live requests."""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from main import app
from routers import data, conversations, chat
from services import firestore_db, data_summary

class Snap:
    def __init__(self, key, value):
        self.id, self.value, self.exists = key, value, value is not None
    def to_dict(self): return dict(self.value or {})
    def get(self, key): return (self.value or {}).get(key)

class Doc:
    def __init__(self, db, name, key):
        self.db, self.name, self.id = db, name, key
    def get(self): return Snap(self.id, self.db.items[self.name].get(self.id))
    def set(self, x): self.db.items[self.name][self.id] = dict(x)
    def update(self, x): self.db.items[self.name][self.id].update(x)
    def delete(self): self.db.items[self.name].pop(self.id, None)

class Coll:
    def __init__(self, db, name, rows=None):
        self.db, self.name, self.rows = db, name, rows
    def document(self, key=None):
        if key is None:
            self.db.n += 1
            key = str(self.db.n)
        return Doc(self.db, self.name, key)
    def order_by(self, key, direction=None):
        rows = sorted(self.db.items[self.name].items(), key=lambda x: x[1].get(key, ""), reverse=True)
        return Coll(self.db, self.name, rows)
    def limit(self, n):
        return Coll(self.db, self.name, (self.rows if self.rows is not None else list(self.db.items[self.name].items()))[:n])
    def stream(self):
        return iter(Snap(k, v) for k, v in (self.rows if self.rows is not None else self.db.items[self.name].items()))

class DB:
    def __init__(self):
        self.items = {"data": {}, "conversations": {}}
        self.n = 0
    def collection(self, name): return Coll(self, name)

class FakeOpenAI:
    last_kwargs = None
    def __init__(self, **kwargs): self.responses = self
    def create(self, **kwargs):
        FakeOpenAI.last_kwargs = kwargs
        return type("Response", (), {"output_text": "관찰: 통계 확인. 가능한 가설: 조건 차이. 추가 검증: 변수 비교."})()

class APITests(unittest.TestCase):
    def setUp(self):
        self.db = DB()
        self.patches = [
            patch.dict(os.environ, {"APP_ACCESS_TOKEN": "mock-token", "OPENAI_API_KEY": "mock-key"}),
            patch.object(firestore_db, "get_db", return_value=self.db),
            patch.object(data, "get_db", return_value=self.db),
            patch.object(conversations, "get_db", return_value=self.db),
            patch.object(chat, "get_db", return_value=self.db),
            patch.object(chat, "OpenAI", FakeOpenAI),
        ]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)
        data_summary.invalidate_summary()
        self.client = TestClient(app)
        self.h = {"X-Access-Token": "mock-token"}
    def test_health_docs_and_auth(self):
        self.assertEqual(self.client.get("/api/health").status_code, 200)
        self.assertEqual(self.client.get("/docs").status_code, 200)
        self.assertEqual(self.client.get("/api/data/summary").status_code, 401)
        self.assertEqual(self.client.get("/api/data/summary", headers=self.h).status_code, 200)
    def test_data_crud(self):
        payload = {"date": "2008-09-01", "value": 3014.5, "memo": "test", "quality_label": -1}
        r = self.client.post("/api/data", json=payload, headers=self.h)
        self.assertEqual(r.status_code, 201, r.text)
        key = r.json()["id"]
        self.assertEqual(len(self.client.get("/api/data", headers=self.h).json()), 1)
        payload["value"] = 3100
        self.assertEqual(self.client.put(f"/api/data/{key}", json=payload, headers=self.h).status_code, 200)
        self.assertEqual(self.client.get("/api/data/summary", headers=self.h).json()["metrics"]["average"], 3100)
        self.assertEqual(self.client.delete(f"/api/data/{key}", headers=self.h).status_code, 200)
    def test_conversation_persistence(self):
        r = self.client.post("/api/conversations", headers=self.h, json={"title": "연구", "messages": [{"role":"user", "content":"안녕"}]})
        self.assertEqual(r.status_code, 201, r.text)
        key = r.json()["id"]
        self.assertEqual(self.client.get("/api/conversations", headers=self.h).json()[0]["message_count"], 1)
        self.assertEqual(self.client.get(f"/api/conversations/{key}", headers=self.h).json()["messages"][0]["content"], "안녕")
        self.assertEqual(self.client.delete(f"/api/conversations/{key}", headers=self.h).status_code, 200)
    def test_mocked_ai_context_and_autosave(self):
        r = self.client.post("/api/chat", headers=self.h, json={"question": "최근 추세는?"})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["message_count"], 2)
        self.assertIn("추가 검증", FakeOpenAI.last_kwargs["instructions"])
        self.assertEqual(len(self.db.items["conversations"]), 1)
