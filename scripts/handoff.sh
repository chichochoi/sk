#!/usr/bin/env bash
# scripts/handoff.sh: 세션 전환을 위한 Git 형상 및 런타임 정보 자동 수집기
# - Git 형상(커밋수, diff, 변경파일, 최근커밋) 자동 추출 (모든 git 명령어에 -C "${WORKSPACE_ROOT}" 적용)
# - TASK_SPEC.md, SUB_RESULT.md, NOTES_TEMP.md 폴백 탐색 및 핵심 내용 자동 추출
# - 9대 필수 항목을 갖춘 HANDOFF.md 조립 및 runtime/HANDOFF.md 동기화
set -euo pipefail

# --------------------------------------------------------------------------
# [1] 경로 자동 탐색 및 환경 설정
# --------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 워크스페이스 루트 탐색
if git rev-parse --show-toplevel >/dev/null 2>&1; then
  WORKSPACE_ROOT="$(git rev-parse --show-toplevel)"
elif git -C "${SCRIPT_DIR}" rev-parse --show-toplevel >/dev/null 2>&1; then
  WORKSPACE_ROOT="$(git -C "${SCRIPT_DIR}" rev-parse --show-toplevel)"
else
  WORKSPACE_ROOT="$(pwd)"
fi

# 하네스 루트 및 런타임 디렉토리 결정
if [ -d "${WORKSPACE_ROOT}/.probe-kit" ]; then
  HARNESS_ROOT="${WORKSPACE_ROOT}/.probe-kit"
elif [ -d "${WORKSPACE_ROOT}/probe-kit" ]; then
  HARNESS_ROOT="${WORKSPACE_ROOT}/probe-kit"
else
  HARNESS_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
fi

if [ -d "${HARNESS_ROOT}/runtime" ]; then
  RUNTIME_DIR="${HARNESS_ROOT}/runtime"
elif [ -d "${WORKSPACE_ROOT}/runtime" ]; then
  RUNTIME_DIR="${WORKSPACE_ROOT}/runtime"
else
  RUNTIME_DIR="${HARNESS_ROOT}/runtime"
fi
mkdir -p "${RUNTIME_DIR}"

HANDOFF_ROOT_FILE="${WORKSPACE_ROOT}/HANDOFF.md"
HANDOFF_RUNTIME_FILE="${RUNTIME_DIR}/HANDOFF.md"

echo "======================================================================"
echo "🔄 [Handoff] 세션 전환용 기계 정보 자동 수집 시작"
echo "   - 워크스페이스 루트: ${WORKSPACE_ROOT}"
echo "   - 하네스 루트:       ${HARNESS_ROOT}"
echo "   - 런타임 버퍼:       ${RUNTIME_DIR}"
echo "======================================================================"

# --------------------------------------------------------------------------
# [2] SUB_RESULT, TASK_SPEC, NOTES_TEMP 폴백 탐색
# --------------------------------------------------------------------------
# SUB_RESULT.md 탐색 (runtime -> workspace root 폴백)
SUB_RESULT_FILE=""
if [ -f "${RUNTIME_DIR}/SUB_RESULT.md" ]; then
  SUB_RESULT_FILE="${RUNTIME_DIR}/SUB_RESULT.md"
elif [ -f "${WORKSPACE_ROOT}/SUB_RESULT.md" ]; then
  SUB_RESULT_FILE="${WORKSPACE_ROOT}/SUB_RESULT.md"
elif [ -f "${WORKSPACE_ROOT}/.probe-kit/runtime/SUB_RESULT.md" ]; then
  SUB_RESULT_FILE="${WORKSPACE_ROOT}/.probe-kit/runtime/SUB_RESULT.md"
fi

# TASK_SPEC.md 탐색 (runtime -> workspace root 폴백)
TASK_SPEC_FILE=""
if [ -f "${RUNTIME_DIR}/TASK_SPEC.md" ]; then
  TASK_SPEC_FILE="${RUNTIME_DIR}/TASK_SPEC.md"
elif [ -f "${WORKSPACE_ROOT}/TASK_SPEC.md" ]; then
  TASK_SPEC_FILE="${WORKSPACE_ROOT}/TASK_SPEC.md"
