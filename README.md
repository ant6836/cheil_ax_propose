# 제일기획 AI 전략 인텔리전스 대시보드

## 파일 구조

```
cheil_ax_propose/
├── dashboard.html       # 메인 대시보드 (브라우저에서 직접 열기)
├── server.py            # Graph-RAG Flask 백엔드
├── 06_daily_summary.py  # PDF → LLM 일일 요약 스크립트
├── .env                 # API 키 설정 (gitignore 처리됨 — 직접 생성 필요)
└── AI_Architecture_Spec.md
```

---

## 실행 방법

### 사전 준비 (최초 1회만)

`.env` 파일을 프로젝트 폴더에 직접 생성하고 아래 내용 입력:

```
API_KEY=실제_API_키_입력
BASE_URL=https://genai-sharedservice-americas.pwcinternal.com/v1/responses
MODEL=vertex_ai.anthropic.claude-sonnet-4-6
```

> `API_KEY`는 `06_daily_summary.py`에서 사용하는 것과 동일한 키.
> `.env`는 `.gitignore`에 포함되어 있어 GitHub에 올라가지 않으므로 매번 직접 생성해야 함.

---

### 매번 실행할 때

**Step 1 — Flask 서버 시작** (PowerShell 창 1개 열어서 실행)

```powershell
& "C:\Users\sleez661\Desktop\vscode\MiroFish-Ko\backend\.venv\Scripts\python.exe" "C:\Users\sleez661\Desktop\vscode\cheil_ax_propose\server.py"
```

아래 메시지가 뜨면 서버 정상 구동:
```
* Running on http://0.0.0.0:5000
```

> 이 PowerShell 창은 사용하는 동안 계속 열어둬야 함.

**Step 2 — 대시보드 열기**

`dashboard.html`을 브라우저로 더블클릭 (또는 드래그해서 열기).

---

### 서버 동작 확인 (선택)

브라우저 주소창에 입력:
```
http://localhost:5000/health
```
→ `{"model":"vertex_ai.anthropic.claude-sonnet-4-6","status":"ok"}` 가 보이면 정상.

---

### 종료

서버 실행 중인 PowerShell 창에서 `Ctrl+C`.

---

## 사용 방법

1. 브라우저에서 `dashboard.html` 열기
2. **Ontology** 탭 클릭
3. **"AI 대화"** 탭 클릭
4. 추천 질문 칩을 클릭하거나 직접 질문 입력
   - `Enter` — 전송
   - `Shift+Enter` — 줄바꿈

### 추천 질문 예시
- "W3 약점을 해소하는 전략 경로는?"
- "제일기획의 가장 긴급한 위협은?"
- "현금 4,700억을 어디에 먼저 투자해야 하나?"

---

## 패키지 (venv에 이미 설치됨)

MiroFish-Ko `.venv`에 필요한 패키지가 모두 포함되어 있어 별도 설치 불필요.

필요 시 수동 설치:
```powershell
& "C:\Users\sleez661\Desktop\vscode\MiroFish-Ko\backend\.venv\Scripts\pip.exe" install flask flask-cors python-dotenv requests
```
