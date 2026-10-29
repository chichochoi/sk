#!/usr/bin/env bash
# scripts/subagent.sh: 메인 에이전트(Sol 6.1 xhigh)가 서브 에이전트(Luna 6 xhigh)를 호출하는 래퍼 스크립트

set -euo pipefail

# 스크립트 절대 경로 기준 디렉터리 자동 계산 (어느 위치에서 실행해도 정상 동작)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HARNESS_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# 워크스페이스 탐색
if git rev-parse --show-toplevel >/dev/null 2>&1; then
  WORKSPACE_DIR="$(git rev-parse --show-toplevel)"
elif [ "$(basename "${HARNESS_ROOT}")" = ".probe-kit" ]; then
  WORKSPACE_DIR="$(cd "${HARNESS_ROOT}/.." && pwd)"
else
  WORKSPACE_DIR="$(pwd)"
fi

# 런타임 디렉터리 탐색
if [ -d "${HARNESS_ROOT}/runtime" ]; then
  RUNTIME_DIR="${HARNESS_ROOT}/runtime"
elif [ -d "${WORKSPACE_DIR}/.probe-kit/runtime" ]; then
  RUNTIME_DIR="${WORKSPACE_DIR}/.probe-kit/runtime"
else
  RUNTIME_DIR="${HARNESS_ROOT}/runtime"
fi
mkdir -p "${RUNTIME_DIR}"

SPEC_FILE="${RUNTIME_DIR}/TASK_SPEC.md"
if [ ! -f "$SPEC_FILE" ] && [ -f "${WORKSPACE_DIR}/TASK_SPEC.md" ]; then
  SPEC_FILE="${WORKSPACE_DIR}/TASK_SPEC.md"
fi

RESULT_FILE="${RUNTIME_DIR}/SUB_RESULT.md"
if [ ! -f "$RESULT_FILE" ] && [ -f "${WORKSPACE_DIR}/SUB_RESULT.md" ]; then
  RESULT_FILE="${WORKSPACE_DIR}/SUB_RESULT.md"
fi

SUB_AGENTS_FILE="${HARNESS_ROOT}/SUB_AGENTS.md"
if [ ! -f "$SUB_AGENTS_FILE" ] && [ -f "${WORKSPACE_DIR}/.probe-kit/SUB_AGENTS.md" ]; then
  SUB_AGENTS_FILE="${WORKSPACE_DIR}/.probe-kit/SUB_AGENTS.md"
fi

cmd_run() {
  if [ ! -f "$SPEC_FILE" ]; then
    echo "❌ [오류] ${SPEC_FILE} 파일이 없습니다."
    echo "   먼저 메인 에이전트(Sol 6.1 xhigh)로 TASK_SPEC.md를 생성하세요."
    exit 1
  fi

  SUB_GUIDE_INSTRUCTION=""
  if [ -f "$SUB_AGENTS_FILE" ]; then
    SUB_GUIDE_INSTRUCTION="${SUB_AGENTS_FILE} 지침과 "
  fi

  PROMPT="[SUB] ${SUB_GUIDE_INSTRUCTION}${SPEC_FILE} 의 지시사항을 읽고 지정된 범위의 코드 구현 및 테스트 검증을 수행한 뒤, 핵심 결과와 변경 사항 위주로 간결하고 명확하게 ${RESULT_FILE} 에 기록해줘 (불필요한 줄 수 제한 없음)."

  echo "=========================================================="
  echo "🚀 [Sub-Agent: Luna 6 (xhigh)] 작업 위임 시작"
  echo "   - 작업 명세: ${SPEC_FILE}"
  echo "   - 결과 파일: ${RESULT_FILE}"
  echo "=========================================================="

  if command -v codex >/dev/null 2>&1 && codex exec --help >/dev/null 2>&1; then
    codex exec -m "luna-6" -c model_reasoning_effort="xhigh" "$PROMPT" || \
    codex exec --profile sub "$PROMPT"
  else
    echo "💡 [안내] 현재 환경에 codex CLI가 없거나 대화형 TUI 전용 환경입니다."
    echo "   우측 '터미널 2 (Luna 6 xhigh)' 창에 아래 1줄을 입력하세요:"
    echo "   --------------------------------------------------------"
    echo "   [SUB] TASK_SPEC 실행해"
    echo "   --------------------------------------------------------"
    exit 0
  fi

  echo ""
  echo "=========================================================="
  echo "✅ [Sub-Agent 실행 완료] 요약 보고서 (${RESULT_FILE}):"
  echo "=========================================================="
  if [ -f "$RESULT_FILE" ]; then
    cat "$RESULT_FILE"
  else
    echo "⚠️ 주의: ${RESULT_FILE} 파일이 생성되지 않았습니다."
  fi
}