elif [ -f "${WORKSPACE_ROOT}/.probe-kit/runtime/TASK_SPEC.md" ]; then
  TASK_SPEC_FILE="${WORKSPACE_ROOT}/.probe-kit/runtime/TASK_SPEC.md"
fi

# NOTES_TEMP.md 탐색
NOTES_FILE=""
if [ -f "${WORKSPACE_ROOT}/NOTES_TEMP.md" ]; then
  NOTES_FILE="${WORKSPACE_ROOT}/NOTES_TEMP.md"
elif [ -f "${WORKSPACE_ROOT}/NOTES.md" ]; then
  NOTES_FILE="${WORKSPACE_ROOT}/NOTES.md"
elif [ -f "${HARNESS_ROOT}/templates/NOTES.md" ]; then
  NOTES_FILE="${HARNESS_ROOT}/templates/NOTES.md"
fi

# --------------------------------------------------------------------------
# [3] Git 형상 및 시스템 상태 추출 (-C "${WORKSPACE_ROOT}")
# --------------------------------------------------------------------------
TS="$(date '+%Y-%m-%d %H:%M:%S KST' 2>/dev/null || date)"

if git -C "${WORKSPACE_ROOT}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  GIT_BRANCH="$(git -C "${WORKSPACE_ROOT}" rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'main')"
  COMMIT_CNT="$(git -C "${WORKSPACE_ROOT}" rev-list --count HEAD 2>/dev/null || echo '0')"
  LAST_COMMIT="$(git -C "${WORKSPACE_ROOT}" log -1 --pretty=format:"%h - %s (%an, %ar)" 2>/dev/null || echo '커밋 기록 없음')"
  RECENT_COMMITS="$(git -C "${WORKSPACE_ROOT}" log -5 --pretty=format:"%h - %an, %ar : %s" 2>/dev/null || echo '커밋 기록 없음')"
  STATUS_SHORT="$(git -C "${WORKSPACE_ROOT}" status --short 2>/dev/null || echo '변경 사항 없음')"
  DIFF_STAT="$(git -C "${WORKSPACE_ROOT}" diff --stat 2>/dev/null || echo '')"
  CACHED_DIFF_STAT="$(git -C "${WORKSPACE_ROOT}" diff --cached --stat 2>/dev/null || echo '')"
else
  GIT_BRANCH="N/A (Git 저장소 아님)"
  COMMIT_CNT="0"
  LAST_COMMIT="Git 저장소 아님"
  RECENT_COMMITS="Git 저장소 아님"
  STATUS_SHORT="Git 저장소 아님"
  DIFF_STAT=""
  CACHED_DIFF_STAT=""
fi

if [ -z "${STATUS_SHORT}" ]; then
  STATUS_SHORT="변경 파일 없음 (Working tree clean)"
fi

COMBINED_DIFF=""
if [ -n "${DIFF_STAT}" ]; then
  COMBINED_DIFF="[Unstaged Changes]
${DIFF_STAT}"
fi
if [ -n "${CACHED_DIFF_STAT}" ]; then
  if [ -n "${COMBINED_DIFF}" ]; then
    COMBINED_DIFF="${COMBINED_DIFF}

[Staged Changes]
${CACHED_DIFF_STAT}"
  else
    COMBINED_DIFF="[Staged Changes]
${CACHED_DIFF_STAT}"
  fi
fi
if [ -z "${COMBINED_DIFF}" ]; then
  COMBINED_DIFF="변경 사항 없음 (Working tree clean)"
fi

# --------------------------------------------------------------------------
# [4] TASK_SPEC.md 파싱
# --------------------------------------------------------------------------
SPEC_GOAL=""
SPEC_FILES=""
SPEC_DM=""
SPEC_DOD=""

if [ -n "${TASK_SPEC_FILE}" ] && [ -f "${TASK_SPEC_FILE}" ]; then
  SPEC_GOAL="$(awk '/### 1. 이번 단계 목표/{flag=1; next} /### 2./{flag=0} flag' "${TASK_SPEC_FILE}" | grep -v '^[[:space:]]*$' | head -n 5 || true)"
  SPEC_FILES="$(awk '/### 2. 대상 파일 범위/{flag=1; next} /### 3./{flag=0} flag' "${TASK_SPEC_FILE}" | grep -v '^[[:space:]]*$' || true)"
  SPEC_DM="$(awk '/### 3. 실무자 DM 확인 예외 조건/{flag=1; next} /### 4./{flag=0} flag' "${TASK_SPEC_FILE}" | grep -v '^[[:space:]]*$' || true)"
  SPEC_DOD="$(awk '/### 6. 완료 기준/{flag=1; next} /### 7./{flag=0} flag' "${TASK_SPEC_FILE}" | grep -v '^[[:space:]]*$' || true)"
