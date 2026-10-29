#!/usr/bin/env bash
# scripts/monitor.sh: 토큰 소모 없는 워크스페이스 상태 요약 및 하네스 모니터링 대시보드

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KIT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
RUNTIME_DIR="${KIT_DIR}/runtime"
WORKSPACE_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

STAGE_NAMES=(
    ""
    "설치"
    "환경확인"
    "터미널분리"
    "DM공략"
    "아이디어토론"
    "케이스매핑"
    "핑퐁구현"
    "검증보고서"
    "감사제출"
    "서술형"
)

render_bar() {
    local pct="$1"
    local width=20
    local filled=$(( pct * width / 100 ))
    [ "${filled}" -gt "${width}" ] && filled="${width}"
    [ "${filled}" -lt 0 ] && filled=0
    local empty=$(( width - filled ))
    local bar=""
    local i
    for ((i=0; i<filled; i++)); do bar="${bar}="; done
    for ((i=0; i<empty; i++)); do bar="${bar} "; done
    echo "[${bar}]"
}

load_state() {
    STATE_ID="1"
    STATE_NAME="설치"
    PROGRESS_PCT="0"

    STATE_SH="${KIT_DIR}/scripts/state.sh"
    if [ -f "$STATE_SH" ]; then
        STATE_OUTPUT=$(bash "$STATE_SH" status 2>/dev/null || true)
        if [ -n "$STATE_OUTPUT" ]; then
            PARSED_ID=$(echo "$STATE_OUTPUT" | grep -E '^STATE_ID=' | head -n 1 | cut -d'=' -f2- || true)
            PARSED_NAME=$(echo "$STATE_OUTPUT" | grep -E '^STATE_NAME=' | head -n 1 | cut -d'=' -f2- || true)
            PARSED_PROGRESS=$(echo "$STATE_OUTPUT" | grep -E '^PROGRESS_PCT=' | head -n 1 | cut -d'=' -f2- || true)

            [ -n "$PARSED_ID" ] && STATE_ID="$PARSED_ID"
            [ -n "$PARSED_NAME" ] && STATE_NAME="$PARSED_NAME"
            [ -n "$PARSED_PROGRESS" ] && PROGRESS_PCT="$PARSED_PROGRESS"
            return 0
        fi
    fi

    # fallback
    STATE_MD="${RUNTIME_DIR}/STATE.md"
    if [ -f "$STATE_MD" ]; then
        RAW_CURRENT=$(sed -n 's/.*STATE:CURRENT=\([0-9]*\).*/\1/p' "$STATE_MD" | head -n 1 || true)
        [ -n "$RAW_CURRENT" ] && STATE_ID="$RAW_CURRENT"
    fi
    if [ "${STATE_ID}" -ge 1 ] && [ "${STATE_ID}" -le 10 ]; then
        STATE_NAME="${STAGE_NAMES[${STATE_ID}]}"
        if [ "${STATE_ID}" -eq 10 ]; then
            PROGRESS_PCT=100
        else
            PROGRESS_PCT=$(( (STATE_ID - 1) * 100 / 9 ))
        fi
    fi
}

