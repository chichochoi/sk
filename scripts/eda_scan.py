#!/usr/bin/env python3
"""
scripts/eda_scan.py
무토큰 초고속 워크스페이스 EDA 스캐너 (표준 라이브러리 전용)
- 테스트 파일 목록 자동 탐지
- CSV / TSV / JSON / JSONL 스키마, 행 수, 결측치, 중복행, 3행 샘플, 수치 min/max 요약
- 최대 200,000행 보호 제한 및 다중 인코딩(utf-8-sig, cp949, latin-1) 폴백 지원
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

IGNORE_DIRS = {
    '.git', '.probe-kit', 'node_modules', 'venv', '.venv',
    '__pycache__', 'dist', 'build', '.next', '.idea', '.vscode'
}

MISSING_TOKENS = {
    '', 'null', 'none', 'nan', 'na', 'n/a', '-999', '-999.0'
}

MAX_ROWS = 200000
MAX_JSON_FILE_SIZE = 10 * 1024 * 1024  # 10MB 초과 대용량 JSON OOM 안전 가드

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
    """
    한글 인코딩 깨짐 및 Windows 개행 변형 방지:
    - 64KB(65536) 바이너리 샘플 기반 인코딩 자동 감지
    - utf-8-sig -> utf-8 -> cp949 -> euc-kr -> latin-1 순 strict 디코딩 검증
    - newline='' 기본 적용으로 Windows CRLF 개행 변형 방지
    """
    encodings = ['utf-8-sig', 'utf-8', 'cp949', 'euc-kr']
    try:
        with open(filepath, 'rb') as f:
            raw_sample = f.read(65536)
    except Exception:
        raw_sample = b''

    if not raw_sample:
        return open(filepath, 'r', encoding='utf-8', newline='', errors='replace'), 'utf-8'

    # Non-ASCII 바이트 포함 여부 확인
    has_non_ascii = any(b >= 128 for b in raw_sample)
    if not has_non_ascii:
        return open(filepath, 'r', encoding='utf-8', newline='', errors='replace'), 'utf-8'

    # Non-ASCII 포함 시 strict 디코딩 순차 시도 (끝단 절단 방지 trim 포함)
    for enc in encodings:
        success = False
        for trim in range(4):
            test_chunk = raw_sample if trim == 0 else raw_sample[:-trim]
            try:
                test_chunk.decode(enc)
                success = True
                break
            except (UnicodeDecodeError, LookupError):
                continue
        if success:
            return open(filepath, 'r', encoding=enc, newline='', errors='replace'), enc

    return open(filepath, 'r', encoding='latin-1', newline='', errors='replace'), 'latin-1'

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

def analyze_tabular(headers, rows, file_label, truncated=False):
    num_cols = len(headers)
    num_rows = len(rows)

    print(f"  * 컬럼 수({num_cols}개): {headers}")
    trunc_note = f" (최대 {MAX_ROWS:,}행 제한 적용)" if truncated else ""
    print(f"  * 총 행 수(헤더 제외): {num_rows:,}행{trunc_note}")

    if num_rows == 0:
        print("  * 데이터가 비어 있습니다.")
        return

    # 결측치 집계 (컬럼별 & 전체)
    col_missing = [0] * num_cols
    total_missing = 0
    col_numerics = [[] for _ in range(num_cols)]

    seen_rows = set()
    dup_count = 0

    for r in rows:
        # 중복 행 체크
        r_tuple = tuple(r)
        if r_tuple in seen_rows:
            dup_count += 1
        else:
            seen_rows.add(r_tuple)

        for col_idx in range(num_cols):
            val = r[col_idx] if col_idx < len(r) else ""
            if is_missing(val):
                col_missing[col_idx] += 1
                total_missing += 1
            else:
                fv = try_float(val)
                if fv is not None:
                    col_numerics[col_idx].append(fv)

    print(f"  * 중복 행 수: {dup_count:,}행 ({dup_count/num_rows*100:.2f}%)")
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
        vals = col_numerics[idx]
        valid_count = num_rows - col_missing[idx]
        if valid_count > 0 and len(vals) >= valid_count * 0.7:
            min_v = min(vals)
            max_v = max(vals)
            min_str = f"{min_v:.2f}".rstrip('0').rstrip('.') if not min_v.is_integer() else f"{int(min_v)}"
            max_str = f"{max_v:.2f}".rstrip('0').rstrip('.') if not max_v.is_integer() else f"{int(max_v)}"
            numeric_summaries.append(f"{name}[min={min_str}, max={max_str}]")

    if numeric_summaries:
        print(f"  * 숫자 컬럼 범위(Min/Max): {', '.join(numeric_summaries)}")

    # 앞 3행 샘플
    sample_count = min(3, len(rows))
    print(f"  * 앞 {sample_count}행 샘플:")
    for s_idx in range(sample_count):
        row_disp = [str(c)[:40] for c in rows[s_idx][:10]]
        if len(rows[s_idx]) > 10:
            row_disp.append(f"... (+{len(rows[s_idx]) - 10} cols)")
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

        rows = []
        truncated = False
        for idx, row in enumerate(reader):
            if idx >= MAX_ROWS:
                truncated = True
                break
            rows.append(row)

        print(f"  * 구분자: '{delim}' | 인코딩: {enc}")
        analyze_tabular(headers, rows, full_path.name, truncated)

def scan_large_json_safe(full_path: Path):
    """
    10MB 초과 대용량 JSON OOM 킬 방지 스트리밍 발췌 요약:
    - json.load()로 전체 적재 시 메모리 고갈 방지
    - 파일의 상위 50줄 또는 1,000자를 안전하게 스트리밍 발췌하여 요약
    - [대용량 JSON 파일 - 안전 발췌 요약] 출력
    """
    file_size = os.path.getsize(full_path)
    size_mb = file_size / (1024 * 1024)
    print(f"  * ⚠️ 대용량 JSON 감지 ({size_mb:.2f} MB > 10MB)")
    print("  * [대용량 JSON 파일 - 안전 발췌 요약]")
    print(f"  * OOM 방지를 위해 상위 50줄 / 1,000자 안전 발췌 스트리밍 분석을 수행합니다.")

    fp, enc = open_with_encoding(full_path)
    lines = []
    char_count = 0
    with fp:
        for idx, line in enumerate(fp):
            if idx >= 50 or char_count >= 1000:
                break
            lines.append(line.rstrip('\r\n'))
            char_count += len(line)

    print(f"  * 인코딩: {enc} | 발췌 라인 수: {len(lines)}줄 (약 {char_count:,}자)")
    print("  * 상위 내용 미리보기:")
    preview_count = min(20, len(lines))
    for idx in range(preview_count):
        preview = lines[idx][:120] + ("..." if len(lines[idx]) > 120 else "")
        print(f"    [{idx + 1:2d}] {preview}")
    if len(lines) > preview_count:
        print(f"    ... (+{len(lines) - preview_count}줄 추가 발췌 내용 생략)")

def scan_json(full_path: Path):
    file_size = os.path.getsize(full_path)
    if file_size > MAX_JSON_FILE_SIZE:
        scan_large_json_safe(full_path)
        return

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

            rows = []
            truncated = len(data) > MAX_ROWS
            for item in data[:MAX_ROWS]:
                if isinstance(item, dict):
                    rows.append([str(item.get(k, "")) if item.get(k) is not None else "" for k in keys])
                else:
                    rows.append([str(item)])
            analyze_tabular(keys, rows, full_path.name, truncated)
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
        items = []
        truncated = False
        for idx, line in enumerate(fp):
            line = line.strip()
            if not line:
                continue
            if len(items) >= MAX_ROWS:
                truncated = True
                break
            try:
                obj = json.loads(line)
                items.append(obj)
            except Exception:
                continue

    if not items:
        print("  * 유효한 JSONL 레코드가 없습니다.")
        return

    if isinstance(items[0], dict):
        keys = []
        for item in items[:100]:
            if isinstance(item, dict):
                for k in item.keys():
                    if k not in keys:
                        keys.append(k)
        rows = []
        for item in items:
            if isinstance(item, dict):
                rows.append([str(item.get(k, "")) if item.get(k) is not None else "" for k in keys])
            else:
                rows.append([str(item)])
        analyze_tabular(keys, rows, full_path.name, truncated)
    else:
        print(f"  * 총 {len(items):,}개 레코드, 샘플: {items[:3]}")

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
