#!/usr/bin/env python3
"""
scripts/sample_check_template.py
반도체 웨이퍼 센서 데이터 과제용 표본 수동 대조 단위 테스트 템플릿 (Case 1 & Case 5 필수)
- 15건의 정상, 중복, 불량, 결측, 경계값 표본 데이터 구성 (SK하이닉스 웨이퍼 센서 도메인)
- 수동 계산된 기댓값(EXPECTED)과 실제 처리 함수 출력값 정밀 비교
- 단계별(원본 -> 중복제거 -> 불량제외 -> 결측제외) 건수 추적 로깅
- 불일치 시 직관적인 diff 출력
- TARGET_MODULE / TARGET_FUNC 동적 로딩 지원 (미지정 시 안내 후 내장 참조 검증, --demo 플래그 시 내장 reference_impl 검증)
- 선택적 입력 파일(CSV/TSV/JSON/JSONL 산출물) 유효성 및 센티널 잔존 검증 지원
"""

import os
import sys
import unittest
import importlib
import difflib
import json
import math
from typing import List, Dict, Any, Optional

# 워크스페이스 루트 및 현재 작업 디렉토리 sys.path 등록 (루트 모듈 임포트 지원)
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

# Windows CP949 환경 대응
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

def safe_print(text, file=None):
    """터미널 인코딩(cp949 등)으로 인한 UnicodeEncodeError 방어 출력 함수"""
    out_file = file or sys.stdout
    try:
        print(text, file=out_file)
    except UnicodeEncodeError:
        encoding = getattr(out_file, "encoding", None) or "utf-8"
        clean_text = text.encode(encoding, errors="replace").decode(encoding, errors="replace")
        print(clean_text, file=out_file)

# --------------------------------------------------------------------------
# [0] 실행 모드 확인 (--demo 플래그 또는 DEMO_MODE 환경변수)
# --------------------------------------------------------------------------
IS_DEMO = "--demo" in sys.argv or os.environ.get("DEMO_MODE", "0") == "1"

# --------------------------------------------------------------------------
# [1] 테스트 대상 모듈 및 함수 설정 (환경 변수 또는 코드 수정)
# --------------------------------------------------------------------------
TARGET_MODULE = os.environ.get("TARGET_MODULE", "").strip()
TARGET_FUNC = os.environ.get("TARGET_FUNC", "").strip()

