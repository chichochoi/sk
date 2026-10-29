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
STATE_ID="1"
STATE_NAME="설치"

if [ -f "${KIT_DIR}/scripts/state.sh" ]; then
  if STATE_STATUS_OUT="$(bash "${KIT_DIR}/scripts/state.sh" status 2>/dev/null)"; then
    PARSED_ID="$(echo "${STATE_STATUS_OUT}" | grep -E '^STATE_ID=' | head -n 1 | cut -d'=' -f2 || true)"
    PARSED_NAME="$(echo "${STATE_STATUS_OUT}" | grep -E '^STATE_NAME=' | head -n 1 | cut -d'=' -f2 || true)"

    [ -n "${PARSED_ID}" ] && STATE_ID="${PARSED_ID}"
    [ -n "${PARSED_NAME}" ] && STATE_NAME="${PARSED_NAME}"
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

# 4. 현재 작업 명세서(TASK_SPEC.md) 수집
TASK_SPEC_SNIPPET=""
if [ -f "${RUNTIME_DIR}/TASK_SPEC.md" ]; then
  TASK_SPEC_SNIPPET="$(cat "${RUNTIME_DIR}/TASK_SPEC.md")"
elif [ -f "${WORKSPACE_ROOT}/TASK_SPEC.md" ]; then
  TASK_SPEC_SNIPPET="$(cat "${WORKSPACE_ROOT}/TASK_SPEC.md")"
else
  TASK_SPEC_SNIPPET="작업 명세서(TASK_SPEC.md)가 아직 생성되지 않았습니다."
fi

# 5. 의사결정 및 DM 메모(NOTES_TEMP.md 또는 templates/NOTES.md) 수집
DECISION_SNIPPET=""
DM_SNIPPET=""
NOTES_TARGET=""
if [ -f "${WORKSPACE_ROOT}/NOTES_TEMP.md" ]; then
  NOTES_TARGET="${WORKSPACE_ROOT}/NOTES_TEMP.md"
elif [ -f "${WORKSPACE_ROOT}/NOTES.md" ]; then
  NOTES_TARGET="${WORKSPACE_ROOT}/NOTES.md"
elif [ -f "${KIT_DIR}/templates/NOTES.md" ]; then
  NOTES_TARGET="${KIT_DIR}/templates/NOTES.md"
fi

if [ -n "${NOTES_TARGET}" ] && [ -f "${NOTES_TARGET}" ]; then
  DECISION_EXTRACT="$(grep -E '\[결정|\[근거|\[검증|\[한계' "${NOTES_TARGET}" 2>/dev/null || true)"
  if [ -n "${DECISION_EXTRACT}" ]; then
    DECISION_SNIPPET="${DECISION_EXTRACT}"
  else
    DECISION_SNIPPET="$(head -n 25 "${NOTES_TARGET}")"
  fi

  DM_EXTRACT="$(sed -n '/## 3\. 실무자 DM Q&A 기록/,/---/p' "${NOTES_TARGET}" 2>/dev/null || true)"
  if [ -n "${DM_EXTRACT}" ]; then
    DM_SNIPPET="${DM_EXTRACT}"
  else
    DM_SNIPPET="기록된 실무자 DM Q&A 내역이 없습니다."
  fi
else
  DECISION_SNIPPET="기록된 NOTES 파일이 없습니다. 메인 에이전트(Sol 6.1 xhigh)가 확정된 결정을 직접 보강하세요."
  DM_SNIPPET="기록된 실무자 DM Q&A 내역이 없습니다."
fi

# 6. HANDOFF.md 파일 생성
cat <<EOF > "${HANDOFF_FILE}"
# 세션 인수인계서 (HANDOFF.md)

이 문서는 이전 세션(구 세션)에서 확정한 핵심 의사결정, 비즈니스 제약, 소스코드 변경 내역 및 다음 액션을 신규 세션으로 무손실 인계하기 위한 표준 인수인계서입니다. 신규 세션은 본 문서를 정독하고 복창한 뒤 작업을 재개해야 합니다.

---

## 1. 현재 메타데이터

