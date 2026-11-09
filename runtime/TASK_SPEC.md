# [TASK_SPEC] 서브 에이전트 작업 명세서

> **작성자:** 메인 아키텍트 (`Sol 6.1 xhigh`)  
> **수신자:** 서브 워커 (`GPT 5.6-terra medium`)  
> **핵심 원칙:** [시작 · 정의 · 기준 · 종료] 4대 축 기반 명세 준수 및 지정 범위 외 임의 수정 절대 금지. 완료 후 `.probe-kit/runtime/SUB_RESULT.md`에 핵심 결과와 변경 사항 위주의 명확한 요약 보고를 남길 것 (불필요한 줄 수 제한 없음).

---

### 1. [시작 / Start] 이번 단계 단일 목표 및 진입 조건 (Entry Conditions)
- **단일 목표 (Single Goal):** 주문 데이터 정제 파이프라인에서 취소 건 제외 및 중복 주문 처리 로직 구현 (단일 모듈 MVP 구현)
- **선행 완료 상태 (Pre-conditions):**
  - 직전 단계(Step 0) 원천 데이터 적재 및 스키마 검증 완료 확인
  - Git 작업 트리가 깨끗한 상태(uncommitted 변경 사항 없음)인지 확인
- **사전 베이스라인 체크 (Baseline Pre-check):**
  - 코드 수정 착수 전 기존 베이스라인 테스트 100% PASS 확인 (`pytest tests/test_aggregator.py`)
  - 사전 베이스라인 실패 시 코드 작성 시작을 금지하고 즉시 원인 보고

### 2. [통제 / Scope] 대상 파일 범위 및 금지 사항 (Hard Constraints)
- **수정 허용 파일:**
  - `src/pipeline/aggregator.py` (함수: `clean_orders`, `calculate_metrics`)
  - `tests/test_edge_cases.py` (신규 예외 케이스 검증 온더플라이 테스트 케이스 추가)
- **수정 절대 금지 파일:**
  - `src/api/routes.py` (기존 API 엔드포인트 및 라우터 인터페이스 보존)
  - `config/settings.py` (시스템 글로벌 설정 및 DB 연결 인터페이스 보존)
  - `.gitignore` (Git 트래킹 제외 목록 수정 절대 금지 - 임시 파일은 `.git/info/exclude`로 통제)
- **금지 사항 (Hard Constraints):**
  - 불필요한 디자인 패턴/캐싱 계층 추가 및 오버엔지니어링 전면 금지 (서술형 답변 대비 단순 명확성 유지)
  - 시크릿, 패스워드, 개인 식별 정보, API 키 코드 내 하드코딩 절대 금지
  - 웹 서버 구동 시 `localhost` 바인딩 금지 (반드시 `0.0.0.0` 바인딩 준수)
  - `.gitignore` 파일 수정 금지 (임시 파일은 `.git/info/exclude`로 통제됨)
  - 시험 중 `git add` / `git commit` / `git reset` / `git clean` 실행 전면 금지 (테스트 코드는 커밋하지 않으며 test 파일은 untracked 상태 유지)

### 3. [정의 / Definition] 도메인 용어·상태 및 입출력 스키마 정의
- **도메인 핵심 용어 정의:**
  - `1 row (주문 레코드)`: 개별 고객의 1회 결제 시도 단위 (고유 식별자: `order_id`)
  - `유효 주문 (Valid Order)`: 정상 결제 완료 상태이며 취소되지 않은 주문 건
  - `전체 주문 수량 (Total Volume)`: 집계 대상 유효 주문의 `quantity` 총합
- **상태 코드(Status/State) 정의:**
  - `ACTIVE`: 정상 진행/완료 주문 (모든 집계 및 통계의 분모·분자에 포함)
  - `CANCELLED`: 고객 취소 또는 관리자 강제 취소 주문 (성공 비율 및 총액 계산 분모에서 완전 제외)
  - `DISCARDED`: 중복 주문 중 이전 타임스탬프를 가진 만료 레코드 (집계 대상에서 제외)
- **입·출력 데이터 스키마 및 계약 (Contract):**
  - **입력 DataFrame/Dict:**
    - `order_id`: string (고유 식별자, 필수)
    - `user_id`: string (고객 ID)
    - `amount`: float (결제 금액, `amount >= 0.0`)
    - `quantity`: int (주문 수량, 양의 정수 `quantity > 0`, null 허용 안 됨)
    - `status`: string (`ACTIVE` | `CANCELLED` | `PENDING`)
    - `updated_at`: ISO-8601 string (`YYYY-MM-DDTHH:MM:SSZ`)
  - **출력 데이터 계약:**
    - 반환 타입: `Tuple[pd.DataFrame, pd.DataFrame]` (`valid_df`, `invalid_df`)
    - 수치 반올림: 집계 지표(예: 전환율, 평균 단가)는 소수점 둘째 자리(`round(x, 2)`)
    - 정렬 순서: `updated_at` 내림차순(최신순), 동률 시 `order_id` 오름차순

