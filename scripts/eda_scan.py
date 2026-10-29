#!/usr/bin/env python3
"""
scripts/eda_scan.py
무토큰 초고속 워크스페이스 EDA 스캐너 (표준 라이브러리 전용)
- 테스트 파일 목록 자동 탐지
- CSV / TSV / JSON / JSONL 스키마, 행 수, 결측치, 중복행, 3행 샘플, 수치 min/max 요약
- 최대 200,000행 보호 제한 및 스트리밍 O(1) 메모리 분석 지원
- 다중 인코딩(utf-8-sig, cp949, latin-1) 폴백 및 대용량 CSV 필드(2GB) 지원
"""

import os
import sys
import csv
import json
import math
from pathlib import Path

# Windows CP949 환경 대응
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

# Major 7: CSV 기본 필드 크기 제한(128KB) 초과 예외 방지 (Windows/C long 호환)
def _init_csv_field_size_limit():
    max_limit = min(2147483647, sys.maxsize)
    while max_limit > 131072:
        try:
            csv.field_size_limit(max_limit)
            break
        except OverflowError:
            max_limit = int(max_limit / 10)

_init_csv_field_size_limit()

IGNORE_DIRS = {
    '.git', '.probe-kit', 'node_modules', 'venv', '.venv',
    '__pycache__', 'dist', 'build', '.next', '.idea', '.vscode'
}

MISSING_TOKENS = {
    '', 'null', 'none', 'nan', 'na', 'n/a', '-999', '-999.0'
}

MAX_ROWS = 200000
MAX_SEEN_HASHES = 20000  # 중복 행 체크용 해시셋 상한선 (메모리 고갈 방지)

def is_missing(val):
    if val is None:
        return True
    s = str(val).strip().lower()
    return s in MISSING_TOKENS

def try_float(val):
    if is_missing(val):
        return None
    try:
        f = float(str(val).replace(',', ''))
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (ValueError, TypeError):
        return None

def open_with_encoding(filepath):
    encodings = ['utf-8-sig', 'cp949', 'latin-1']
    for enc in encodings:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                f.read(4096)
            return open(filepath, 'r', encoding=enc, errors='replace'), enc
        except (UnicodeDecodeError, LookupError):
            continue
    return open(filepath, 'r', encoding='latin-1', errors='replace'), 'latin-1'

def is_test_file(path_obj: Path) -> bool:
    name = path_obj.name.lower()
    parts = [p.lower() for p in path_obj.parts]
    if 'tests' in parts or 'test' in parts:
        return True
    if name.startswith('test_') or name.endswith('_test.py') or name.endswith('_test.go'):
        return True
    for ext in ('.test.js', '.spec.js', '.test.ts', '.spec.ts', '.test.jsx', '.spec.jsx', '.test.tsx', '.spec.tsx'):
        if name.endswith(ext):
            return True
    return False

