#!/usr/bin/env bash
# scripts/handoff.sh: 세션 분할 및 인수인계를 위한 기계 정보 자동 수집 및 HANDOFF.md 스켈레톤 생성 스크립트

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KIT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
RUNTIME_DIR="${KIT_DIR}/runtime"
WORKSPACE_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

HANDOFF_FILE="${RUNTIME_DIR}/HANDOFF.md"
mkdir -p "${RUNTIME_DIR}"

NOW="$(date '+%Y-%m-%d %H:%M:%S')"

# 1. STATE 정보 수집 (state.sh 인터페이스 연동 또는 폴백)
STATE_ID="7"
STATE_NAME="핑퐁구현"
ELAPSED_MIN="--분"
REMAIN_MIN="--분"
PROGRESS_PCT="--%"
DELAY_MIN="0분"
STATE_RAW_OUTPUT=""

if [ -f "${KIT_DIR}/scripts/state.sh" ]; then
  if STATE_STATUS_OUT="$(bash "${KIT_DIR}/scripts/state.sh" status 2>/dev/null)"; then
    STATE_RAW_OUTPUT="${STATE_STATUS_OUT}"
    PARSED_ID="$(echo "${STATE_STATUS_OUT}" | grep -E '^STATE_ID=' | head -n 1 | cut -d'=' -f2 || true)"
    PARSED_NAME="$(echo "${STATE_STATUS_OUT}" | grep -E '^STATE_NAME=' | head -n 1 | cut -d'=' -f2 || true)"
    PARSED_ELAPSED="$(echo "${STATE_STATUS_OUT}" | grep -E '^ELAPSED_MIN=' | head -n 1 | cut -d'=' -f2 || true)"
    PARSED_REMAIN="$(echo "${STATE_STATUS_OUT}" | grep -E '^REMAIN_MIN=' | head -n 1 | cut -d'=' -f2 || true)"
    PARSED_PROGRESS="$(echo "${STATE_STATUS_OUT}" | grep -E '^PROGRESS_PCT=' | head -n 1 | cut -d'=' -f2 || true)"
    PARSED_DELAY="$(echo "${STATE_STATUS_OUT}" | grep -E '^DELAY_MIN=' | head -n 1 | cut -d'=' -f2 || true)"

    [ -n "${PARSED_ID}" ] && STATE_ID="${PARSED_ID}"
    [ -n "${PARSED_NAME}" ] && STATE_NAME="${PARSED_NAME}"
    [ -n "${PARSED_ELAPSED}" ] && ELAPSED_MIN="${PARSED_ELAPSED}분"
    [ -n "${PARSED_REMAIN}" ] && REMAIN_MIN="${PARSED_REMAIN}분"
    [ -n "${PARSED_PROGRESS}" ] && PROGRESS_PCT="${PARSED_PROGRESS}%"
    [ -n "${PARSED_DELAY}" ] && DELAY_MIN="${PARSED_DELAY}분"
  fi
elif [ -f "${RUNTIME_DIR}/STATE.md" ]; then
  CUR_ID="$(sed -n 's/.*STATE:CURRENT=\([0-9]*\).*/\1/p' "${RUNTIME_DIR}/STATE.md" | head -n 1 || true)"
  [ -n "${CUR_ID}" ] && STATE_ID="${CUR_ID}"
fi

# 2. Git 형상 정보 수집
COMMIT_COUNT="$(git rev-list --count HEAD 2>/dev/null || echo "0")"
LATEST_COMMIT="$(git log -1 --pretty=format:"%h %s" 2>/dev/null || echo "커밋 없음")"
GIT_LOG_5="$(git log --oneline -5 2>/dev/null || echo "Git 커밋 기록이 없습니다.")"
GIT_DIFF_STAT="$(git diff --stat 2>/dev/null || true)"
[ -z "${GIT_DIFF_STAT}" ] && GIT_DIFF_STAT="작업 디렉토리(Working Tree) 변경 사항 없음 (클린)"

