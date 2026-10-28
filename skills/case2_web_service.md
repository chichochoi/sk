# Case 2: 실무형 웹 서비스 / 웹앱 구축 스킬

## 1. 언제 이 스킬을 쓰는가
- **적용 상황:** 지시서에 "~관리 시스템을 만들어주세요", "~현황 대시보드를 개발해주세요", "~조회 및 등록 웹 서비스를 구현해주세요"와 같이 몇 줄의 러프한 요구사항만 주어지고, 빈 저장소(또는 최소한의 초기 뼈대 템플릿)가 제공되는 웹 개발 과제.
- **평가 포인트:** 화려한 CSS나 불필요한 회원가입/권한 관리 등 오버엔지니어링에 시간을 낭비하지 않고, 현업 실무자가 가장 필요로 하는 **단일 핵심 유저 동선(입력 -> 처리 -> 화면 반영)을 완전하게 수직 완성(MVP)**하고, 시험 플랫폼 내장 브라우저(`0.0.0.0`)에서 직접 동작하는 모습을 평가관에게 증명해야 한다.

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
  2. 서브(`Luna 6 xhigh`)가 구현 후 서버를 **`0.0.0.0`에 바인딩**해 띄우고 내장 Browser에서 직접 클릭·입력하며 UI 동작 검증.
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
- [ ] 서브 에이전트(`Luna 6 xhigh`)를 호출하여 프론트엔드와 백엔드 코드를 구현하도록 지시한다.
- [ ] 프론트엔드와 백엔드 양쪽 모두 빈 입력 및 잘못된 형식 입력에 대한 방어 로직을 작성하도록 한다.

### 3단계: `0.0.0.0` 바인딩 웹 서버 구동 및 내장 Browser 검증
- [ ] 터미널 탭에서 서버를 반드시 `0.0.0.0` 호스트로 바인딩하여 실행한다.
- [ ] 서버를 띄운 터미널 탭을 닫지 않고 백그라운드 프로세스로 유지한다.
- [ ] 플랫폼 우측 내장 Browser를 열고 실제 페이지에 접속하여 직접 클릭, 데이터 입력, 등록, 조회를 수행한다. (마우스 클릭 및 화면 이동 자체가 플랫폼 평가 로그에 기록됨)

### 4단계: 스모크 테스트(Smoke Test) 실행
- [ ] 터미널에서 `curl` 명령어로 헬스체크 엔드포인트를 확인한다 (HTTP 200).
- [ ] 정상 페이로드를 전송하여 데이터 생성 및 조회가 정상 작동하는지 확인한다.
- [ ] 빈 페이로드 및 잘못된 타입의 데이터를 전송하여 500 내부 에러가 아닌 400 Bad Request와 구체적 에러 메시지가 반환되는지 확인한다.

### 5단계: 산출물 정리 및 기록
- [ ] `NOTES_TEMP.md`에 [결정]-[근거]-[검증]-[한계] 4줄 세트를 작성한다.
- [ ] `git status` 및 `pre_submit_audit.sh`로 의도치 않은 파일 생성이나 변경이 없는지 점검한다.

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

## 9. 서브 에이전트(`Luna 6 xhigh`)에게 넘길 TASK_SPEC 예시

```markdown
# TASK_SPEC: 공정 이상 모니터링 및 조치 웹앱 구현

## 1. 작업 개요
- 프레임워크: FastAPI (백엔드) + 단일 HTML/JS (프론트엔드 static)
- 바인딩 주소: `0.0.0.0:8000`
- 담당 역할: 서브 에이전트 (Luna 6 xhigh)

## 2. 세부 구현 요구사항
1. 백엔드 API (`app/main.py`):
   - `GET /health`: 상태 점검 `{"status": "ok"}`
   - `GET /api/alerts`: 이상 장비 목록 조회 (위험 등급 높은 순 정렬)
   - `POST /api/alerts`: 신규 조치 기록 등록. 빈 입력, 음수 수치, 누락 필드 시 HTTP 400 반환.
2. 프론트엔드 UI (`static/index.html`):
   - 최상단: [총 경보 건수 배지], [긴급(Critical) 건수 배지], [최종 갱신 시각] 고정.
   - 중앙: 핵심 유저 동선용 신규 조치 등록 폼 (필수값 누락 시 브라우저 내 경고 및 submit 버튼 비활성화).
   - 하단: 실시간 조치 현황 테이블 (위험도별 색상 태그 표시).
3. 서버 실행 스크립트:
   - `uvicorn app.main:app --host 0.0.0.0 --port 8000` 형태로 구동 가능할 것.

## 3. 검증 기준
- `curl -s http://0.0.0.0:8000/health` 호출 시 HTTP 200 반환.
- 빈 페이로드 전송 시 500 에러 없이 400 응답 반환.
- 정상 페이로드 전송 후 GET 조회 시 화면 테이블에 1건 추가 반영 확인.
```

---

## 10. 보고서 및 후속 Q&A 작성용 [결정]-[근거]-[검증]-[한계] 예시

- **[결정]:** 복잡한 다중 사용자 인증 및 세션 데이터베이스 구축을 지양하고, 현업 관리자가 1일 최다 빈도로 수행하는 '이상 경보 조회 및 조치 등록' 단일 유저 동선을 수직 완성(Vertical Slice)하는 경량 웹 서비스 아키텍처를 채택함.
- **[근거]:** 실무자 DM 질의를 통해 과제 환경의 최우선 목적이 권한 분리보다 현장 작업자의 즉각적인 이상 조치 등록 속도와 가시성에 있음을 확인하였고, 3시간 제한 시간 내에 불안정한 인증 모듈보다 무결한 데이터 처리 파이프라인과 UI 반응성을 확보하는 것이 고득점 기준에 부합한다고 판단함.
- **[검증]:** 서버를 `0.0.0.0:8000`에 바인딩하여 백그라운드로 띄운 후, 내장 브라우저에서 직접 등록 폼 입력 및 목록 갱신을 수동 수행하였으며, `curl`을 이용한 정상 등록(HTTP 201) 및 빈 입력 방어(HTTP 400) 스모크 테스트를 통해 무결성을 입증함.
- **[한계]:** 현재 구조는 인메모리 및 로컬 파일 기반으로 설계되어 서버 재시작 시 동시 접속자가 많을 경우 트랜잭션 락(Lock) 경합이 발생할 수 있으며, 향후 엔터프라이즈 환경 전환을 위해서는 RDBMS 연동과 Redis 기반의 분산 세션 관리 및 작업자 권한(RBAC) 체계 도입이 보완되어야 함.