def analyze_tabular(headers, row_iterator, file_label, truncated=False):
    """
    스트리밍 O(1) 메모리 기반 테이블 분석 함수
    전체 행을 메모리에 적재하지 않고 한 행씩 누적 갱신하여 OOM을 방지합니다.
    """
    num_cols = len(headers)
    num_rows = 0
    is_truncated = truncated

    col_missing = [0] * num_cols
    total_missing = 0
    col_numeric_count = [0] * num_cols
    col_min = [None] * num_cols
    col_max = [None] * num_cols

    samples = []
    seen_hashes = set()
    dup_count = 0
    seen_capped = False

    for r in row_iterator:
        if num_rows >= MAX_ROWS:
            is_truncated = True
            break
        num_rows += 1

        # 1) 앞 3행 샘플 보관
        if len(samples) < 3:
            samples.append(list(r))

        # 2) 중복 행 해시 체크 (상한 제한으로 메모리 고갈 방지)
        r_hash = hash(tuple(r))
        if r_hash in seen_hashes:
            dup_count += 1
        else:
            if len(seen_hashes) < MAX_SEEN_HASHES:
                seen_hashes.add(r_hash)
            else:
                seen_capped = True

        # 3) 컬럼별 결측치 및 수치 min/max 집계 (O(1) 스트리밍)
        for col_idx in range(num_cols):
            val = r[col_idx] if col_idx < len(r) else ""
            if is_missing(val):
                col_missing[col_idx] += 1
                total_missing += 1
            else:
                fv = try_float(val)
                if fv is not None:
                    col_numeric_count[col_idx] += 1
                    cur_min = col_min[col_idx]
                    if cur_min is None or fv < cur_min:
                        col_min[col_idx] = fv
                    cur_max = col_max[col_idx]
                    if cur_max is None or fv > cur_max:
                        col_max[col_idx] = fv

    print(f"  * 컬럼 수({num_cols}개): {headers}")
    trunc_note = f" (최대 {MAX_ROWS:,}행 제한 적용)" if is_truncated else ""
    print(f"  * 총 행 수(헤더 제외): {num_rows:,}행{trunc_note}")

    if num_rows == 0:
        print("  * 데이터가 비어 있습니다.")
        return

    dup_note = f" (상위 {MAX_SEEN_HASHES:,}개 고유 행 기준)" if seen_capped else ""
    print(f"  * 중복 행 수: {dup_count:,}행 ({dup_count/num_rows*100:.2f}%){dup_note}")
    print(f"  * 총 결측 셀 수: {total_missing:,}개 (전체 {num_rows * num_cols:,}셀 중 {total_missing/(num_rows*num_cols)*100:.2f}%)")

    # 컬럼별 결측치 상세
    missing_details = []
    for idx, name in enumerate(headers):
        cnt = col_missing[idx]
        pct = (cnt / num_rows * 100) if num_rows > 0 else 0
        if cnt > 0:
            missing_details.append(f"{name}: {cnt:,}건({pct:.1f}%)")
    if missing_details:
        print(f"  * 컬럼별 결측 상세: {', '.join(missing_details)}")
    else:
        print("  * 컬럼별 결측: 없음 (완전 데이터)")

    # 수치 컬럼 min/max
    numeric_summaries = []
    for idx, name in enumerate(headers):
        valid_count = num_rows - col_missing[idx]
        if valid_count > 0 and col_numeric_count[idx] >= valid_count * 0.7:
            min_v = col_min[idx]
            max_v = col_max[idx]
            if min_v is not None and max_v is not None:
                min_str = f"{min_v:.2f}".rstrip('0').rstrip('.') if not min_v.is_integer() else f"{int(min_v)}"
                max_str = f"{max_v:.2f}".rstrip('0').rstrip('.') if not max_v.is_integer() else f"{int(max_v)}"
                numeric_summaries.append(f"{name}[min={min_str}, max={max_str}]")

    if numeric_summaries:
        print(f"  * 숫자 컬럼 범위(Min/Max): {', '.join(numeric_summaries)}")

    # 앞 3행 샘플
    sample_count = len(samples)
    print(f"  * 앞 {sample_count}행 샘플:")
    for s_idx in range(sample_count):
        s_row = samples[s_idx]
        row_disp = [str(c)[:40] for c in s_row[:10]]
        if len(s_row) > 10:
            row_disp.append(f"... (+{len(s_row) - 10} cols)")
        print(f"    [{s_idx + 1}] {row_disp}")

def scan_csv_tsv(full_path: Path):
    fp, enc = open_with_encoding(full_path)
    with fp:
        suffix = full_path.suffix.lower()
        delim = '\t' if suffix == '.tsv' else ','
        sample_chunk = fp.read(4096)
        fp.seek(0)

        if suffix != '.tsv':
            try:
                sniffer = csv.Sniffer()
                sniffed_delim = sniffer.sniff(sample_chunk).delimiter
                if sniffed_delim in (',', ';', '\t', '|'):
                    delim = sniffed_delim
            except Exception:
                delim = ','

        reader = csv.reader(fp, delimiter=delim)
        try:
            headers = next(reader, [])
        except StopIteration:
            headers = []

        if not headers:
            print("  * 빈 파일입니다.")
            return

        print(f"  * 구분자: '{delim}' | 인코딩: {enc}")
        analyze_tabular(headers, reader, full_path.name)