GIT_DIFF_CACHED="$(git diff --cached --stat 2>/dev/null || true)"
[ -z "${GIT_DIFF_CACHED}" ] && GIT_DIFF_CACHED="스테이징된(Staged) 변경 사항 없음"

GIT_UNTRACKED="$(git status -s 2>/dev/null | grep '^\?\?' | head -n 10 || true)"
[ -z "${GIT_UNTRACKED}" ] && GIT_UNTRACKED="미추적 파일 없음"

# 3. 직전 서브 에이전트 결과(SUB_RESULT.md) 수집
SUB_RESULT_SNIPPET=""
if [ -f "${RUNTIME_DIR}/SUB_RESULT.md" ]; then
  SUB_RESULT_SNIPPET="$(cat "${RUNTIME_DIR}/SUB_RESULT.md")"
else
  SUB_RESULT_SNIPPET="직전 서브 에이전트 실행 결과 파일(${RUNTIME_DIR}/SUB_RESULT.md)이 아직 생성되지 않았습니다."
fi

# 4. 의사결정 메모(NOTES_TEMP.md 또는 templates/NOTES.md) 수집
DECISION_SNIPPET=""
NOTES_TARGET=""
if [ -f "${WORKSPACE_ROOT}/NOTES_TEMP.md" ]; then
  NOTES_TARGET="${WORKSPACE_ROOT}/NOTES_TEMP.md"
elif [ -f "${WORKSPACE_ROOT}/NOTES.md" ]; then
  NOTES_TARGET="${WORKSPACE_ROOT}/NOTES.md"
elif [ -f "${KIT_DIR}/templates/NOTES.md" ]; then
  NOTES_TARGET="${KIT_DIR}/templates/NOTES.md"
fi

if [ -n "${NOTES_TARGET}" ] && [ -f "${NOTES_TARGET}" ]; then
  DECISION_EXTRACT="$(grep -E '\[결정|\[근거|\[포기' "${NOTES_TARGET}" 2>/dev/null || true)"
  if [ -n "${DECISION_EXTRACT}" ]; then
    DECISION_SNIPPET="${DECISION_EXTRACT}"
  else
    DECISION_SNIPPET="$(head -n 25 "${NOTES_TARGET}")"
  fi
else
  DECISION_SNIPPET="기록된 NOTES 파일이 없습니다. 메인 에이전트(Sol 6.1 xhigh)가 확정된 결정을 직접 보강하세요."
fi

# 5. HANDOFF.md 파일 생성
cat <<EOF > "${HANDOFF_FILE}"
# 세션 인수인계서 (HANDOFF.md)

이 문서는 이전 세션(구 세션)에서 확정한 핵심 의사결정, 비즈니스 제약, 소스코드 변경 내역 및 다음 액션을 신규 세션으로 무손실 인계하기 위한 표준 인수인계서입니다. 신규 세션은 본 문서를 정독하고 복창한 뒤 작업을 재개해야 합니다.

---

## 1. 현재 메타데이터

