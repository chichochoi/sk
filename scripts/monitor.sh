#!/usr/bin/env bash
# scripts/monitor.sh: 토큰 소모 없는 워크스페이스 상태 요약 및 페이스메이커 모니터링 스크립트

set -euo pipefail

# 스크립트 위치 기준 디렉터리 자동 계산
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KIT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
RUNTIME_DIR="${KIT_DIR}/runtime"
WORKSPACE_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# STATE 기본 단계 이름 매핑 (10단계 타임라인)
get_stage_name_by_id() {
  case "$1" in
    1) echo "설치" ;;
    2) echo "환경확인" ;;
    3) echo "터미널분리" ;;
    4) echo "DM공략" ;;
    5) echo "아이디어토론" ;;
    6) echo "케이스매핑" ;;
    7) echo "핑퐁구현" ;;
    8) echo "검증보고서" ;;
    9) echo "감사제출" ;;
    10) echo "서술형" ;;
    *) echo "미정" ;;
  esac
}

# STATE 목표 종료 오프셋(분) (10:00 기준)
get_stage_target_offset() {
  case "$1" in
    1) echo 3 ;;
    2) echo 5 ;;
    3) echo 8 ;;
    4) echo 15 ;;
    5) echo 25 ;;
    6) echo 30 ;;
    7) echo 140 ;;
    8) echo 165 ;;
    9) echo 175 ;;
    10) echo 210 ;;
    *) echo 175 ;;
  esac
}

# 상태 정보 로드
load_state() {
  STATE_ID="1"
  STATE_NAME="설치"
  ELAPSED_MIN="0"
  REMAIN_MIN="175"
  PROGRESS_PCT="0"
  TIME_PCT="0"
  DELAY_MIN="0"

  STATE_SH="${KIT_DIR}/scripts/state.sh"
  if [ -f "$STATE_SH" ]; then
    STATE_OUTPUT=$(bash "$STATE_SH" status 2>/dev/null || true)
    if [ -n "$STATE_OUTPUT" ]; then
      PARSED_ID=$(echo "$STATE_OUTPUT" | grep -E '^STATE_ID=' | head -n 1 | cut -d'=' -f2- || true)
      PARSED_NAME=$(echo "$STATE_OUTPUT" | grep -E '^STATE_NAME=' | head -n 1 | cut -d'=' -f2- || true)
      PARSED_ELAPSED=$(echo "$STATE_OUTPUT" | grep -E '^ELAPSED_MIN=' | head -n 1 | cut -d'=' -f2- || true)
      PARSED_REMAIN=$(echo "$STATE_OUTPUT" | grep -E '^REMAIN_MIN=' | head -n 1 | cut -d'=' -f2- || true)
      PARSED_PROGRESS=$(echo "$STATE_OUTPUT" | grep -E '^PROGRESS_PCT=' | head -n 1 | cut -d'=' -f2- || true)
      PARSED_TIME=$(echo "$STATE_OUTPUT" | grep -E '^TIME_PCT=' | head -n 1 | cut -d'=' -f2- || true)
      PARSED_DELAY=$(echo "$STATE_OUTPUT" | grep -E '^DELAY_MIN=' | head -n 1 | cut -d'=' -f2- || true)

      [ -n "$PARSED_ID" ] && STATE_ID="$PARSED_ID"
      [ -n "$PARSED_NAME" ] && STATE_NAME="$PARSED_NAME"
      [ -n "$PARSED_ELAPSED" ] && ELAPSED_MIN="$PARSED_ELAPSED"
      [ -n "$PARSED_REMAIN" ] && REMAIN_MIN="$PARSED_REMAIN"
      [ -n "$PARSED_PROGRESS" ] && PROGRESS_PCT="$PARSED_PROGRESS"
      [ -n "$PARSED_TIME" ] && TIME_PCT="$PARSED_TIME"
      [ -n "$PARSED_DELAY" ] && DELAY_MIN="$PARSED_DELAY"
      return 0
    fi
  fi

  # state.sh 미구현 또는 실패 시 runtime/STATE.md 직접 파싱 (Fallback)
  STATE_MD="${RUNTIME_DIR}/STATE.md"
  if [ -f "$STATE_MD" ]; then
    RAW_CURRENT=$(sed -n 's/.*STATE:CURRENT=\([0-9]*\).*/\1/p' "$STATE_MD" | head -n 1 || true)
    [ -n "$RAW_CURRENT" ] && STATE_ID="$RAW_CURRENT"
  fi
  STATE_NAME=$(get_stage_name_by_id "$STATE_ID")

  # 현재 시각 분 환산
  NOW_TIME=$(date +%H:%M)
  NOW_H=$(echo "$NOW_TIME" | cut -d':' -f1 | sed 's/^0*//')
  NOW_M=$(echo "$NOW_TIME" | cut -d':' -f2 | sed 's/^0*//')
  [ -z "$NOW_H" ] && NOW_H=0
  [ -z "$NOW_M" ] && NOW_M=0
  NOW_TOTAL=$(( NOW_H * 60 + NOW_M ))

  # 시작 시각 분 환산 (기본 10:00)
  START_STR="10:00"
  if [ -f "$STATE_MD" ]; then
    RAW_START=$(sed -n 's/.*STATE:START=\([0-9:]*\).*/\1/p' "$STATE_MD" | head -n 1 || true)
    [ -n "$RAW_START" ] && START_STR="$RAW_START"
  fi
  if [ -n "${PROBE_START:-}" ]; then
    START_STR="$PROBE_START"
  fi
  START_H=$(echo "$START_STR" | cut -d':' -f1 | sed 's/^0*//')
  START_M=$(echo "$START_STR" | cut -d':' -f2 | sed 's/^0*//')
  [ -z "$START_H" ] && START_H=0
  [ -z "$START_M" ] && START_M=0
  START_TOTAL=$(( START_H * 60 + START_M ))

  ELAPSED_MIN=$(( NOW_TOTAL - START_TOTAL ))
  if [ "$ELAPSED_MIN" -lt 0 ]; then
    ELAPSED_MIN=0
  fi
  REMAIN_MIN=$(( 175 - ELAPSED_MIN ))
  if [ "$REMAIN_MIN" -lt 0 ]; then
    REMAIN_MIN=0
  fi

  # PROGRESS_PCT = (CURRENT-1)/9*100 (10단계는 100)
  if [ "$STATE_ID" -ge 10 ]; then
    PROGRESS_PCT=100
  elif [ "$STATE_ID" -le 1 ]; then
    PROGRESS_PCT=0
  else
    PROGRESS_PCT=$(( (STATE_ID - 1) * 100 / 9 ))
  fi

  # TIME_PCT = 경과 / 175 * 100 (0~100 클램프)
  TIME_PCT=$(( ELAPSED_MIN * 100 / 175 ))
  if [ "$TIME_PCT" -gt 100 ]; then
    TIME_PCT=100
  elif [ "$TIME_PCT" -lt 0 ]; then
    TIME_PCT=0
  fi

  # DELAY_MIN = 경과시간 - 목표종료시간
  TARGET_OFFSET=$(get_stage_target_offset "$STATE_ID")
  DELAY_MIN=$(( ELAPSED_MIN - TARGET_OFFSET ))
}

