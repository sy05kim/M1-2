# M1-2: 반도체 공정 R&D 데이터 분석 AI 비서

> **상태 (2026-11-24)**: 사용자 실습으로 로컬 Firestore 데이터 1,561건 조회, Swagger 200, 대시보드 그래프가 확인됨. **Render 백엔드 및 Vercel 프론트엔드 배포 완료; 공개 웹에서 Firestore 데이터 1,561건과 그래프 확인(사용자 화면). 실제 AI 응답은 아직 미검증.**

## 시작하기 (처음 실행하는 사람을 위한 안내)

**첫 번째 목표는 API 키를 연결하는 것이 아니라 FastAPI 서버를 실행해 `/docs`를 보는 것입니다.**
자세한 실행 안내: **[START_HERE.md](START_HERE.md)**. 필수 증빙: **[제출 체크리스트](docs/SUBMISSION_CHECKLIST.md)**. 기존 PC에서 설치 완료라면 프로젝트 폴더의 `RUN_LOCAL.bat`을 더블클릭해 서버 두 개를 실행할 수 있습니다.

진행 순서: ① 코드 실행/테스트 → ② Firebase 연결 → ③ SECOM 원본 수집/가져오기 →
④ GPT 채팅 확인 → ⑤ Vercel/Render 배포 → ⑥ 제출 스크린샷 촬영.

## 서비스 소개

