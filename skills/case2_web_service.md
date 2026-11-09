# Case 2: 실무형 웹 서비스 / 웹앱 구축 스킬

## 1. 언제 이 스킬을 쓰는가
- **적용 상황:** 지시서에 "~관리 시스템을 만들어주세요", "~현황 대시보드를 개발해주세요", "~조회 및 등록 웹 서비스를 구현해주세요"와 같이 몇 줄의 러프한 요구사항만 주어지고, 빈 저장소(또는 최소한의 초기 뼈대 템플릿)가 제공되는 웹 개발 과제.
- **평가 포인트:** 화려한 CSS나 불필요한 회원가입/권한 관리 등 오버엔지니어링에 시간을 낭비하지 않고, 현업 실무자가 가장 필요로 하는 **단일 핵심 유저 동선(입력 -> 처리 -> 화면 반영)을 완전하게 수직 완성(MVP)**하고, 시험 플랫폼 내장 브라우저(`0.0.0.0`)에서 직접 동작하는 모습을 평가관에게 증명해야 한다.
- **연계 스킬 교차 참조:** 반도체 밸류체인 DAG 수급 충격·후공정 병목 What-If 시뮬레이터(#14), 직무별 Level-Adaptive AI 튜터(#15), 멀티 페르소나 Dual-Mode 통합 플랫폼 과제는 [.probe-kit/skills/case7_fde_valuechain_app.md](case7_fde_valuechain_app.md)를 우선 적용하며, 식단 최적화 및 개인 맞춤 추천 변형(#12)은 Case 5 / Case 7 스킬을 참조한다.

---

## 2. 원본 공략법 전문 (Single Source of Truth)

### 🌐 Case 2. 실무형 웹 서비스 / 웹앱 구축 미션 (출제 확률: 상 — 코파톤 원형)
* **연동 스킬:** `.probe-kit/skills/case2_web_service.md`
* **판별:** *"~서비스를 만들어주세요"* 몇 줄의 러프한 지시서 + 빈 프로젝트(또는 기본 템플릿).
* **전용 필수 질문:**
  * *"핵심 사용자가 이 화면에 들어와서 하루에 가장 자주 수행하는 핵심 행동 1~2개가 무엇인가요?"* (동선 우선순위 파악)
  * *"일반 사용자 외에 운영자(관리자) 역할이 따로 있나요? 로그인/권한 분리가 필수인가요?"*
  * *"목록이나 대시보드를 보여줄 때 현업 사용자가 가장 먼저 확인해야 하는 핵심 정보(도메인 디테일)가 무엇인가요?"*
* **무감점 Solve 시퀀스:**
  1. 복잡한 회원가입/DB 설계 등 오버엔지니어링을 쳐내고, 메인(`Sol 6.1 xhigh`)이 실무자가 꼽은 **핵심 유저 동선 1개를 수직 완성(입력 → 백엔드 처리 → 화면 표시)**하도록 `TASK_SPEC.md` 작성.
  2. 서브(`GPT 5.6-terra medium`)가 구현 후 서버를 **`0.0.0.0`에 바인딩**해 띄우고 내장 Browser에서 직접 클릭·입력하며 UI 동작 검증.
  3. 실무자에게 캐낸 도메인 중요 정보를 화면 최상단에 배치하고, 빈 입력/잘못된 입력에 대한 예외 방어(에러 메시지 표시) 추가.

---

## 3. 단계별 실행 체크리스트

### 1단계: 실무자 인터뷰 및 핵심 유저 동선 1개 정의
- [ ] 실무자 DM을 통해 핵심 타깃 사용자의 하루 최다 빈도 행동 1~2개를 파악한다.
- [ ] 인증/권한(로그인, 회원가입, 세션)이 필수 과제 범위인지, 아니면 단일 공용 권한으로 충분한지 확인한다.
- [ ] 목록 및 대시보드 화면 최상단에 배치해야 할 핵심 도메인 지표(상태 배지, 주요 카운트 등)를 확인한다.
- [ ] 입력 → 백엔드 비즈니스 처리 → 화면 출력으로 이어지는 수직 완성(MVP) 범위를 확정한다.

### 2단계: 작업 명세서 작성 및 서브 에이전트 위임
- [ ] 메인 에이전트(`Sol 6.1 xhigh`)가 `.probe-kit/runtime/TASK_SPEC.md`에 API 스펙, 입력 유효성 검증 규칙, 화면 UI 배치 요구사항을 작성한다.
- [ ] 서브 에이전트(`GPT 5.6-terra medium`)를 호출하여 프론트엔드와 백엔드 코드를 구현하도록 지시한다.
- [ ] 프론트엔드와 백엔드 양쪽 모두 빈 입력 및 잘못된 형식 입력에 대한 방어 로직을 작성하도록 한다.

### 3단계: `0.0.0.0` 바인딩 웹 서버 구동 및 내장 Browser 검증
- [ ] 터미널 탭에서 서버를 반드시 `0.0.0.0` 호스트로 바인딩하여 실행한다.
- [ ] 서버를 띄운 터미널 탭을 닫지 않고 백그라운드 프로세스로 유지한다.
- [ ] 플랫폼 우측 내장 Browser를 열고 실제 페이지에 접속하여 직접 클릭, 데이터 입력, 등록, 조회를 수행한다. (마우스 클릭 및 화면 이동 자체가 플랫폼 평가 로그에 기록됨)

### 4단계: 스모크 테스트(Smoke Test) 및 온더플라이 검증 실행
- [ ] 이번 태스크의 실무자 DM 요구사항(유효성 검증, 경계값 방어 등)에 맞춘 온더플라이 테스트 스크립트(예: `tests/test_*.py` 또는 ad-hoc 검증 스크립트)를 직접 작성하여 실행한다 (고정 템플릿 사용 금지, 태스크 맞춤형 ad-hoc 작성, `git commit` 금지 및 untracked 유지).
- [ ] 터미널에서 `curl` 명령어로 헬스체크 엔드포인트를 확인한다 (HTTP 200).
- [ ] 정상 페이로드를 전송하여 데이터 생성 및 조회가 정상 작동하는지 확인한다.
- [ ] 빈 페이로드 및 잘못된 타입의 데이터를 전송하여 500 내부 에러가 아닌 400 Bad Request와 구체적 에러 메시지가 반환되는지 확인한다.

### 5단계: 산출물 정리 및 기록
- [ ] `NOTES_TEMP.md`에 [결정]-[근거]-[검증]-[한계] 4줄 세트를 작성한다.
- [ ] `git status` 및 `pre_submit_audit.sh` (또는 Windows/PowerShell 시 `pre_submit_audit.py`)로 의도치 않은 파일 생성이나 변경이 없는지 점검한다 (시험 중 `git add`/`commit`/`reset`/`clean` 금지, 테스트 코드는 untracked 유지).

---

## 4. `0.0.0.0` 바인딩 실행 명령 예시 (프레임워크별)

시험 플랫폼 내장 Browser 미리보기 및 채점 환경은 가상 컨테이너 내부 통신을 사용하므로, `localhost` 또는 `127.0.0.1`로 서버를 구동하면 브라우저 창에서 연결 거부(`ERR_CONNECTION_REFUSED`)가 발생한다. 반드시 모든 인터페이스에서 수신할 수 있도록 **`0.0.0.0`에 바인딩**해야 한다. 또한 검증 및 채점 중에는 서버를 구동한 터미널 탭을 절대로 종료하지 않는다.

### 1. Python Flask
```bash
# 방법 A: CLI 실행 (권장)
export FLASK_APP=app.py
flask run --host=0.0.0.0 --port=5000

# 방법 B: python 코드로 직접 실행 시 (app.py 내부)
# app.run(host="0.0.0.0", port=5000, debug=False)
python3 app.py
```

### 2. Python FastAPI / Uvicorn
```bash
# 기본 실행
uvicorn main:app --host 0.0.0.0 --port 8000

# 개발 리로드 모드 필요 시
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Node.js Express
```javascript
// server.js 소스코드 내부
const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;
const HOST = '0.0.0.0';

app.listen(PORT, HOST, () => {
  console.log(`Server is running on http://${HOST}:${PORT}`);
});
```
```bash
# 터미널 실행 명령
HOST=0.0.0.0 PORT=3000 node server.js
```

### 4. Streamlit
```bash
# Streamlit 실행 (0.0.0.0 바인딩 및 CORS 비활성화 권장)
streamlit run app.py --server.address=0.0.0.0 --server.port=8501 --server.enableCORS=false --server.enableXsrfProtection=false
```

### 5. Vite (React / Vue / Svelte)
```bash
# Vite 개발 서버 실행
npx vite --host 0.0.0.0 --port 5173

# package.json 스크립트 수정 시: "dev": "vite --host 0.0.0.0 --port 5173"
npm run dev
```

---

## 5. 핵심 유저 동선 1개 수직 완성 (MVP) 및 도메인 정보 최상단 배치 규칙

### 수직 완성(Vertical Slice) 원칙
1. **오버엔지니어링 절대 배제:**
   - 복잡한 JWT 인증, OAuth2 연동, 회원가입/비밀번호 재설정 페이지는 요구사항에 명시되지 않는 한 일체 개발하지 않는다.
   - 단일 공용 세션 또는 관리자 토글 버튼 하나로 단순화한다.
2. **단일 수직 플로우의 완결성:**
   - [입력 폼 작성] → [클라이언트 유효성 검증] → [백엔드 API 호출] → [데이터베이스/인메모리 저장 및 비즈니스 검증] → [목록 갱신 및 화면 즉시 렌더링]
   - 이 하나의 플로우가 예외 없이 부드럽게 완벽 작동하도록 구현한다.

### 도메인 핵심 정보 최상단 배치 원칙
현업 실무자가 시스템을 열었을 때 가장 먼저 확인하는 3대 정보 요소를 화면 상단 헤더 또는 상단 대시보드 카드 영역에 고정 배치한다:
1. **전체 건수 및 상태별 카운트 배지:** (예: 전체 150건 | 정상 135건 | 주의 12건 | 긴급 조치 3건)
2. **시스템 헬스 및 최종 동기화 시간:** (예: 센서 상태: 정상 연결 | 최종 데이터 수신: 2026-10-28 14:02:15 KST)
3. **핵심 도메인 필터 바:** 날짜 선택, 긴급 등급 필터, 검색어를 1열에 정렬하여 즉시 필터링 가능하게 구성.

---

## 6. 빈 입력 및 잘못된 입력 UI 방어 규칙 (프론트엔드 + 백엔드 이중 방어)

평가 시 채점관과 자동 테스트는 반드시 **빈 문자열, 공백 문자, 음수, 문자열 입력 칸에 숫자/특수문자 삽입, 누락된 필수 필드**를 전송하여 시스템이 죽는지(500 Internal Server Error) 테스트한다. 따라서 프론트엔드와 백엔드 양쪽 모두 방어막을 구축해야 한다.

### 프론트엔드 방어 규칙
1. 모든 필수 입력 필드에 `required` 속성과 적절한 `type` (number, email, date 등) 및 `min`, `max` 속성을 부여한다.
2. 폼 제출 버튼(`submit`)은 필수 입력이 누락되었거나 처리 중인 상태(`isSubmitting`)일 때 `disabled` 상태로 전환하여 연타로 인한 중복 제출을 방지한다.
3. 입력 실패 시 폼 하단에 빨간색 명확한 에러 메시지 텍스트를 표시한다 (단순 `alert()` 지양).

### 백엔드 방어 규칙
1. 모든 요청 바디(JSON)를 파싱할 때 누락된 키가 있는지 검사한다.
2. 누락되거나 타입이 불일치하는 경우 HTTP 500이 아닌 **HTTP 400 (Bad Request)** 상태 코드와 함께 오류 필드명 및 원인을 명확한 JSON으로 반환한다.
3. 전역 예외 처리기(Global Exception Handler)를 등록하여 예상치 못한 에러 발생 시에도 서버 프로세스가 죽지 않고 표준 JSON 에러 포맷을 반환하도록 한다.

```python
# 백엔드 유효성 검증 및 예외 방어 예시 (FastAPI)
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from typing import Optional

app = FastAPI()

class EquipmentLogRequest(BaseModel):
    equipment_id: str = Field(description="장비 고유 번호 (공백 불가)", min_length=1)
    temperature: float = Field(description="공정 온도 (-50 ~ 1500)", ge=-50.0, le=1500.0)
    operator_name: str = Field(description="작업자 이름", min_length=2)

    @field_validator("equipment_id")
    @classmethod
    def validate_equipment_id(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("장비 고유 번호는 공백일 수 없습니다.")
        return stripped

@app.post("/api/v1/logs", status_code=status.HTTP_201_CREATED)
def create_equipment_log(payload: EquipmentLogRequest):
    # 비즈니스 처리
    return {"status": "SUCCESS", "data": payload.model_dump()}
```

---

## 7. 스모크 테스트(Smoke Test) curl 실행 예시

서브 에이전트 작업 완료 후 터미널에서 직접 실행할 엔드포인트 검증 명령:

```bash
# 1. 헬스체크 엔드포인트 검증 (기대: 200 OK)
curl -s -o /dev/null -w "%{http_code}\n" http://0.0.0.0:8000/health

# 2. 정상 등록 요청 테스트 (기대: 201 Created 또는 200 OK 및 생성된 ID 반환)
curl -s -X POST http://0.0.0.0:8000/api/v1/logs \
  -H "Content-Type: application/json" \
  -d '{"equipment_id": "EQP-001", "temperature": 420.5, "operator_name": "홍길동"}' | jq .

# 3. 빈 입력 및 공백 방어 테스트 (기대: 400 Bad Request 또는 422 Unprocessable Entity)
curl -s -X POST http://0.0.0.0:8000/api/v1/logs \
  -H "Content-Type: application/json" \
  -d '{"equipment_id": "   ", "temperature": 420.5, "operator_name": ""}' | jq .

# 4. 수치 범위 초과 비정상 입력 방어 테스트 (기대: 400 Bad Request)
curl -s -X POST http://0.0.0.0:8000/api/v1/logs \
  -H "Content-Type: application/json" \
  -d '{"equipment_id": "EQP-001", "temperature": 9999.0, "operator_name": "홍길동"}' | jq .

# 5. 목록 조회 엔드포인트 및 도메인 정렬 확인
curl -s http://0.0.0.0:8000/api/v1/logs | jq '.[0:3]'
```

---

## 8. 실무자 DM 확인 질문 목록

1. *"핵심 사용자가 이 화면에 들어와서 하루에 가장 자주 수행하는 핵심 행동 1~2개가 무엇인가요? (예: 장비 이상 목록 조회 후 조치 상태 업데이트, 신규 점검 일지 등록 등)"*
2. *"일반 사용자 외에 운영자(관리자) 역할이 따로 있나요? 로그인/권한 분리가 필수인가요, 아니면 관리자/조회자 모드 토글로 충분한가요?"*
3. *"목록이나 대시보드를 보여줄 때 현업 사용자가 가장 먼저 확인해야 하는 핵심 정보(도메인 디테일, 요약 수치, 위험 배지 등)가 무엇인가요?"*
4. *"등록 시 필수 입력값과 선택 입력값의 구분 기준은 무엇이며, 잘못된 입력 시 현업에 안내해야 하는 기본 에러 메시지 규칙이 있나요?"*

---

## 9. 서브 에이전트(`GPT 5.6-terra medium`)에게 넘길 TASK_SPEC 예시

메인 에이전트(`Sol 6.1 xhigh`)는 아래 [시작 · 정의 · 기준 · 종료] 4대 핵심 축 기반 7대 표준 규격의 명세서를 작성하여 서브 에이전트에게 구현을 위임한다.

```markdown
# [TASK_SPEC] 공정 이상 모니터링 및 조치 웹앱 수직 완성 (MVP)

> **작성자:** 메인 아키텍트 (`Sol 6.1 xhigh`)  
> **수신자:** 서브 워커 (`GPT 5.6-terra medium`)  
> **핵심 원칙:** [시작 · 정의 · 기준 · 종료] 4대 축 기반 명세 준수 및 지정 범위 외 임의 수정 절대 금지. 완료 후 `.probe-kit/runtime/SUB_RESULT.md`에 핵심 결과와 변경 사항 위주의 명확한 요약 보고를 남길 것 (불필요한 줄 수 제한 없음).

---

### 1. [시작 / Start] 단일 목표 및 진입 조건 (Entry Conditions)
- **단일 목표 (Single Goal):** 공정 이상 모니터링 대시보드에서 실무자가 1일 최다 빈도로 수행하는 '이상 경보 목록 조회 → 조치 내용 등록 → 화면 즉시 반영' 단일 핵심 유저 동선 1개 수직 완성 (MVP)
- **선행 완료 상태 (Pre-conditions):**
  - 백엔드(FastAPI) 및 프론트엔드 static 디렉토리 구조 생성 확인
  - `0.0.0.0:8000` 바인딩 포트 충돌 여부 및 가용 상태 확인
  - Git 작업 트리가 깨끗한 상태(uncommitted 변경 사항 없음)인지 확인
- **사전 베이스라인 체크 (Baseline Pre-check):**
  - 기존 웹 서버 구동 상태 또는 헬스체크 테스트 PASS 확인 (`curl -s http://0.0.0.0:8000/health` 또는 `pytest tests/test_api_endpoints.py`)
  - 사전 베이스라인 실패 시 코드 작성 시작을 금지하고 즉시 원인 보고

### 2. [통제 / Scope] 대상 파일 범위 및 금지 사항 (Hard Constraints)
- **수정 허용 파일:**
  - `app/main.py` (FastAPI 엔드포인트 및 입력 유효성 검증 로직)
  - `static/index.html` (도메인 정보 상단 배치 및 등록 폼/목록 테이블 단일 UI)
  - `tests/test_api_endpoints.py` (신규 엔드포인트 유효성 검증 온더플라이 테스트)
- **수정 절대 금지 파일:**
  - 복잡한 사용자 테이블, 세션 관리 등 불필요한 인증 관련 신규 모듈 생성 금지
  - 글로벌 시스템 환경설정 및 DB 엔진 파일
  - `.gitignore` (Git 트래킹 제외 목록 수정 금지 - 임시 파일은 `.git/info/exclude`로 통제)
- **5대 금지사항 (Hard Constraints):**
  - 회원가입, JWT, 복잡한 권한 관리 등 요구사항에 없는 오버엔지니어링 전면 금지 (단일 공용 세션 원칙)
  - 서버 실행 시 `localhost` / `127.0.0.1` 바인딩 절대 금지 (반드시 `0.0.0.0` 바인딩 준수)
  - 시크릿, 패스워드, 개인 식별 정보, API 키 코드 내 하드코딩 절대 금지
  - `.gitignore` 파일 수정 금지 (임시 파일은 `.git/info/exclude`로 통제)
  - 시험 중 `git add` / `git commit` / `git reset` / `git clean` 실행 전면 금지 (테스트 코드는 커밋하지 않으며 test 파일은 untracked 상태 유지)

### 3. [정의 / Definition] 도메인 용어·상태 및 입출력 스키마
- **도메인 핵심 엔터티 및 용어 정의:**
  - `Alert (이상 경보 건)`: 공정 장비의 센서 이상 임계값 초과로 발생한 경보 엔터티 (식별자: `alert_id`)
  - `ActionLog (조치 기록)`: 현장 작업자가 특정 경보에 대해 수행한 유지보수 작업 기록 (식별자: `action_id`)
- **경보 상태 코드(Alert Status) 정의:**
  - `PENDING`: 현장 조치 대기 상태 (화면 상 빨간색 태그)
  - `IN_PROGRESS`: 점검 및 조치 진행 중 상태 (주황색 태그)
  - `RESOLVED`: 조치 완료 및 정상화 상태 (초록색 태그)
- **API 요청/응답 JSON 스키마 및 HTTP 상태 코드 계약:**
  - **1) 헬스체크 (`GET /health`):**
    - 응답: HTTP 200 OK `{"status": "ok"}`
  - **2) 이상 목록 조회 (`GET /api/alerts`):**
    - 응답: HTTP 200 OK `[{"alert_id": "ALT-001", "equipment_id": "EQP-01", "severity": "CRITICAL", "status": "PENDING", "created_at": "..."}]`
    - 정렬: `severity` 우선순위(`CRITICAL` -> `WARNING`), 동일 등급 내 `created_at` 최신순
  - **3) 조치 등록 (`POST /api/alerts/{alert_id}/actions`):**
    - 요청 Body: `{"action_type": string (필수, 1자 이상), "operator_name": string (필수, 2자 이상), "comment": string (선택)}`
    - 성공 응답: HTTP 201 Created `{"status": "SUCCESS", "data": {"action_id": "ACT-1001", "alert_id": "ALT-001", "operator_name": "홍길동", "action_type": "부품교체", "created_at": "..."}}`
    - 유효성 검증 실패 (빈 문자열, 누락 필드, 음수): HTTP 400 Bad Request `{"status": "ERROR", "message": "필수 입력값 누락 또는 유효하지 않은 입력", "invalid_fields": ["operator_name"]}`
    - 미존재 경보 ID: HTTP 404 Not Found `{"status": "ERROR", "message": "해당 alert_id를 찾을 수 없습니다."}`

