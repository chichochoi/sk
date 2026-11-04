# Case 3: 기존 레거시 코드베이스 디버깅 및 신규 기능 확장 스킬

## 1. 언제 이 스킬을 쓰는가
- **적용 상황:** 시험 시작 시점에 이미 완성도 높은 코드베이스(수십 개의 파일, 기존 단위/통합 테스트 스위트, 설정 파일, 기존 API 서버 등)가 주어지고, 특정 버그를 수정(예: 로그인 실패, 결제 오류, 특정 파라미터 누락 버그)하거나 신규 엔드포인트/기능을 추가하라는 지시가 제공되는 과제.
- **평가 포인트:** 기존 시스템의 규격과 아키텍처를 존중하고, 수정 전/후의 테스트 로그를 남겨 회귀(Regression)가 없음을 증명하며, 합의되지 않은 파일(설정, 라이브러리 버전, 다른 모듈)을 무분별하게 변경하지 않는 **최소 범위 수정 원칙**을 평가관에게 증명해야 한다.

---

## 2. 원본 공략법 전문 (Single Source of Truth)

### 🛠️ Case 3. 기존 레거시 코드베이스 디버깅 및 신규 기능 확장 (출제 확률: 상 — 공식 Good 예시)
* **연동 스킬:** `.probe-kit/skills/case3_legacy_debug.md`
* **판별:** 이미 코드·문서·테스트가 갖춰진 프로젝트 + 버그 수정(예: 로그인 실패, API 오류) 및 기능 추가 지시.
* **전용 필수 지시 & 질문:**
  * *(실무자 DM)* *"신규 기능 추가나 버그 수정 시 기존 API 엔드포인트 경로, 응답 JSON 스키마, 인증 방식은 그대로 유지해야 하나요?"*
  * *(메인/서브 지시)* *"수정하기 전에 먼저 버그 원인 후보와 변경될 파일 범위를 알려줘. 기존 인증 방식과 인터페이스는 절대 바꾸지 마."*
* **무감점 Solve 시퀀스:**
  1. 시작 직후 **기존 테스트 스위트를 실행해 베이스라인(초기 통과/실패 현황) 로그**를 남김.
  2. 원인 진단 및 변경 파일 범위를 확정한 뒤 서브(`GPT 5.6-terra medium`)가 합의된 범위만 최소 수정.
  3. 기존 테스트 재실행(Regression 방지) + 신규 기능의 정상/실패 경로 테스트 추가 실행.
  4. `git diff`로 합의 범위 밖의 파일이 변경되지 않았는지 전수 확인.

---

## 3. 단계별 실행 체크리스트

### 1단계: 기존 테스트 스위트 실행 및 베이스라인 로그 보존
- [ ] 코드나 설정을 1바이트도 수정하기 전에, 터미널에서 기존 테스트 명령(예: `pytest`, `npm test`, `python3 -m unittest`)을 실행한다.
- [ ] 실행 결과를 텍스트 파일(예: `baseline_test_result.log`)로 저장하고 초기 통과 건수 및 실패 건수를 기록한다.
- [ ] 기존 테스트 중 이미 실패하고 있던 테스트가 있는지, 아니면 전원 통과 상태인지 분별한다.

### 2단계: 실무자 인터뷰 및 하위 호환성 원칙 확정
- [ ] 실무자 DM을 통해 기존 API 엔드포인트 URL, HTTP 메서드, 응답 JSON 키 명명 규칙, 인증 방식(Bearer 토큰, 세션 쿠키 등)을 100% 유지해야 함을 확인한다.
- [ ] 신규 기능 추가 시 기존 클라이언트가 깨지지 않도록 하위 호환성(옵셔널 필드 처리 등) 기준을 합의한다.

### 3단계: 원인 진단, 변경 파일 범위 확정 및 서브 에이전트 위임
- [ ] 메인 에이전트(`Sol 6.1 xhigh`)가 버그 원인 가설을 수립하고, 변경할 파일 목록(최대 1~3개 파일로 한정)을 확정한다.
- [ ] 메인 에이전트가 `.probe-kit/runtime/TASK_SPEC.md`에 대상 파일의 절대 경로와 변경 범위를 엄격히 명시한다.
- [ ] 서브 에이전트(`GPT 5.6-terra medium`)를 호출하여 지정된 파일의 해당 함수/클래스 영역만 최소 수정하도록 지시한다.
- [ ] 전체 포매터 일괄 적용(Prettier, Black 등)으로 인한 불필요한 라인 변경을 엄격히 금지한다.