cmd_once() {
    load_state

    echo "================================================================================"
    echo "🛰️  [Probe-Kit Monitor Dashboard]"
    echo "================================================================================"
    echo ""
    echo "📊 [1. 현재 진행 단계 (STATE)]"
    echo "   - 진행 단계: [${STATE_ID}/10] ${STATE_NAME}"
    echo "   - 전체 진척: $(render_bar "${PROGRESS_PCT}") ${PROGRESS_PCT}%"
    echo ""

    echo "📋 [2. 런타임 버퍼 갱신 상태 (TASK_SPEC & SUB_RESULT)]"
    SPEC_FILE="${RUNTIME_DIR}/TASK_SPEC.md"
    [ ! -f "$SPEC_FILE" ] && [ -f "${WORKSPACE_DIR}/TASK_SPEC.md" ] && SPEC_FILE="${WORKSPACE_DIR}/TASK_SPEC.md"

    if [ -f "$SPEC_FILE" ]; then
        SPEC_MOD="$(stat -c '%y' "$SPEC_FILE" 2>/dev/null || date -r "$SPEC_FILE" 2>/dev/null || echo "알 수 없음")"
        SPEC_SIZE="$(wc -c < "$SPEC_FILE" 2>/dev/null || echo 0)"
        echo "   - TASK_SPEC.md: 🟢 존재함 (${SPEC_SIZE} bytes, 최근 수정: ${SPEC_MOD})"
        GOAL_LINE="$(grep -m 1 -E '^\- \*\*목표:\*\*|^목표:' "$SPEC_FILE" 2>/dev/null || head -n 5 "$SPEC_FILE" | grep -v '^#' | head -n 1 || true)"
        [ -n "$GOAL_LINE" ] && echo "     └─ 핵심 목표: ${GOAL_LINE}"
    else
        echo "   - TASK_SPEC.md: ⚪ 없음 (메인 에이전트 작성을 대기 중)"
    fi

    RESULT_FILE="${RUNTIME_DIR}/SUB_RESULT.md"
    [ ! -f "$RESULT_FILE" ] && [ -f "${WORKSPACE_DIR}/SUB_RESULT.md" ] && RESULT_FILE="${WORKSPACE_DIR}/SUB_RESULT.md"

    if [ -f "$RESULT_FILE" ]; then
        RESULT_MOD="$(stat -c '%y' "$RESULT_FILE" 2>/dev/null || date -r "$RESULT_FILE" 2>/dev/null || echo "알 수 없음")"
        RESULT_SIZE="$(wc -c < "$RESULT_FILE" 2>/dev/null || echo 0)"
        echo "   - SUB_RESULT.md: 🟢 존재함 (${RESULT_SIZE} bytes, 최근 수정: ${RESULT_MOD})"
        STATUS_LINE="$(grep -m 1 -E '^1\. 작업 상태:' "$RESULT_FILE" 2>/dev/null || true)"
        [ -n "$STATUS_LINE" ] && echo "     └─ 최근 보고: ${STATUS_LINE}"
    else
        echo "   - SUB_RESULT.md: ⚪ 없음 (서브 에이전트 실행 결과를 대기 중)"
    fi
    echo ""

    echo "📁 [3. 최근 수정 파일 및 Git 작업 트리 상태]"
    GIT_STATUS=$(git -C "$WORKSPACE_DIR" status --short 2>/dev/null || true)
    if [ -n "$GIT_STATUS" ]; then
        echo "$GIT_STATUS" | sed 's/^/   /'
    else
        echo "   (깨끗함 - 변경사항 없음 또는 Git 비활성화)"
    fi
    echo ""

    echo "📈 [4. Git 변경량 통계 (diff --stat)]"
    GIT_DIFF_STAT=$(git -C "$WORKSPACE_DIR" diff --stat 2>/dev/null || true)
    if [ -n "$GIT_DIFF_STAT" ]; then
        echo "$GIT_DIFF_STAT" | sed 's/^/   /'
    else
        echo "   (스테이징되지 않은 diff 없음)"
    fi
    echo ""

    echo "💬 [5. 현재 단계 권장 가이드]"
    case "$STATE_ID" in
        1|2|3)
            echo "   [초기 설정]: 원클릭 하네스 설치 확인 및 좌측 터미널(Sol 6.1), 우측 터미널(Luna 6) 분리 완료 후 'bash .probe-kit/scripts/state.sh next' 실행"
            ;;
        4)
            echo "   [DM 공략]: 업무 담당자 DM에 3대 질문(포맷/예외/인터페이스) 질의 후 답변을 NOTES_TEMP.md에 기록"
            ;;
        5|6)
            echo "   [설계 및 매핑]: 메인 에이전트(Sol)와 간결한 아키텍처(MVP) 확정 후 첫 TASK_SPEC.md 발행"
            ;;
        7)
            echo "   [핑퐁 구현]: 메인(TASK_SPEC 작성) ↔ 서브(Luna 구현/검증 & SUB_RESULT 작성 후 /clear) 루프 진행"
            ;;
        8)
            echo "   [검증 및 보고서]: 표본 수동 대조 및 SUBMISSION_REPORT.md 최종 작성 (신규 기능 추가 중단)"
            ;;
        9)
            echo "   [감사 및 제출]: bash .probe-kit/scripts/pre_submit_audit.sh 실행 → 하네스 영구 보존 확인 → 제출"
            ;;
        10)
            echo "   [서술형]: 후속 6문항 4문장 타이핑 공식(판단-근거-검증-한계)으로 직접 서술형 작성"
            ;;
        *)
            echo "   'bash .probe-kit/scripts/state.sh status' 로 현재 단계를 확인하세요."
            ;;
    esac
    echo "================================================================================"
}

cmd_watch() {
    while true; do
        clear 2>/dev/null || true
        cmd_once
        echo ""
        echo "⏱️  [30초 주기 자동 갱신 중... 종료하려면 Ctrl+C 를 누르세요]"
        sleep 30
    done
}

ACTION="${1:-once}"
case "$ACTION" in
    once)
        cmd_once
        ;;
    watch)
        cmd_watch
        ;;
    -h|--help|help)
        echo "사용법: $0 [once|watch]"
        echo "  once  : 현재 워크스페이스 상태 요약 1회 출력 (기본값)"
        echo "  watch : 30초마다 화면을 갱신하며 상황판 유지"
        exit 0
        ;;
    *)
        echo "❌ 알 수 없는 명령: $ACTION"
        echo "사용법: $0 [once|watch]"
        exit 1
        ;;
esac