def scan_json(full_path: Path):
    fp, enc = open_with_encoding(full_path)
    with fp:
        print(f"  * 인코딩: {enc}")
        try:
            data = json.load(fp)
        except Exception as e:
            print(f"  * JSON 파싱 오류: {e}")
            return

    if isinstance(data, list):
        print(f"  * JSON 구조: 리스트 (총 {len(data):,}개 항목)")
        if not data:
            return

        if isinstance(data[0], dict):
            keys = []
            for item in data[:100]:
                if isinstance(item, dict):
                    for k in item.keys():
                        if k not in keys:
                            keys.append(k)

            # 불필요한 전체 리스트 복제를 피하고 제너레이터로 스트리밍 전달
            def json_list_gen():
                for item in data:
                    if isinstance(item, dict):
                        yield [str(item.get(k, "")) if item.get(k) is not None else "" for k in keys]
                    else:
                        yield [str(item)]

            analyze_tabular(keys, json_list_gen(), full_path.name)
        else:
            print(f"  * 단일 값 리스트 샘플: {data[:5]}")
    elif isinstance(data, dict):
        keys = list(data.keys())
        print(f"  * JSON 구조: 딕셔너리 (최상위 키 {len(keys)}개)")
        print(f"  * 최상위 키 목록: {keys[:20]}")
        sample_dict = {k: str(data[k])[:60] for k in keys[:5]}
        print(f"  * 상위 키 미리보기: {sample_dict}")
    else:
        print(f"  * 단일 리터럴: {type(data)} = {data}")

def scan_jsonl(full_path: Path):
    fp, enc = open_with_encoding(full_path)
    with fp:
        print(f"  * 형식: JSON Lines (JSONL) | 인코딩: {enc}")

        # 키 목록 및 형태 파악을 위해 상위 100행 탐색
        keys = []
        is_dict = False
        non_dict_samples = []
        preview_count = 0

        for line in fp:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                preview_count += 1
                if isinstance(obj, dict):
                    is_dict = True
                    for k in obj.keys():
                        if k not in keys:
                            keys.append(k)
                else:
                    if len(non_dict_samples) < 3:
                        non_dict_samples.append(obj)
            except Exception:
                continue
            if preview_count >= 100:
                break

        if preview_count == 0:
            print("  * 유효한 JSONL 레코드가 없습니다.")
            return

        fp.seek(0)

        if is_dict:
            def jsonl_gen():
                for line in fp:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    if isinstance(obj, dict):
                        yield [str(obj.get(k, "")) if obj.get(k) is not None else "" for k in keys]
                    else:
                        yield [str(obj)]

            analyze_tabular(keys, jsonl_gen(), full_path.name)
        else:
            total_items = 0
            for line in fp:
                if line.strip():
                    total_items += 1
            print(f"  * 총 {total_items:,}개 레코드, 샘플: {non_dict_samples[:3]}")

def scan_workspace(root_path: str):
    root = Path(root_path).resolve()
    print("=" * 65)
    print(f"[EDA SCAN] 워크스페이스 구조 및 데이터 무토큰 요약")
    print(f"   루트 경로: {root}")
    print("=" * 65)

    if not root.exists():
        print(f"[오류] 경로가 존재하지 않습니다: {root}")
        sys.exit(1)

    data_files = []
    test_files = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and not d.startswith('.')]
        rel_dir = Path(dirpath).relative_to(root)

        for f in sorted(filenames):
            rel_p = rel_dir / f if str(rel_dir) != '.' else Path(f)
            if is_test_file(rel_p):
                test_files.append(rel_p)
            if f.lower().endswith(('.csv', '.tsv', '.json', '.jsonl')):
                data_files.append(rel_p)

    print(f"\n[1] 테스트 파일 목록 ({len(test_files)}개 발견):")
    if test_files:
        for tf in test_files[:25]:
            print(f"   - {tf}")
        if len(test_files) > 25:
            print(f"   ... (+{len(test_files) - 25}개 추가 파일)")
    else:
        print("   (발견된 테스트 파일 없음)")

    print(f"\n[2] 데이터 파일 목록 ({len(data_files)}개 발견):")
    if data_files:
        for df in data_files:
            print(f"   - {df}")
    else:
        print("   (발견된 데이터 파일 없음)")

    for df in data_files:
        full_p = root / df
        size_bytes = full_p.stat().st_size
        if size_bytes < 1024 * 1024:
            size_str = f"{size_bytes / 1024:.1f} KB"
        else:
            size_str = f"{size_bytes / (1024 * 1024):.2f} MB"

        print(f"\n---------------------------------------------------------")
        print(f"[DATA SUMMARY] {df} ({size_str})")
        print(f"---------------------------------------------------------")

        try:
            suffix = df.suffix.lower()
            if suffix in ('.csv', '.tsv'):
                scan_csv_tsv(full_p)
            elif suffix == '.jsonl':
                scan_jsonl(full_p)
            elif suffix == '.json':
                scan_json(full_p)
        except Exception as e:
            print(f"  * 파일 스캔 중 예외 발생: {e}")

    print("\n" + "=" * 65)
    print("[EDA SCAN 완료]")
    print("=" * 65)

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else '.'
    scan_workspace(target)
