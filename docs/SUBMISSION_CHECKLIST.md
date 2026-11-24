# M1-2 final submission checklist

**Project:** Semiconductor Process R&D AI Assistant (UCI SECOM, 2008 data)

## Evidence required
- [x] FastAPI local Swagger confirmed, summary HTTP 200, 1,561 valid sensor measurements confirmed (prior user-run tests)
- [ ] Live GPT request grounded in the Firestore summary; capture question + answer + summary
- [ ] Real Firestore data CRUD create or edit, displayed in UI; avoid altering the 1,561 originals (delete temporary test item)
- [ ] Conversation save, list and reload, captured from the UI
- [ ] Render deployed and `https://.../docs` verified
- [ ] Vercel deployed, linked to Render API, final URL verified
- [ ] Update README URLs and attach screenshots: chat, CRUD, conversation history, Swagger
- [ ] Check GitHub does NOT contain `.env`, `serviceAccountKey.json`, access token or SECOM raw data

## Deployment setup
Render Web Service: root `backend`; build `pip install -r requirements.txt`; start `uvicorn main:app --host 0.0.0.0 --port $PORT`.

Render secret environment variables:
`OPENAI_API_KEY`, `OPENAI_MODEL`, `FIREBASE_SERVICE_ACCOUNT_JSON`, `APP_ACCESS_TOKEN`, `ALLOWED_ORIGINS`.

Vercel: root `frontend`, framework Other, `API_BASE_URL` is the public Render HTTPS URL; build from `vercel.json`. Set `ALLOWED_ORIGINS` to the final Vercel origin and redeploy Render.

No secret key belongs in GitHub or browser JavaScript. ChatGPT Plus subscriptions do not pay for API calls; billing is separate.

## Presentation (approx. 40 seconds)
"I developed a semiconductor process R&D assistant using publicly available SECOM inspection data. I stored 1,561 valid measurements in Firestore and use FastAPI to calculate statistics, trends, and variation. The backend passes the summary as context to GPT so the assistant can distinguish observed findings from possible hypotheses and further tests. The interface includes data editing and past conversations. Because the underlying variables are anonymous and historical, the project does not identify real fault causes or prove process optimization."

## Final URLs
- Frontend Vercel: NOT DEPLOYED
- Backend Render: NOT DEPLOYED
- Swagger: NOT DEPLOYED

See README for detailed execution instructions and caveats.
