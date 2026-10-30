#!/usr/bin/env python3
"""
scripts/handoff.py: 세션 전환 및 단계별 진행 상태 기록을 위한 OS 독립형 Python 3 도구
- bash가 제한되거나 실패하는 환경(WSL E_ACCESSDENIED 등)에서 OS 독립적으로 동작하는 대체 스크립트
- 표준 라이브러리(stdlib)만 사용하며, 외부 패키지 의존성 없음
- 워크스페이스 외부 파일/디렉토리 생성 원천 차단 및 UTF-8 인코딩 보장
"""

import datetime
import os
import re
import shutil
import sys

# Windows cp949 등 비 UTF-8 터미널 출력 환경 대응
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(errors="replace")
    except Exception:
        pass


def safe_print(text):
    """
    터미널 인코딩(cp949 등)으로 인해 유니코드 이모지 출력 시 발생하는 UnicodeEncodeError를 방어합니다.
    """
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
        print(text.encode(encoding, errors="replace").decode(encoding, errors="replace"))


def resolve_paths():
    """
    스크립트 위치 및 워크스페이스 구조를 기반으로 안전하게 경로를 탐색합니다.
    절대로 워크스페이스 외부(HOME, C:/Users 등)로 벗어나지 않습니다.
    """
    script_path = os.path.abspath(__file__)
    scripts_dir = os.path.dirname(script_path)
    parent_dir = os.path.dirname(scripts_dir)
    grandparent_dir = os.path.dirname(parent_dir)

    # 1) 현재 디렉토리 및 상대 경로 기준 우선 탐색
    if os.path.isdir(".probe-kit"):
        workspace_root = os.path.abspath(".")
        harness_root = os.path.join(workspace_root, ".probe-kit")
    elif os.path.isdir("../.probe-kit"):
        workspace_root = os.path.abspath("..")
        harness_root = os.path.join(workspace_root, ".probe-kit")
    elif os.path.isdir(os.path.join(grandparent_dir, ".probe-kit")):
        workspace_root = grandparent_dir
        harness_root = os.path.join(grandparent_dir, ".probe-kit")
    elif os.path.isdir("probe-kit"):
        workspace_root = os.path.abspath(".")
        harness_root = os.path.join(workspace_root, "probe-kit")
    elif os.path.isdir(os.path.join(grandparent_dir, "probe-kit")):
        workspace_root = grandparent_dir
        harness_root = os.path.join(grandparent_dir, "probe-kit")
    else:
        workspace_root = grandparent_dir
        harness_root = parent_dir

    # 안전장치: HOME 디렉토리로 잘못 빠지는 것 방지
    home = os.path.expanduser("~")
    if os.path.abspath(workspace_root) == os.path.abspath(home) and not os.path.isdir(os.path.join(workspace_root, ".probe-kit")):
        workspace_root = grandparent_dir

    # 런타임 디렉토리 결정
    if os.path.isdir(os.path.join(harness_root, "runtime")):
        runtime_dir = os.path.join(harness_root, "runtime")
    elif os.path.isdir(os.path.join(workspace_root, "runtime")):
        runtime_dir = os.path.join(workspace_root, "runtime")
    else:
        runtime_dir = os.path.join(harness_root, "runtime")

    os.makedirs(runtime_dir, exist_ok=True)
    return workspace_root, harness_root, runtime_dir