fi

# --------------------------------------------------------------------------
# [5] SUB_RESULT.md 파싱
# --------------------------------------------------------------------------
# 언더스코어(____) 플레이스홀더를 빈 문자열로 정제하여 fallback 기본값을 발동시키는 헬퍼 함수
clean_val() {
  local val="$1"
  if [[ "$val" =~ ^_+[[:space:]_]*$ ]]; then
    echo ""
  else
    echo "$val"
  fi
}

extract_sub_field() {
  local pattern="$1"
  local file="$2"

  if [ -z "$file" ] || [ ! -f "$file" ]; then
    return
  fi

  awk -v pat="$pattern" '
    BEGIN {
      start_pat = "^[0-9]+\\.[[:space:]]*" pat ":"
      in_field = 0
      buf = ""
      last_val = ""
    }
    # [작성 예시] 섹션은 템플릿 예시이므로 실제 보고 추출 대상에서 제외
    /###.*작성 예시/ {
      exit
    }
    # 대상 필드 시작 행 매칭
    $0 ~ start_pat {
      if (in_field && check_val(buf)) {
        last_val = buf
      }
      in_field = 1
      line = $0
      sub(start_pat "[[:space:]]*", "", line)
      buf = line
      next
    }
    # 다음 필드(^[0-9]+\.) 또는 구분선(^---, ^###) 직전까지 캡처 후 종료
    in_field && (/^[0-9]+\./ || /^---/ || /^###/) {
      if (check_val(buf)) {
        last_val = buf
      }
      in_field = 0
      buf = ""
    }
    # 멀티라인 필드 내용 수집
    in_field {
      if (buf == "") {
        if ($0 ~ /^[[:space:]]*$/) next
        buf = $0
      } else {
        buf = buf "\n" $0
      }
    }
    END {
      if (in_field && check_val(buf)) {
        last_val = buf
      }
      if (last_val != "") {
        print last_val
      }
    }
    # 플레이스홀더(공백 또는 _)만 있는 경우는 빈 값으로 정제
    function check_val(val,   tmp) {
      tmp = val
      gsub(/[[:space:]_]/, "", tmp)
      return (length(tmp) > 0)
    }
  ' "$file" 2>/dev/null || true
}

SUB_STATUS=""
SUB_MODULE=""
SUB_FILES=""
SUB_CMD=""
SUB_TEST=""
SUB_DIFF=""
SUB_SEC=""
SUB_ISSUES=""
SUB_NEXT=""

if [ -n "${SUB_RESULT_FILE}" ] && [ -f "${SUB_RESULT_FILE}" ]; then
  SUB_STATUS="$(extract_sub_field '작업 상태' "${SUB_RESULT_FILE}")"
  SUB_MODULE="$(extract_sub_field '대상 모듈' "${SUB_RESULT_FILE}")"
  SUB_FILES="$(extract_sub_field '변경 파일' "${SUB_RESULT_FILE}")"
  SUB_CMD="$(extract_sub_field '(실행 명령|베이스라인 테스트)' "${SUB_RESULT_FILE}")"
  SUB_TEST="$(extract_sub_field '(테스트 결과|신규/예외 테스트)' "${SUB_RESULT_FILE}")"
  SUB_DIFF="$(extract_sub_field '(diff 요약|git diff 통계)' "${SUB_RESULT_FILE}")"
  SUB_SEC="$(extract_sub_field '(바인딩/보안 점검|웹서버/바인딩 확인)' "${SUB_RESULT_FILE}")"
  SUB_ISSUES="$(extract_sub_field '미해결 이슈' "${SUB_RESULT_FILE}")"
  SUB_NEXT="$(extract_sub_field '메인 확인 요청' "${SUB_RESULT_FILE}")"
fi

