#!/usr/bin/env bash
# scripts/pre_submit_audit.sh: 제출 직전(12:40) 종합 무감점 사전 점검 스크립트
# - Git 변경 범위(diff --stat)
# - 민감정보 평문 노출 스캔
# - localhost/127.0.0.1 바인딩 경고
# - 시스템 메모리 상태
# - 임시/하네스 파일 git 노출 확인 및 클린업 안내

# 감사 스크립트는 실패 항목이 있어도 끝까지 완주해야 하므로 errexit(-e)는 사용하지 않음
set -u
set -o pipefail 2>/dev/null || true

PASS_COUNT=0
WARN_COUNT=0

record_pass() {
  local msg="$1"
  echo "✅ [PASS] ${msg}"
  PASS_COUNT=$((PASS_COUNT + 1))
}

record_warn() {
  local msg="$1"
  echo "⚠️ [WARN] ${msg}"
  WARN_COUNT=$((WARN_COUNT + 1))
}

echo "=========================================================="
echo "🔍 [Cofa Probe 제출 전 최종 감사 (Pre-Submit Audit)]"
echo "   실행 시각: $(date '+%Y-%m-%d %H:%M:%S' 2>/dev/null || date)"
echo "=========================================================="

# --------------------------------------------------------------------------
# [1] Git 저장소 상태 및 변경 범위 점검
# --------------------------------------------------------------------------
echo -e "\n📌 [1] Git 변경 파일 범위 점검 (합의 범위 외 수정 여부)"
if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "--- [git status --short] ---"
  git status --short || true

  echo "--- [git diff --stat] ---"
  git diff --stat || true

  MODIFIED_COUNT=$(git status --porcelain 2>/dev/null | wc -l || echo 0)
  record_pass "Git 저장소 점검 완료 (현재 변경/추적 대상: ${MODIFIED_COUNT}개 항목)"
else
  echo "⚪ [SKIP] 현재 디렉토리가 Git 저장소가 아닙니다. Git 점검을 건너뜁니다."
fi

# --------------------------------------------------------------------------
# [2] 민감정보(API Key, Secret, Token, Private Key) 평문 노출 스캔
# --------------------------------------------------------------------------
echo -e "\n📌 [2] 민감정보(API 키, 시크릿, 토큰, 비밀키) 평문 노출 스캔"
SENSITIVE_PATTERN="sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|-----BEGIN .*PRIVATE KEY-----|(api[_-]?key|secret|password|token)[[:space:]]*[:=][[:space:]]*['\"][^'\"]{6,}"

LEAK_RESULTS=""
if command -v grep >/dev/null 2>&1; then
  # .probe-kit, .git, node_modules, venv 등 제외 후 검사
  LEAK_RESULTS=$(grep -rnEI "${SENSITIVE_PATTERN}" \
    --exclude-dir={.git,node_modules,__pycache__,.venv,venv,dist,build,.probe-kit} \
    --exclude="*.md" \
    --exclude="pre_submit_audit.sh" \
    . 2>/dev/null || true)

  if [ -n "$LEAK_RESULTS" ]; then
    echo "🚨 [주의] 아래 파일에서 민감정보 패턴이 감지되었습니다:"
    echo "$LEAK_RESULTS"
    record_warn "민감정보 하드코딩 의심 패턴이 발견되었습니다! 환경 변수(.env)로 분리하세요."
  else
    record_pass "민감정보 하드코딩 의심 패턴 없음"
  fi
else
  echo "⚪ [SKIP] grep 명령을 사용할 수 없어 민감정보 스캔을 건너뜁니다."
fi

# --------------------------------------------------------------------------
# [3] 웹 서버 localhost / 127.0.0.1 바인딩 경고 점검 (0.0.0.0 바인딩 필수)
# --------------------------------------------------------------------------
echo -e "\n📌 [3] 웹 서버 네트워크 바인딩 점검 (localhost vs 0.0.0.0)"
BINDING_PATTERN="(host[[:space:]]*=[[:space:]]*['\"](localhost|127\.0\.0\.1)['\"]|listen[[:space:]]+.*(localhost|127\.0\.0\.1)|--host[=[:space:]]+(localhost|127\.0\.0\.1))"

