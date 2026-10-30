#!/usr/bin/env bash
# init.sh - Cofa Probe 메인/서브 에이전트 이원화 하네스 자동 설치 스크립트
# 원클릭 설치 예시:
# git clone https://github.com/chichochoi/sk.git /tmp/probe-kit && bash /tmp/probe-kit/init.sh
set -euo pipefail

KIT_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ "$(basename "$KIT_SRC")" = "scripts" ]; then
  KIT_SRC="$(cd "$KIT_SRC/.." && pwd)"
fi
WORKSPACE_DIR="${1:-}"

if [ -z "$WORKSPACE_DIR" ]; then
  if git rev-parse --show-toplevel >/dev/null 2>&1; then
    WORKSPACE_DIR="$(git rev-parse --show-toplevel)"
  else
    WORKSPACE_DIR="$(pwd)"
    echo "⚠️ [경고] 현재 디렉토리가 git 저장소가 아닙니다. 현재 디렉토리를 워크스페이스로 사용합니다: $WORKSPACE_DIR"
  fi
fi

# 워크스페이스 경로 정규화 (존재하는 디렉토리인 경우 절대 경로로 변환)
if [ -d "$WORKSPACE_DIR" ]; then
  WORKSPACE_DIR="$(cd "$WORKSPACE_DIR" && pwd)"
fi

echo "======================================================================"
echo "🚀 [probe-kit] Cofa Probe 하네스 자동 세팅 시작"
echo "   - KIT_SRC:       $KIT_SRC"
echo "   - WORKSPACE_DIR: $WORKSPACE_DIR"
echo "======================================================================"

echo "=== [1/6] 외부 git push 원천 차단 (보안 안전장치) ==="
if [ "$KIT_SRC" != "$WORKSPACE_DIR" ]; then
  if [ -d "$KIT_SRC/.git" ]; then
    rm -rf "$KIT_SRC/.git"
    echo "-> $KIT_SRC/.git 삭제 완료 (시험 중 외부 push 실수 차단)"
  fi
else
  echo "-> [안전장치] KIT_SRC가 워크스페이스 자신이므로 .git 삭제를 건너뜁니다."
fi