### 4. [기준 / Criteria] 비즈니스 판정 기준 및 경계값 (Acceptance & Boundary Criteria)
- **실무자 DM 확인 비즈니스 규칙:**
  - 화면 최상단에 3대 도메인 정보([총 경보 건수 배지], [긴급(Critical) 건수 배지], [최종 동기화 시각])를 고정 배치
  - 조치 등록 즉시 목록 테이블의 상태가 갱신되어 새로고침 없이 확인 가능할 것
- **수치 경계값 및 유효성 검증 기준:**
  - `operator_name`: 최소 2자 이상 (공백 제외), 공백 문자열(`"   "`) 입력 시 400 에러 처리
  - `action_type`: 허용 문자열 길이 1자 이상 50자 이하
- **결측/예외 처리 기준 (이중 방어막):**
  - 프론트엔드: 필수 필드 미입력 시 `submit` 버튼 비활성화 및 빨간색 에러 텍스트 표시
  - 백엔드: 전역 예외 처리기를 등록하여 어떤 비정상 페이로드가 유입되어도 HTTP 500이 아닌 **HTTP 400/422**와 원인 JSON 반환
- **충돌 시 우선순위:**
  - 화려한 스타일링이나 불필요한 부가기능보다 **단일 핵심 유저 동선의 수직 완성 및 500 에러 방어(안정성)** 최우선