BINDING_FOUND=""
if command -v grep >/dev/null 2>&1; then
  BINDING_FOUND=$(grep -rnEI "${BINDING_PATTERN}" \
    --include="*.py" --include="*.js" --include="*.ts" --include="*.sh" --include="*.yaml" --include="*.yml" \
    --exclude-dir={.git,node_modules,__pycache__,.venv,venv,dist,build,.probe-kit} \
    . 2>/dev/null || true)

  if [ -n "$BINDING_FOUND" ]; then
    echo "⚠️ [주의] localhost / 127.0.0.1 바인딩 패턴이 감지되었습니다:"
    echo "$BINDING_FOUND"
    record_warn "웹 서버가 localhost로 바인딩되면 채점기 또는 브라우저에서 접근이 차단됩니다. 반드시 '0.0.0.0'으로 바인딩하세요!"
  else
    record_pass "localhost 하드코딩 없음 (0.0.0.0 권장 준수)"
  fi
else
  echo "⚪ [SKIP] grep 명령을 사용할 수 없어 바인딩 점검을 건너뜁니다."
fi

# --------------------------------------------------------------------------
# [4] 시스템 리소스(Memory/Swap) 여유 상태 점검
# --------------------------------------------------------------------------
echo -e "\n📌 [4] 시스템 메모리 상태 점검"
if command -v free >/dev/null 2>&1; then
  free -m 2>/dev/null || true
  record_pass "free 명령으로 메모리 여유 상태 확인 완료"
elif [ -f "/proc/meminfo" ]; then
  grep -E "(MemTotal|MemFree|MemAvailable|SwapTotal|SwapFree)" /proc/meminfo 2>/dev/null || true
  record_pass "/proc/meminfo 로 메모리 상태 확인 완료"
else
  echo "ℹ️ [알림] 리눅스 free / /proc/meminfo 환경이 아닙니다 (Windows 호스트 환경)."
  record_pass "메모리 점검 완료 (비리눅스 환경)"
fi

# --------------------------------------------------------------------------
# [5] 임시 파일 및 하네스 파일의 Git Status 노출 여부 점검
# --------------------------------------------------------------------------
echo -e "\n📌 [5] 임시 파일 및 하네스 파일 Git 노출 여부 점검"
if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  EXPOSED_PROBE=$(git status --porcelain 2>/dev/null | grep -E "(\.probe-kit|NOTES_TEMP\.md|TASK_SPEC\.md|SUB_RESULT\.md)" || true)
  if [ -n "$EXPOSED_PROBE" ]; then
    echo "⚠️ [주의] 아래 임시 파일/하네스가 git status에 노출되어 있습니다:"
    echo "$EXPOSED_PROBE"
    record_warn ".git/info/exclude 에 등록하거나 제출 직전 삭제하세요."
  else
    record_pass "임시 파일(.probe-kit, NOTES_TEMP.md 등)이 git status에 노출되지 않음"
  fi
else
  echo "⚪ [SKIP] Git 저장소가 아니므로 건너뜁니다."
fi

# --------------------------------------------------------------------------
# [6] 제출 직전 클린업 명령 안내
# --------------------------------------------------------------------------
echo -e "\n=========================================================="
echo "🧹 [제출 직전(12:40) 필수 클린업 지침]"
echo "=========================================================="
echo "1. 제출 전 시험 워크스페이스에서 임시 파일을 완전히 삭제하세요:"
echo "   rm -rf .probe-kit NOTES_TEMP.md TASK_SPEC.md SUB_RESULT.md"
echo ""
echo "2. 에디터의 모든 열린 탭이 '저장됨(Ctrl+S)' 상태인지 확인하세요!"
echo "   (에디터 미저장 파일은 제출 시점 채점기에 반영되지 않습니다)"
echo "=========================================================="

# --------------------------------------------------------------------------
# [7] 감사 결과 요약 및 종료 코드 반환
# --------------------------------------------------------------------------
echo ""
echo "=========================================================="
echo "📊 [감사 결과 요약] PASS: ${PASS_COUNT}건 | WARN: ${WARN_COUNT}건"
echo "=========================================================="

if [ "$WARN_COUNT" -gt 0 ]; then
  echo "⚠️ 경고 항목이 있습니다. 위 점검 내역을 확인하고 조치하세요."
  exit 1
else
  echo "🎉 모든 사전 점검 항목을 통과했습니다. 제출 준비 완료!"
  exit 0
fi