### 4단계: 기존 테스트 재실행(회귀 방지) 및 신규 테스트 작성
- [ ] 수정 후 기존 테스트 스위트를 동일하게 재실행하여 기존 통과 건들이 단 하나도 깨지지 않았음을 확인한다.
- [ ] 매 태스크마다 실무자 DM 요구사항에 맞춘 온더플라이 테스트 코드(예: `tests/test_*.py` 또는 ad-hoc 검증 스크립트)를 즉석 작성하여 실행한다 (고정 템플릿 사용 금지, 태스크 맞춤형 ad-hoc 작성, `git commit` 금지 및 untracked 유지).
- [ ] 수정한 버그가 재발하지 않도록 검증하는 단위 테스트(재현 테스트)를 추가한다.
- [ ] 신규 추가 기능에 대한 정상 케이스 1개 + 비정상/경계 케이스 1개 이상의 단위 테스트를 작성하고 실행한다.

### 5단계: `git diff --stat` 및 `git diff` 전수 검증
- [ ] 터미널에서 `git diff --stat`를 실행하여 실제로 변경된 파일 목록이 작업 명세서에 합의된 파일과 정확히 일치하는지 확인한다.
- [ ] `git diff`를 실행하여 의도하지 않은 주석 삭제, 공백 변경, 불필요한 리팩토링이 포함되지 않았는지 라인 단위로 점검한다.
- [ ] `NOTES_TEMP.md`에 [결정]-[근거]-[검증]-[한계] 4줄 세트를 작성한다.

---

## 4. 베이스라인 테스트 우선 실행 규칙

코드를 단 한 줄이라도 수정하기 전에 초기 상태의 테스트 로그를 남기는 것은 Cofa Probe 평가 시스템의 자동 수집 로그(기술 축)에서 **가장 높은 가산점을 받는 핵심 행동**이다.

### 베이스라인 테스트 실행 및 로그 기록 표준 명령
```bash
# Python pytest 환경
pytest -v | tee baseline_test_result.log

# Python unittest 환경
python3 -m unittest discover -s tests -v 2>&1 | tee baseline_test_result.log

# Node.js Jest / Mocha 환경
npm test -- --verbose 2>&1 | tee baseline_test_result.log
```

### 베이스라인 로그 분석 기준
1. **기존 테스트가 100% 통과 중인 경우:** 수정 후에도 이 모든 테스트가 100% 통과해야 하며, 단 하나의 실패도 용납되지 않는다.
2. **기존 테스트 중 특정 테스트가 이미 실패하고 있던 경우:** 해당 실패 테스트가 이번 과제에서 수정해야 할 목표 버그인지 확인한다.
3. **테스트 프레임워크가 없는 경우:** 즉시 `tests/` 디렉토리에 기본 스모크 테스트 또는 메인 진입점 실행 스크립트를 작성하여 초기 동작 상태를 증명한다.

---

## 5. 기존 API / 인증 / 라우터 시그니처 보존 원칙

레거시 시스템을 수정할 때 AI가 가장 흔히 저지르는 치명적 실수는 "더 깔끔한 코드"를 만든다며 기존 인터페이스를 마음대로 변경하는 것이다. 이는 자동 채점 스크립트에서 0점 처리되는 주원인이다.

### 엄격히 보존해야 할 시그니처 4대 요소
1. **엔드포인트 URL 및 HTTP 메서드:**
   - 예: 기존 `/api/v1/auth/login` (POST)를 임의로 `/api/login`이나 `/auth/token`으로 변경 금지.
2. **요청 파라미터 및 바디 JSON 키 명명법:**
   - 예: 기존 요청이 `{"user_id": "operator_01", "auth_pw": "secure_pass_123"}`라면, 임의로 `username`, `password`로 변경 금지.
