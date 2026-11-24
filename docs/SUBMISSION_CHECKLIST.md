# M1-2 final submission checklist

**Project:** Semiconductor Process R&D AI Assistant (UCI SECOM, 2008 data)

## Evidence required
- [x] FastAPI local Swagger confirmed, summary HTTP 200, 1,561 valid sensor measurements confirmed (prior user-run tests)
- [ ] Live GPT request grounded in the Firestore summary; capture question + answer + summary
- [ ] Real Firestore data CRUD create or edit, displayed in UI; avoid altering the 1,561 originals (delete temporary test item)
- [ ] Conversation save, list and reload, captured from the UI
- [x] Render backend deployed Live: https://m1-2-secom-rnd-api.onrender.com (user observed `/api/health` 200)
- [x] Vercel frontend Git deployment READY; production alias assigned (2026-11-24)\n- [x] Vercel `API_BASE_URL` set to Render origin and rebuilt READY; user confirmed 1,561 records and chart in deployed frontend\n- [ ] Actual AI reply and conversation-history persistence on deployed site (Gemini API key required)
- [ ] Update README URLs and attach screenshots: chat, CRUD, conversation history, Swagger
- [ ] Check GitHub does NOT contain `.env`, `serviceAccountKey.json`, access token or SECOM raw data

## Deployment setup
Render Web Service: root `backend`; build `pip install -r requirements.txt`; start `uvicorn main:app --host 0.0.0.0 --port $PORT`.

Render secret environment variables:
`GEMINI_API_KEY` (free-tier option), `GEMINI_MODEL` (optional), `OPENAI_API_KEY` (optional), `OPENAI_MODEL` (optional), `FIREBASE_SERVICE_ACCOUNT_JSON`, `APP_ACCESS_TOKEN`, `ALLOWED_ORIGINS`.

Vercel: root `frontend`, framework Other, `API_BASE_URL` is the public Render HTTPS URL; build from `vercel.json`. Set `ALLOWED_ORIGINS` to the final Vercel origin and redeploy Render.

No secret key belongs in GitHub or browser JavaScript. ChatGPT Plus subscriptions do not pay for API calls; billing is separate.

## Presentation (approx. 40 seconds)
"I developed a semiconductor process R&D assistant using publicly available SECOM inspection data. I stored 1,561 valid measurements in Firestore and use FastAPI to calculate statistics, trends, and variation. The backend passes the summary as context to GPT so the assistant can distinguish observed findings from possible hypotheses and further tests. The interface includes data editing and past conversations. Because the underlying variables are anonymous and historical, the project does not identify real fault causes or prove process optimization."

## Final URLs
- Frontend Vercel (READY; backend data and chart verified): https://m1-2-secom-rnd-ai.vercel.app
- Backend Render: https://m1-2-secom-rnd-api.onrender.com
- Swagger: https://m1-2-secom-rnd-api.onrender.com/docs

See README for detailed execution instructions and caveats.