# --------------------------------------------------------------------------
# [2] 내장 참조 구현체 (Reference Implementation)
#     - 비즈니스 로직:
#       1) wafer_id 기준 중복 제거 (최초 발생 건 유지)
#       2) status가 scrap, discard, abnormal 불량 웨이퍼 제외
#       3) thickness 결측치(None, "", -999, NaN) 제외
#       4) lot_id별 유효 두께(thickness) 합산 (소수점 둘째자리 반올림)
# --------------------------------------------------------------------------
def reference_impl(wafers: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    웨이퍼 센서 측정 데이터 정제 및 Lot별 두께(thickness) 합산 참조 함수
    단계별 필터링 카운트를 표준 출력으로 기록합니다.
    """
    total_raw = len(wafers)

    # 1. wafer_id 기준 중복 제거 (최초 발생 건 유지)
    seen_wafer_ids = set()
    deduped_wafers = []
    dup_count = 0
    for w in wafers:
        wid = w.get("wafer_id")
        if wid in seen_wafer_ids:
            dup_count += 1
            continue
        seen_wafer_ids.add(wid)
        deduped_wafers.append(w)

    # 2. 불량 웨이퍼(scrap, discard, abnormal) 제외
    active_wafers = []
    defect_count = 0
    defect_statuses = {"scrap", "discard", "abnormal"}
    for w in deduped_wafers:
        status = str(w.get("status", "")).strip().lower()
        if status in defect_statuses:
            defect_count += 1
            continue
        active_wafers.append(w)

    # 3. thickness 결측치(None, "", -999, NaN) 제외
    valid_wafers = []
    missing_thickness_count = 0
    missing_tokens = {None, "", "none", "nan", "null", "-999", "-999.0", -999, -999.0}

    for w in active_wafers:
        thk_raw = w.get("thickness")
        if thk_raw in missing_tokens:
            missing_thickness_count += 1
            continue
        try:
            thk = float(thk_raw)
            if thk in (-999.0,) or math.isnan(thk):
                missing_thickness_count += 1
                continue
            valid_wafers.append((w["lot_id"], thk))
        except (ValueError, TypeError):
            missing_thickness_count += 1
            continue

    # 단계별 건수 로깅 출력
    print("\n" + "=" * 60)
    print("[파이프라인 단계별 처리 건수 로깅]")
    print(f"  1. 원본 데이터 수                  : {total_raw}건")
    print(f"  2. 중복 wafer_id 제거 후           : {len(deduped_wafers)}건 (중복 제거: {dup_count}건)")
    print(f"  3. 불량 웨이퍼 제외 후             : {len(active_wafers)}건 (불량 제외: {defect_count}건)")
    print(f"  4. thickness 결측치 제외 후 유효 건수: {len(valid_wafers)}건 (결측 제외: {missing_thickness_count}건)")
    print("=" * 60)

    # 4. lot_id별 유효 두께(thickness) 합산 (소수점 둘째자리 반올림)
    result: Dict[str, float] = {}
    for lid, thk in valid_wafers:
        result[lid] = round(result.get(lid, 0.0) + thk, 2)

    return result

# --------------------------------------------------------------------------
# [3] 표본 데이터 (정상 6 + 중복 2 + 불량 3 + 결측 3 + 경계값 1 = 총 15건)
# --------------------------------------------------------------------------
SAMPLES: List[Dict[str, Any]] = [
    # --- [정상 건: 6건] ---
    {
        "wafer_id": "W-001",
        "lot_id": "LOT-101",
        "thickness": 100.0,
        "status": "NORMAL",
        "timestamp": "2026-10-28 09:00:00"
    },
    {
        "wafer_id": "W-002",
        "lot_id": "LOT-101",
        "thickness": 101.2,
        "status": "NORMAL",
        "timestamp": "2026-10-28 09:15:00"
    },
    {
        "wafer_id": "W-003",
        "lot_id": "LOT-102",
        "thickness": 99.5,
        "status": "NORMAL",
        "timestamp": "2026-10-28 09:30:00"
    },
    {
        "wafer_id": "W-004",
        "lot_id": "LOT-102",
        "thickness": 100.5,
        "status": "NORMAL",
        "timestamp": "2026-10-28 10:00:00"
    },
    {
        "wafer_id": "W-005",
        "lot_id": "LOT-103",
        "thickness": 98.0,
        "status": "NORMAL",
        "timestamp": "2026-10-28 10:30:00"
    },
    {
        "wafer_id": "W-006",
        "lot_id": "LOT-103",
        "thickness": 102.0,
        "status": "NORMAL",
        "timestamp": "2026-10-28 11:00:00"
    },

    # --- [중복 유입 건: 2건] (이미 유입된 wafer_id 재유입 -> 최초 건 유지 원칙으로 제외) ---
    {
        "wafer_id": "W-001",  # W-001 중복 (두께가 달라도 최초 건 유지 원칙)
        "lot_id": "LOT-101",
        "thickness": 150.0,
        "status": "NORMAL",
        "timestamp": "2026-10-28 11:15:00"
    },
    {
        "wafer_id": "W-003",  # W-003 동일 웨이퍼 센서 재전송 중복
        "lot_id": "LOT-102",
        "thickness": 99.5,
        "status": "NORMAL",
        "timestamp": "2026-10-28 11:20:00"
    },

    # --- [불량 웨이퍼 건: 3건] (status in scrap, discard, abnormal -> 집계 제외) ---
    {
        "wafer_id": "W-007",
        "lot_id": "LOT-101",
        "thickness": 95.0,
        "status": "SCRAP",     # 대문자 SCRAP
        "timestamp": "2026-10-28 11:30:00"
    },
    {
        "wafer_id": "W-008",
        "lot_id": "LOT-102",
        "thickness": 105.0,
        "status": "discard",   # 소문자 discard
        "timestamp": "2026-10-28 11:45:00"
    },
    {
        "wafer_id": "W-009",
        "lot_id": "LOT-103",
        "thickness": 88.0,
        "status": "abnormal",  # abnormal 상태 필터링 검증
        "timestamp": "2026-10-28 12:30:00"
    },

    # --- [결측치 건: 3건] (thickness가 None, 센티널 -999, 공백 "" -> 집계 제외) ---
    {
        "wafer_id": "W-010",
        "lot_id": "LOT-101",
        "thickness": None,     # Null / None 결측
        "status": "NORMAL",
        "timestamp": "2026-10-28 12:00:00"
    },
    {
        "wafer_id": "W-011",
        "lot_id": "LOT-102",
        "thickness": -999.0,   # 센티널 결측 표기 (-999.0)
        "status": "NORMAL",
        "timestamp": "2026-10-28 12:15:00"
    },
    {
        "wafer_id": "W-012",
        "lot_id": "LOT-103",
        "thickness": "",       # 공백 문자열("") 결측치
        "status": "NORMAL",
        "timestamp": "2026-10-28 12:45:00"
    },

    # --- [경계값 건: 1건] (정상 상태 및 소수점 가산 정밀도 검증) ---
    {
        "wafer_id": "W-013",
        "lot_id": "LOT-101",
        "thickness": 98.8,     # 경계값: 소수점 정밀도 검증 (100.0 + 101.2 + 98.8 = 300.0)
        "status": "NORMAL",
        "timestamp": "2026-10-28 13:00:00"
    },
]

# --------------------------------------------------------------------------
# [4] 수동 검산 기댓값 (EXPECTED)
#     - 계산 근거:
#       * LOT-101: W-001(100.0) + W-002(101.2) + W-013(98.8) = 300.0
#                  (W-001 중복 제외, W-007 SCRAP 불량 제외, W-010 None 결측 제외)
#       * LOT-102: W-003(99.5) + W-004(100.5) = 200.0
#                  (W-003 중복 제외, W-008 discard 불량 제외, W-011 -999.0 결측 제외)
#       * LOT-103: W-005(98.0) + W-006(102.0) = 200.0
#                  (W-009 abnormal 불량 제외, W-012 "" 결측 제외)
# --------------------------------------------------------------------------
EXPECTED: Dict[str, float] = {
    "LOT-101": 300.0,
    "LOT-102": 200.0,
    "LOT-103": 200.0,
}

# --------------------------------------------------------------------------
# [5] 동적 함수 로더
# --------------------------------------------------------------------------
def load_target_function():
    if IS_DEMO:
        print("[데모 모드] 내장 reference_impl 을 사용해 자체 검증을 수행합니다. (--demo 옵션 활성화)")
        return reference_impl

    if TARGET_MODULE and TARGET_FUNC:
        try:
            mod = importlib.import_module(TARGET_MODULE)
            fn = getattr(mod, TARGET_FUNC)
            print(f"[타깃 로드 성공] {TARGET_MODULE}.{TARGET_FUNC} 함수를 사용합니다.")
            return fn
        except Exception as e:
            err_msg = f"[타깃 로드 실패] {TARGET_MODULE}.{TARGET_FUNC} 로드 불가 ({e}). 실제 구현 코드를 확인하세요."
            print(f"❌ {err_msg}", file=sys.stderr)
            raise ImportError(err_msg)

    print("\n" + "=" * 60)
    print("ℹ️ [안내] TARGET_MODULE 및 TARGET_FUNC 환경변수가 미지정되어,")
    print("   내장 참조 구현체(reference_impl) 데모 모드로 검증을 수행합니다.")
    print("   👉 실제 과제 함수 검증 시 아래와 같이 환경변수를 지정하여 실행하세요:")
    print("      TARGET_MODULE=src.pipeline TARGET_FUNC=process_wafers python3 scripts/sample_check_template.py")
    print("=" * 60 + "\n")
    return reference_impl

# --------------------------------------------------------------------------
# [6] 산출물 데이터 파일 유효성 및 센티널 잔존 검증 (verify_output_file)
# --------------------------------------------------------------------------
def verify_output_file(file_path: str):
    """
    선택적 산출물 데이터 파일(.csv, .tsv, .json, .jsonl 등) 유효성 및 센티널 잔존 검증
    """
    safe_print("=" * 70)
    safe_print(f"🔍 [산출물 파일 정밀 검증 모드] 대상 파일: {file_path}")
    safe_print("=" * 70)

    # 1. 파일 존재 여부 확인
    if not os.path.exists(file_path):
        safe_print(f"❌ [파일 검증 실패] {file_path}: 파일이 존재하지 않습니다.", file=sys.stderr)
        safe_print("=" * 70)
        sys.exit(1)

    # 2. 파일 크기 > 0 바이트 확인
    file_size = os.path.getsize(file_path)
    if file_size == 0:
        safe_print(f"❌ [파일 검증 실패] {file_path}: 파일 크기가 0 바이트입니다 (빈 파일).", file=sys.stderr)
        safe_print("=" * 70)
        sys.exit(1)

    ext = os.path.splitext(file_path)[1].lower()
    record_count = 0
    leaks = []

    # 미정제 센티널 및 결측 토큰 (-999, -999.0, -9999, < DL, ND, NaN, null 등)
    sentinel_str_set = {"-999", "-999.0", "-9999", "< dl", "<dl", "nd", "nan", "null"}

    def check_val_sentinel(val: Any) -> Optional[str]:
        if val is None:
            return "null/None"
        if isinstance(val, (int, float)):
            if val in (-999, -999.0, -9999):
                return str(val)
            if math.isnan(val):
                return "NaN"
            return None
        s = str(val).strip().lower()
        if s in sentinel_str_set:
            return str(val).strip()
        if s.startswith("<") and "dl" in s:
            return str(val).strip()
        return None

    try:
        if ext in (".csv", ".tsv"):
            delimiter = "\t" if ext == ".tsv" else ","
            import csv
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.reader(f, delimiter=delimiter)
                rows = [row for row in reader if any(cell.strip() for cell in row)]

            total_rows = len(rows)
            if total_rows == 0:
                safe_print(f"❌ [파일 검증 실패] {file_path}: 유효한 레코드가 0건입니다 (빈 파일).", file=sys.stderr)
                safe_print("=" * 70)
                sys.exit(1)

            # 첫 행이 헤더인지 데이터인지 (2행 이상이면 첫 행은 헤더로 간주하여 데이터 행 수 = total_rows - 1)
            if total_rows > 1:
                data_rows = rows[1:]
                record_count = len(data_rows)
            else:
                data_rows = rows
                record_count = 1

            for r_idx, row in enumerate(data_rows, start=1):
                for c_idx, cell in enumerate(row):
                    token = check_val_sentinel(cell)
                    if token:
                        leaks.append(f"행 {r_idx}, 열 {c_idx+1}: '{token}'")

        elif ext == ".json":
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)

            if isinstance(data, list):
                record_count = len(data)
                items = enumerate(data, start=1)
            elif isinstance(data, dict):
                record_count = len(data)
                items = data.items()
            else:
                record_count = 1
                items = [(1, data)]

            if record_count == 0:
                safe_print(f"❌ [파일 검증 실패] {file_path}: 유효한 레코드가 0건입니다 (빈 JSON).", file=sys.stderr)
                safe_print("=" * 70)
                sys.exit(1)

            def scan_json_obj(obj, loc_prefix):
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        scan_json_obj(v, f"{loc_prefix}.{k}")
                elif isinstance(obj, list):
                    for idx, item in enumerate(obj):
                        scan_json_obj(item, f"{loc_prefix}[{idx}]")
                else:
                    tok = check_val_sentinel(obj)
                    if tok:
                        leaks.append(f"{loc_prefix}: '{tok}'")

            for loc, elem in items:
                scan_json_obj(elem, f"레코드 {loc}")

        elif ext == ".jsonl":
            lines = []
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line_s = line.strip()
                    if line_s:
                        lines.append(line_s)

            record_count = len(lines)
            if record_count == 0:
                safe_print(f"❌ [파일 검증 실패] {file_path}: 유효한 레코드가 0건입니다 (빈 JSONL).", file=sys.stderr)
                safe_print("=" * 70)
                sys.exit(1)

            def scan_json_obj(obj, loc_prefix):
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        scan_json_obj(v, f"{loc_prefix}.{k}")
                elif isinstance(obj, list):
                    for idx, item in enumerate(obj):
                        scan_json_obj(item, f"{loc_prefix}[{idx}]")
                else:
                    tok = check_val_sentinel(obj)
                    if tok:
                        leaks.append(f"{loc_prefix}: '{tok}'")

            for r_idx, line in enumerate(lines, start=1):
                try:
                    obj = json.loads(line)
                    scan_json_obj(obj, f"행 {r_idx}")
                except Exception as je:
                    leaks.append(f"행 {r_idx}: JSON 파싱 오류 ({je})")

        else:
            # 일반 텍스트 라인 기반 폴백 검증
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                lines = [l.strip() for l in f if l.strip()]
            record_count = len(lines)
            if record_count == 0:
                safe_print(f"❌ [파일 검증 실패] {file_path}: 유효한 레코드가 0건입니다.", file=sys.stderr)
                safe_print("=" * 70)
                sys.exit(1)
            for r_idx, line in enumerate(lines, start=1):
                for tok in ("-999.0", "-9999", "-999", "< DL", "<DL", "ND", "NaN", "null"):
                    if tok.lower() in line.lower():
                        leaks.append(f"행 {r_idx}: '{tok}'")

    except Exception as e:
        safe_print(f"❌ [파일 검증 실패] {file_path}: 파일 파싱 중 에러 발생 ({e})", file=sys.stderr)
        safe_print("=" * 70)
        sys.exit(1)

    if leaks:
        leak_sample = ", ".join(leaks[:5])
        if len(leaks) > 5:
            leak_sample += f" 외 {len(leaks)-5}건"
        safe_print(f"❌ [파일 검증 실패] {file_path}: 미정제 센티널/결측 {len(leaks)}건 누출 감지! ({leak_sample})", file=sys.stderr)
        safe_print("   👉 결측치/센티널(-999, NaN, null 등) 정제 로직을 확인하세요.", file=sys.stderr)
        safe_print("=" * 70)
        sys.exit(1)

    safe_print(f"  * 대상 파일        : {file_path}")
    safe_print(f"  * 파일 크기        : {file_size:,} bytes")
    safe_print(f"  * 유효 레코드 수   : {record_count:,}건")
    safe_print(f"  * 센티널/결측 누출 : 0건 (Clean)")
    safe_print("=" * 70)
    safe_print(f"✅ [파일 검증 통과] {file_path}: 총 {record_count}건 레코드, 센티널/결측 누출 0건 정상 확인!")
    sys.exit(0)

# --------------------------------------------------------------------------
# [7] 단위 테스트 케이스 및 불일치 diff 출력
# --------------------------------------------------------------------------
class TestSampleCheck(unittest.TestCase):
    def test_pipeline_output_against_expected(self):
        try:
            target_fn = load_target_function()
        except Exception as e:
            self.fail(f"타깃 모듈 로드 실패: {e}")

        actual = target_fn(SAMPLES)

        print("\n[집계 결과]")
        print(f"  * 실제 출력값 (Actual)  : {actual}")
        print(f"  * 수동 기댓값 (Expected): {EXPECTED}")

        if actual != EXPECTED:
            actual_json = json.dumps(actual, indent=2, sort_keys=True, ensure_ascii=False)
            expected_json = json.dumps(EXPECTED, indent=2, sort_keys=True, ensure_ascii=False)
            diff = difflib.unified_diff(
                expected_json.splitlines(),
                actual_json.splitlines(),
                fromfile="EXPECTED (수동 검산)",
                tofile="ACTUAL (함수 출력)",
                lineterm=""
            )
            diff_text = "\n".join(diff)
            self.fail(
                f"\n[기댓값 불일치 발생!]\n"
                f"--------------------------------------------------\n"
                f"{diff_text}\n"
                f"--------------------------------------------------\n"
                f"원인 점검: 중복 제거 누락, 불량 상태(scrap/discard/abnormal) 필터 누락, 결측치(-999/None) 처리 누락 확인 요망"
            )

        # 각 LOT별 개별 검증
        for lot_id, exp_val in EXPECTED.items():
            self.assertIn(lot_id, actual, f"LOT ID {lot_id} 누락")
            self.assertAlmostEqual(
                actual[lot_id], exp_val, places=2,
                msg=f"LOT {lot_id} 집계 두께 불일치: 실제 {actual[lot_id]} != 기댓값 {exp_val}"
            )

        print("\n[검증 통과] 15건 표본(정상/중복/불량/결측/경계값) 수동 기댓값과 100% 일치합니다!\n")

def print_help():
    print("""사용법:
  # 1. 내장 참조 구현체 자체 데모 검증 (--demo 플래그)
  python3 .probe-kit/scripts/sample_check_template.py --demo

  # 2. 산출물 데이터 파일 유효성 및 센티널 누출 검증
  python3 .probe-kit/scripts/sample_check_template.py [input_path]
  예: python3 .probe-kit/scripts/sample_check_template.py output/cleaned_data.csv

  # 3. 실제 과제 모듈 및 함수 지정 대조 실행
  TARGET_MODULE=src.pipeline TARGET_FUNC=process_wafers python3 .probe-kit/scripts/sample_check_template.py
""")

if __name__ == "__main__":
    # 1. --help / -h 플래그 처리
    if any(arg in sys.argv[1:] for arg in ("-h", "--help", "help")):
        print_help()
        sys.exit(0)

    # 2. 위치 인자 [input_path] 확인 (--demo 제외, '-'로 시작하지 않는 첫 인자)
    input_path = None
    for arg in sys.argv[1:]:
        if not arg.startswith("-"):
            input_path = arg
            break

    if input_path and not IS_DEMO:
        verify_output_file(input_path)

    # 3. --demo 또는 TARGET_MODULE / TARGET_FUNC 단위 테스트 실행
    #    unittest.main()의 인자 충돌 방지를 위해 sys.argv 초기화
    sys.argv = [sys.argv[0]]
    unittest.main(verbosity=2)