3. **응답 JSON 스키마 구조 및 상태 코드:**
   - 기존 응답 구조가 `{"status": "SUCCESS", "result": {"token": "sample_token_abc123"}}`라면 최상단에 바로 `{"access_token": "sample_token_abc123"}`를 반환하도록 변경 금지.
   - 성공 시 상태 코드가 200인지 201인지 기존 규격을 준수.
4. **기존 인증 방식:**
   - Header `Authorization: Bearer <token>` 방식, Cookie 세션 방식, 또는 Custom Header (`X-API-KEY`) 방식을 임의로 교체하지 말 것.

---

## 6. 최소 범위 수정 및 `git diff` 검증 절차

서브 에이전트(`GPT 5.6-terra medium`)가 작업을 마친 직후, 메인 에이전트와 수험자는 반드시 아래 절차에 따라 변경 범위를 전수 검증한다.

### 1단계: 변경 파일 목록 및 변경 라인 수 확인 (`git diff --stat`)
```bash
git status --short
git diff --stat
```
- **검증 기준:** 변경된 파일 수가 합의된 범위(예: 1~2개 파일) 이내여야 한다. 불필요한 파일(README, 패키지 락 파일, 설정 파일 등)이 수정 목록에 나타나면 즉시 원복한다.

### 2단계: 상세 변경 내역 라인별 감사 (`git diff`)
```bash
git diff
```
- **검증 체크포인트:**
  - 불필요한 전역 포매팅으로 수백 줄의 인덴트나 공백이 바뀌지 않았는가?
  - 기존 주석이나 비즈니스 로직 설명이 삭제되지 않았는가?
  - 디버깅용으로 삽입했던 임시 `print()`, `console.log()` 구문이 남아있지 않은가?
  - 비밀번호, API 키, 로컬 경로 등 민감 정보가 하드코딩되지 않았는가?

### 3단계: 원복 필요 시 명령
> ⚠️ **주의:** 시험 중 `git add`, `git commit`, `git reset`, `git clean` 실행은 전면 금지됩니다. 잘못 수정한 특정 파일만 원래대로 되돌릴 때 `git checkout -- <file>` 또는 `git restore <file>`을 사용하며, `git reset`이나 `git clean`은 절대 실행하지 마세요.

```bash
# 특정 파일만 원래대로 되돌리기
git checkout -- path/to/unintended_file.py

# 신규 생성된 불필요한 임시 파일 제거 (git clean 대신 직접 rm)
rm -f path/to/temp_debug.py
```

---

## 7. 회귀 테스트 및 신규 테스트 작성 규칙

수정이 완료되면 반드시 다음 두 가지 유형의 테스트를 모두 실행하여 평가 로그를 남긴다.

### 1. 회귀 테스트 (Regression Test)
기존에 통과하던 기능이 수정 작업으로 인해 망가지지 않았음을 검증:
```bash
# 수정 후 전체 테스트 스위트 재실행
pytest -v | tee after_fix_test_result.log

# 베이스라인과 결과 비교 (실패 항목이 0건이어야 함)
diff baseline_test_result.log after_fix_test_result.log || true
```

### 2. 신규 단위 테스트 추가 (버그 재발 방지 및 신규 기능)
매 태스크마다 고정 템플릿이 아닌 실무자 DM 요구사항에 맞춰 온더플라이 ad-hoc 테스트(`tests/test_*.py`, 예: `tests/test_bugfix_and_new_feature.py`)를 신규 생성하여 실행 (git commit 없이 untracked 유지)하며 아래 3가지 케이스를 포함:
- **Case A (버그 재현 및 해결 확인):** 버그가 발생했던 특정 조건(예: 특수문자가 포함된 아이디로 로그인 시)을 재현하고 정상 동작함을 확인.
- **Case B (신규 기능 정상 경로):** 새롭게 추가된 기능의 대표 정상 입력 케이스 확인.
- **Case C (신규 기능 예외/실패 경로):** 새 기능에 잘못된 인자나 결측값이 들어왔을 때 지정된 예외(400 에러 등)가 발생하는지 확인.

---

## 8. 실무자 DM 확인 질문 목록