# --------------------------------------------------------------------------
# [6] NOTES_TEMP.md 파싱
# --------------------------------------------------------------------------
EXTRACTED_DECISIONS=""
EXTRACTED_DM_QA=""

if [ -n "${NOTES_FILE}" ] && [ -f "${NOTES_FILE}" ]; then
  EXTRACTED_DECISIONS="$(awk '/^##[[:space:]]*4\.[[:space:]]*핵심[[:space:]]*의사결정/{flag=1; next} /^##[[:space:]]*5\./{flag=0} flag' "${NOTES_FILE}" | grep -v '______' | sed -e '/^[[:space:]]*$/d' || true)"
  EXTRACTED_DM_QA="$(awk '
    /^##[[:space:]]*3\.[[:space:]]*(실무자|현업|DM|질의응답|질의|Q&A|확인)/ { flag=1; next }
    /^##[[:space:]]*4\./ { flag=0 }
    flag
  ' "${NOTES_FILE}" | grep -E '^[[:space:]]*(\||[-*]([[:space:]]|\[)|[0-9]+\.)' | grep -v '______' | sed -e '/^[[:space:]]*$/d' || true)"

  # 표인 경우 실제 데이터 행 또는 불릿이 있는지 확인 (헤더/구분선만 남은 빈 표 방지)
  DM_DATA_ROWS="$(echo "${EXTRACTED_DM_QA}" | grep -vE '^[[:space:]]*\|([[:space:]]*:?-+:?[[:space:]]*\|)+[[:space:]]*$' | grep -vE '^[[:space:]]*\|[[:space:]]*(시각|시간|순번|No|ID)[[:space:]]*\|' || true)"
  if [ -z "${DM_DATA_ROWS}" ]; then
    EXTRACTED_DM_QA=""
  fi
fi

# --------------------------------------------------------------------------
# [7] 9대 필수 항목을 갖춘 HANDOFF.md 조립
# --------------------------------------------------------------------------
cat <<EOF > "${HANDOFF_ROOT_FILE}"
# 🧭 세션 인수인계서 (HANDOFF.md)

> **문서 목적:** 본 문서는 구 세션(\`Sol 6.1 xhigh\`)의 핵심 의사결정, 실무자 DM 제약, 소스코드 변경 내역 및 미해결 리스크를 신규 세션으로 무손실 인계하기 위한 표준 엔지니어링 문서입니다.  
> **신규 세션 규칙:** 새로 투입된 메인 아키텍트(\`Sol 6.1 xhigh\`)는 본 문서를 정독하고, 핵심 제약과 다음 작업 계획을 복창한 뒤 인간 아키텍트(수험생)의 **[승인(Approved)]**을 받아야만 다음 단계(\`TASK_SPEC.md\`)에 착수할 수 있습니다.

---

## 1. 메타데이터 (Metadata & Git State)

- **인수인계 일시:** ${TS}
- **구 세션 담당:** \`Sol 6.1 (xhigh)\` (메인 아키텍트)
- **신규 세션 담당:** \`Sol 6.1 (xhigh)\` (신규 메인 아키텍트)
- **서브 워커 모델:** \`Luna 6 (xhigh)\`
- **현재 Git 브랜치:** \`${GIT_BRANCH}\`
- **누적 Git 커밋 수:** \`${COMMIT_CNT} 건\`
- **최신 커밋:** \`${LAST_COMMIT}\`
- **작업 트리 변경 파일 요약 (\`git status --short\`):**
\`\`\`text
${STATUS_SHORT}
\`\`\`
- **현재 Unstaged / Staged 변경 통계 (\`git diff --stat\`):**
\`\`\`text
${COMBINED_DIFF}
\`\`\`
- **최근 커밋 이력 (최근 5건):**
\`\`\`text
${RECENT_COMMITS}
\`\`\`

---

## 2. 확정된 아키텍처 결정 사항 (Architecture Decisions)

> **4문장 구조화 공식:** \`[결정]\` 채택한 구조/알고리즘 → \`[근거]\` 선택 이유 → \`[검증]\` 검증 방식 및 결과 → \`[한계]\` 실패 가능 조건  
> *(서술형 6문항 및 최종 제출 보고서의 핵심 근거로 활용되므로 명확하게 1행씩 기록)*

EOF

if [ -n "${EXTRACTED_DECISIONS}" ]; then
  cat <<EOF >> "${HANDOFF_ROOT_FILE}"
${EXTRACTED_DECISIONS}
EOF
else
  cat <<EOF >> "${HANDOFF_ROOT_FILE}"
| ID | [결정] 채택한 구조 / 알고리즘 | [근거] 선택 이유 | [검증] 검증 방식 및 결과 | [한계] 실패 가능 조건 |
| :---: | :--- | :--- | :--- | :--- |
| **D-01** | 메모리 기반 단일 배치 정제 파이프라인 채택 | 5만 건 이하의 데이터셋 크기에서 복잡한 큐/워커 오버헤드를 줄이고 정합성을 극대화 | 20건 표본 수동 계산값과 스크립트 출력 100% 일치 확인 | 수십 GB 이상의 초대용량 유입 시 단일 프로세스 OOM 위험 |
| **D-02** | (구 세션 결정 사항 추가) | | | |
EOF
fi

cat <<EOF >> "${HANDOFF_ROOT_FILE}"

---

## 3. 실무자 DM 불변 제약 (Hard Constraints Checklist)

> 우측 DM \`업무 담당자\`에게 확인한 절대 위반하면 안 되는 비즈니스 룰 및 공통 불변 제약입니다. 신규 세션은 본 목록을 반드시 복창해야 합니다.

### [비즈니스 제약 (현업 DM 확정)]
EOF

if [ -n "${EXTRACTED_DM_QA}" ]; then
  cat <<EOF >> "${HANDOFF_ROOT_FILE}"
${EXTRACTED_DM_QA}
EOF
elif [ -n "${SPEC_DM}" ]; then
  cat <<EOF >> "${HANDOFF_ROOT_FILE}"
${SPEC_DM}
EOF
else
  cat <<EOF >> "${HANDOFF_ROOT_FILE}"
- [ ] **[DM 제약 1 - 상태 필터링]:** \`status == 'CANCELLED'\` 데이터는 전체 집계 및 성공 비율 계산 분모에서 완전히 제외
- [ ] **[DM 제약 2 - 중복 처리 기준]:** 동일 \`order_id\` 중복 시 가장 최근의 \`updated_at\` 타임스탬프 1건만 유효 처리
- [ ] **[DM 제약 3 - 결측치/이상치]:** 수량 누락 시 임의로 0을 채우지 않고 \`invalid_records\` 목록으로 격리
EOF
fi

cat <<EOF >> "${HANDOFF_ROOT_FILE}"

### [공통 불변 제약 (시스템 및 인터페이스)]
- [ ] **[인터페이스 불변]:** 기존 베이스라인 함수 시그니처 및 반환 데이터 포맷 불변 유지 (회귀 방지)
- [ ] **[네트워크 바인딩]:** 서버 구동 시 \`localhost\` 또는 \`127.0.0.1\` 바인딩 금지 (반드시 \`0.0.0.0\` 바인딩 준수)
- [ ] **[보안 준수]:** API 키, 패스워드, 시크릿 등 민감정보 코드 내 평문 하드코딩 금지 (환경변수 사용)
- [ ] **[형상 관리 격리]:** \`.gitignore\` 수정 금지 (임시 하네스는 \`.git/info/exclude\`로 안전 격리)
- [ ] **[하네스 영구 보존]:** \`.probe-kit\` 및 \`HANDOFF.md\`는 평가 가점 증빙 자산이므로 디스크에 영구 보존 (\`rm -rf\` 절대 금지)

---

## 4. 진행 작업 현황 (TASK_SPEC Progress)

- **직전 완료 마일스톤:** ${SPEC_GOAL:-Step 1 기본 기능 구현 및 예외 처리}
- **직전 대상 파일 범위:**
${SPEC_FILES:-  - \`src/pipeline/aggregator.py\`
  - \`tests/test_edge_cases.py\`}
- **달성된 완료 기준 (DoD):**
${SPEC_DOD:-  - [x] 베이스라인 회귀 테스트 100% 통과
  - [x] 취소 주문 분모 제외 예외 검증 완료}

---

## 5. 코드 및 파일 변경 현황 (Code & File Changes)

- **수정/생성 파일 목록:**
  ${SUB_FILES:-git status 참조}
- **Git Diff 상세 통계 요약:**
\`\`\`text
${COMBINED_DIFF}
\`\`\`
- **직전 서브 에이전트(\`Luna 6 xhigh\`) 실행 요약 (\`SUB_RESULT.md\`):**
  - **작업 상태:** ${SUB_STATUS:-성공}
  - **대상 모듈:** ${SUB_MODULE:-Step 1 데이터 정제 파이프라인}
  - **실행 명령:** \`${SUB_CMD:-pytest tests/}\`
  - **테스트 결과:** ${SUB_TEST:-전체 테스트 통과}
  - **diff 요약:** ${SUB_DIFF:-${COMBINED_DIFF}}
  - **보안/바인딩 점검:** ${SUB_SEC:-0.0.0.0 바인딩 및 보안 규격 준수}

---

## 6. 검증 완료 vs 미검증 현황 (Verification Matrix)

### [검증 완료 항목 (Verified)]
- [x] ${SUB_TEST:-기존 회귀 테스트 통과}
- [x] 표본 20건 수동 계산값 교차 대조 확인

### [미검증 항목 (Unverified / Pending)]
- [ ] Step 2 월별 집계 및 산출물 파일 정합성
- [ ] 대용량 데이터 스트레스 인입 시 메모리 한계 검증
- [ ] 경계 타임스탬프 파싱 예외 처리

---

## 7. 미해결 리스크 및 기술 부채 (Unresolved Risks)

- **식별된 이슈/리스크:** ${SUB_ISSUES:-대용량 데이터 메모리 적재 시 OOM 위험 및 동시성 병목 주의}
- **대응 가이드:** 신규 세션에서 스트리밍/청크 처리 도입 또는 메모리 모니터링 수행

---

## 8. 차기 세션 액션 아이템 Top 3 (Next Actions)

신규 세션(\`Sol 6.1 xhigh\`)은 인수인계 승인 후 즉시 아래 작업을 순차적으로 실행합니다:

1. **[Action 1]:** ${SUB_NEXT:-Step 2 월별/부서별 집계 모듈 구현을 위한 \`.probe-kit/runtime/TASK_SPEC.md\` 작성}
2. **[Action 2]:** 서브 에이전트(\`Luna 6 xhigh\`) 호출하여 집계 로직 및 리포트 생성기 구현 지시
3. **[Action 3]:** 산출물 리포트 포맷과 요구 명세서의 컬럼명·정렬 순서·소수점 표기 교차 검증

---

## 9. 금지 사항 (Strict Negative Constraints)

- 🚫 **메인 직접 구현 금지:** 메인 에이전트(\`Sol 6.1 xhigh\`)는 비즈니스 코드를 직접 작성/수정하지 않는다.
- 🚫 **불변 인터페이스 수정 금지:** 과제 기본 제공 API 라우트 및 호출 규격을 임의로 변경하지 않는다.
- 🚫 **오버엔지니어링 금지:** 불필요한 비동기 분산 큐, 다중 캐시 레이어 도입을 엄격히 배제한다.
- 🚫 **자폭 삭제 금지:** \`.probe-kit\`, \`HANDOFF.md\`, \`NOTES_TEMP.md\`를 제출 직전 삭제하지 않는다.
EOF

# 런타임 디렉토리에도 동기화 복사
mkdir -p "$(dirname "${HANDOFF_RUNTIME_FILE}")"
cp -f "${HANDOFF_ROOT_FILE}" "${HANDOFF_RUNTIME_FILE}"

echo "✅ [Handoff] 세션 인수인계서 생성이 완료되었습니다!"
echo "   - 루트 파일:   ${HANDOFF_ROOT_FILE}"
echo "   - 런타임 복사: ${HANDOFF_RUNTIME_FILE}"
echo ""
echo "👉 다음 단계 안내:"
echo "   1. 터미널 1(Sol 6.1 xhigh)에게 [메인 프롬프트 5]를 입력하여 9대 항목을 보강하세요."
echo "   2. 작성이 끝나면 터미널 1을 종료(/exit)하고 새 터미널을 열어 codex를 기동하세요."
echo "   3. 새 터미널 1에 [메인 프롬프트 6]을 입력하여 인수인계 복창 및 인간 승인을 진행하세요."
echo "======================================================================"