### 4. [기준 / Criteria] 비즈니스 판정 기준 및 경계값 (Acceptance & Boundary Criteria)
- **실무자 DM 확인 비즈니스 규칙:**
  - **규칙 1 (취소 주문 제외):** `status == 'CANCELLED'` 데이터는 전체 집계 및 성공 비율 계산 분모에서 완전히 제외
  - **규칙 2 (중복 주문 최신화):** 동일한 `order_id`가 복수 개 존재할 경우 가장 최근의 `updated_at` 타임스탬프를 가진 레코드 1건만 유지 (`DISCARDED` 처리)
  - **규칙 3 (결측치 기본값 대체 금지):** `quantity` 필드가 누락(null/NaN/빈값)된 경우 임의로 `0`으로 채우지 않고 해당 행을 `invalid_records` 목록으로 분리
- **수치 경계값 및 임계값(Threshold) 기준:**
  - 결제 금액 유효 범위: `amount >= 0.0` (0원은 허용하되 음수 `< 0.0`는 이상치 처리)
  - 주문 수량 경계값: `quantity >= 1` (0 이하의 수량 `quantity <= 0`은 유효 주문 불인정)
  - 타임스탬프 비교: `updated_at` 비교 시 동일 초인 경우 원천 인덱스 후순위 우선
- **결측치·이상치 처리 기준:**
  - 임의 0 대체 및 임의 드롭 금지: 유효하지 않은 모든 레코드는 `invalid_records`로 격리하여 원인 보존
- **기준 충돌 시 우선순위:**
  - 처리 속도(Throughput)보다 **데이터 정합성 및 보존(Data Integrity)** 최우선
  - 성능 최적화를 위한 배치 건너뛰기 금지, 모든 이상치 분리 격리 원칙 준수

### 5. [검증 / Verification] 실행할 검증 명령어
- **1) 베이스라인 회귀 검증 (Baseline Regression Test):**
  - `pytest tests/test_aggregator.py` (기존 테스트 5건 전원 통과 확인)
- **2) 태스크 맞춤 온더플라이(On-the-fly) ad-hoc 테스트 (필수):**
  - 매 태스크마다 실무자 DM 요구사항에 맞춘 전용 테스트 코드(예: `tests/test_edge_cases.py` 또는 ad-hoc 검증 스크립트)를 온더플라이로 즉석 작성하여 실행
  - *고정 템플릿 사용 금지, git commit 없이 untracked 유지*
- **3) 정상 경로 + 예외/경계값 검증 (Happy Path & Edge Cases):**
  - `python3 tests/test_edge_cases.py` (정상 주문, 취소 주문, 중복 ID, 결측 필드 입력 검증)
  - 필요 시 Python 한 줄 커맨드로 데이터 정합성 ad-hoc 검증:
    `python3 -c "import tests.test_edge_cases as t; t.run_boundary_checks()"`

### 6. [정의 & 기준 / DoD] 완료 정의 (Definition of Done)
- [ ] 기존 베이스라인 테스트가 깨짐 없이 100% 통과할 것 (`pytest tests/test_aggregator.py`)
- [ ] `[정의]` 섹션에 명시된 입·출력 데이터 스키마 및 반환 타입 계약을 정확히 준수할 것
- [ ] `[기준]` 섹션의 실무자 DM 규칙(취소 건 분모 제외, 중복 최신화, 결측치 격리) 및 경계값 조건이 전원 통과할 것
- [ ] 태스크별 DM 요구사항에 맞춘 온더플라이 테스트 코드를 직접 작성·실행하여 통과하고 결과를 `SUB_RESULT.md`에 기록할 것 (git commit 금지, untracked 유지)
- [ ] `git diff --stat` 확인 시 지정된 수정 허용 파일 외 변경이 일체 없을 것

### 7. [종료 / End] 종료 조건, 멈춤 조건 및 완료 후 조치 (Exit & Stop Protocol)
- **멈춤 조건 (Stop / Abort Condition) - 발견 즉시 구현 중단 및 대기:**
  - 지정 파일 범위 밖의 파일 수정이 불가피한 구조적 결함을 발견했을 때
  - 요구사항, 도메인 상태 정의, 또는 입출력 스키마에 모호성이 있어 자의적 해석이 필요할 때
  - 사전 베이스라인 테스트 실패 또는 회귀 실패의 원인이 불명확할 때
  - *위 상황 발생 시 임의 추측 구현을 즉시 멈추고 `SUB_RESULT.md`에 [차단(블로커)] 사유를 기록 후 메인에게 보고*
- **완료 후 필수 조치 (Post-Completion Actions):**
  1. `.probe-kit/runtime/SUB_RESULT.md` 요약 보고서 작성 (필수 항목 표준 양식 준수, 불필요한 줄 수 제한 없음)
  2. `bash .probe-kit/scripts/handoff.sh log "sub done: <요약>"` 실행 (실패 시 `python3 .probe-kit/scripts/handoff.py log "sub done" "<요약>"`, 여의치 않을 시 `runtime/HANDOFF.md` 표에 직접 추가)
  3. 메인 에이전트에게 완료 보고 후 **서브 터미널에서 즉시 `/clear` 실행** (누적 토큰 0 리셋 필수)