M1-1의 [UCI SECOM 반도체 제조 공정 분석](https://github.com/sy05kim/M1-1)을 확장해,
공정 측정 데이터의 기간/개수/평균/최대/최소/최근 추세/변동성/이상치 후보를 보여주고,
**관찰(근거) → 가능한 가설 → 추가 검증 제안**을 구분하는 R&D 연구 보조 채팅을 제공하는 학습용 웹 서비스입니다.
주별 품질 판정률은 참고 지표로만 사용합니다. **공정 조건 최적화 성과를 입증한 서비스가 아닙니다.**

**R&D 데이터 해석 주의**: `sensor_001`은 실제 물리 단위/공정 의미가 공개되지 않은 익명 변수입니다.
검사 시각은 연속 센서 데이터와 다르며, 이상치와 불량 원인의 인과성을 단정할 수 없습니다.
이 서비스는 실제 공정 제어 시스템이 아닙니다.

## 기술 스택

- Backend: Python 3.10+, FastAPI, Pydantic, Uvicorn
- Database: Firebase Firestore (`data`, `conversations`)
- AI: Google Gemini API (`GEMINI_MODEL`, 기본 `gemini-2.5-flash-lite`, 무료 등급 제공) 또는 OpenAI Responses API (`OPENAI_MODEL`, 기본 `gpt-4.1-mini`). `GEMINI_API_KEY`가 있으면 Gemini를 우선 사용합니다.
- Frontend: HTML / CSS / JavaScript (프레임워크 없음; SVG 그래프)
- Deployment: Backend Render, Frontend Vercel

## 설계와 폴더

```
M1-2_SECOM_RND_AI/
├── backend/
│   ├── main.py                 # FastAPI + CORS + Swagger
│   ├── config.py               # 환경 변수
│   ├── security.py             # 비공개 접근 토큰
│   ├── models.py               # Pydantic 요청 검증
│   ├── routers/                # data / conversations / chat
│   ├── services/               # Firestore 연결 / 요약 통계 / R&D 프롬프트
│   ├── scripts/                # SECOM 가져오기 / 데모 데이터
│   ├── tests/
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── public/                 # 순수 HTML, CSS, JS 소스
│   ├── build.js                # Vercel 빌드 시 공개 API URL 삽입
│   └── vercel.json
└── README.md
```

데이터 경로: Firestore `data` 컬렉션 하나에 `{date, recorded_at, value, memo, quality_label}` 저장.
`quality_label`은 선택 사항(`-1=정상`, `1=불량`)입니다. `date,value,memo`는 기본 필드입니다.
대화 경로: Firestore `conversations` 컬렉션에 `{title, messages, created_at, updated_at}` 저장.

## 1. 로컬 백엔드 실행 (Windows VS Code PowerShell)

1. Python 3.10 이상을 준비합니다. **첫 `/docs` 실행에는 Firebase/OpenAI 키가 필요 없습니다.** 기능 테스트 전에 준비하세요.
2. `backend` 디렉터리에서:

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

3. `.env`에 실제 키를 설정합니다.
   - Firebase 콘솔 → 프로젝트 설정 → 서비스 계정 → 새 비공개 키 생성.
   - 생성한 JSON 파일을 **`backend/serviceAccountKey.json`**에 저장. **절대로 GitHub에 업로드하지 마세요.**
   - `FIREBASE_SERVICE_ACCOUNT_PATH=./serviceAccountKey.json`으로 설정.
   - `OPENAI_API_KEY`와 **임의의 강한 비공개 `APP_ACCESS_TOKEN`**을 설정.
   - 처음 Swagger `/docs`만 확인할 때는 `.env` 설정 없이 실행할 수 있습니다.
   - `ALLOWED_ORIGINS`에 현재 프론트엔드 주소를 넣습니다.
4. 실행:

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

- Swagger: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/api/health
- API 인증: Swagger의 데이터/대화/채팅 요청에 `x-access-token` 헤더에 `.env`의 토큰 입력.

**주의**: 백엔드는 토큰이 없으면 데이터를 제공하지 않습니다(401/503). OpenAI 키는 브라우저에 노출되지 않습니다.

## 2. 기존 SECOM 실제 데이터 불러오기

기존 M1-1의 `data/raw/secom.data` 및 `secom_labels.data`를 `M1-2_SECOM_RND_AI/data/raw/`에 복사합니다.
M1-1 분석 파일의 품질 지표와 정확히 일치하는지 살피려면 1,567개의 원본 기록에서 결측 상태를 확인해야 합니다.

```powershell
# backend 폴더에서: 먼저 검증만 (DB 저장 없음)
python scripts/import_secom.py ../data/raw/secom.data ../data/raw/secom_labels.data

# 개수와 데이터 출처 확인 후 DB에 업로드
python scripts/import_secom.py ../data/raw/secom.data ../data/raw/secom_labels.data --confirm
```

대표 분석 변수 `sensor_001`는 **1,567건 중 결측 6건**이므로 값이 존재하는 **1,561개 관측치**를 저장합니다.
따라서 새 서비스에서 표시하는 `quality.fail_rate_pct`는 **가져온 1,561건 중 라벨 있는 표본에 대한 비율**이며,
M1-1의 원본 전체 불량률 **6.637% (104/1,567)** 와 다를 수 있습니다. 같은 원본을 비교할 때 분모를 구분하세요.

빠른 연습만 필요하다면 `python scripts/seed_demo.py --confirm`으로 **합성 데모 데이터** 120건을 추가할 수 있지만,
이는 실제 SECOM 값이 아닙니다. 실제 원본을 가져올 때 데모 레코드가 섞이지 않도록 Firestore에서 분리·삭제하세요.

## 3. 로컬 프론트엔드 실행

프론트는 빌드 도구가 필수는 아닙니다.

```powershell
cd ../frontend/public
Copy-Item config.example.js config.js
python -m http.server 8001
```

- 브라우저에서 http://localhost:8001
- 로컬 프론트 주소 `http://localhost:8001`가 백엔드 `ALLOWED_ORIGINS`에 있는지 확인하세요.
- 상단 입력창에 `.env`의 `APP_ACCESS_TOKEN`을 입력하면 데이터에 접근할 수 있습니다.
- `config.js`는 공개 API URL만 담습니다. 다른 비밀 키를 넣지 마세요.

## 4. API 목록 / 확인

| 기능 | HTTP | 주소 | 동작 |
|---|---|---|---|
| 데이터 추가 | POST | `/api/data` | date, value, memo, quality_label |
| 데이터 목록 | GET | `/api/data?limit=120` | 최신 자료 최대 120건 (최대 2000) |
| 데이터 수정 | PUT | `/api/data/{id}` | 기존 필드 전체 변경 |
| 데이터 삭제 | DELETE | `/api/data/{id}` | 데이터 삭제 |
| 데이터 요약 | GET | `/api/data/summary` | 기간/개수/통계/추세/변동성/불량률/주별 통계/IQR 이상치 |
| 대화 저장 | POST | `/api/conversations` | 대화 메시지 저장 |
| 대화 목록 | GET | `/api/conversations` | 최신 100개, 메시지는 미포함 |
| 대화 불러오기 | GET | `/api/conversations/{id}` | 전체 메시지 제공 (요구 사항 A) |
| 대화 삭제 | DELETE | `/api/conversations/{id}` | 대화 삭제 |
| AI 채팅 | POST | `/api/chat` | 컨텍스트 주입 + 자동 저장 |
| 헬스 | GET | `/api/health` | 연결 확인 (인증 불필요) |

모든 `/api/data`, `/api/conversations`, `/api/chat` 엔드포인트는 `X-Access-Token` 헤더가 필수입니다.

### 요금 없는 Gemini 채팅 연결\n\nGoogle AI Studio https://aistudio.google.com/apikey 에서 Gemini API 키를 발급받은 후 Render Environment에 `GEMINI_API_KEY`를 **비공개** 값으로 저장하고 재배포합니다. 기본 모델은 `gemini-2.5-flash-lite`이며 무료 등급은 사용량 제한이 있습니다. `OPENAI_API_KEY`는 없어도 됩니다. 기존 `/api/chat` 엔드포인트, 대화 이력 및 Firestore 컨텍스트 주입은 그대로입니다. 유료 모델로 자동 전환하거나 OpenAI 비용을 발생시키지 않습니다. Google 무료 등급 입력 데이터는 제품 개선에 사용될 수 있어 **공개 SECOM 요약 데이터 외 개인·기밀 데이터를 넣지 마세요.** 과제에서 GPT/OpenAI 모델 자체가 필수라면 모델 변경 사실을 제출 자료에 정확히 기재해야 합니다.\n\n### 요청 예시

`POST /api/data`:

```json
{"date":"2008-09-01","value":3014.5,"memo":"테스트 관측치","quality_label":-1}
```

`POST /api/chat`:

```json
{"question":"최근 추세와 평균은 어때?","conversation_id":null}
```

대화가 시작된 뒤 반환한 `conversation_id`를 다음 `/api/chat` 요청에 함께 보내면 기존 대화에 이어 붙습니다.

### 요약·컨텍스트 주입 원리

1. `/api/chat`이 `/api/data/summary`와 동일한 `get_summary()` 서비스를 실행.
2. 서비스가 Firestore `data`를 읽어 요약(`count`, `metrics`, `trend`, `variability`, `quality`, `weekly_quality`, `outliers`)을 계산.
3. `services/research_prompt.py`의 `system_context()`가 요약 JSON을 시스템 지침에 삽입. 공정 해석 요청이라면 관찰/가설/검증을 구분하도록 안내.
4. `GEMINI_API_KEY`가 있으면 Google Gemini OpenAI 호환 Chat Completions API, 없으면 OpenAI Responses API가 이전 12개 메시지와 새 질문을 처리합니다(OpenAI 경로는 `store=False`).
5. AI 응답과 사용자 질문을 Firestore `conversations`에 저장.
6. 프론트가 AI 답변과 대화 기록을 갱신.

API는 사용자 데이터 전체가 아닌 **요약 통계**만 모델에 전달합니다. 따라서 상세 사건 질문은 근거 부족을 고지합니다.
최근 추세는 **최근 20건 평균 vs 직전 20건 평균**을 비교하고, ±2% 이내는 유지로 봅니다.
이는 시간당 변화율이나 관리도 규칙이 아닙니다. 40건 미만이면 데이터 부족입니다.
변동성은 **최근 30건과 직전 30건의 모집단 표준편차**를 비교합니다(최소 60건). 변동성이 ±10% 이내면 *유지*로 표시하는 설명용 임계값이며, 공정 관리한계나 검증된 판단 기준이 아닙니다.

Firestore 요약은 서버 메모리에 **최대 5분 캐시**됩니다. 현재 서버 프로세스에서 CRUD하면 캐시가 무효화되며,
다른 관리도구에서 직접 변경한 경우 최대 5분 늦게 반영될 수 있습니다.

## 5. 테스트

```powershell
cd backend
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

이 테스트는 실제 비밀키 없이 통계·Pydantic·연구 프롬프트 로직을 검사합니다. 모의 Firestore 및 OpenAI를 사용하는 추가 API 통합 테스트는 로컬 최종점검 ZIP에 포함되며 테스트 10개가 통과했습니다.
실제 통합 테스트는 Firebase/Render/Vercel에 연결 후 아래 체크리스트로 별도 진행해야 합니다.

## 6. Render 백엔드 배포

1. 기존 GitHub 저장소 `https://github.com/sy05kim/M1-2`에 `M1-2_SECOM_RND_AI` 내용 업로드 (`.env`, 키 JSON, 원본 데이터 제외).
2. Render → New → Web Service → GitHub 저장소 선택.
3. **Root Directory**: `backend` (저장소 루트에 backend 폴더가 있을 때)
4. **Build Command**: `pip install -r requirements.txt`
5. **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. **Environment**에 다음을 등록:
   - `GEMINI_API_KEY`: Google AI Studio에서 무료 등급 키를 발급받아 설정 (비공개; 우선 사용)\n   - `GEMINI_MODEL`: `gemini-2.5-flash-lite` (선택사항)\n   - `OPENAI_API_KEY`: OpenAI API 개인 키 (선택사항, 비공개)
   - `OPENAI_MODEL`: 사용할 Responses API 호환 모델
   - `FIREBASE_SERVICE_ACCOUNT_JSON`: Firebase 서비스 계정 JSON 원문 전체 (비공개)
   - `APP_ACCESS_TOKEN`: 강력한 비공개 토큰 (비공개)
   - `ALLOWED_ORIGINS`: `https://m1-2-secom-rnd-ai.vercel.app`
7. Render 서버 주소 끝에 `/docs`를 붙여 Swagger 확인.

**중요**: Render에는 서비스 계정 키 파일을 업로드하지 않습니다. `FIREBASE_SERVICE_ACCOUNT_JSON` 환경 변수를 사용합니다.
무료 티어에서 콜드스타트로 첫 요청이 느릴 수 있어서 채팅 화면에 안내 문구를 표시하도록 했습니다.

## 7. Vercel 프론트엔드 배포

1. Vercel → Add New Project → 같은 GitHub 저장소 선택.
2. **Root Directory**: `frontend`
3. Framework Preset: **Other** (프레임워크 없음)
4. `vercel.json`의 설정을 사용 (`node build.js` / Output Directory: `dist`).
5. **Environment Variables** → `API_BASE_URL=https://YOUR-BACKEND.onrender.com` 설정.
6. Deploy. 프론트 공개 페이지에서 서버 연결 토큰을 입력하고 동작을 확인.
7. Vercel 최종 주소를 확인해 Render `ALLOWED_ORIGINS`에 추가한 뒤 Render 재배포.

**주의**: Vercel 정적 JS에서는 서버 환경 변수를 런타임에 바로 읽을 수 없으므로 `build.js`가
배포 시 공개 `API_BASE_URL`을 `config.js`에 씁니다. 환경 변수를 바꾸면 Vercel을 다시 배포하세요.

## 8. 배포 URL (실제 배포 후 직접 기재)

- 프론트엔드 URL (데이터/그래프 화면 확인): https://m1-2-secom-rnd-ai.vercel.app
- 백엔드 API URL: https://m1-2-secom-rnd-api.onrender.com
- Swagger UI URL: https://m1-2-secom-rnd-api.onrender.com/docs

## 9. 제출 스크린샷 (실제 동작 확인 후 첨부)

- [ ] **1. 채팅**: 요약 카드 + 사용자 질문 + 데이터 기반 AI 답변 + 로딩 표시
- [ ] **2. 데이터 관리**: 새 데이터 추가 또는 수정 전/후가 보이는 화면
- [ ] **3. 대화 기록**: 목록에서 특정 대화를 눌러 과거 메시지가 재표시된 화면
- [ ] **4. Swagger**: `/docs` 엔드포인트 목록과 성공 응답 예시
- [ ] **5. Render/Vercel**: 두 배포 URL 접속 화면

스크린샷 저장 권장 폴더 `screenshots/` (실제 촬영 후 추가).
키와 접근 토큰이 보이지 않게 주의하세요.

## 10. 운영 주의

- OpenAI API에는 별도 요금이 발생할 수 있습니다. `max_output_tokens=400`, 최근 메시지 12개 제한 적용.
- Firestore 읽기/쓰기 및 Render/Vercel 배포도 서비스 요금/무료 한도 영향을 받을 수 있습니다.
- 단일 공유 토큰은 교육용 1인 프로젝트 방어선일 뿐이고, 다중 사용자 개인별 인증/권한을 제공하지 않습니다.
- 프론트의 API_BASE_URL은 공개되므로 **이곳에 비밀 키를 넣지 않습니다**.
- 사용자가 초대한 외부인이 같은 토큰으로 데이터를 수정할 수 있습니다. 공개 시에는 인증/권한 설계를 강화해야 합니다.
- SECOM 원본 자료 출처: McCann & Johnston, UCI SECOM, https://doi.org/10.24432/C54305 (CC BY 4.0 출처 표시).

## 11. 공부 순서

1. **Firestore 역할**: 자료를 저장해 서버를 껐다 켜도 남는 이유.
2. **FastAPI**: URL마다 라우터가 다른 기능을 실행하고 `services/`로 통계·프롬프트를 분리하는 원리.
3. **Pydantic**: 날짜/숫자/라벨 검증이 잘못된 입력을 막는 이유.
4. **컨텍스트 주입**: 요약 JSON을 GPT 시스템 지침에 넣고 관찰·가설·검증을 구분하는 원리.
5. **프론트엔드**: `fetch()` 요청 → 결과 표시 → 로딩/UI 갱신.
6. **배포**: CORS, 비밀 환경 변수, Render와 Vercel의 역할.

원 프로젝트: https://github.com/sy05kim/M1-1
