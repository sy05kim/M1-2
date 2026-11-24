# Test results (2026-11-24)

- Local source archive: 10 unit/mock integration tests passed using Python unittest.
- Scope: summary statistics, Pydantic validation, R&D prompt, authenticated CRUD, conversation storage/reload/deletion, mocked AI chat with context injection and auto-save.
- Syntax: Python compileall passed, JavaScript syntax check and static Vercel build passed.
- Historical user-confirmed local results: 1,561 SECOM records in Firestore, data summary HTTP 200, working chart.
- **NOT YET VERIFIED:** live OpenAI request, actual conversation writes to user's Firestore, Render deployment, Vercel deployment.
- Mocked API tests never call the real model and do not guarantee real integrations.