def append_log_row(target_file, harness_root, ts, step, msg):
    """
    대상 HANDOFF.md 파일의 '단계별 갱신 로그' 표에 새 로그 행을 추가합니다.
    파일이 존재하지 않으면 templates/HANDOFF.md 에서 안전하게 초기화합니다.
    """
    new_row = f"| {ts} | {step} | {msg} |"
    target_dir = os.path.dirname(target_file)
    if target_dir:
        os.makedirs(target_dir, exist_ok=True)

    if not os.path.exists(target_file):
        template_file = os.path.join(harness_root, "templates", "HANDOFF.md")
        if os.path.isfile(template_file):
            shutil.copyfile(template_file, target_file)
        else:
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(
                    "# 🧭 세션 인수인계서 (HANDOFF.md)\n\n"
                    "## 단계별 갱신 로그 (Step Update Log)\n\n"
                    "| 시각 (Time) | 단계 (Step) | 요약 (Summary) |\n"
                    "| :--- | :--- | :--- |\n"
                )

    with open(target_file, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    has_log_section = any(re.search(r"단계별\s*갱신\s*로그", line) for line in lines)

    if has_log_section:
        new_lines = []
        in_sec = False
        in_table = False
        inserted = False

        for line in lines:
            if re.match(r"^#{1,6}\s*.*단계별\s*갱신\s*로그", line):
                in_sec = True

            if in_sec and line.startswith("|"):
                in_table = True
                new_lines.append(line)
                continue

            if in_sec and in_table and not inserted and not line.startswith("|"):
                new_lines.append(new_row + "\n")
                inserted = True
                in_table = False
                in_sec = False

            new_lines.append(line)

        if in_sec and in_table and not inserted:
            new_lines.append(new_row + "\n")
            inserted = True

        out_content = "".join(new_lines)
    else:
        out_content = "".join(lines)
        if not out_content.endswith("\n"):
            out_content += "\n"
        out_content += (
            "\n---\n\n"
            "## 단계별 갱신 로그 (Step Update Log)\n\n"
            "| 시각 (Time) | 단계 (Step) | 요약 (Summary) |\n"
            "| :--- | :--- | :--- |\n"
            f"{new_row}\n"
        )

    tmp_file = target_file + ".tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        f.write(out_content)
    os.replace(tmp_file, target_file)


def parse_args():
    """
    명령줄 인자를 파싱하여 (step, msg)를 반환합니다.
    handoff.sh log 와 100% 동일한 인자 처리 규칙을 적용합니다.
    """
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        safe_print("사용법: python3 .probe-kit/scripts/handoff.py log \"<step>\" \"<message>\"")
        safe_print("예시:   python3 .probe-kit/scripts/handoff.py log \"탐색\" \"Case 식별 및 초기 분석 완료\"")
        sys.exit(0 if len(sys.argv) >= 2 and sys.argv[1] in ("-h", "--help", "help") else 1)

    subcmd = sys.argv[1]
    if subcmd != "log":
        safe_print(f"⚠️ 지원하지 않는 서브커맨드입니다: {subcmd}")
        safe_print("사용 가능한 서브커맨드: log")
        sys.exit(1)

    args = sys.argv[2:]
    if len(args) == 0:
        step = "기록"
        msg = "단계별 진행 상태 기록"
    elif len(args) == 1:
        raw = args[0]
        m = re.match(r"^([A-Za-z0-9가-힣_\ -]+)[:\|]\s*(.+)$", raw)
        if m:
            step = m.group(1).strip()
            msg = m.group(2).strip()
        elif re.match(r"^(TASK_SPEC\s*issued|TASK_SPEC|sub\s*done|SUB_RESULT|verification\s*done|verification|검증\s*완료|서브\s*완료)", raw):
            m2 = re.match(r"^(TASK_SPEC\s*issued|TASK_SPEC|sub\s*done|SUB_RESULT|verification\s*done|verification|검증\s*완료|서브\s*완료)", raw)
            step = m2.group(1).strip()
            msg = raw
        elif re.match(r"^(Step\s*[0-9]+)", raw):
            m3 = re.match(r"^(Step\s*[0-9]+)", raw)
            step = m3.group(1).strip()
            msg = raw
        else:
            step = "진행"
            msg = raw
    else:
        step = args[0]
        msg = " ".join(args[1:])

    return step, msg


def main():
    step, msg = parse_args()
    workspace_root, harness_root, runtime_dir = resolve_paths()

    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S KST")
    handoff_runtime_file = os.path.join(runtime_dir, "HANDOFF.md")
    handoff_root_file = os.path.join(workspace_root, "HANDOFF.md")

    append_log_row(handoff_runtime_file, harness_root, ts, step, msg)
    if os.path.abspath(handoff_root_file) != os.path.abspath(handoff_runtime_file):
        append_log_row(handoff_root_file, harness_root, ts, step, msg)

    safe_print("✅ [Handoff] 단계별 갱신 로그 추가 완료:")
    safe_print(f"   - 시각: {ts}")
    safe_print(f"   - 단계: {step}")
    safe_print(f"   - 내용: {msg}")
    safe_print(f"   - 대상: {handoff_runtime_file}")


if __name__ == "__main__":
    main()
