# [TASK_SPEC] 서브 에이전트 작업 명세서

> **작성자:** 메인 아키텍트 (`Sol 6.1 xhigh`)  
> **수신자:** 서브 워커 (`Luna 6 xhigh`)  
> **규칙:** 본 명세서에 지정된 파일 범위와 제약 조건 외 임의 수정 금지. 완료 후 `.probe-kit/runtime/SUB_RESULT.md`에 10줄 이내로 보고할 것.

---

### 1. 이번 단계 목표
- **목표:** 주문 데이터 정제 파이프라인에서 취소 건 제외 및 중복 주문 처리 로직 구현 (단일 모듈 MVP 구현)

### 2. 대상 파일 범위
- **수정 허용 파일:**
  - `src/pipeline/aggregator.py` (함수: `clean_orders`, `calculate_metrics`)
  - `tests/test_edge_cases.py` (신규 예외 케이스 검증 테스트 케이스 추가)
- **수정 절대 금지 파일:**
  - `src/api/routes.py` (기존 API 엔드포인트 및 라우터 인터페이스 보존)
  - `config/settings.py` (시스템 글로벌 설정 및 DB 연결 인터페이스 보존)
  - `.gitignore` (Git 트래킹 제외 목록 수정 절대 금지)

### 3. 실무자 DM 확인 예외 조건 (현업 비즈니스 규칙)
- **조건 1 (취소 주문 제외):** `status == 'CANCELLED'` 데이터는 전체 집계 및 성공 비율 계산 분모에서 완전히 제외
- **조건 2 (중복 주문 최신화):** 동일한 `order_id`가 복수 개 존재할 경우 가장 최근의 `updated_at` 타임스탬프를 가진 레코드 1건만 유지
- **조건 3 (결측치 기본값):** `quantity` 필드가 누락(null/NaN/빈값)된 경우 기본값 `0`으로 채우지 않고 해당 행을 `invalid_records` 목록으로 분리

### 4. 금지 사항 (Hard Constraints)
- 불필요한 디자인 패턴/캐싱 계층 추가 및 오버엔지니어링 전면 금지 (서술형 답변 대비 단순 명확성 유지)
- 시크릿, 패스워드, 개인 식별 정보, API 키 코드 내 하드코딩 절대 금지
- 웹 서버 구동 시 `localhost` 바인딩 금지 (반드시 `0.0.0.0` 바인딩 준수)
- `.gitignore` 파일 수정 금지 (임시 파일은 `.git/info/exclude`로 통제됨)

### 5. 실행할 검증 명령어
- **베이스라인 테스트 (회귀 방지):**
  - `pytest tests/test_aggregator.py` (기존 테스트 5건 전원 통과 확인)
- **정상 경로 및 예외 케이스 테스트:**
  - `python tests/test_edge_cases.py` (정상 주문, 취소 주문, 중복 ID, 결측 필드 입력 검증)

### 6. 완료 기준 (Definition of Done)
- [ ] 기존 베이스라인 테스트가 깨짐 없이 100% 통과할 것
- [ ] 취소 데이터 분모 제외 및 중복 최신화 로직이 예외 테스트를 통해 검증될 것
- [ ] `git diff --stat` 확인 시 지정된 2개 파일 외 변경이 없을 것

### 7. 보고 형식
- 서브 에이전트는 작업 완료 직후 `.probe-kit/runtime/SUB_RESULT.md` 표준 10줄 양식에 따라 결과를 기록하고, 메인 에이전트에게 알린 후 `/clear`를 준비할 것.