### 5. [검증 / Verification] 실행할 검증 명령어
- **1) 헬스체크 및 베이스라인 검증:**
  - `curl -s -o /dev/null -w "%{http_code}\n" http://0.0.0.0:8000/health` (HTTP 200 확인)
- **2) 태스크 맞춤 온더플라이(On-the-fly) ad-hoc 테스트 (필수):**
  - 실무자 DM 요구사항에 맞춘 온더플라이 API 테스트(`tests/test_api_endpoints.py`) 작성 및 실행
  - `pytest tests/test_api_endpoints.py -v` (통과 확인, *git commit 없이 untracked 유지*)
- **3) 정상·예외·경계값 스모크 curl 검증:**
  - 정상 등록 (201 Created):
    `curl -s -X POST http://0.0.0.0:8000/api/alerts/ALT-001/actions -H "Content-Type: application/json" -d '{"action_type": "점검", "operator_name": "홍길동"}' | jq .`
  - 빈 문자열 방어 (400 Bad Request):
    `curl -s -X POST http://0.0.0.0:8000/api/alerts/ALT-001/actions -H "Content-Type: application/json" -d '{"action_type": "", "operator_name": "  "}' | jq .`
- **4) 내장 브라우저 수동 검증:**
  - 플랫폼 내장 Browser 창에서 `http://0.0.0.0:8000` 접속 후 직접 조치 등록 클릭 및 상단 배지/테이블 변경 육안 확인