- **작성 시각:** ${NOW} KST
- **현재 진행 단계 (STATE):**
  - 단계 번호 (STATE_ID): \`${STATE_ID}\`
  - 단계 명칭 (STATE_NAME): \`${STATE_NAME}\`
  - 경과 시간 (ELAPSED_MIN): \`${ELAPSED_MIN}\`
  - 마감까지 잔여 시간 (REMAIN_MIN): \`${REMAIN_MIN}\`
  - 진척률 (PROGRESS_PCT): \`${PROGRESS_PCT}\`
  - 목표 대비 지연 시간 (DELAY_MIN): \`${DELAY_MIN}\`
- **Git 형상 관리 현황:**
  - 누적 커밋 수: \`${COMMIT_COUNT}개\`
  - 최신 커밋 해시 및 메시지: \`${LATEST_COMMIT}\`
- **최근 5개 Git 커밋 내역:**
\`\`\`text
${GIT_LOG_5}
\`\`\`
- **인수인계 발생 사유 (해당 항목 체크):**
  - [x] Step 1 핵심 기능 구현 완료 직후 컨텍스트 리셋
  - [ ] 메인 에이전트의 이전 제약 망각(Drift) 방지
  - [ ] 대규모 방향 전환 (A안 폐기 후 B안 전환)
  - [ ] 구현 종료 및 최종 검증/보고서 모드 진입

---

## 2. 인간이 확정한 아키텍처 결정 사항 ([결정] - [근거] - [포기한 대안])

${DECISION_SNIPPET}

### [결정 1] 핵심 데이터 처리 및 아키텍처 방향
- **결정:** 대용량 데이터는 메모리 청크 스트리밍 방식으로 처리하며, 복잡한 프레임워크 도입 없이 파이썬 표준 라이브러리 위주로 구현한다.
- **근거:** 시험장 환경의 4GB RAM 제한 조건에서 OOM 크래시를 방지하고 외부 패키지 설치 의존성을 배제하기 위함.
- **포기한 대안:** 외부 대용량 분산 처리 라이브러리 도입 (설치 지연 및 환경 비호환 리스크로 배제).

### [결정 2] 인터페이스 및 호환성 보장
- **결정:** 기존 레거시 함수 시그니처와 반환 데이터 포맷을 100% 동일하게 유지한다.
- **근거:** 베이스라인 채점 에이전트의 블랙박스 회귀 테스트 통과율을 보장하기 위함.
- **포기한 대안:** 레거시 코드 전면 리팩토링 및 API 재설계 (테스트 호환성 파괴 위험으로 폐기).

---

## 3. 실무자 DM 핵심 제약 체크리스트 (Hard Constraints)

아래 항목은 실무자 에이전트와의 질의응답을 통해 확정된 불변의 도메인 규칙입니다. 신규 세션은 코드를 작성하거나 검증할 때 이 규칙을 절대 위반해서는 안 됩니다:

- [x] **[제약 1 - 취소/환불 데이터 배제]:** 취소 또는 환불 상태인 레코드는 매출 집계 및 전환율 분모에서 완전히 제외할 것.
- [x] **[제약 2 - 중복 데이터 처리]:** 중복 식별자 발생 시 가장 최신 타임스탬프 기준 1건만 유효 레코드로 인정할 것.
- [x] **[제약 3 - 레거시 모듈 보호]:** 기존 인증 및 설정 모듈의 핵심 시그니처를 절대 임의 변경하지 말 것.
- [x] **[제약 4 - 네트워크 바인딩]:** 모든 웹 애플리케이션 및 API 서비스는 반드시 호스트 \`0.0.0.0\`으로 바인딩할 것.
- [x] **[제약 5 - 추가 외부 라이브러리 동결]:** 사전에 허용되지 않은 신규 서드파티 라이브러리 설치 금지.

---

## 4. 소스코드 및 파일 변경 현황

### 1) 미반영 작업 트리 변경 사항 (\`git diff --stat\`)
\`\`\`text
${GIT_DIFF_STAT}
\`\`\`

### 2) 스테이징된 변경 사항 (\`git diff --cached --stat\`)
\`\`\`text
${GIT_DIFF_CACHED}
\`\`\`

### 3) 신규 미추적 파일 목록 (\`git status -s\`)
\`\`\`text
${GIT_UNTRACKED}
\`\`\`

### 4) 손대면 안 되는 보호 대상 파일
- 기존 베이스라인 테스트 파일 (예: \`tests/baseline/*\`)
- 시스템 환경 설정 및 인증 토큰 파일
- 과제 하네스 설정 파일

---

## 5. 검증 완료된 항목 vs 실패/미검증 항목

### 1) ✅ 직전 서브 에이전트 실행 요약 (\`SUB_RESULT.md\` 발췌)
\`\`\`markdown
${SUB_RESULT_SNIPPET}
\`\`\`

### 2) ⚠️ 실패 및 미검증 항목 (Edge Cases to Verify)
- 결측치(\`None\`, 빈 문자열) 유입 시 방어 로직 검증 필요
- 극단적 경계값(음수 값, 대규모 볼륨) 스트레스 테스트 미수행
- 모듈 간 결합 통합 테스트 미수행

---

## 6. 미해결 리스크 및 기술 부채

- **데이터 파싱 안전장치:** 예외 데이터 유입 시 파이프라인 중단 방지를 위한 안전 형변환 보강 필요.
- **임시 하드코딩 요소:** 프로덕션 환경 분기를 위한 환경변수 처리 점검 필요.
- **제출 규격 점검:** 채점기가 요구하는 출력 파일명 및 포맷 최종 준수 여부 점검 필요.

---

## 7. 새 세션이 즉시 실행해야 할 다음 1~3가지 행동 (Next Actions)

신규 세션은 복창 완료 및 인간의 승인을 받은 즉시 아래 3가지 행동을 순서대로 수행해야 합니다:

- [ ] **Action 1:** 미검증 예외 케이스(결측치, 경계값) 방어 로직 보강을 위한 서브 지시서(\`.probe-kit/runtime/TASK_SPEC.md\`) 작성 및 위임.
- [ ] **Action 2:** 다음 단계 기능 모듈 구현 명세 수립 및 단위 테스트 검증 지시.
- [ ] **Action 3:** 마일스톤 완료 후 \`bash .probe-kit/scripts/state.sh next\` 실행 및 진척률 동기화.

---

## 8. 새 세션 금지 사항 (Hard Constraints for New Session)

- **[금지 1] 메인 에이전트의 비즈니스 코드 직접 작성 금지:** 메인은 오직 아키텍트 역할만 수행하며, 코드 구현은 반드시 서브 에이전트에게 위임한다.
- **[금지 2] 실무자 DM 합의 사항 번복 금지:** 제3절의 도메인 불변 규칙을 임의로 왜곡하거나 삭제하지 않는다.
- **[금지 3] 기존 베이스라인 테스트 임의 수정 금지:** 테스트 통과를 위해 테스트 단언문(assert)을 변조하는 행위를 절대 엄금한다.
- **[금지 4] 승인 없는 외부 라이브러리 설치 금지:** 표준 라이브러리와 기존 환경 내에서만 구현한다.
EOF

# 워크스페이스 루트에도 편의용 HANDOFF.md 복사본 보장 (.git/info/exclude로 자동 격리됨)
if [ -n "${WORKSPACE_ROOT:-}" ] && [ "${WORKSPACE_ROOT}" != "${RUNTIME_DIR}" ] && [ -d "${WORKSPACE_ROOT}" ]; then
  cp "${HANDOFF_FILE}" "${WORKSPACE_ROOT}/HANDOFF.md" 2>/dev/null || true
fi

# 6. 사용자 안내 메시지 출력
echo "================================================================================"
echo "📋 [HANDOFF] 세션 인수인계서 자동 생성 완료"
echo "================================================================================"
echo "  - 저장 위치: ${HANDOFF_FILE}"
echo "  - 수집 정보: 현재 STATE(${STATE_NAME}), Git 커밋 ${COMMIT_COUNT}건, diff 현황, 최신 SUB_RESULT"
echo "--------------------------------------------------------------------------------"
echo "👉 [다음 단계 1 — 구 세션 메인 에이전트 보강]:"
echo "   현재 터미널의 메인 에이전트(Sol 6.1 xhigh)에게 [메인 프롬프트 5]를 입력하여"
echo "   인간과의 합의 내용, 실무자 DM 제약, Next Actions 1~3을 최종 보강하세요."
echo ""
echo "👉 [다음 단계 2 — 신규 세션 전환 및 복창]:"
echo "   구 세션 종료 후 새 터미널에서 Sol 6.1 xhigh 세션을 시작하고,"
echo "   [메인 프롬프트 6]을 입력하여 결정 사항을 복창하게 한 뒤 승인하세요."
echo "================================================================================"
