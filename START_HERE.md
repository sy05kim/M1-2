# START HERE · 1단계 FastAPI 실행하기

이번 프로젝트는 **반도체 공정 R&D AI 비서**입니다. 먼저 서버가 동작하는지 확인하고, 그다음 데이터와 GPT를 연결합니다.

## 오늘의 목표: Swagger API 문서 열기

### 1. ZIP 압축 풀고 VS Code로 열기

1. 프로젝트 ZIP 파일을 압축 해제합니다.
2. VS Code를 열고 **파일 → 폴더 열기**를 클릭합니다.
3. 압축을 푼 **`M1-2_SECOM_RND_AI`** 폴더를 선택합니다. `backend`, `frontend`, `README.md`가 보이면 맞게 연 것입니다.
4. VS Code 메뉴에서 **터미널 → 새 터미널**을 엽니다. 윈도우 PowerShell을 기준으로 설명합니다.

### 2. 가상환경 준비 및 설치

아래 명령어를 **한 줄씩** 입력하고 Enter를 누르세요.

```powershell
cd backend
py -3 --version
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

- Python 3.10 이상이어야 합니다.
- 위 명령은 환경을 활성화하지 않아도 실행됩니다. PowerShell 실행 정책 때문에 `Activate.ps1` 오류가 발생하는 것을 피할 수 있습니다.
- `No module named ...` 오류가 나면 설치 명령의 완료 여부를 확인하세요.

### 3. 백엔드 실행

같은 터미널에서 실행합니다.

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

터미널에 `Uvicorn running on http://127.0.0.1:8000`이 보이면 브라우저를 열고:

- **API 문서**: http://127.0.0.1:8000/docs
- **서버 상태**: http://127.0.0.1:8000/api/health

`GET /api/health`를 누르고 **Try it out → Execute**를 누르면 `{ "status": "ok", ... }`가 돌아옵니다.
이 단계에서는 Firebase와 GPT가 아직 연결되지 않아도 정상입니다. `data/chat` 엔드포인트는 인증/키 설정 이후 사용합니다.

### 4. 자동 테스트 (새 터미널에서)

VS Code의 **터미널 + 버튼**으로 새 터미널을 열고:

```powershell
cd backend
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

`Ran 6 tests`와 `OK`가 나타나면 통계 계산·입력 검증·프롬프트 테스트를 통과한 것입니다.

### 오늘 이해할 개념

- **백엔드(FastAPI)**: 데이터를 받아 검증하고 DB와 AI를 호출하는 서버입니다.
- **API**: 프론트와 서버가 기능을 요청하는 주소입니다. `/api/data/summary`는 계산한 통계를 돌려주는 주소입니다.
- **Swagger UI**: 각 API를 브라우저에서 확인하고 직접 테스트하는 문서 화면입니다.
- **라우터와 서비스**: `routers/`는 URL/요청 처리를, `services/`는 통계·DB·AI 지침 같은 재사용 로직을 맡습니다.

### 스스로 설명할 1문장

> 프론트는 사용자 화면을, FastAPI는 요청을 처리하고 데이터베이스 및 GPT API와 연결하는 역할을 합니다.

### 다음 단계 예고

1. Firebase 프로젝트와 Firestore Database 생성
2. 서비스 계정 키를 `backend/serviceAccountKey.json`에 **로컬에서만** 보관
3. `.env.example`을 `.env`로 복사하고 비공개 키와 토큰 등록
4. SECOM 실제 데이터 준비 후 `scripts/import_secom.py`로 가져오기
5. 프론트 데이터 관리·채팅·대화 기록 확인

**주의:** OpenAI API 키, Firebase 서비스 계정 JSON, `APP_ACCESS_TOKEN`은 채팅에 붙여넣거나 GitHub에 올리지 마세요. 배포 URL과 키는 완전히 다릅니다.