1. *"신규 기능 추가나 버그 수정 시 기존 API 엔드포인트 경로, 응답 JSON 스키마, 인증 방식은 그대로 유지해야 하나요?"*
2. *"버그 수정 대상 외에 기존 모듈에서 리팩토링이나 라이브러리 버전 업데이트를 수행해도 되나요, 아니면 기존 의존성을 엄격히 유지해야 하나요?"*
3. *"신규 기능의 에러 응답 포맷(HTTP 상태 코드 및 에러 메시지 형식)은 기존 시스템의 어떤 에러 핸들러 규격을 따라야 하나요?"*
4. *"기존 테스트 스위트 중 현재 실패하고 있는 테스트(`[테스트명]`)가 있는데, 이 실패가 이번 수정 과제에서 해결해야 할 대상인가요?"*

---

## 9. 서브 에이전트(`GPT 5.6-terra medium`)에게 넘길 TASK_SPEC 예시

```markdown
# TASK_SPEC: 인증 토큰 만료 버그 수정 및 세션 연장 API 추가

## 1. 작업 개요
- 대상 파일: `services/auth_service.py`, `routers/auth_router.py` (단 2개 파일만 수정 허용)
- 신규 테스트 파일: `tests/test_auth_patch.py`
- 담당 역할: 서브 에이전트 (GPT 5.6-terra medium)

## 2. 세부 구현 요구사항
1. 버그 수정 (`services/auth_service.py`):
   - 현상: 토큰 만료 시간 계산 시 UTC 타임존 오프셋 누락으로 조기 만료 판정 발생.
   - 조치: `datetime.now(timezone.utc)` 기준으로 만료 여부를 판정하도록 수정.
   - 금지: 기존 암호화 알고리즘(HS256) 및 시크릿 키 로딩 로직은 절대 수정 금지.
2. 기능 추가 (`routers/auth_router.py`):
   - 엔드포인트: `POST /api/v1/auth/refresh`
   - 요청 헤더: `Authorization: Bearer <old_token>`
   - 응답 스키마: `{"status": "SUCCESS", "data": {"token": "refreshed_jwt_token_sample", "expires_in": 3600}}` (기존 로그인 응답 구조와 100% 일치시킬 것)
   - 만료되었거나 변조된 토큰 전송 시: HTTP 401 `{"status": "ERROR", "message": "Invalid token"}` 반환.

## 3. 검증 기준
- 수정 전 기존 테스트 통과 유지: `pytest tests/test_legacy_auth.py` PASS.
- 신규 태스크 맞춤 온더플라이 테스트 통과: `pytest tests/test_auth_patch.py` 3개 케이스(정상 연장, 만료 토큰 연장 거부, 위조 토큰 거부) PASS (git commit 금지, untracked 유지).
- `git diff --stat` 검증 시 변경 파일이 2개(`auth_service.py`, `auth_router.py`) 외에 없을 것.
```

---

## 10. 보고서 및 후속 Q&A 작성용 [결정]-[근거]-[검증]-[한계] 예시

- **[결정]:** 인증 모듈의 토큰 조기 만료 버그 수정 및 세션 연장 API 추가 시, 기존 서비스 아키텍처를 전면 리팩토링하지 않고 `services/auth_service.py`와 `routers/auth_router.py` 단 2개 파일에 한해 국소적으로 최소 수정(Minimal Scoped Fix)함.
- **[근거]:** 실무자 DM을 통해 기존 웹/모바일 클라이언트가 사용 중인 API 시그니처와 JSON 응답 규격을 100% 보존해야 함을 확인하였으며, 대규모 리팩토링은 잠재적 회귀 버그(Regression)를 유발할 위험이 높다는 실무 품질 원칙을 근거로 삼음.
- **[검증]:** 코드 수정 전 기존 테스트 스위트를 실행하여 베이스라인 로그(18개 테스트 통과)를 기록하였고, 수정 후 전체 테스트 재실행을 통해 기존 18개 테스트가 모두 통과함을 확인하였으며, 신규 추가한 재현 및 경계값 테스트 3건(`tests/test_auth_patch.py`)을 포함한 총 21개 테스트 100% 통과 및 `git diff --stat`를 통한 2개 파일 최소 변경을 전수 확인함.
- **[한계]:** 이번 조치는 타임존 오프셋 계산 버그를 해결한 핫픽스(Hotfix) 수준의 최소 수정이므로, 향후 토큰 블랙리스트 관리 및 Redis 기반의 분산 토큰 무효화(Revocation) 기능을 도입하여 보안성을 강화하는 구조적 고도화가 후속 과제로 요구됨.