### 6. [정의 & 기준 / DoD] 완료 정의 (Definition of Done)
- [ ] 서버가 `0.0.0.0:8000`에 바인딩되어 백그라운드에서 정상 구동 중일 것
- [ ] 내장 브라우저에서 조치 등록 폼 제출 시 테이블에 즉시 반영되는 단일 동선이 수직 완성될 것
- [ ] 비정상/빈 페이로드 전송 시 500 에러 없이 HTTP 400/422 응답이 반환될 것
- [ ] 온더플라이 단위 테스트(`tests/test_api_endpoints.py`)가 100% PASS할 것 (git commit 금지, untracked 유지)
- [ ] `git diff --stat` 확인 시 지정된 수정 허용 파일 외 변경이 없을 것

### 7. [종료 / End] 종료 조건, 멈춤 조건 및 완료 후 조치 (Exit & Stop Protocol)
- **멈춤 조건 (Stop / Abort Condition) - 발견 즉시 구현 중단 및 대기:**
  - `0.0.0.0:8000` 포트 점유 충돌로 자체 해결이 불가할 때
  - 백엔드와 프론트엔드 간 API 계약(요청/응답 스키마)의 모호성이 발생했을 때
  - 사전 베이스라인 테스트 실패 원인이 불명확할 때
  - *위 상황 발생 시 즉시 구현을 멈추고 `SUB_RESULT.md`에 [차단(블로커)] 사유 기록 후 메인 보고*