- **작성 시각:** ${NOW} KST
- **현재 진행 단계 (STATE):**
  - 단계 번호 (STATE_ID): \`${STATE_ID}/10\`
  - 단계 명칭 (STATE_NAME): \`${STATE_NAME}\`
- **Git 형상 관리 현황:**
  - 누적 커밋 수: \`${COMMIT_COUNT}개\`
  - 최신 커밋 해시 및 메시지: \`${LATEST_COMMIT}\`
- **최근 5개 Git 커밋 내역:**
\`\`\`text
${GIT_LOG_5}
\`\`\`
- **인수인계 발생 사유 (해당 항목 체크):**
  - [ ] 모듈 구현 마일스톤 완료 직후 컨텍스트 리셋 (/clear 전)
  - [ ] 메인 에이전트의 이전 제약 망각(Drift) 방지
  - [ ] 아키텍처 또는 구현 방향 전환
  - [ ] 구현 종료 및 최종 검증/보고서 모드 진입

---

## 2. 인간이 확정한 아키텍처 결정 사항 ([결정] - [근거] - [검증] - [한계])

${DECISION_SNIPPET}

### 💡 아키텍처 및 구현 일반 가이드
- **[단순성 유지]:** 과제 요구사항에 필요한 최소한의 구조(MVP)를 구현하고 불필요한 복잡성이나 오버엔지니어링을 배제합니다.
- **[인터페이스 및 호환성 보장]:** 기존 함수 시그니처와 반환 데이터 포맷을 보존하여 회귀 테스트 깨짐을 방지합니다.
- **[검증 근거 보존]:** 모든 구현 결정마다 실제 테스트 결과와 표본 대조 결과를 NOTES.md에 기록합니다.

---

## 3. 실무자 DM 핵심 제약 체크리스트 (Hard Constraints)

${DM_SNIPPET}

### 🛡️ 시험 공통 불변 규칙 (Universal Hard Constraints)
- [ ] **[공통 제약 1 - 인터페이스 보호]:** 기존 베이스라인 테스트 및 핵심 모듈의 함수 시그니처를 절대 임의 변경하지 말 것.
- [ ] **[공통 제약 2 - 네트워크 바인딩]:** 모든 웹 애플리케이션 및 API 서비스는 반드시 호스트 \`0.0.0.0\`으로 바인딩할 것.
- [ ] **[공통 제약 3 - 민감정보 보호]:** 시크릿, 패스워드, API 키 등을 코드 내에 하드코딩하지 말 것.
- [ ] **[공통 제약 4 - 외부 라이브러리 동결]:** 사전에 허용되지 않은 신규 서드파티 라이브러리 설치 금지 (표준 라이브러리 우선).
- [ ] **[공통 제약 5 - 하네스 영구 보존]:** .probe-kit, NOTES_TEMP.md, STATE.md 등 하네스 및 런타임 파일은 절대 삭제하지 않고 보존할 것.

---

## 4. 현재 진행 작업 명세서 (TASK_SPEC.md 발췌)

\`\`\`markdown
${TASK_SPEC_SNIPPET}
\`\`\`

---

## 5. 소스코드 및 파일 변경 현황

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
- 과제 하네스 설정 파일 및 .gitignore

---

## 6. 검증 완료된 항목 vs 실패/미검증 항목

### 1) ✅ 직전 서브 에이전트 실행 요약 (\`SUB_RESULT.md\` 발췌)
\`\`\`markdown
${SUB_RESULT_SNIPPET}
\`\`\`

### 2) ⚠️ 실패 및 미검증 항목 (Edge Cases to Verify)
- 결측치(\`None\`, 빈 문자열) 유입 시 방어 로직 검증 여부
- 극단적 경계값(음수 값, 대규모 볼륨, 비정상 포맷) 스트레스 테스트 검증 여부
- 모듈 간 결합 통합 테스트 및 회귀 테스트 통과 여부

---

## 7. 미해결 리스크 및 기술 부채

- **예외 처리 안전장치:** 비정상 입력 유입 시 중단 방지를 위한 안전 형변환 및 예외 처리 점검.
- **환경 분기 점검:** 프로덕션/테스트 환경 분기를 위한 환경변수 처리 점검.
- **제출 규격 점검:** 채점기가 요구하는 필수 파일명 및 포맷 최종 준수 여부 점검.

---

## 8. 새 세션이 즉시 실행해야 할 다음 1~3가지 행동 (Next Actions)

신규 세션은 복창 완료 및 인간의 승인을 받은 즉시 아래 3가지 행동을 순서대로 수행해야 합니다:

- [ ] **Action 1:** 미검증 예외 케이스(결측치, 경계값) 방어 로직 보강을 위한 서브 지시서(\`.probe-kit/runtime/TASK_SPEC.md\`) 작성 및 위임.
- [ ] **Action 2:** 다음 단계 기능 모듈 구현 명세 수립 및 단위 테스트 검증 지시.
- [ ] **Action 3:** 마일스톤 완료 후 \`bash .probe-kit/scripts/state.sh next\` 실행 및 상태 동기화.

---

## 9. 새 세션 금지 사항 (Hard Constraints for New Session)

- **[금지 1] 메인 에이전트의 비즈니스 코드 직접 작성 금지:** 메인은 오직 아키텍트 역할만 수행하며, 코드 구현은 반드시 서브 에이전트에게 위임한다.
- **[금지 2] 실무자 DM 합의 사항 번복 금지:** 제3절의 도메인 불변 규칙을 임의로 왜곡하거나 삭제하지 않는다.
- **[금지 3] 기존 베이스라인 테스트 임의 수정 금지:** 테스트 통과를 위해 테스트 단언문(assert)을 변조하는 행위를 절대 엄금한다.
- **[금지 4] 승인 없는 외부 라이브러리 설치 금지:** 표준 라이브러리와 기존 환경 내에서만 구현한다.
EOF

# 워크스페이스 루트에도 편의용 HANDOFF.md 복사본 보장 (.git/info/exclude로 자동 격리됨)
if [ -n "${WORKSPACE_ROOT:-}" ] && [ "${WORKSPACE_ROOT}" != "${RUNTIME_DIR}" ] && [ -d "${WORKSPACE_ROOT}" ]; then
  cp "${HANDOFF_FILE}" "${WORKSPACE_ROOT}/HANDOFF.md" 2>/dev/null || true
fi

# 7. 사용자 안내 메시지 출력
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
