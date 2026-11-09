#!/usr/bin/env bash
# scripts/subagent.sh: 메인 에이전트(Sol 6.1 xhigh)가 서브 에이전트(GPT 5.6-terra medium)를 호출하는 래퍼 스크립트

set -euo pipefail

# 워크스페이스 또는 하네스 위치 자동 탐지
if [ -d ".probe-kit/runtime" ]; then
  RUNTIME_DIR=".probe-kit/runtime"
  HARNESS_ROOT=".probe-kit"
elif [ -d "runtime" ]; then
  RUNTIME_DIR="runtime"
  HARNESS_ROOT="."
else
  RUNTIME_DIR=".probe-kit/runtime"
  HARNESS_ROOT=".probe-kit"
fi

SPEC_FILE="${RUNTIME_DIR}/TASK_SPEC.md"
RESULT_FILE="${RUNTIME_DIR}/SUB_RESULT.md"
SUB_AGENTS_FILE="${HARNESS_ROOT}/SUB_AGENTS.md"

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

  PROMPT="[SUB] ${SUB_GUIDE_INSTRUCTION}${SPEC_FILE} 의 [시작·정의·기준·종료] 규격을 준수하여, 1) 사전 베이스라인 확인, 2) 정의·기준에 맞춘 허용 범위 내 코드 구현, 3) 태스크 맞춤 온더플라이 테스트 검증을 수행하고, 멈춤 조건 발생 시 즉시 중단 보고하며, 완료 후 ${RESULT_FILE} 에 핵심 결과와 변경 사항 위주로 기록해줘. (보고 완료 후 터미널 /clear 필수)"

  echo "=========================================================="
  echo "🚀 [Sub-Agent: GPT 5.6-terra medium] 작업 위임 시작"
  echo "   - 작업 명세: ${SPEC_FILE}"
  echo "   - 결과 파일: ${RESULT_FILE}"
  echo "=========================================================="

  if command -v codex >/dev/null 2>&1 && codex exec --help </dev/null >/dev/null 2>&1; then
    # 표준 codex CLI 단일 실행 (비표준 플래그 및 연쇄 호출 제거로 토큰 폭증/코드 오염 원천 차단)
    if ! codex exec -m "gpt-5.6-terra" -c model_reasoning_effort="medium" --dangerously-bypass-confirmation --skip-git-repo-check "$PROMPT" < /dev/null; then
      echo ""
      echo "⚠️ [경고] codex 서브 에이전트(GPT 5.6-terra) 자동 실행 실패 또는 비정상 종료."
      echo "   우측 '터미널 2 (GPT 5.6-terra medium)' 창에 아래 1줄을 입력하여 수동으로 실행하세요:"
      echo "   --------------------------------------------------------"
      echo "   [SUB] TASK_SPEC 실행해"
      echo "   --------------------------------------------------------"
      exit 1
    fi
  else
    echo "💡 [안내] 현재 환경에 codex CLI가 없거나 대화형 TUI 전용 환경입니다."
    echo "   우측 '터미널 2 (GPT 5.6-terra medium)' 창에 아래 1줄을 입력하세요:"
    echo "   --------------------------------------------------------"
    echo "   [SUB] TASK_SPEC 실행해"
    echo "   --------------------------------------------------------"
    exit 1
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
🧭 [듀얼 터미널 운용 가이드: Sol 6.1 xhigh × GPT 5.6-terra medium]
======================================================================

1. 터미널 분담 원칙
   - [터미널 1 (좌측)] 메인 에이전트: Sol 6.1 xhigh
     * 역할: 요구사항 분석, 실무자 DM 협의, 아키텍처 설계, TASK_SPEC.md 작성
     * 명세 규격: [시작 · 정의 · 기준 · 종료] 4대 축 기반 7대 표준 섹션 준수
     * 절대 금지: 직접 코드 수정, 대용량 파일 열람, 직접 테스트 실행
   - [터미널 2 (우측)] 서브 에이전트: GPT 5.6-terra medium
     * 역할: 사전 베이스라인 확인, 정의·기준 준수 구현, 온더플라이 테스트 검증, SUB_RESULT.md 작성
     * 절대 금지: 메인 합의 범위를 벗어난 임의 파일 수정, 멈춤 조건 무시 자의적 판단

2. 핸드셰이크 프로토콜 (4대 핵심 축 기반)
   [단계 1 - 시작(Start)] 메인(Sol)이 .probe-kit/runtime/TASK_SPEC.md 작성
                          (단일 목표, 진입 조건, 허용 범위, 5대 금지사항 선언)
   [단계 2 - 시작(Start)] 서브(GPT 5.6-terra)가 착수 전 사전 베이스라인 테스트 PASS 확인
                          (베이스라인 실패 또는 멈춤 조건 발생 시 즉시 구현 중단 및 보고)
   [단계 3 - 정의·기준(Definition & Criteria)]
                          서브가 TASK_SPEC에 명시된 도메인 스키마와 비즈니스 기준을 준수하여
                          지정된 수정 허용 파일에 한해 국소 구현
   [단계 4 - 검증(Verification)]
                          서브가 베이스라인 회귀 검증 및 태스크 맞춤 온더플라이 ad-hoc 테스트
                          (tests/test_*.py) 직접 작성·실행 (git commit 금지, untracked 유지)
   [단계 5 - 종료(End)]   서브가 작업 완료 후 .probe-kit/runtime/SUB_RESULT.md 요약 보고서 기록
                          → handoff.sh log 실행 → 메인(Sol)에게 보고 후 서브 터미널 /clear 실행
   [단계 6 - 메인 검토]   메인(Sol)이 SUB_RESULT.md 및 git diff 검토 후 다음 태스크 진행

3. ⚠️ 컨텍스트 초기화 (/clear) 타이밍 (토큰 70% 절감 핵심)
   - 터미널 2 (GPT 5.6-terra): 각 단위 작업(TASK_SPEC) 완료 및 SUB_RESULT.md 보고 직후
     반드시 '/clear' 실행! (새 작업 전 컨텍스트를 비워 환각 및 토큰 폭발 방지)
   - 터미널 1 (Sol): 대단위 마일스톤 완료 후 핵심 결정을 NOTES_TEMP.md에 기록한 뒤
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
  echo "  run    : TASK_SPEC.md 기반으로 서브 에이전트(GPT 5.6-terra medium)를 호출하여 작업 수행"
  echo "  guide  : 메인(Sol)-서브(GPT 5.6-terra) 듀얼 터미널 운용 지침 및 /clear 타이밍 안내"
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
  help|--help|-h)
    cmd_usage
    exit 0
    ;;
  *)
    cmd_usage
    exit 1
    ;;
esac
