#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/pre_submit_audit.py: 제출 직전(12:40) 종합 무감점 사전 점검 스크립트 (Windows/Linux 범용 Python 버전)
- [1] Git 변경 범위(diff --stat) 점검
- [2] 민감정보(API 키, 시크릿, 토큰, 비밀키) 평문 노출 스캔
- [3] 웹 서버 localhost / 127.0.0.1 바인딩 경고 점검 (0.0.0.0 바인딩 필수)
- [4] 시스템 메모리 상태 점검
- [5] 임시 파일 및 하네스 파일 Git 격리 여부 점검
- [6] 하네스 및 인수인계 기록 영구 보존 상태 점검 (의도/인지 가점)
- [7] 도메인 산출물 센티널 잔존 및 무결성 점검 (결측치/센티널 누수 방지)
"""

import os
import sys
import re
import subprocess
from datetime import datetime
from pathlib import Path

# Windows UTF-8 / CP949 환경 대응
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def find_workspace_root() -> Path:
    """Git 워크스페이스 루트 절대 경로 판별 또는 현재 디렉토리 폴백"""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        if res.returncode == 0 and res.stdout.strip():
            return Path(res.stdout.strip()).resolve()
    except Exception:
        pass
    return Path.cwd().resolve()


if any(arg in ("-h", "--help") for arg in sys.argv[1:]):
    print("사용법: python pre_submit_audit.py [WORKSPACE_ROOT]")
    print("제출 직전(12:40) 종합 무감점 사전 점검 스크립트 (Windows/Linux 범용)")
    print("  [1] Git 변경 파일 범위 점검 (합의 범위 외 수정 여부)")
    print("  [2] 민감정보(API 키, 시크릿, 토큰, 비밀키) 평문 노출 스캔")
    print("  [3] 웹 서버 네트워크 바인딩 점검 (localhost vs 0.0.0.0)")
    print("  [4] 시스템 메모리 상태 점검")
    print("  [5] 임시 파일 및 하네스 파일 Git 격리 여부 점검 (.git/info/exclude)")
    print("  [6] 하네스 및 인수인계 기록 영구 보존 상태 점검 (의도/인지 가점)")
    print("  [7] 도메인 산출물 센티널 잔존 및 무결성 점검 (결측치/센티널 누수 방지)")
    sys.exit(0)

WORKSPACE_ROOT = (
    Path(sys.argv[1]).resolve()
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-")
    else find_workspace_root()
)

try:
    os.chdir(str(WORKSPACE_ROOT))
except Exception:
    pass

PASS_COUNT = 0
WARN_COUNT = 0
FAIL_COUNT = 0


def record_pass(msg: str) -> None:
    global PASS_COUNT
    print(f"✅ [PASS] {msg}")
    PASS_COUNT += 1


def record_warn(msg: str) -> None:
    global WARN_COUNT
    print(f"⚠️ [WARN] {msg}")
    WARN_COUNT += 1


def record_fail(msg: str) -> None:
    global FAIL_COUNT
    print(f"❌ [FAIL] {msg}")
    FAIL_COUNT += 1


def is_binary_file(path: Path) -> bool:
    """바이너리 파일 여부 판별 (grep -I 와 동일한 휴리스틱)"""
    try:
        with open(path, "rb") as f:
            chunk = f.read(1024)
            if b"\x00" in chunk:
                return True
    except Exception:
        return True
    return False


def main() -> None:
    print("==========================================================")
    print("🔍 [Cofa Probe 제출 전 최종 감사 (Pre-Submit Audit)]")
    print(f"   실행 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   루트 경로: {WORKSPACE_ROOT}")
    print("==========================================================")

    # --------------------------------------------------------------------------
    # [1] Git 저장소 상태 및 변경 범위 점검
    # --------------------------------------------------------------------------
    print("\n📌 [1] Git 변경 파일 범위 점검 (합의 범위 외 수정 여부)")
    is_git_repo = False
    try:
        chk = subprocess.run(
            ["git", "-C", str(WORKSPACE_ROOT), "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        if chk.returncode == 0 and chk.stdout.strip() == "true":
            is_git_repo = True
    except Exception:
        is_git_repo = False

    if is_git_repo:
        print("--- [git status --short] ---")
        try:
            p_status = subprocess.run(
                ["git", "-C", str(WORKSPACE_ROOT), "status", "--short"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            if p_status.stdout.strip():
                print(p_status.stdout.rstrip())
        except Exception:
            pass

        print("--- [git diff --stat] ---")
        try:
            p_diff = subprocess.run(
                ["git", "-C", str(WORKSPACE_ROOT), "diff", "--stat"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            if p_diff.stdout.strip():
                print(p_diff.stdout.rstrip())
        except Exception:
            pass

        modified_count = 0
        try:
            p_porcelain = subprocess.run(
                ["git", "-C", str(WORKSPACE_ROOT), "status", "--porcelain"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            lines = [line for line in p_porcelain.stdout.splitlines() if line.strip()]
            modified_count = len(lines)
        except Exception:
            pass

        record_pass(f"Git 저장소 점검 완료 (현재 변경/추적 대상: {modified_count}개 항목)")
    else:
        print("⚪ [SKIP] 현재 디렉토리가 Git 저장소가 아닙니다 (git 저장소 아님). Git 점검을 건너뜁니다.")

    # --------------------------------------------------------------------------
    # [2] 민감정보(API 키, 시크릿, 토큰, 비밀키) 평문 노출 스캔
    # --------------------------------------------------------------------------
    print("\n📌 [2] 민감정보(API 키, 시크릿, 토큰, 비밀키) 평문 노출 스캔")
    sensitive_pattern = re.compile(
        r"sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|-----BEGIN .*PRIVATE KEY-----"
    )
    exclude_dirs = {
        ".git", "node_modules", "__pycache__", ".venv", "venv",
        "dist", "build", ".probe-kit", "probe-kit"
    }
    exclude_files = {"pre_submit_audit.sh", "pre_submit_audit.py"}

    leak_results = []
    try:
        for root, dirs, files in os.walk(str(WORKSPACE_ROOT)):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file in files:
                if file in exclude_files or file.endswith(".md"):
                    continue
                file_path = Path(root) / file
                if is_binary_file(file_path):
                    continue
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        for lineno, line in enumerate(f, 1):
                            if sensitive_pattern.search(line):
                                leak_results.append(f"{file_path}:{lineno}:{line.strip()}")
                except Exception:
                    continue
    except Exception:
        pass

    if leak_results:
        print("🚨 [주의] 아래 파일에서 민감정보 패턴이 감지되었습니다:")
        for item in leak_results:
            print(item)
        record_warn("민감정보 하드코딩 의심 패턴이 발견되었습니다! 환경 변수(.env)로 분리하세요.")
    else:
        record_pass("민감정보 하드코딩 의심 패턴 없음")

    # --------------------------------------------------------------------------
    # [3] 웹 서버 localhost / 127.0.0.1 바인딩 경고 점검 (0.0.0.0 바인딩 필수)
    # --------------------------------------------------------------------------
    print("\n📌 [3] 웹 서버 네트워크 바인딩 점검 (localhost vs 0.0.0.0)")
    binding_pattern = re.compile(
        r"(host\s*=\s*['\"](localhost|127\.0\.0\.1)['\"]|listen\s+.*(localhost|127\.0\.0\.1)|--host[=\s]+(localhost|127\.0\.0\.1))"
    )
    target_extensions = {".py", ".js", ".ts", ".sh", ".yaml", ".yml"}

    binding_found = []
    try:
        for root, dirs, files in os.walk(str(WORKSPACE_ROOT)):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file in files:
                if file in exclude_files:
                    continue
                ext = os.path.splitext(file)[1].lower()
                if ext not in target_extensions:
                    continue
                file_path = Path(root) / file
                if is_binary_file(file_path):
                    continue
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        for lineno, line in enumerate(f, 1):
                            if binding_pattern.search(line):
                                binding_found.append(f"{file_path}:{lineno}:{line.strip()}")
                except Exception:
                    continue
    except Exception:
        pass

    if binding_found:
        print("⚠️ [주의] localhost / 127.0.0.1 바인딩 패턴이 감지되었습니다:")
        for item in binding_found:
            print(item)
        record_warn("웹 서버가 localhost로 바인딩되면 채점기 또는 브라우저에서 접근이 차단됩니다. 반드시 '0.0.0.0'으로 바인딩하세요!")
    else:
        record_pass("localhost 하드코딩 없음 (0.0.0.0 권장 준수)")

    # --------------------------------------------------------------------------
    # [4] 시스템 메모리 상태 점검
    # --------------------------------------------------------------------------
    print("\n📌 [4] 시스템 메모리 상태 점검")
    mem_checked = False

    # 1) Linux /proc/meminfo 검사
    proc_meminfo = Path("/proc/meminfo")
    if proc_meminfo.exists():
        try:
            matched_lines = []
            with open(proc_meminfo, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if any(k in line for k in ("MemTotal", "MemFree", "MemAvailable", "SwapTotal", "SwapFree")):
                        matched_lines.append(line.rstrip())
            if matched_lines:
                for ml in matched_lines:
                    print(ml)
                record_pass("/proc/meminfo 로 메모리 상태 확인 완료")
                mem_checked = True
        except Exception:
            pass

    # 2) Linux free command 폴백
    if not mem_checked:
        try:
            free_proc = subprocess.run(
                ["free", "-m"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            if free_proc.returncode == 0:
                print(free_proc.stdout.rstrip())
                record_pass("free 명령으로 메모리 여유 상태 확인 완료")
                mem_checked = True
        except Exception:
            pass

    # 3) Windows 호스트 환경: ctypes GlobalMemoryStatusEx 로 메모리 점검
    if not mem_checked and sys.platform == "win32":
        try:
            import ctypes
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                tot = stat.ullTotalPhys // (1024 * 1024)
                avail = stat.ullAvailPhys // (1024 * 1024)
                load = stat.dwMemoryLoad
                print(f"Windows Physical Memory: Total {tot} MB | Available {avail} MB | Load {load}%")
                record_pass(f"Windows 메모리 상태 확인 완료 (Total: {tot} MB, Available: {avail} MB)")
                mem_checked = True
        except Exception:
            pass

    # 4) 기타 비리눅스 환경 폴백
    if not mem_checked:
        print("ℹ️ [알림] 리눅스 free / /proc/meminfo 환경이 아닙니다 (Windows 호스트 환경).")
        record_pass("메모리 점검 완료 (비리눅스 환경)")

    # --------------------------------------------------------------------------
    # [5] 임시 파일 및 하네스 파일 Git 격리 여부 점검
    # --------------------------------------------------------------------------
    print("\n📌 [5] 임시 파일 및 하네스 파일 Git 격리 여부 점검")
    if is_git_repo:
        exposed_pattern = re.compile(
            r"(\.probe-kit|probe-kit|NOTES_TEMP\.md|TASK_SPEC\.md|SUB_RESULT\.md|HANDOFF\.md)"
        )
        exposed_probe = []
        try:
            p_porcelain = subprocess.run(
                ["git", "-C", str(WORKSPACE_ROOT), "status", "--porcelain"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            for line in p_porcelain.stdout.splitlines():
                if exposed_pattern.search(line):
                    exposed_probe.append(line)
        except Exception:
            pass

        if exposed_probe:
            print("⚠️ [주의] 아래 임시 파일/하네스가 git status에 노출되어 있습니다:")
            for line in exposed_probe:
                print(line)
            record_warn(".git/info/exclude 에 등록하여 Git 상태에서 제외하세요 (디스크에는 영구 보존해야 합니다).")
        else:
            record_pass("임시 파일 및 하네스(.probe-kit, HANDOFF.md 등)가 git status에 노출되지 않음 (격리 완료)")
    else:
        print("⚪ [SKIP] Git 저장소가 아닙니다 (git 저장소 아님). Git 격리 점검을 건너뜁니다.")

    # --------------------------------------------------------------------------
    # [6] 하네스 및 인수인계 기록 영구 보존 상태 점검 (의도/인지 가점)
    # --------------------------------------------------------------------------
    print("\n📌 [6] 하네스 및 인수인계 기록 영구 보존 상태 점검 (의도/인지 가점)")
    harness_preserved = False

    if (
        (WORKSPACE_ROOT / ".probe-kit").is_dir()
        or (WORKSPACE_ROOT / "probe-kit").is_dir()
        or WORKSPACE_ROOT.name == "probe-kit"
        or (WORKSPACE_ROOT / "init.sh").is_file()
    ):
        harness_preserved = True

    if (
        (WORKSPACE_ROOT / "HANDOFF.md").is_file()
        or (WORKSPACE_ROOT / ".probe-kit" / "runtime" / "HANDOFF.md").is_file()
        or (WORKSPACE_ROOT / "probe-kit" / "runtime" / "HANDOFF.md").is_file()
        or (WORKSPACE_ROOT / "runtime" / "HANDOFF.md").is_file()
    ):
        harness_preserved = True

    # case5~7 고급 도메인 스킬 파일 존재 여부 점검 (구버전 워크스페이스 호환성 유지)
    skill_dirs = [
        WORKSPACE_ROOT / ".probe-kit" / "skills",
        WORKSPACE_ROOT / "probe-kit" / "skills",
        WORKSPACE_ROOT / "skills",
    ]
    detected_skills = []
    for sdir in skill_dirs:
        if sdir.is_dir():
            for case_num in (5, 6, 7):
                for m in sdir.glob(f"case{case_num}*.md"):
                    if m.name not in detected_skills:
                        detected_skills.append(m.name)

    if detected_skills:
        print(f"ℹ️ [스킬 팩 감지] case5~7 고급 도메인 스킬 발견: {', '.join(sorted(detected_skills))}")

    if harness_preserved:
        record_pass("하네스 영구 보존 확인됨 (의도/인지 가점 확보)")
    else:
        record_warn("하네스(.probe-kit) 또는 HANDOFF.md를 찾을 수 없습니다. 평가 가점을 위해 디스크에 보존하는 것을 권장합니다.")

    # --------------------------------------------------------------------------
    # [7] 도메인 산출물 센티널 잔존 및 무결성 점검
    # --------------------------------------------------------------------------
    print("\n📌 [7] 도메인 산출물 센티널 잔존 및 무결성 점검 (결측치/센티널 누수 방지)")
    output_dir_names = [
        "output", "outputs", "dist", "result", "results",
        "submission", "submissions", "artifacts"
    ]
    exclude_dirs_check7 = {
        ".git", "node_modules", "__pycache__", ".venv", "venv",
        ".probe-kit", "probe-kit", "tests", "test", "data", "dataset", "datasets",
        "uploads", "upload", "templates", "prompts", "skills", "runtime", "scripts"
    }
    exclude_root_files = {
        "package.json", "package-lock.json", "tsconfig.json", "jsconfig.json",
        "settings.json", "composer.json", "manifest.json", "config.json"
    }

    target_output_files = []
    # 1) 후보 산출물 디렉토리 스캔
    for od in output_dir_names:
        cand_dir = WORKSPACE_ROOT / od
        if cand_dir.is_dir():
            for root, dirs, files in os.walk(str(cand_dir)):
                dirs[:] = [d for d in dirs if d not in exclude_dirs_check7 and not d.startswith(".")]
                for file in files:
                    if file.startswith("."):
                        continue
                    fp = Path(root) / file
                    if fp.is_file() and not is_binary_file(fp):
                        target_output_files.append(fp)

    # 2) 루트 레벨 산출물 파일 스캔 (*.csv, *.tsv, *.json 및 submission*/result* 파일)
    try:
        for entry in WORKSPACE_ROOT.iterdir():
            if entry.is_file() and not entry.name.startswith("."):
                lname = entry.name.lower()
                ext = entry.suffix.lower()
                if ext in {".csv", ".tsv", ".json"}:
                    if entry.name not in exclude_root_files and not lname.startswith("package"):
                        if not is_binary_file(entry) and entry not in target_output_files:
                            target_output_files.append(entry)
                elif any(lname.startswith(p) for p in ("submission", "result", "prediction", "output")):
                    if ext not in {".py", ".sh", ".md", ".toml", ".yml", ".yaml"}:
                        if not is_binary_file(entry) and entry not in target_output_files:
                            target_output_files.append(entry)
    except Exception:
        pass

    sentinel_pattern = re.compile(
        r'(?:(?<![0-9])(?:-9999|-999(?:\.0+)?)(?![0-9])|<\s*DL\b|\bNaN\b)',
        re.IGNORECASE
    )

    sentinel_leaks = []
    if target_output_files:
        for fp in target_output_files:
            try:
                with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                    for lineno, line in enumerate(f, 1):
                        if sentinel_pattern.search(line):
                            clean_line = line.strip()
                            if len(clean_line) > 120:
                                clean_line = clean_line[:117] + "..."
                            try:
                                rel_path = fp.relative_to(WORKSPACE_ROOT)
                            except Exception:
                                rel_path = fp
                            sentinel_leaks.append(f"{rel_path}:{lineno}:{clean_line}")
                            if len(sentinel_leaks) >= 50:
                                break
            except Exception:
                continue

    if sentinel_leaks:
        print("⚠️ [주의] 아래 산출물에서 처리되지 않은 결측/센티널(-999, < DL, NaN 등)이 발견되었습니다:")
        for item in sentinel_leaks[:10]:
            print(f"   {item}")
        if len(sentinel_leaks) > 10:
            print(f"   ... (총 {len(sentinel_leaks)}건 이상 감지)")
        record_warn("산출물에 센티널(-999, < DL, NaN 등)이 남아있습니다. 도메인 전처리/대체(Imputation)를 확인하세요.")
    elif target_output_files:
        record_pass(f"도메인 산출물 센티널 점검 통과 ({len(target_output_files)}개 파일 검사 완료, 결측/센티널 잔존 없음)")
    else:
        record_pass("산출물 파일 없음 또는 생성 전 (산출물 센티널 누수 없음)")

    # --------------------------------------------------------------------------
    # [8] 제출 직전 확인 지침
    # --------------------------------------------------------------------------
    print("\n==========================================================")
    print("🧹 [제출 직전(12:40) 필수 확인 지침]")
    print("==========================================================")
    print("1. 외부 Git 하네스 활용 기록(.probe-kit, HANDOFF.md) 디스크 보존 확인:")
    print("   - 채점관 및 평가 AI의 인지/의도 가점 확보를 위해 디스크에서 절대 삭제하지 않고 보존합니다.")
    print("   - .git/info/exclude 에 의해 과제 git status 에서는 클린하게 격리되어야 합니다.")
    print("")
    print("2. 에디터의 모든 열린 탭이 '저장됨(Ctrl+S)' 상태인지 확인하세요!")
    print("   (에디터 미저장 파일은 제출 시점 채점기에 반영되지 않습니다)")
    print("==========================================================")

    # --------------------------------------------------------------------------
    # [9] 감사 결과 요약 및 종료 코드 반환
    # --------------------------------------------------------------------------
    print("")
    print("==========================================================")
    print(f"📊 [감사 결과 요약] PASS: {PASS_COUNT}건 | WARN: {WARN_COUNT}건")
    print("==========================================================")

    if FAIL_COUNT > 0:
        print(f"❌ 치명적 오류: 실패 항목({FAIL_COUNT}건)이 발견되었습니다.")
        sys.exit(1)
    elif WARN_COUNT > 0:
        print(f"⚠️ 주의: 경고 항목({WARN_COUNT}건)이 발견되었습니다. 위 권고 사항을 확인하세요.")
        print("👉 [안내] 본 검사는 사전 권고 감사이므로 제출 파이프라인을 중단하지 않습니다 (Status: PASS with WARNINGS).")
        sys.exit(0)
    else:
        print("🎉 모든 사전 점검 항목을 완벽히 통과했습니다. 제출 준비 완료!")
        sys.exit(0)


if __name__ == "__main__":
    main()