# 1회 상태 출력
cmd_once() {
  load_state
  NOW_TIME=$(date +%H:%M)
  GAP=$(( TIME_PCT - PROGRESS_PCT ))

  echo "================================================================================"
  echo "🛰️  [Probe-Kit Monitor Dashboard] ${NOW_TIME} 기준"
  echo "================================================================================"
  echo ""

  # 경보 배너 판정
  if [ "$GAP" -ge 15 ]; then
    echo "################################################################################"
    echo "🚨 [긴급 경보: 페이스메이커 발령] 시간 소진율이 진척률보다 15%p 이상 앞서고 있습니다!"
    echo "   - 진척 현황: STATE ${STATE_ID}단계 (${STATE_NAME}) [진척률: ${PROGRESS_PCT}%]"
    echo "   - 시간 소진: ${TIME_PCT}% (${ELAPSED_MIN}분 경과 / ${REMAIN_MIN}분 남음 | 목표 대비 지연: ${DELAY_MIN}분)"
    echo "   - 격차(위험도): +${GAP}%p 지연 중"
    echo "   - 즉각 조치: 비핵심 기능 전면 폐기 및 P0 핵심 기능 중심 긴급 범위 축소(Scope Cut) 단행 권고!"
    echo "################################################################################"
  elif [ "$GAP" -ge 10 ]; then
    echo "--------------------------------------------------------------------------------"
    echo "⚠️  [주의 경보] 시간 소진율이 진척률을 10%p 초과하고 있습니다. (격차: +${GAP}%p | 지연: ${DELAY_MIN}분)"
    echo "   - 작업 단위를 최소 단위(단일 함수/모듈)로 좁히고 구현 시간 초과에 유의하세요."
    echo "--------------------------------------------------------------------------------"
  else
    echo "✅ [정상 페이스] 진척률: ${PROGRESS_PCT}% | 시간 소진: ${TIME_PCT}% (격차: ${GAP}%p | 지연: ${DELAY_MIN}분)"
  fi
  echo ""

  # 1. 진척 및 시간 현황 상세
  echo "📊 [진척 및 시간 현황]"
  echo "   - 현재 단계: STATE ${STATE_ID}단계 (${STATE_NAME})"
  echo "   - 진척률: ${PROGRESS_PCT}% | 시간 소진율: ${TIME_PCT}% (총 175분 중 ${ELAPSED_MIN}분 경과 / ${REMAIN_MIN}분 남음)"
  echo "   - 목표 대비 지연: ${DELAY_MIN}분"
  echo ""

  # 2. Git 워크스페이스 상태
  echo "📁 [Git 워크스페이스 상태 (status --short)]"
  GIT_STATUS=$(git -C "$WORKSPACE_DIR" status --short 2>/dev/null || true)
  if [ -n "$GIT_STATUS" ]; then
    echo "$GIT_STATUS" | sed 's/^/   /'
  else
    echo "   (깨끗함 - 워크스페이스 변경사항 없음)"
  fi
  echo ""

  # 3. Git diff 통계
  echo "📈 [Git 변경량 통계 (diff --stat)]"
  GIT_DIFF_STAT=$(git -C "$WORKSPACE_DIR" diff --stat 2>/dev/null || true)
  if [ -n "$GIT_DIFF_STAT" ]; then
    echo "$GIT_DIFF_STAT" | sed 's/^/   /'
  else
    echo "   (스테이징되지 않은 diff 없음)"
  fi
  echo ""

  # 4. 최신 서브 작업 보고 (SUB_RESULT.md) 상위 발췌
  echo "📝 [최신 서브 에이전트 작업 보고 (SUB_RESULT.md 발췌)]"
  SUB_RESULT_PATH="${RUNTIME_DIR}/SUB_RESULT.md"
  if [ -f "$SUB_RESULT_PATH" ]; then
    head -n 25 "$SUB_RESULT_PATH" | sed 's/^/   /'
  else
    echo "   (아직 ${SUB_RESULT_PATH} 파일이 생성되지 않았습니다)"
  fi
  echo ""

  # 5. 감시 세션(Sol 6.1 xhigh) 복붙 추천 프롬프트
  echo "--------------------------------------------------------------------------------"
  echo "💬 [감시자 세션(Pane 3: Sol 6.1 xhigh) 복붙 추천 프롬프트]"
  if [ "$GAP" -ge 15 ]; then
    echo "[MONITOR] 현재 시간소진 ${TIME_PCT}% vs 진척 ${PROGRESS_PCT}%로 15%p 이상 지연되었습니다. 현재 구현 중인 기능 중 즉시 쳐내야 할 항목(Scope Cut)과 사수해야 할 P0를 판정해줘."
  elif [ "$STATE_ID" -eq 7 ]; then
    echo "[MONITOR] 현재 7단계(핑퐁구현) 진행 중입니다. monitor.sh 현황을 보고 드리프트 및 증거 누락 여부, 다음 15분 액션을 진단해줘."
  elif [ "$STATE_ID" -ge 8 ]; then
    echo "[MONITOR] 현재 제출/감사 단계(${STATE_NAME})입니다. 검증 증거 누락 및 제출 요건 충족 여부를 최종 점검해줘."
  else
    echo "[MONITOR] 현재 STATE ${STATE_ID}단계(${STATE_NAME}) 진행 중입니다. 현재 워크스페이스 상태를 점검하고 지금 당장 취해야 할 딱 1가지 행동을 제시해줘."
  fi
  echo "--------------------------------------------------------------------------------"
}

# 30초 주기 상황판 모니터링
cmd_watch() {
  while true; do
    clear 2>/dev/null || true
    cmd_once
    echo ""
    echo "⏱️  [30초 주기 자동 갱신 중... 종료하려면 Ctrl+C 를 누르세요]"
    sleep 30
  done
}

# 메인 엔트리포인트
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
    echo "  once  : 현재 워크스페이스 상태 및 페이스메이커 요약 1회 출력 (기본값)"
    echo "  watch : 30초마다 화면을 갱신하며 상황판 유지"
    exit 0
    ;;
  *)
    echo "❌ 알 수 없는 명령: $ACTION"
    echo "사용법: $0 [once|watch]"
    exit 1
    ;;
esac
