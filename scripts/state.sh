#!/usr/bin/env bash
# ==============================================================================
# Cofa Probe STATE 10단계 추적 및 전환 관리 엔진 (scripts/state.sh)
# ==============================================================================
set -euo pipefail

# 1. 디렉터리 및 워크스페이스 자동 탐지
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KIT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
RUNTIME_DIR="${KIT_DIR}/runtime"
STATE_FILE="${RUNTIME_DIR}/STATE.md"
WORKSPACE="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# 2. 10단계 정의 및 일정 (V2_CONTRACT 준수)
# ID 1~10 (인덱스 1 기반)
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

# 시작 시각 기준 오프셋 (분 단위)
# 1: 10:00~10:03 (+0 ~ +3)
# 2: 10:03~10:05 (+3 ~ +5)
# 3: 10:05~10:08 (+5 ~ +8)
# 4: 10:08~10:15 (+8 ~ +15)
# 5: 10:15~10:25 (+15 ~ +25)
# 6: 10:25~10:30 (+25 ~ +30)
# 7: 10:30~12:20 (+30 ~ +140)
# 8: 12:20~12:45 (+140 ~ +165)
# 9: 12:45~12:55 (+165 ~ +175)
# 10: 13:00~13:30 (+180 ~ +210)
STAGE_START_OFFSETS=(0 0 3 5 8 15 25 30 140 165 180)
STAGE_END_OFFSETS=(0 3 5 8 15 25 30 140 165 175 210)