cmd_guide() {
  cat <<'EOF'
======================================================================
🧭 [듀얼 터미널 운용 가이드: Sol 6.1 xhigh × Luna 6 xhigh]
======================================================================

1. 터미널 분담 원칙
   - [터미널 1 (좌측)] 메인 에이전트: Sol 6.1 xhigh
     * 역할: 요구사항 분석, 실무자 DM 협의, 설계, TASK_SPEC.md 작성
     * 절대 금지: 직접 코드 수정, 대용량 파일 열람, 직접 테스트 실행
   - [터미널 2 (우측)] 서브 에이전트: Luna 6 xhigh
     * 역할: 코드 구현, 단위/통합 테스트 실행, 디버깅, SUB_RESULT.md 작성
     * 절대 금지: 메인 합의 범위를 벗어난 임의 파일 수정

2. 핸드셰이크 프로토콜
   [단계 1] 메인(Sol)이 .probe-kit/runtime/TASK_SPEC.md 작성
   [단계 2] 서브(Luna) 실행:
           - CLI 환경: bash .probe-kit/scripts/subagent.sh run
           - TUI 환경: 터미널 2에 '[SUB] TASK_SPEC 실행해' 입력
   [단계 3] 서브(Luna)가 작업 완료 후 .probe-kit/runtime/SUB_RESULT.md 기록
   [단계 4] 메인(Sol)이 SUB_RESULT.md 내용 검토 후 다음 태스크 진행

3. ⚠️ 컨텍스트 초기화 (/clear) 타이밍 (토큰 70% 절감 핵심)
   - 터미널 2 (Luna): 각 단위 작업(TASK_SPEC) 완료 및 SUB_RESULT.md 보고 직후
     반드시 '/clear' 실행! (새 작업 전 컨텍스트를 비워 환각 및 토큰 폭발 방지)
   - 터미널 1 (Sol): 대단위 마일스톤 완료 후 핵심 결정을 NOTES.md에 기록한 뒤
     필요 시 '/clear' 실행
======================================================================
EOF
}

cmd_status() {
  echo "=========================================================="
  echo "📋 [Sub-Agent 작업 버퍼 상태 점검]"
  echo "=========================================================="

  if [ -f "$SPEC_FILE" ]; then
    echo "📄 [TASK_SPEC] 존재함: ${SPEC_FILE}"
    echo "   - 수정 시각: $(stat -c '%y' "$SPEC_FILE" 2>/dev/null || date -r "$SPEC_FILE" 2>/dev/null || echo "알 수 없음")"
    echo "   - 크기: $(wc -c < "$SPEC_FILE" 2>/dev/null || echo 0) bytes"
  else
    echo "⚪ [TASK_SPEC] 없음 (${SPEC_FILE})"
  fi

  echo "----------------------------------------------------------"

  if [ -f "$RESULT_FILE" ]; then
    echo "📄 [SUB_RESULT] 존재함: ${RESULT_FILE}"
    echo "   - 수정 시각: $(stat -c '%y' "$RESULT_FILE" 2>/dev/null || date -r "$RESULT_FILE" 2>/dev/null || echo "알 수 없음")"
    echo "   - 크기: $(wc -c < "$RESULT_FILE" 2>/dev/null || echo 0) bytes"
    echo "   [최신 보고 내용]:"
    cat "$RESULT_FILE"
  else
    echo "⚪ [SUB_RESULT] 없음 (${RESULT_FILE})"
  fi
  echo "=========================================================="
}

cmd_usage() {
  echo "사용법: bash .probe-kit/scripts/subagent.sh [run|guide|status]"
  echo ""
  echo "  run    : TASK_SPEC.md 기반으로 서브 에이전트(Luna 6 xhigh)를 호출하여 작업 수행 (기본값)"
  echo "  guide  : 메인(Sol)-서브(Luna) 듀얼 터미널 운용 지침 및 /clear 타이밍 안내"
  echo "  status : TASK_SPEC.md 및 SUB_RESULT.md 파일 상태와 최신 보고 내용 확인"
}

ACTION="${1:-run}"

case "$ACTION" in
  run)
    cmd_run
    ;;
  guide)
    cmd_guide
    ;;
  status)
    cmd_status
    ;;
  -h|--help|help)
    cmd_usage
    exit 0
    ;;
  *)
    echo "❌ 알 수 없는 명령: $ACTION"
    echo ""
    cmd_usage
    exit 1
    ;;
esac