echo "=== [2/6] probe-kit 하네스 파일을 워크스페이스(.probe-kit)로 배포 ==="
TARGET_KIT="$WORKSPACE_DIR/.probe-kit"
mkdir -p "$TARGET_KIT"
TARGET_KIT="$(cd "$TARGET_KIT" && pwd)"
if [ "$KIT_SRC" != "$TARGET_KIT" ]; then
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --exclude='.git' "$KIT_SRC/" "$TARGET_KIT/"
  else
    cp -rf "$KIT_SRC"/. "$TARGET_KIT/" 2>/dev/null || cp -r "$KIT_SRC"/* "$TARGET_KIT/" 2>/dev/null || true
    rm -rf "$TARGET_KIT/.git"
  fi
  echo "-> $TARGET_KIT 로 하네스 파일 복사 완료"
else
  echo "-> 하네스가 이미 $TARGET_KIT 에 위치하고 있습니다."
fi

find "$TARGET_KIT" -type f \( -name "*.sh" -o -name "*.py" \) -exec chmod +x {} + 2>/dev/null || true
echo "-> 스크립트 실행 권한(chmod +x) 설정 완료"

echo "=== [3/6] 워크스페이스 Git 오염 방지 (.git/info/exclude) 등록 ==="
if [ -d "$WORKSPACE_DIR/.git" ]; then
  mkdir -p "$WORKSPACE_DIR/.git/info"
  EXCLUDE_FILE="$WORKSPACE_DIR/.git/info/exclude"
  touch "$EXCLUDE_FILE"
  for item in "/.probe-kit" "/.probe-kit/" "/runtime/" "/NOTES_TEMP.md" "/TASK_SPEC.md" "/SUB_RESULT.md" "/EDA_SUMMARY.txt" "/HANDOFF.md"; do
    if ! grep -qxF "$item" "$EXCLUDE_FILE" 2>/dev/null; then
      echo "$item" >> "$EXCLUDE_FILE"
    fi
  done
  echo "-> .git/info/exclude 등록 완료 (.probe-kit, runtime/, HANDOFF.md 등 차단, .gitignore 미수정)"
else
  echo "⚠️ [경고] .git 디렉토리가 존재하지 않아 .git/info/exclude 등록을 건너뜁니다."
fi

echo "=== [4/6] 런타임 버퍼 보장 및 실시간 메모장/인수인계서 준비 ==="
mkdir -p "$TARGET_KIT/runtime"
if [ -f "$TARGET_KIT/templates/NOTES.md" ]; then
  if [ ! -f "$WORKSPACE_DIR/NOTES_TEMP.md" ]; then
    cp "$TARGET_KIT/templates/NOTES.md" "$WORKSPACE_DIR/NOTES_TEMP.md"
    echo "-> templates/NOTES.md -> $WORKSPACE_DIR/NOTES_TEMP.md 복사 완료"
  else
    echo "-> 기존 $WORKSPACE_DIR/NOTES_TEMP.md 유지"
  fi
else
  echo "💡 [안내] $TARGET_KIT/templates/NOTES.md 파일이 없어 복사를 대기합니다."
fi

# HANDOFF.md 템플릿 복사 (존재하지 않을 때만 복사, 기존 파일 절대 덮어쓰기 금지)
HANDOFF_TEMPLATE=""
if [ -f "$TARGET_KIT/templates/HANDOFF.md" ]; then
  HANDOFF_TEMPLATE="$TARGET_KIT/templates/HANDOFF.md"
elif [ -f "$KIT_SRC/templates/HANDOFF.md" ]; then
  HANDOFF_TEMPLATE="$KIT_SRC/templates/HANDOFF.md"
fi

if [ -n "$HANDOFF_TEMPLATE" ]; then
  if [ ! -f "$TARGET_KIT/runtime/HANDOFF.md" ]; then
    cp "$HANDOFF_TEMPLATE" "$TARGET_KIT/runtime/HANDOFF.md"
    echo "-> templates/HANDOFF.md -> $TARGET_KIT/runtime/HANDOFF.md 복사 완료"
  else
    echo "-> 기존 $TARGET_KIT/runtime/HANDOFF.md 유지 (덮어쓰기 방지)"
  fi
  if [ -d "$WORKSPACE_DIR/runtime" ] && [ ! -f "$WORKSPACE_DIR/runtime/HANDOFF.md" ]; then
    cp "$HANDOFF_TEMPLATE" "$WORKSPACE_DIR/runtime/HANDOFF.md"
    echo "-> templates/HANDOFF.md -> $WORKSPACE_DIR/runtime/HANDOFF.md 복사 완료"
  fi
else
  echo "💡 [안내] templates/HANDOFF.md 파일이 없어 복사를 대기합니다."
fi

echo "=== [5/6] 워크스페이스 구조 및 데이터 무토큰 초기 스캔 ==="
EDA_SCRIPT="$TARGET_KIT/scripts/eda_scan.py"
EDA_OUTPUT="$TARGET_KIT/runtime/EDA_SUMMARY.txt"
if [ -f "$EDA_SCRIPT" ]; then
  PYTHON_BIN=""
  if command -v python3 >/dev/null 2>&1 && python3 -c "import sys; sys.exit(0)" >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  elif command -v python >/dev/null 2>&1 && python -c "import sys; sys.exit(0)" >/dev/null 2>&1; then
    PYTHON_BIN="python"
  fi

  if [ -n "$PYTHON_BIN" ]; then
    "$PYTHON_BIN" "$EDA_SCRIPT" "$WORKSPACE_DIR" > "$EDA_OUTPUT" 2>&1 || true
    cat "$EDA_OUTPUT" 2>/dev/null || true
    echo "-> $PYTHON_BIN 기반 초기 EDA 스캔 완료: $EDA_OUTPUT"
  else
    echo "-> [경고] 유효한 python3 실행기를 찾지 못해 EDA 스캔을 건너뜁니다."
  fi
else
  echo "💡 [안내] $EDA_SCRIPT 가 아직 준비되지 않아 초기 EDA 스캔을 건너뜁니다."
fi

echo "=== [6/6] Codex 글로벌 하네스(~/.codex) 및 모델 프리셋 설정 ==="
CODEX_DIR="${HOME:-}/.codex"
TS="$(date +%Y%m%d_%H%M%S)"
codex_install_failed=0

if [ -z "${HOME:-}" ] || ! mkdir -p "$CODEX_DIR" 2>/dev/null; then
  echo "⚠️ [경고] ~/.codex 설치 실패(권한): 건너뜀. 에이전트에게 .probe-kit/AGENTS.md를 직접 읽게 하세요"
  codex_install_failed=1
fi

backup_and_copy() {
  local src="$1"
  local dst="$2"
  if [ "$codex_install_failed" -eq 1 ]; then
    return 0
  fi
  if [ -f "$src" ]; then
    if [ -f "$dst" ]; then
      if ! cp "$dst" "${dst}.bak.${TS}" 2>/dev/null; then
        echo "⚠️ [경고] ~/.codex 설치 실패(권한): 건너뜀. 에이전트에게 .probe-kit/AGENTS.md를 직접 읽게 하세요"
        codex_install_failed=1
        return 0
      fi
      echo "-> 기존 $(basename "$dst") 백업 생성: ${dst}.bak.${TS}"
    fi
    if ! cp "$src" "$dst" 2>/dev/null; then
      echo "⚠️ [경고] ~/.codex 설치 실패(권한): 건너뜀. 에이전트에게 .probe-kit/AGENTS.md를 직접 읽게 하세요"
      codex_install_failed=1
      return 0
    fi
    echo "-> $dst 설치 완료"
  fi
}

backup_and_copy "$TARGET_KIT/AGENTS.md" "$CODEX_DIR/AGENTS.md"
backup_and_copy "$TARGET_KIT/AGENTS.md" "$CODEX_DIR/instructions.md"
backup_and_copy "$TARGET_KIT/config.toml" "$CODEX_DIR/config.toml"
backup_and_copy "$TARGET_KIT/SUB_AGENTS.md" "$CODEX_DIR/SUB_AGENTS.md"

echo "======================================================================"
echo "🎉 [probe-kit] 메인(Sol 6.1 xhigh) × 서브(Luna 6 xhigh) 하네스 설치 완료!"
echo "======================================================================"
echo "▶ 저장소 URL:    https://github.com/chichochoi/sk.git"
echo "▶ 워크스페이스:  $WORKSPACE_DIR"
echo "▶ 하네스 디렉토리: $TARGET_KIT"
echo ""
if [ "$codex_install_failed" -eq 1 ]; then
  echo "⚠️ [주의] ~/.codex 설치가 건너뛰어졌습니다(권한 제한 등)."
  echo "   -> 에이전트 시작 시 프롬프트에 '먼저 .probe-kit/AGENTS.md(또는 SUB_AGENTS.md)를 읽고' 지침을 반드시 포함하세요."
  echo ""
fi
echo "▶ 다음 행동 순서:"
echo "   1) 실전 라이브 런북 확인: .probe-kit/foruser.md (프롬프트 원문: .probe-kit/prompts/02_codex_prompts.md)"
echo "   2) [터미널 1 - 메인 아키텍트]: 'codex' 실행 -> '/model'에서 [Sol 6.1 (xhigh)] 선택"
echo "      (역할: 요구사항 분석, 설계, .probe-kit/runtime/TASK_SPEC.md 작성 및 서브 결과 검토)"
echo "      (※ ~/.codex 설치 실패 시: 프롬프트 첫머리에 '먼저 .probe-kit/AGENTS.md를 읽고' 지시 포함)"
echo "   3) [터미널 2 - 서브 워커]: 새 탭 열기 -> 'codex' 실행 -> '/model'에서 [Luna 6 (xhigh)] 선택"
echo "      (역할: TASK_SPEC.md 읽고 코드 구현·테스트 실행 -> SUB_RESULT.md 작성 후 /clear)"
echo "      (※ ~/.codex 설치 실패 시: 프롬프트 첫머리에 '먼저 .probe-kit/SUB_AGENTS.md를 읽고' 지시 포함)"
echo "      ※ 비대화형 CLI 지원 환경인 경우 메인 창에서 'bash .probe-kit/scripts/subagent.sh' 실행 가능"
echo "   4) [Handoff 로깅 규칙]: handoff 로그는 에이전트가 실행되는 터미널과 같은 셸에서 실행. bash가 실패하면(WSL E_ACCESSDENIED 등) 'python3 .probe-kit/scripts/handoff.py log \"<step>\" \"<msg>\"' 사용. 그래도 안 되면 runtime/HANDOFF.md 표에 직접 한 줄 추가"
echo ""
echo "▶ 시험 종료 직전 필수 점검 및 클린업 안내:"
echo "   - 사전 무감점 감사: bash .probe-kit/scripts/pre_submit_audit.sh (또는 python3 .probe-kit/scripts/pre_submit_audit.py)"
echo "   - 하네스 영구 보존: 채점관/평가 AI 확인 및 가점(의도/인지) 확보를 위해 .probe-kit 및 런타임 기록(HANDOFF.md 등)은 삭제하지 않고 디스크에 영구 보존하여 제출합니다."
echo "   - Git 형상 점검:   git status 가 클린한지 확인 (.git/info/exclude 로 자동 격리됨)"
echo "   - 에디터 열린 파일: 모든 탭 '저장됨(Ctrl+S)' 상태 최종 확인"
echo "======================================================================"