---

## 🚨 [CCTV / Safety Vision 특화] 안전관제·비전 파이프라인 레거시 버그 타격 포인트

> **만약 CCTV(Safety Vision AI 추론 후처리 코드베이스 / 안전관제 레거시 API)에 관련된 문제라면, 위 기존의 일반 로그인·결제 버그 예시가 아니라 아래 새로 만든 [CCTV·비전 코드베이스 5대 빈출 버그 체크리스트]를 참고하세요.**

---

### 1. CCTV·비전 레거시 디버깅 접근 원칙
- CCTV 비전 AI 및 안전관제 코드베이스 디버깅은 모델 자체(가중치/신경망)를 재학습시키는 것이 아니라, **모델 추론 후처리(Post-processing), 프레임 시계열 추적기(Tracker), 좌표 변환, 경보 판정 로직에 잠복한 소프트웨어 버그를 국소적으로 최소 수정(Minimal Scoped Patch)**하는 것이 출제 의도입니다.
- 아래 5대 패턴은 코파톤 및 실기 평가에서 빈번하게 출제되는 대표적 결함 유형입니다.

---

### 2. CCTV·비전 코드베이스 5대 빈출 버그 체크리스트 및 최소 수정 가이드

#### 버그 1. BBox 좌표계 형식 혼동 (`[x1, y1, x2, y2]` vs `[x, y, w, h]`)
- **증상**: 침입 판정 시 객체가 위험구역 밖에 있는데 침입으로 오판되거나, 쓰러짐 종횡비가 비정상적으로 계산됨.
- **원인**: YOLO 계열의 `[cx, cy, w, h]` 또는 OpenCV의 `[x, y, w, h]` 포맷을 `[x1, y1, x2, y2]`(좌상단-우하단)로 착각하여 `x2 - x1` 대신 너비 자리에 다시 빼기를 적용하거나, `y2`를 높이로 오인.
- **버그 코드 (Before)**:
  ```python
  # bbox가 [x, y, w, h]로 들어오는데 [x1, y1, x2, y2]로 취급하여 버그 발생
  x1, y1, x2, y2 = det["bbox"]
  width = x2 - x1   # 음수 또는 엉뚱한 값 발생!
  height = y2 - y1
  aspect_ratio = width / height
  ```
- **수정 코드 (After - 최소 수정)**:
  ```python
  raw_bbox = det["bbox"]
  # 포맷 명세 확인 후 정규화 (예: [x, y, w, h] -> [x1, y1, x2, y2])
  if len(raw_bbox) == 4:
      x, y, w, h = raw_bbox
      x1, y1, x2, y2 = x, y, x + w, y + h
      aspect_ratio = float(w) / max(float(h), 1e-6)
  ```

---

#### 버그 2. 24시간 모니터링 타임존(UTC vs KST) 및 교대조(Shift) 자정 경계 버그
- **증상**: 야간 교대조(22:00 ~ 익일 06:00)의 사고 건수가 자정(00:00)을 기점으로 날짜가 바뀌면서 두 개로 쪼개지거나, UTC(+0)와 KST(+9) 오프셋 불일치로 집계에서 9시간 누락됨.
- **원인**: 타임스탬프를 단순히 `datetime.fromtimestamp(ts).day`로 묶어 자정 넘김을 다른 근무조로 분리해버리거나 타임존 없이 `datetime.utcnow()`와 `datetime.now()`를 혼용.
- **버그 코드 (Before)**:
  ```python
  # 자정(00:00) 기준으로 shift_date를 분리하여 야간조 인시던트가 단절됨
  event_date = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
  shift_records[event_date].append(event)
  ```
- **수정 코드 (After - 최소 수정)**:
  ```python
  from datetime import datetime, timezone, timedelta
  KST = timezone(timedelta(hours=9))

  # 야간조(Shift C: 전일 22:00 ~ 당일 06:00) 처리 기준 보정 (새벽 00~06시는 전일 야간조에 귀속)
  dt = datetime.fromtimestamp(ts, tz=KST)
  if dt.hour < 6:
      work_date = (dt - timedelta(days=1)).strftime("%Y-%m-%d")
      shift_type = "NIGHT"
  elif 6 <= dt.hour < 14:
      work_date = dt.strftime("%Y-%m-%d")
      shift_type = "DAY"
  else: # 14:00 ~ 22:00: SWING / EVENING
      work_date = dt.strftime("%Y-%m-%d")
      shift_type = "SWING" if dt.hour < 22 else "NIGHT"
  ```