- **완료 후 필수 조치 (Post-Completion Actions):**
  1. `.probe-kit/runtime/SUB_RESULT.md` 요약 보고서 작성 (필수 항목 표준 양식 준수, 불필요한 줄 수 제한 없음)
  2. `bash .probe-kit/scripts/handoff.sh log "sub done: web service MVP complete"` 실행 (실패 시 `python3 .probe-kit/scripts/handoff.py log "sub done" "web service MVP complete"`, 여의치 않을 시 `runtime/HANDOFF.md` 표에 직접 추가)
  3. 메인 에이전트에게 완료 보고 후 **서브 터미널에서 즉시 `/clear` 실행** (누적 토큰 리셋)
```

---

## 10. 보고서 및 후속 Q&A 작성용 [결정]-[근거]-[검증]-[한계] 예시

- **[결정]:** 복잡한 다중 사용자 인증 및 세션 데이터베이스 구축을 지양하고, 현업 관리자가 1일 최다 빈도로 수행하는 '이상 경보 조회 및 조치 등록' 단일 유저 동선을 수직 완성(Vertical Slice)하는 경량 웹 서비스 아키텍처를 채택함.
- **[근거]:** 실무자 DM 질의를 통해 과제 환경의 최우선 목적이 권한 분리보다 현장 작업자의 즉각적인 이상 조치 등록 속도와 가시성에 있음을 확인하였고, 3시간 제한 시간 내에 불안정한 인증 모듈보다 무결한 데이터 처리 파이프라인과 UI 반응성을 확보하는 것이 고득점 기준에 부합한다고 판단함.
- **[검증]:** 서버를 `0.0.0.0:8000`에 바인딩하여 백그라운드로 띄운 후, 내장 브라우저에서 직접 등록 폼 입력 및 목록 갱신을 수동 수행하였으며, `curl`을 이용한 정상 등록(HTTP 201) 및 빈 입력 방어(HTTP 400) 스모크 테스트를 통해 무결성을 입증함.
- **[한계]:** 현재 구조는 인메모리 및 로컬 파일 기반으로 설계되어 서버 재시작 시 동시 접속자가 많을 경우 트랜잭션 락(Lock) 경합이 발생할 수 있으며, 향후 엔터프라이즈 환경 전환을 위해서는 RDBMS 연동과 Redis 기반의 분산 세션 관리 및 작업자 권한(RBAC) 체계 도입이 보완되어야 함.
