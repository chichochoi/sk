#!/usr/bin/env bash
# init.sh - Cofa Probe 메인/서브 에이전트 이원화 하네스 자동 설치 스크립트
# 원클릭 설치 예시:
# git clone https://github.com/chichochoi/sk.git /tmp/probe-kit && bash /tmp/probe-kit/init.sh
set -euo pipefail

KIT_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="${1:-}"

if [ -z "$WORKSPACE_DIR" ]; then
  if git rev-parse --show-toplevel >/dev/null 2>&1; then
    WORKSPACE_DIR="$(git rev-parse --show-toplevel)"
  else
    WORKSPACE_DIR="$(pwd)"
    echo "⚠️ [경고] 현재 디렉토리가 git 저장소가 아닙니다. 현재 디렉토리를 워크스페이스로 사용합니다: $WORKSPACE_DIR"
  fi
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

echo "=== [3/6] Codex 글로벌 하네스(~/.codex) 및 모델 프리셋 설정 ==="
mkdir -p "$HOME/.codex"
TS="$(date +%Y%m%d_%H%M%S)"

backup_and_copy() {
  local src="$1"
  local dst="$2"
  if [ -f "$src" ]; then
    if [ -f "$dst" ]; then
      cp "$dst" "${dst}.bak.${TS}"
      echo "-> 기존 $(basename "$dst") 백업 생성: ${dst}.bak.${TS}"
    fi
    cp "$src" "$dst"
    echo "-> $dst 설치 완료"
  fi
}

backup_and_copy "$TARGET_KIT/AGENTS.md" "$HOME/.codex/AGENTS.md"
backup_and_copy "$TARGET_KIT/AGENTS.md" "$HOME/.codex/instructions.md"
backup_and_copy "$TARGET_KIT/config.toml" "$HOME/.codex/config.toml"
backup_and_copy "$TARGET_KIT/SUB_AGENTS.md" "$HOME/.codex/SUB_AGENTS.md"

echo "=== [4/6] 워크스페이스 Git 오염 방지 (.git/info/exclude) 등록 ==="
if [ -d "$WORKSPACE_DIR/.git" ]; then
  mkdir -p "$WORKSPACE_DIR/.git/info"
  EXCLUDE_FILE="$WORKSPACE_DIR/.git/info/exclude"
  touch "$EXCLUDE_FILE"
  for item in ".probe-kit" ".probe-kit/" "NOTES_TEMP.md" "TASK_SPEC.md" "SUB_RESULT.md" "EDA_SUMMARY.txt"; do
    if ! grep -qxF "$item" "$EXCLUDE_FILE" 2>/dev/null; then
      echo "$item" >> "$EXCLUDE_FILE"
    fi
  done
  echo "-> .git/info/exclude 등록 완료 (.probe-kit, NOTES_TEMP.md, TASK_SPEC.md, SUB_RESULT.md, EDA_SUMMARY.txt 차단, .gitignore 미수정)"
else
  echo "⚠️ [경고] .git 디렉토리가 존재하지 않아 .git/info/exclude 등록을 건너뜁니다."
fi

echo "=== [5/6] 런타임 버퍼 보장 및 실시간 메모장(NOTES_TEMP.md) 준비 ==="
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

echo "=== [6/6] 워크스페이스 구조 및 데이터 무토큰 초기 스캔 ==="
EDA_SCRIPT="$TARGET_KIT/scripts/eda_scan.py"
EDA_OUTPUT="$TARGET_KIT/runtime/EDA_SUMMARY.txt"
if [ -f "$EDA_SCRIPT" ]; then
  if command -v python3 >/dev/null 2>&1; then
    python3 "$EDA_SCRIPT" "$WORKSPACE_DIR" > "$EDA_OUTPUT" 2>&1 || true
    cat "$EDA_OUTPUT" 2>/dev/null || true
    echo "-> python3 기반 초기 EDA 스캔 완료: $EDA_OUTPUT"
  elif command -v python >/dev/null 2>&1; then
    python "$EDA_SCRIPT" "$WORKSPACE_DIR" > "$EDA_OUTPUT" 2>&1 || true
    cat "$EDA_OUTPUT" 2>/dev/null || true
    echo "-> python 기반 초기 EDA 스캔 완료: $EDA_OUTPUT"
  else
    echo "⚠️ [경고] python/python3을 찾을 수 없어 EDA 스캔을 건너뜁니다."
  fi
else
  echo "💡 [안내] $EDA_SCRIPT 가 아직 준비되지 않아 초기 EDA 스캔을 건너뜁니다."
fi

echo "======================================================================"
echo "🎉 [probe-kit] 메인(Sol 6.1 xhigh) × 서브(Luna 6 xhigh) 하네스 설치 완료!"
echo "======================================================================"
echo "▶ 저장소 URL:    https://github.com/chichochoi/sk.git"
echo "▶ 워크스페이스:  $WORKSPACE_DIR"
echo "▶ 하네스 디렉토리: $TARGET_KIT"
echo ""
echo "▶ 다음 행동 순서:"
echo "   1) 메인 프롬프트 1 확인: .probe-kit/prompts/02_codex_prompts.md"
echo "   2) [터미널 1 - 메인 아키텍트]: 'codex' 실행 -> '/model'에서 [Sol 6.1 (xhigh)] 선택"
echo "      (역할: 요구사항 분석, 설계, .probe-kit/runtime/TASK_SPEC.md 작성 및 서브 결과 검토)"
echo "   3) [터미널 2 - 서브 워커]: 새 탭 열기 -> 'codex' 실행 -> '/model'에서 [Luna 6 (xhigh)] 선택"
echo "      (역할: TASK_SPEC.md 읽고 코드 구현·테스트 실행 -> SUB_RESULT.md 작성 후 /clear)"
echo "      ※ 비대화형 CLI 지원 환경인 경우 메인 창에서 'bash .probe-kit/scripts/subagent.sh' 실행 가능"
echo ""
echo "▶ 시험 종료 직전 필수 점검 및 클린업 안내:"
echo "   - 사전 무감점 감사: bash .probe-kit/scripts/pre_submit_audit.sh"
echo "   - 임시 파일 정리:   rm -rf .probe-kit NOTES_TEMP.md TASK_SPEC.md SUB_RESULT.md"
echo "   - 에디터 열린 파일: 모든 탭 '저장됨(Ctrl+S)' 상태 최종 확인"
echo "======================================================================"