---

#### 버그 3. 연속 프레임 상태 초기화(Reset) 및 루프 종료 누락(Off-by-one / Flush)
- **증상**: 10초 동안 지속된 침입인데 `duration`이 항상 1프레임(0.0초)으로 찍히거나, 영상 마지막 프레임까지 이어진 사고가 결과 리스트에서 누락됨.
- **원인**: 프레임 순회 루프 내부에서 세션 카운터나 상태 변수를 매 반복마다 `streak = 0`으로 초기화하거나, 루프가 끝난 뒤 마지막 진행 중인 사고를 결과 리스트에 `append`하지 않고 종료.
- **버그 코드 (Before)**:
  ```python
  for frame in frames:
      active_alarm = None # 루프 내부에서 초기화하여 연속 상태 파괴!
      if is_danger(frame):
          active_alarm = update_alarm(frame)
  # 루프 종료 후 마지막 active_alarm flush 누락!
  return confirmed_alarms
  ```
- **수정 코드 (After - 최소 수정)**:
  ```python
  active_alarm = None # 루프 외부에서 상태 유지
  for frame in frames:
      if is_danger(frame):
          if active_alarm is None:
              active_alarm = {"start": frame["time"], "end": frame["time"]}
          else:
              active_alarm["end"] = frame["time"]
      else:
          if active_alarm and (active_alarm["end"] - active_alarm["start"] >= min_sec):
              confirmed_alarms.append(active_alarm)
          active_alarm = None

  # 중요: 루프 종료 후 마지막 진행 중이던 사고 Flush 필수!
  if active_alarm and (active_alarm["end"] - active_alarm["start"] >= min_sec):
      confirmed_alarms.append(active_alarm)
  return confirmed_alarms
  ```

---

#### 버그 4. ZeroDivision 및 NoneType 크래시
- **증상**: 객체가 카메라 화각 경계에 걸쳐 높이 `h == 0`이거나 노이즈로 `bbox` 필드가 `None` 또는 비어있을 때 파이프라인 전체가 `ZeroDivisionError` 또는 `TypeError`로 중단됨.
- **원인**: BBox 유효성 검사 없이 바로 나눗셈 또는 인덱싱 수행.
- **버그 코드 (Before)**:
  ```python
  w = bbox[2] - bbox[0]
  h = bbox[3] - bbox[1]
  ratio = w / h  # h가 0일 때 ZeroDivisionError 크래시!
  ```
- **수정 코드 (After - 최소 수정)**:
  ```python
  if not bbox or len(bbox) < 4:
      return None
  w = max(0.0, float(bbox[2] - bbox[0]))
  h = max(0.0, float(bbox[3] - bbox[1]))
  if h <= 0.0 or w <= 0.0:
      return None
  ratio = w / max(h, 1e-6)
  ```

---

#### 버그 5. 임계값 등호(`>=` vs `>`) 불일치 및 부동소수점 오차
- **증상**: 정확히 5.0초 동안 지속되었거나 confidence가 정확히 0.70인 경계 케이스가 누락되어 테스트가 1건 차이로 실패함.
- **원인**: 명세서에는 "5초 이상(`>= 5.0`)"으로 명시되었으나 코드에 `> 5.0`으로 작성되었거나, `0.1 + 0.2` 부동소수점 오차로 미달 처리.
- **버그 코드 (Before)**:
  ```python
  # 명세: "지속시간 5.0초 이상"
  if duration > 5.0 and conf > 0.7:  # 5.0초 정확한 경계값 탈락
      trigger_alert()
  ```
- **수정 코드 (After - 최소 수정)**:
  ```python
  # 부동소수점 마진(1e-5) 및 이상(>=) 정확 반영
  if (duration + 1e-5) >= 5.0 and (conf + 1e-5) >= 0.70:
      trigger_alert()
  ```