# 3. 시간 변환 함수 (BusyBox / bash 호환, date -d 절대 사용 금지)
to_minutes() {
    local t="$1"
    local hh="${t%%:*}"
    local mm="${t#*:}"
    echo $(( 10#${hh:-0} * 60 + 10#${mm:-0} ))
}

to_time_str() {
    local total_min="$1"
    local h=$(( (total_min / 60) % 24 ))
    local m=$(( total_min % 60 ))
    printf "%02d:%02d\n" "$h" "$m"
}

# 4. 상태 파일 읽기 및 메타데이터 관리
get_current_stage() {
    local cur=""
    if [ -f "${STATE_FILE}" ]; then
        cur=$(sed -n 's/.*STATE:CURRENT=\([0-9]*\).*/\1/p' "${STATE_FILE}" 2>/dev/null | head -n 1)
    fi
    if [ -z "${cur}" ]; then
        echo "1"
    else
        echo "${cur}"
    fi
}

get_start_time() {
    if [ -n "${PROBE_START:-}" ]; then
        echo "${PROBE_START}"
        return
    fi
    local st=""
    if [ -f "${STATE_FILE}" ]; then
        st=$(sed -n 's/.*STATE:START=\([0-9:]*\).*/\1/p' "${STATE_FILE}" 2>/dev/null | head -n 1)
    fi
    if [ -z "${st}" ]; then
        echo "10:00"
    else
        echo "${st}"
    fi
}

update_state_header() {
    local new_cur="$1"
    local new_start="$2"
    local tmp_file="${STATE_FILE}.tmp.$$"

    if [ ! -f "${STATE_FILE}" ]; then
        init_state_file "${new_cur}" "${new_start}"
        return
    fi

    if grep -q "STATE:CURRENT=" "${STATE_FILE}"; then
        sed -e "s/<!-- STATE:CURRENT=[0-9]* -->/<!-- STATE:CURRENT=${new_cur} -->/" \
            -e "s/<!-- STATE:START=[0-9:]* -->/<!-- STATE:START=${new_start} -->/" \
            "${STATE_FILE}" > "${tmp_file}" && mv "${tmp_file}" "${STATE_FILE}"
    else
        {
            echo "<!-- STATE:CURRENT=${new_cur} -->"
            echo "<!-- STATE:START=${new_start} -->"
            cat "${STATE_FILE}"
        } > "${tmp_file}" && mv "${tmp_file}" "${STATE_FILE}"
    fi
}

init_state_file() {
    local cur="${1:-1}"
    local st="${2:-10:00}"
    mkdir -p "${RUNTIME_DIR}"
    cat <<EOF > "${STATE_FILE}"
<!-- STATE:CURRENT=${cur} -->
<!-- STATE:START=${st} -->
# ⏱️ Cofa Probe 진행 단계 (STATE) 추적 로그

> 과제 마감: 10:00 ~ 12:55 (175분) / 후속 서술형: 13:00 ~ 13:30 (30분)
> 본 문서는 Cofa Probe의 실시간 진행 단계 및 3대 전환 감사 기록을 보존하는 공식 로그입니다.

---

## 📋 10단계 타임라인 가이드
| ID | 단계명 | 목표 시각 | 소요 | 핵심 작업 |
|---|---|---|---|---|
| 1 | 설치 | 10:00 ~ 10:03 | 3분 | 원클릭 클론 & 하네스 장착 스크립트 실행 |
| 2 | 환경확인 | 10:03 ~ 10:05 | 2분 | Git 워크스페이스 보호 및 무토큰 EDA 확인 |
| 3 | 터미널분리 | 10:05 ~ 10:08 | 3분 | 터미널 1(Sol 메인) ↔ 터미널 2(Luna 서브) 분리 |
| 4 | DM공략 | 10:08 ~ 10:15 | 7분 | 실무자 DM 3대 질문 (포맷/예외/인터페이스) 질의 |
| 5 | 아이디어토론 | 10:15 ~ 10:25 | 10분 | 인간 주도 가설 제시 & 트레이드오프 비교 & 결정 |
| 6 | 케이스매핑 | 10:25 ~ 10:30 | 5분 | 4개 케이스 판별 & 스킬 연동 (.probe-kit/skills/) |
| 7 | 핑퐁구현 | 10:30 ~ 12:20 | 110분 | 메인 TASK_SPEC ↔ 서브 구현 핑퐁 루프 |
| 8 | 검증보고서 | 12:20 ~ 12:45 | 25분 | 표본 15건 대조 및 최종 보고서 초안 작성 |
| 9 | 감사제출 | 12:45 ~ 12:55 | 10분 | 사전 감사(pre_submit_audit) & 하네스 정리 & 최종 제출 |
| 10 | 서술형 | 13:00 ~ 13:30 | 30분 | 후속 6문항 4문장 공식 직접 서술 |

---

## 🛡️ 3대 전환 감사 질문
1. **드리프트 없나?** — 5단계(아이디어토론)에서 내가 결정한 방향과 지금 구현이 어긋나지 않았나?
2. **증거 없는 체크 없나?** — '완료'라고 한 항목마다 실행 로그·테스트 결과가 실제로 있나?
3. **너무 순조롭지 않았나?** — 실패 경로(빈 입력·결측·경계값)를 안 돌려봐서 순조로웠던 건 아닌가?

---

## 📝 단계 전환 로그
## [${st}] 1.설치 시작 (초기화)
- 상태: 1단계 진입 완료
- 시작 시각: ${st}
EOF
}

# 5. 진행률 및 지연 시간 메트릭 계산
calc_metrics() {
    CURRENT=$(get_current_stage)
    START=$(get_start_time)

    # 범위 보정 (1~10)
    if [ "${CURRENT}" -lt 1 ] || [ "${CURRENT}" -gt 10 ]; then
        CURRENT=1
    fi

    CURRENT_NAME="${STAGE_NAMES[${CURRENT}]}"
    START_MIN=$(to_minutes "${START}")

    NOW_STR=$(date +%H:%M)
    NOW_MIN=$(to_minutes "${NOW_STR}")

    ELAPSED_MIN=$(( NOW_MIN - START_MIN ))
    REMAIN_MIN=$(( 175 - ELAPSED_MIN ))

    # PROGRESS_PCT = (CURRENT-1)/9*100 (10단계는 100)
    if [ "${CURRENT}" -eq 10 ]; then
        PROGRESS_PCT=100
    else
        PROGRESS_PCT=$(( (CURRENT - 1) * 100 / 9 ))
    fi

    # TIME_PCT = 경과/175*100 (0~100 클램프)
    TIME_PCT=$(( ELAPSED_MIN * 100 / 175 ))
    if [ "${TIME_PCT}" -lt 0 ]; then
        TIME_PCT=0
    elif [ "${TIME_PCT}" -gt 100 ]; then
        TIME_PCT=100
    fi

    # DELAY_MIN = 현재시각 - 현재 단계 목표 종료시각 (양수=지연, 음수=여유)
    STAGE_TARGET_END_OFFSET=${STAGE_END_OFFSETS[${CURRENT}]}
    STAGE_TARGET_END_MIN=$(( START_MIN + STAGE_TARGET_END_OFFSET ))
    DELAY_MIN=$(( NOW_MIN - STAGE_TARGET_END_MIN ))

    STAGE_TARGET_START_OFFSET=${STAGE_START_OFFSETS[${CURRENT}]}
    STAGE_TARGET_START_MIN=$(( START_MIN + STAGE_TARGET_START_OFFSET ))
    STAGE_TARGET_START_STR=$(to_time_str "${STAGE_TARGET_START_MIN}")
    STAGE_TARGET_END_STR=$(to_time_str "${STAGE_TARGET_END_MIN}")
}

render_bar() {
    local pct="$1"
    local width=20
    local filled=$(( pct * width / 100 ))
    if [ "${filled}" -gt "${width}" ]; then
        filled="${width}"
    elif [ "${filled}" -lt 0 ]; then
        filled=0
    fi
    local empty=$(( width - filled ))
    local bar=""
    local i
    for ((i=0; i<filled; i++)); do bar="${bar}="; done
    for ((i=0; i<empty; i++)); do bar="${bar} "; done
    echo "[${bar}]"
}

# 6. 서브커맨드 구현
cmd_status() {
    if [ ! -f "${STATE_FILE}" ]; then
        init_state_file 1 "$(get_start_time)"
    fi
    calc_metrics

    local status_desc=""
    if [ "${DELAY_MIN}" -gt 0 ]; then
        status_desc="⚠️ ${DELAY_MIN}분 지연 (목표 종료 ${STAGE_TARGET_END_STR})"
    elif [ "${DELAY_MIN}" -eq 0 ]; then
        status_desc="🟢 정시 진행 중 (목표 종료 ${STAGE_TARGET_END_STR})"
    else
        local early=$(( -DELAY_MIN ))
        status_desc="🟢 정상 (${STAGE_TARGET_END_STR}까지 ${early}분 여유)"
    fi

    local remain_desc=""
    if [ "${REMAIN_MIN}" -ge 0 ]; then
        remain_desc="${REMAIN_MIN}분"
    else
        local overtime=$(( -REMAIN_MIN ))
        remain_desc="0분 (${overtime}분 초과)"
    fi

    echo "============================================================"
    echo "⏱️  Cofa Probe 진행 상태 (STATE)"
    echo "============================================================"
    echo "* 현재 단계: [${CURRENT}/10] ${CURRENT_NAME}"
    echo "* 목표 시각: ${STAGE_TARGET_START_STR} ~ ${STAGE_TARGET_END_STR} (현재: ${NOW_STR})"
    echo "* 경과 시간: ${ELAPSED_MIN}분 / 과제 175분 (마감까지: ${remain_desc})"
    echo "* 과제 진척: $(render_bar "${PROGRESS_PCT}") ${PROGRESS_PCT}% (1~9단계 기준)"
    echo "* 시간 소진: $(render_bar "${TIME_PCT}") ${TIME_PCT}% (175분 기준)"
    echo "* 지연 상태: ${status_desc}"
    echo "============================================================"
    echo "STATE_ID=${CURRENT}"
    echo "STATE_NAME=${CURRENT_NAME}"
    echo "ELAPSED_MIN=${ELAPSED_MIN}"
    echo "REMAIN_MIN=${REMAIN_MIN}"
    echo "PROGRESS_PCT=${PROGRESS_PCT}"
    echo "TIME_PCT=${TIME_PCT}"
    echo "DELAY_MIN=${DELAY_MIN}"
}

cmd_next() {
    local yes_flag=0
    for arg in "$@"; do
        if [ "$arg" = "--yes" ] || [ "$arg" = "-y" ]; then
            yes_flag=1
        fi
    done

    if [ ! -f "${STATE_FILE}" ]; then
        init_state_file 1 "$(get_start_time)"
    fi
    calc_metrics

    local old_stage="${CURRENT}"
    local old_name="${CURRENT_NAME}"

    if [ "${old_stage}" -ge 10 ]; then
        echo "ℹ️ 이미 최종 단계([10/10] 서술형)입니다. 더 이상 전환할 단계가 없습니다."
        return 0
    fi

    local new_stage=$(( old_stage + 1 ))
    local new_name="${STAGE_NAMES[${new_stage}]}"

    local ans1=""
    local ans2=""
    local ans3=""

    # TTY 검사 및 대화형 질의 (비TTY 또는 --yes 시 건너뛰고 '⚠️ 미응답' 기록)
    if [ -t 0 ] && [ "${yes_flag}" -eq 0 ]; then
        echo "============================================================"
        echo "🛡️  단계 전환 3대 자기감사 [${old_stage}.${old_name} → ${new_stage}.${new_name}]"
        echo "   (주의: 답이 비어있어도 경고 후 전환은 진행됩니다)"
        echo "============================================================"

        echo -n "1. [드리프트 없나?] 5단계(아이디어토론)에서 내가 결정한 방향과 지금 구현이 어긋나지 않았나? > "
        read -r ans1 || ans1=""
        if [ -z "$(echo "${ans1}" | tr -d '[:space:]')" ]; then
            echo "   ⚠️ 경고: 답변이 비어 있습니다. (미응답으로 기록)"
            ans1="⚠️ 미응답"
        fi

        echo -n "2. [증거 없는 체크 없나?] '완료'라고 한 항목마다 실행 로그·테스트 결과가 실제로 있나? > "
        read -r ans2 || ans2=""
        if [ -z "$(echo "${ans2}" | tr -d '[:space:]')" ]; then
            echo "   ⚠️ 경고: 답변이 비어 있습니다. (미응답으로 기록)"
            ans2="⚠️ 미응답"
        fi

        echo -n "3. [너무 순조롭지 않았나?] 실패 경로(빈 입력·결측·경계값)를 안 돌려봐서 순조로웠던 건 아닌가? > "
        read -r ans3 || ans3=""
        if [ -z "$(echo "${ans3}" | tr -d '[:space:]')" ]; then
            echo "   ⚠️ 경고: 답변이 비어 있습니다. (미응답으로 기록)"
            ans3="⚠️ 미응답"
        fi
        echo "============================================================"
    else
        ans1="⚠️ 미응답"
        ans2="⚠️ 미응답"
        ans3="⚠️ 미응답"
    fi

    # 이전 단계 목표 대비 지연 기록
    local delay_log=""
    if [ "${DELAY_MIN}" -gt 0 ]; then
        delay_log="+${DELAY_MIN}분 지연"
    elif [ "${DELAY_MIN}" -eq 0 ]; then
        delay_log="0분 (정시 완료)"
    else
        delay_log="${DELAY_MIN}분 (조기 완료)"
    fi

    # STATE.md 에 전환 로그 append
    cat <<EOF >> "${STATE_FILE}"

## [${NOW_STR}] ${old_stage}.${old_name} → ${new_stage}.${new_name}
- 전환 시각: ${NOW_STR} (이전 단계 목표 대비: ${delay_log})
- [감사 1] 드리프트 없나? : ${ans1}
- [감사 2] 증거 없는 체크 없나? : ${ans2}
- [감사 3] 너무 순조롭지 않았나? : ${ans3}
EOF

    # 헤더 CURRENT 갱신
    update_state_header "${new_stage}" "${START}"

    echo "✅ 단계 전환 완료: [${old_stage}.${old_name}] → [${new_stage}.${new_name}]"
}

cmd_set() {
    local target="${1:-}"
    if [ -z "${target}" ] || ! [[ "${target}" =~ ^[0-9]+$ ]] || [ "${target}" -lt 1 ] || [ "${target}" -gt 10 ]; then
        echo "❌ 오류: 1부터 10 사이의 유효한 단계 번호를 지정해야 합니다. (입력: '${target}')" >&2
        exit 1
    fi

    if [ ! -f "${STATE_FILE}" ]; then
        init_state_file 1 "$(get_start_time)"
    fi
    calc_metrics

    local old_stage="${CURRENT}"
    local old_name="${CURRENT_NAME}"
    local new_stage="${target}"
    local new_name="${STAGE_NAMES[${new_stage}]}"

    cat <<EOF >> "${STATE_FILE}"

## [${NOW_STR}] 강제 이동: ${old_stage}.${old_name} → ${new_stage}.${new_name}
- 전환 시각: ${NOW_STR} (수동 변경)
- 사유: 수동 set ${target} 명령 실행
EOF

    update_state_header "${new_stage}" "${START}"
    echo "✅ 단계 강제 이동 완료: [${old_stage}.${old_name}] → [${new_stage}.${new_name}]"
}

cmd_log() {
    if [ -f "${STATE_FILE}" ]; then
        cat "${STATE_FILE}"
    else
        echo "⚠️ STATE 파일이 존재하지 않습니다: ${STATE_FILE}"
        echo "   'bash ${BASH_SOURCE[0]} init' 명령으로 초기화할 수 있습니다."
    fi
}

cmd_init() {
    local st="$(get_start_time)"
    init_state_file 1 "${st}"
    echo "✅ STATE.md 초기화 완료: CURRENT=1, START=${st}"
    echo "   파일: ${STATE_FILE}"
}

show_usage() {
    cat <<EOF
사용법: $(basename "$0") <명령어> [옵션]

Cofa Probe 10단계 타임라인 추적 및 상태 관리 스크립트입니다.

명령어:
  status         현재 단계, 남은 시간, 진척률 및 지연 상태 확인
  next [--yes]   다음 단계로 전환 (3대 감사 질문 확인; --yes 지정 시 건너뛰기)
  set <1-10>     지정한 단계 번호로 강제 이동
  log            STATE.md 전체 진행 로그 출력
  init           STATE.md 초기화 (1단계 설치, START=10:00)

환경변수:
  PROBE_START    시험 시작 시각 지정 (기본값: 10:00, 형식: HH:MM, 예: PROBE_START=10:05)

단계 일람 (총 10단계, 1~9단계 과제 마감 175분):
  1: 설치 (10:00~10:03)      6: 케이스매핑 (10:25~10:30)
  2: 환경확인 (10:03~10:05)    7: 핑퐁구현 (10:30~12:20)
  3: 터미널분리 (10:05~10:08)  8: 검증보고서 (12:20~12:45)
  4: DM공략 (10:08~10:15)    9: 감사제출 (12:45~12:55)
  5: 아이디어토론 (10:15~10:25) 10: 서술형 (13:00~13:30)
EOF
}

main() {
    local cmd="${1:-}"
    shift || true

    case "${cmd}" in
        status)
            cmd_status "$@"
            ;;
        next)
            cmd_next "$@"
            ;;
        set)
            cmd_set "$@"
            ;;
        log)
            cmd_log "$@"
            ;;
        init)
            cmd_init "$@"
            ;;
        -h|--help|help|"")
            show_usage
            if [ -z "${cmd}" ]; then
                exit 1
            fi
            exit 0
            ;;
        *)
            echo "❌ 알 수 없는 명령어: ${cmd}" >&2
            echo "" >&2
            show_usage >&2
            exit 1
            ;;
    esac
}

main "$@"
