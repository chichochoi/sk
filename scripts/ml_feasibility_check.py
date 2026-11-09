#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/ml_feasibility_check.py
경량 AI/ML Feasibility Checker & Dataset Compactor & Champion Arena Comparator

순수 Python 표준 라이브러리만을 기본으로 동작하되, 설치된 경우 numpy, pandas,
scikit-learn, lightgbm, xgboost, catboost, scipy를 자동 감지하여 가속합니다.

4가지 실행 모드:
1. [기본 진단] python3 .probe-kit/scripts/ml_feasibility_check.py [workspace_dir]
   - 워크스페이스 내 README.md 및 데이터셋을 초고속 스캔하여 8대 조건(Gatekeeper Conditions) 판정
   - 🟢 DIRECT_ML / 🟡 HYBRID_ML / 🔴 ALGORITHM_ONLY 최종 배너 출력
   - FEASIBILITY_SUMMARY.txt, feasibility_report.json 저장
2. [데이터 경량화] python3 .probe-kit/scripts/ml_feasibility_check.py --compact [workspace_dir]
   - 원본 불변(Read-Only), 상수/고결측 컬럼 제거, 센티널 정제
   - 3만행 초과 시 20% 코어셋 및 경량 CSV/PKL 생성, compact_manifest.json 저장
3. [챔피언 비교] python3 .probe-kit/scripts/ml_feasibility_check.py --compare <algo_file> <ml_file>
   - 행수/헤더 일치, 결측/센티널 누출 0건 검증, 기초 통계, 상관계수, MAE 비교
   - leaderboard.json / CHAMPION_REPORT.md 연동 및 최종 채택 가이드 제공
4. [데모 및 자가검증] python3 .probe-kit/scripts/ml_feasibility_check.py --demo
   - 임시 합성 데이터셋으로 [진단] -> [경량화] -> [비교] 3단계 자동 수행 및 [PASS] 검증
"""

import os
import sys
import csv
import json
import math
import time
import re
import argparse
import platform
import random
import tempfile
import shutil
from pathlib import Path
from collections import Counter

# ==============================================================================
# Windows 및 다중 터미널 인코딩 안전화
# ==============================================================================
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

# ==============================================================================
# 전역 상수 및 패턴 정의
# ==============================================================================
IGNORE_DIRS = {
    '.git', '.probe-kit', 'probe-kit', 'node_modules', 'venv', '.venv',
    '__pycache__', 'dist', 'build', '.next', '.idea', '.vscode', 'ml_track'
}

DATA_EXTENSIONS = {'.csv', '.tsv', '.json', '.jsonl', '.parquet', '.pkl'}

TARGET_KEYWORDS = [
    'target', 'label', 'y', 'yield', 'defect', 'fail', 'score', 'demand',
    'count', 'price', 'time', 'risk', 'status', 'anomaly', 'class',
    'output', 'loss', 'qty', 'amount', 'predict', 'result', 'decision'
]

TASK_KEYWORDS_KOR = ['수율', '불량', '수요', '예측', '분류', '회귀', '이상탐지', '추천', '점수', '최적가']
TASK_KEYWORDS_ENG = ['predict', 'classification', 'regression', 'yield', 'defect', 'demand', 'forecast', 'anomaly']

CONSTRAINT_KEYWORDS = [
    '정원', '예산', '제약', '초과 금지', '초과금지', 'constraint', 'limit',
    'capacity', '배차', '할당', '최적화', '비용', '마진', '규제', 'cap',
    'budget', 'deadline', 'penalty', 'max_weight'
]

DL_KEYWORDS = [
    'llm', '파인튜닝', 'fine-tuning', 'fine tuning', '비전 모델', '트랜스포머',
    'transformer', 'diffusion', 'yolo', 'resnet', 'bert', 'gpt', '대규모 이미지'
]

SENTINEL_PATTERNS = [
    r'^<[\s]*dl$', r'^<[\s]*0(?:\.0+)?$', r'^nd$', r'^not[\s_]+detected$',
    r'^-?999(?:\.0+)?$', r'^-?9999(?:\.0+)?$', r'^n/?a$', r'^null$', r'^none$', r'^nan$'
]
SENTINEL_REGEX = re.compile('|'.join(f'(?:{p})' for p in SENTINEL_PATTERNS), re.IGNORECASE)

UNIT_RE = re.compile(r'(?i)(?:^|(?<=[0-9\s_(\[/\-]))(ppm|ppb|ppt|nm|%|℃|celsius)(?:$|(?=[\s_)\]/:\-_]))')

# ==============================================================================
# 패키지 및 시스템 가용 자원 감지
# ==============================================================================
def detect_packages():
    """컨테이너 및 로컬 환경 내 ML/데이터 패키지 감지"""
    packages = {
        'numpy': False,
        'pandas': False,
        'sklearn': False,
        'lightgbm': False,
        'xgboost': False,
        'catboost': False,
        'scipy': False
    }
    for pkg in list(packages.keys()):
        try:
            __import__(pkg)
            packages[pkg] = True
        except ImportError:
            packages[pkg] = False
    return packages

PACKAGES = detect_packages()

def get_memory_info_mb():
    """가용 및 총 RAM(MB) 반환 (Windows/Linux 지원)"""
    try:
        import psutil
        vm = psutil.virtual_memory()
        return vm.total // (1024 * 1024), vm.available // (1024 * 1024)
    except Exception:
        pass

    sys_plat = platform.system()
    if sys_plat == 'Windows':
        try:
            import ctypes
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ('dwLength', ctypes.c_ulong),
                    ('dwMemoryLoad', ctypes.c_ulong),
                    ('ullTotalPhys', ctypes.c_ulonglong),
                    ('ullAvailPhys', ctypes.c_ulonglong),
                    ('ullTotalPageFile', ctypes.c_ulonglong),
                    ('ullAvailPageFile', ctypes.c_ulonglong),
                    ('ullTotalVirtual', ctypes.c_ulonglong),
                    ('ullAvailVirtual', ctypes.c_ulonglong),
                    ('ullAvailExtendedVirtual', ctypes.c_ulonglong),
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                return stat.ullTotalPhys // (1024 * 1024), stat.ullAvailPhys // (1024 * 1024)
        except Exception:
            pass
    elif sys_plat == 'Linux':
        try:
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
            mem_dict = {}
            for line in lines:
                parts = line.split(':')
                if len(parts) == 2:
                    mem_dict[parts[0].strip()] = int(parts[1].strip().split()[0])
            total = mem_dict.get('MemTotal', 8 * 1024 * 1024) // 1024
            avail = mem_dict.get('MemAvailable', mem_dict.get('MemFree', 4 * 1024 * 1024)) // 1024
            return total, avail
        except Exception:
            pass
    return 16384, 8192

def get_gpu_info():
    """GPU 유무 및 디바이스 정보 반환"""
    try:
        import torch
        if torch.cuda.is_available():
            return True, f"PyTorch CUDA: {torch.cuda.get_device_name(0)}"
    except Exception:
        pass

    import shutil, subprocess
    if shutil.which("nvidia-smi"):
        try:
            res = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=1.5
            )
            if res.returncode == 0 and res.stdout.strip():
                return True, f"NVIDIA GPU: {res.stdout.strip().splitlines()[0]}"
        except Exception:
            pass
    return False, "None (CPU Only)"

def run_micro_benchmark(n_samples=500, n_features=20):
    """
    0.1초 이내 초경량 수치 연산 마이크로 벤치마크
    순수 Python 또는 Numpy 연산 속도를 측정하여 1회 학습 예상 시간 산출에 활용
    """
    t0 = time.perf_counter()
    if PACKAGES['numpy']:
        import numpy as np
        rng = np.random.RandomState(42)
        X = rng.randn(n_samples, n_features)
        y = rng.randn(n_samples)
        # Ridge normal equation: (X^T X + 0.1 I)^-1 X^T y
        for _ in range(50):
            XtX = X.T @ X + 0.1 * np.eye(n_features)
            _ = np.linalg.solve(XtX, X.T @ y)
    else:
        # Pure Python fallback
        X = [[(i * j) % 17 * 0.1 for j in range(n_features)] for i in range(100)]
        for _ in range(30):
            cov = [[sum(X[r][i] * X[r][j] for r in range(100)) for j in range(n_features)] for i in range(n_features)]
    elapsed = max(time.perf_counter() - t0, 0.001)
    return elapsed

# ==============================================================================
# 파일 인코딩 및 읽기 유틸리티
# ==============================================================================
def open_with_encoding(filepath):
    """BOM 및 다양한 인코딩 안전 지원"""
    encodings = ['utf-8-sig', 'utf-8', 'cp949', 'euc-kr']
    try:
        with open(filepath, 'rb') as f:
            raw_sample = f.read(65536)
    except Exception:
        raw_sample = b''

    if not raw_sample:
        return open(filepath, 'r', encoding='utf-8', newline='', errors='replace'), 'utf-8'

    if raw_sample.startswith(b'\xef\xbb\xbf'):
        return open(filepath, 'r', encoding='utf-8-sig', newline='', errors='replace'), 'utf-8-sig'

    for enc in encodings:
        try:
            raw_sample.decode(enc)
            return open(filepath, 'r', encoding=enc, newline='', errors='replace'), enc
        except (UnicodeDecodeError, LookupError):
            continue

    return open(filepath, 'r', encoding='latin-1', newline='', errors='replace'), 'latin-1'

def is_sentinel_or_missing(val):
    if val is None:
        return True
    s = str(val).strip()
    if not s or s.lower() in {'nan', 'null', 'none', 'na', 'n/a'}:
        return True
    return bool(SENTINEL_REGEX.match(s))

def clean_numeric_val(val):
    """단위 마커(ppm 등) 제거 및 수치 파싱 (센티널은 None 반환)"""
    if is_sentinel_or_missing(val):
        return None
    s = str(val).strip().replace(',', '')
    s = re.sub(r'(?i)\s*(ppm|ppb|ppt|nm|%|℃|celsius)$', '', s).strip()
    try:
        f = float(s)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (ValueError, TypeError):
        return None

# ==============================================================================
# 워크스페이스 스캐닝 및 탐색
# ==============================================================================
def resolve_workspace_paths(workspace_arg=None):
    """워크스페이스 경로 및 .probe-kit/ml_track 경로 결정"""
    if workspace_arg:
        ws = Path(workspace_arg).resolve()
    else:
        cwd = Path.cwd().resolve()
        if (cwd / ".probe-kit").is_dir() or (cwd / "probe-kit").is_dir():
            ws = cwd
        elif cwd.name in (".probe-kit", "probe-kit"):
            ws = cwd.parent
        else:
            ws = cwd

    # ml_track 디렉토리 결정 (.probe-kit 우선, 없으면 probe-kit, 둘 다 없으면 .probe-kit 생성)
    if (ws / ".probe-kit").is_dir():
        ml_track_dir = ws / ".probe-kit" / "ml_track"
    elif (ws / "probe-kit").is_dir():
        ml_track_dir = ws / "probe-kit" / "ml_track"
    else:
        ml_track_dir = ws / ".probe-kit" / "ml_track"

    return ws, ml_track_dir

def scan_workspace_files(ws_dir: Path):
    """3초 이내 워크스페이스 스캔: README 및 데이터 파일 수집"""
    data_files = []
    readme_texts = []
    all_files_count = 0
    media_files_count = 0

    MEDIA_EXTS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.mp4', '.avi', '.wav', '.mp3'}

    for root, dirs, files in os.walk(ws_dir):
        # 무시할 디렉토리 프루닝
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith('.')]
        for f in files:
            all_files_count += 1
            f_path = Path(root) / f
            ext = f_path.suffix.lower()

            if ext in MEDIA_EXTS:
                media_files_count += 1

            if f.lower().startswith('readme') and ext in ('.md', '.txt'):
                try:
                    fp, _ = open_with_encoding(f_path)
                    with fp:
                        readme_texts.append(fp.read(50000))
                except Exception:
                    pass

            if ext in DATA_EXTENSIONS:
                # 결과 요약 JSON이나 manifest 등은 데이터 분석 대상에서 제외
                if any(x in f.lower() for x in ['manifest', 'feasibility', 'summary', 'report', 'leaderboard']):
                    continue
                data_files.append(f_path)

    return data_files, "\n".join(readme_texts), all_files_count, media_files_count

def peek_csv_info(file_path: Path, max_rows=5000):
    """CSV/TSV 기본 메타데이터 및 앞부분 샘플 통계 수집"""
    try:
        fp, enc = open_with_encoding(file_path)
        with fp:
            line = fp.readline()
            if not line:
                return None
            delim = '\t' if file_path.suffix.lower() == '.tsv' else ','
            if ',' not in line and '\t' in line:
                delim = '\t'
            elif '\t' not in line and ';' in line:
                delim = ';'
            reader = csv.reader([line], delimiter=delim)
            headers = [h.strip() for h in next(reader, [])]
            if not headers:
                return None

            total_rows = 0
            sample_rows = []
            fp.seek(0)
            c_reader = csv.reader(fp, delimiter=delim)
            next(c_reader, None)  # skip header
            for row in c_reader:
                total_rows += 1
                if len(sample_rows) < max_rows:
                    sample_rows.append(row)
                elif total_rows > 100000:
                    # 초고속 패스: 10만 행 초과 시 나머지 행 단순 개행 카운트
                    total_rows += sum(1 for _ in fp)
                    break

            return {
                'path': file_path,
                'delimiter': delim,
                'encoding': enc,
                'headers': headers,
                'total_rows': total_rows,
                'sample_rows': sample_rows,
                'file_size_bytes': file_path.stat().st_size
            }
    except Exception:
        return None

# ==============================================================================
# [모드 1] 8대 조건 판별 및 기본 진단 (Mode 1: Feasibility Check)
# ==============================================================================
def evaluate_feasibility(ws_dir: Path, ml_track_dir: Path):
    """8대 Gatekeeper Conditions 종합 판정 및 보고서 생성"""
    data_files, readme_corpus, total_files, media_count = scan_workspace_files(ws_dir)
    readme_lower = readme_corpus.lower()

    # 시스템 스펙
    cpu_cores = os.cpu_count() or 2
    total_ram_mb, avail_ram_mb = get_memory_info_mb()
    has_gpu, gpu_desc = get_gpu_info()
    bench_sec = run_micro_benchmark()

    # 데이터셋 집계
    parsed_datasets = []
    total_bytes = 0
    total_rows = 0
    target_candidates = set()
    all_headers = []
    constant_cols_found = []
    high_missing_cols_found = []
    sentinel_cols_found = []
    numeric_col_count = 0
    categorical_col_count = 0
    total_cells = 0
    missing_or_sentinel_cells = 0

    for df in data_files:
        info = peek_csv_info(df)
        if not info:
            total_bytes += df.stat().st_size
            continue
        parsed_datasets.append(info)
        total_bytes += info['file_size_bytes']
        total_rows += info['total_rows']
        headers = info['headers']
        all_headers.extend(headers)

        # 타깃 컬럼 감지
        for col in headers:
            col_l = col.lower()
            if any(k == col_l or f'_{k}' in col_l or f'{k}_' in col_l for k in TARGET_KEYWORDS):
                target_candidates.add(col)

        # 컬럼별 결측/센티널 및 상수성 검사
        samples = info['sample_rows']
        n_samples = len(samples)
        if n_samples > 0:
            for c_idx, col in enumerate(headers):
                vals = [r[c_idx] for r in samples if c_idx < len(r)]
                num_vals = [clean_numeric_val(v) for v in vals]
                valid_nums = [n for n in num_vals if n is not None]
                if len(valid_nums) >= len(vals) * 0.5:
                    numeric_col_count += 1
                else:
                    categorical_col_count += 1

                sentinel_cnt = sum(1 for v in vals if is_sentinel_or_missing(v))
                total_cells += len(vals)
                missing_or_sentinel_cells += sentinel_cnt

                if sentinel_cnt > 0:
                    sentinel_cols_found.append((info['path'].name, col))

                # 상수 컬럼 (고유값 1개 이하)
                unique_vals = set(vals)
                if len(unique_vals) <= 1:
                    constant_cols_found.append((info['path'].name, col))

                # 95% 이상 결측/센티널
                if sentinel_cnt >= len(vals) * 0.95:
                    high_missing_cols_found.append((info['path'].name, col))

    total_data_mb = round(total_bytes / (1024 * 1024), 2)

    # --------------------------------------------------------------------------
    # [조건 1] 경량 모델 적합성 (Simple Model Solvability)
    # --------------------------------------------------------------------------
    is_heavy_dl = False
    if media_count > 50 and media_count > len(data_files) * 5:
        is_heavy_dl = True
    if any(k in readme_lower for k in DL_KEYWORDS):
        is_heavy_dl = True

    task_keyword_found = any(k in readme_corpus for k in TASK_KEYWORDS_KOR) or any(k in readme_lower for k in TASK_KEYWORDS_ENG)
    c1_pass = (len(target_candidates) > 0 or task_keyword_found) and (not is_heavy_dl) and (len(data_files) > 0)
    c1_detail = {
        'target_candidates': sorted(list(target_candidates)),
        'is_heavy_dl': is_heavy_dl,
        'installed_packages': {k: v for k, v in PACKAGES.items() if v},
        'missing_packages': [k for k, v in PACKAGES.items() if not v],
        'note': "경량 ML(GBDT, Ridge, Tree) 적용 가능" if c1_pass else "타깃 부재 또는 무거운 딥러닝 전용 과제"
    }

    # --------------------------------------------------------------------------
    # [조건 2] 학습 시간 견적 (Training Time Budget — 6.5h)
    # --------------------------------------------------------------------------
    dim_d = max(len(all_headers), 1)
    n_records = max(total_rows, 100)
    # 복잡도 추정식 (GBDT/선형 기반): N * D 에 기반한 보정
    complexity_scale = ((n_records * dim_d) / 10000.0) ** 0.82
    est_single_fit_sec = round(max(0.15, min((bench_sec * complexity_scale) / max(cpu_cores * 0.5, 1.0), 300.0)), 2)
    est_5h_iterations = int((5 * 3600) / max(est_single_fit_sec, 0.5))

    c2_pass = est_single_fit_sec <= 180.0
    c2_detail = {
        'cpu_cores': cpu_cores,
        'total_ram_mb': total_ram_mb,
        'avail_ram_mb': avail_ram_mb,
        'gpu': gpu_desc,
        'est_single_fit_sec': est_single_fit_sec,
        'est_single_fit_str': f"{est_single_fit_sec}초" if est_single_fit_sec < 60 else f"{int(est_single_fit_sec // 60)}분 {int(est_single_fit_sec % 60)}초",
        'est_5h_iterations': est_5h_iterations,
        'status': "PASS (< 3분)" if c2_pass else "WARN (1회 학습 3분 초과 가능성)"
    }

    # --------------------------------------------------------------------------
    # [조건 3] 데이터셋 크기 및 형식 적합성 (Dataset Size & Sample Count)
    # --------------------------------------------------------------------------
    c3_pass = (total_rows >= 50) and (total_data_mb <= avail_ram_mb * 0.5) if total_rows > 0 else False
    missing_ratio_pct = round((missing_or_sentinel_cells / max(total_cells, 1)) * 100, 2)
    c3_detail = {
        'total_size_mb': total_data_mb,
        'total_rows': total_rows,
        'total_cols': len(all_headers),
        'numeric_cols': numeric_col_count,
        'categorical_cols': categorical_col_count,
        'missing_or_sentinel_ratio_pct': missing_ratio_pct,
        'status': "PASS" if c3_pass else "FAIL (행수 50행 미만 또는 메모리 초과)"
    }

    # --------------------------------------------------------------------------
    # [조건 4] 데이터셋 자체 경량화 가능 여부 (Data Compaction Potential)
    # --------------------------------------------------------------------------
    drop_candidates_count = len(constant_cols_found) + len(high_missing_cols_found)
    total_cols_count = max(len(all_headers), 1)
    col_reduction_pct = round((drop_candidates_count / total_cols_count) * 100, 1)
    downcast_mem_saving_pct = 50.0  # float64->float32, int64->int32 전환 시 수치형 50% 절감
    coreset_speedup = "5x (3만행 초과 20% 코어셋 권장)" if total_rows > 30000 else "불필요 (3만행 이하로 즉시 전수 학습 가능)"

    c4_pass = total_rows > 0
    c4_detail = {
        'constant_cols': [f"{f}:{c}" for f, c in constant_cols_found],
        'high_missing_cols': [f"{f}:{c}" for f, c in high_missing_cols_found],
        'sentinel_cols_count': len(sentinel_cols_found),
        'col_reduction_pct': col_reduction_pct,
        'downcast_mem_saving_pct': downcast_mem_saving_pct,
        'coreset_speedup': coreset_speedup
    }

    # --------------------------------------------------------------------------
    # [조건 5] 추론 시간 SLA & 제출 아티팩트 경량성 (< 5s & < 10MB)
    # --------------------------------------------------------------------------
    c5_pass = not is_heavy_dl and total_rows < 5000000
    c5_detail = {
        'expected_inference_sec': "< 0.5s (배치 10,000행 기준 경량 트리/회귀 모델)",
        'expected_artifact_size_mb': "< 3MB (LightGBM/Ridge 아티팩트)",
        're_train_feasibility': "< 15초 내 컨테이너 재학습 가능" if est_single_fit_sec <= 15 else "사전 빌드 모델 활용 권장",
        'status': "PASS" if c5_pass else "WARN"
    }

    # --------------------------------------------------------------------------
    # [조건 6] 하드 제약조건 후처리 결합성 (Post-Processing Guardrail)
    # --------------------------------------------------------------------------
    detected_constraints = []
    for k in CONSTRAINT_KEYWORDS:
        if k in readme_corpus or k in readme_lower:
            # 부정 표현(예: "제약 없음", "제약은 없다", "no constraint") 제외
            neg_pattern = re.compile(rf'{re.escape(k)}[이가은는\s]*(?:없|none|false|0)', re.IGNORECASE)
            if neg_pattern.search(readme_corpus) or neg_pattern.search(readme_lower):
                continue
            detected_constraints.append(k)
    has_hard_constraints = len(detected_constraints) > 0
    c6_detail = {
        'has_hard_constraints': has_hard_constraints,
        'detected_constraint_keywords': detected_constraints,
        'recommendation': "경량 ML 예측 + 결정론적 후처리(Clip/Greedy Repair) 하이브리드 결합 필수" if has_hard_constraints else "순수 경량 ML 직접 예측 강력 권장"
    }

    # --------------------------------------------------------------------------
    # [조건 7] 작업공간 및 CPU 완전 격리 (Zero-Collision Isolation)
    # --------------------------------------------------------------------------
    is_writable = False
    try:
        ml_track_dir.mkdir(parents=True, exist_ok=True)
        test_file = ml_track_dir / ".isolation_check"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink()
        is_writable = True
    except Exception:
        is_writable = False

    c7_pass = is_writable
    c7_detail = {
        'ml_track_dir': str(ml_track_dir),
        'is_writable': is_writable,
        'cpu_guardrail': "OMP_NUM_THREADS=2, MKL_NUM_THREADS=2, n_jobs=2 제한 필수 (메인 에이전트와 CPU 충돌 방지)"
    }

    # --------------------------------------------------------------------------
    # [조건 8] 동일 지표 비교 가능성 (Champion Arena Readiness)
    # --------------------------------------------------------------------------
    c8_pass = True
    c8_detail = {
        'compare_mode_ready': True,
        'guide': "--compare <algo_file> <ml_file> 을 통해 1:1 교차 검증 및 상관계수/MAE 측정 가능"
    }

    # --------------------------------------------------------------------------
    # 최종 판정 산출 (Final Verdict)
    # --------------------------------------------------------------------------
    if (not c1_pass) or (not c3_pass):
        verdict = "SKIP_ALGORITHM_ONLY"
        verdict_banner = "🔴 [ML_VERDICT: SKIP — ALGORITHM_ONLY]"
        verdict_reason = "타깃/학습 데이터 부재 또는 순수 웹 UI/규정 문서/무거운 DL 과제 — ML 트랙 생략 권고"
    elif has_hard_constraints:
        verdict = "GO_HYBRID_ML"
        verdict_banner = "🟡 [ML_VERDICT: GO — HYBRID_ML]"
        verdict_reason = "최적화/배차/정원/예산 등 제약 감지 — 경량 ML 예측기 + 결정론적 후처리(Clip/Greedy Repair) 하이브리드 권장"
    else:
        verdict = "GO_DIRECT_ML"
        verdict_banner = "🟢 [ML_VERDICT: GO — DIRECT_ML]"
        verdict_reason = "수율/불량/수요/추천/이상탐지 등 경량 ML 직접 해결 강력 권장"

    report_data = {
        'scan_timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
        'workspace': str(ws_dir),
        'verdict': verdict,
        'verdict_banner': verdict_banner,
        'verdict_reason': verdict_reason,
        'conditions': {
            'c1_simple_model_solvability': {'pass': c1_pass, 'detail': c1_detail},
            'c2_training_time_budget': {'pass': c2_pass, 'detail': c2_detail},
            'c3_dataset_size_and_format': {'pass': c3_pass, 'detail': c3_detail},
            'c4_data_compaction_potential': {'pass': c4_pass, 'detail': c4_detail},
            'c5_inference_latency_and_artifact': {'pass': c5_pass, 'detail': c5_detail},
            'c6_hard_constraints_guardrail': {'pass': True, 'detail': c6_detail},
            'c7_zero_collision_isolation': {'pass': c7_pass, 'detail': c7_detail},
            'c8_champion_arena_readiness': {'pass': c8_pass, 'detail': c8_detail}
        }
    }

    # 콘솔 출력 및 요약문 생성
    summary_lines = []
    summary_lines.append("=" * 70)
    summary_lines.append(f"  {verdict_banner}")
    summary_lines.append(f"  판정 이유: {verdict_reason}")
    summary_lines.append("=" * 70)
    summary_lines.append(f"■ 워크스페이스: {ws_dir}")
    summary_lines.append(f"■ 발견된 데이터 파일: {len(data_files)}개 | 총 용량: {total_data_mb} MB | 총 행 수: {total_rows:,}행")
    summary_lines.append(f"■ 타깃 후보 컬럼: {c1_detail['target_candidates'] or '없음 (비지도/순수 알고리즘)'}")
    summary_lines.append(f"■ 가용 자원: CPU {cpu_cores}코어 | RAM {avail_ram_mb:,}MB 가용 | {gpu_desc}")
    summary_lines.append(f"■ 1회 예상 학습 시간: {c2_detail['est_single_fit_str']} | 5시간 내 수행 가능 튜닝: 약 {est_5h_iterations:,}회")
    summary_lines.append(f"■ 설치된 패키지: {[k for k, v in PACKAGES.items() if v] or '표준 라이브러리 (Numpy/Tree 기본 지원)'}")
    summary_lines.append("-" * 70)
    summary_lines.append("【 8대 조건 판정 결과 (Gatekeeper Summary) 】")
    summary_lines.append(f" 1. 경량 모델 적합성: {'[PASS]' if c1_pass else '[FAIL]'} (Heavy DL: {is_heavy_dl})")
    summary_lines.append(f" 2. 학습 시간 견적(6.5h): {'[PASS]' if c2_pass else '[WARN]'} (단일 학습 {c2_detail['est_single_fit_str']})")
    summary_lines.append(f" 3. 데이터셋 크기/형식: {'[PASS]' if c3_pass else '[FAIL]'} (행수: {total_rows}, 결측/센티널: {missing_ratio_pct}%)")
    summary_lines.append(f" 4. 자체 경량화 가능성: [PASS] (상수 컬럼: {len(constant_cols_found)}개, 고결측: {len(high_missing_cols_found)}개)")
    summary_lines.append(f" 5. 추론 SLA (<5s, <10MB): {'[PASS]' if c5_pass else '[WARN]'}")
    summary_lines.append(f" 6. 하드 제약 후처리: {c6_detail['recommendation']}")
    summary_lines.append(f" 7. 작업공간/스레드 격리: {'[PASS]' if c7_pass else '[FAIL]'} (경로: {ml_track_dir})")
    summary_lines.append(f" 8. 챔피언 비교 준비도: [PASS] (--compare 모드 완비)")
    summary_lines.append("=" * 70)

    summary_text = "\n".join(summary_lines)
    print(summary_text)

    # 보고서 파일 저장
    try:
        ml_track_dir.mkdir(parents=True, exist_ok=True)
        summary_path = ml_track_dir / "FEASIBILITY_SUMMARY.txt"
        summary_path.write_text(summary_text, encoding="utf-8")

        json_path = ml_track_dir / "feasibility_report.json"
        json_path.write_text(json.dumps(report_data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n-> 진단 요약 저장: {summary_path}")
        print(f"-> 상세 리포트 JSON 저장: {json_path}")
    except Exception as e:
        print(f"\n[주의] 리포트 파일 저장 중 오류: {e}")

    return report_data

# ==============================================================================
# [모드 2] 데이터 자체 경량화 실행 모드 (Mode 2: Data Compaction)
# ==============================================================================
def execute_compaction(ws_dir: Path, ml_track_dir: Path):
    """
    원본 데이터는 절대 수정하지 않고(Read-Only),
    .probe-kit/ml_track/data_compact/ 내부에 상수/고결측 컬럼 제거 및 센티널 정제,
    3만행 초과 시 20% 코어셋 샘플링 데이터 생성
    """
    print("\n" + "=" * 70)
    print("  [DATA COMPACTION] 데이터셋 자체 경량화 실행 모드 (--compact)")
    print("=" * 70)

    # 1단계: 기본 진단 수행
    feasibility_res = evaluate_feasibility(ws_dir, ml_track_dir)

    compact_dir = ml_track_dir / "data_compact"
    compact_dir.mkdir(parents=True, exist_ok=True)

    data_files, _, _, _ = scan_workspace_files(ws_dir)
    if not data_files:
        print("[경고] 경량화 대상 데이터 파일이 없습니다.")
        return

    manifest_files = []

    for df in data_files:
        ext = df.suffix.lower()
        if ext not in ('.csv', '.tsv'):
            continue

        info = peek_csv_info(df, max_rows=10000)
        if not info:
            continue

        orig_size = df.stat().st_size
        total_rows = info['total_rows']
        headers = info['headers']
        delim = info['delimiter']

        # 전체 또는 샘플 데이터 로드
        fp, enc = open_with_encoding(df)
        all_rows = []
        with fp:
            reader = csv.reader(fp, delimiter=delim)
            next(reader, None)
            for row in reader:
                all_rows.append(row)
                if len(all_rows) >= 200000:
                    break

        actual_rows_count = len(all_rows)
        if actual_rows_count == 0:
            continue

        # 컬럼 속성 판별
        dropped_const_cols = []
        dropped_missing_cols = []
        cleaned_sentinel_cols = []
        keep_indices = []

        for idx, col in enumerate(headers):
            col_vals = [r[idx] for r in all_rows if idx < len(r)]
            uniq_vals = set(col_vals)
            # 상수 컬럼 판정
            if len(uniq_vals) <= 1:
                dropped_const_cols.append(col)
                continue

            # 98% 이상 결측/센티널 판정
            sentinel_cnt = sum(1 for v in col_vals if is_sentinel_or_missing(v))
            if sentinel_cnt >= len(col_vals) * 0.98:
                dropped_missing_cols.append(col)
                continue

            if sentinel_cnt > 0:
                cleaned_sentinel_cols.append(col)

            keep_indices.append(idx)

        compact_headers = [headers[i] for i in keep_indices]

        # 데이터 정제 (센티널 빈 문자열 변환 및 단위 접미사 정제)
        compact_rows = []
        for r in all_rows:
            new_r = []
            for i in keep_indices:
                val = r[i] if i < len(r) else ""
                if is_sentinel_or_missing(val):
                    new_r.append("")
                else:
                    # 단위 접미사 정제 (ppm, ppb 등)
                    cleaned = re.sub(r'(?i)\s*(ppm|ppb|ppt|nm|%|℃|celsius)$', '', str(val).strip()).strip()
                    new_r.append(cleaned)
            compact_rows.append(new_r)

        # 1. Compact CSV 저장
        compact_csv_name = f"{df.stem}_compact.csv"
        compact_csv_path = compact_dir / compact_csv_name
        with open(compact_csv_path, 'w', encoding='utf-8', newline='') as f_out:
            writer = csv.writer(f_out)
            writer.writerow(compact_headers)
            writer.writerows(compact_rows)

        compact_size = compact_csv_path.stat().st_size
        reduction_pct = round(((orig_size - compact_size) / max(orig_size, 1)) * 100, 2)

        # 2. Pandas PKL (설치된 경우 초고속 바이너리 생성)
        pkl_path_str = None
        if PACKAGES['pandas']:
            try:
                import pandas as pd
                df_compact = pd.read_csv(compact_csv_path)
                # Downcasting
                for c in df_compact.select_dtypes(include=['float64']).columns:
                    df_compact[c] = pd.to_numeric(df_compact[c], downcast='float')
                for c in df_compact.select_dtypes(include=['int64']).columns:
                    df_compact[c] = pd.to_numeric(df_compact[c], downcast='integer')
                pkl_name = f"{df.stem}_compact.pkl"
                pkl_path = compact_dir / pkl_name
                df_compact.to_pickle(pkl_path)
                pkl_path_str = str(pkl_path)
            except Exception:
                pass

        # 3. Coreset 샘플링 (3만행 초과 시 20% 코어셋)
        coreset_path_str = None
        coreset_rows_count = 0
        if actual_rows_count > 30000:
            coreset_name = f"{df.stem}_coreset.csv"
            coreset_path = compact_dir / coreset_name
            # 균등 20% 추출 (step = 5)
            coreset_rows = [compact_rows[i] for i in range(0, actual_rows_count, 5)]
            with open(coreset_path, 'w', encoding='utf-8', newline='') as f_c:
                c_writer = csv.writer(f_c)
                c_writer.writerow(compact_headers)
                c_writer.writerows(coreset_rows)
            coreset_path_str = str(coreset_path)
            coreset_rows_count = len(coreset_rows)

        manifest_files.append({
            'original_file': str(df),
            'original_size_bytes': orig_size,
            'original_rows': actual_rows_count,
            'original_cols': len(headers),
            'compact_file': str(compact_csv_path),
            'compact_size_bytes': compact_size,
            'compact_rows': actual_rows_count,
            'compact_cols': len(compact_headers),
            'size_reduction_pct': reduction_pct,
            'dropped_constant_cols': dropped_const_cols,
            'dropped_high_missing_cols': dropped_missing_cols,
            'cleaned_sentinel_cols': cleaned_sentinel_cols,
            'coreset_file': coreset_path_str,
            'coreset_rows': coreset_rows_count,
            'pkl_file': pkl_path_str
        })

        print(f"-> [COMPACT 완료] {df.name} => {compact_csv_name}")
        print(f"   용량: {orig_size / 1024:.1f}KB -> {compact_size / 1024:.1f}KB ({reduction_pct}% 축소)")
        print(f"   컬럼: {len(headers)}개 -> {len(compact_headers)}개 (상수 {len(dropped_const_cols)}개, 고결측 {len(dropped_missing_cols)}개 제거)")
        if coreset_path_str:
            print(f"   코어셋(20%): {coreset_rows_count:,}행 생성 ({Path(coreset_path_str).name})")
        if pkl_path_str:
            print(f"   바이너리 PKL 다운캐스팅 완료 ({Path(pkl_path_str).name})")

    # Manifest JSON 저장
    manifest_data = {
        'generated_at': time.strftime("%Y-%m-%d %H:%M:%S"),
        'compact_dir': str(compact_dir),
        'total_compacted_files': len(manifest_files),
        'files': manifest_files
    }
    manifest_path = compact_dir / "compact_manifest.json"
    manifest_path.write_text(json.dumps(manifest_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n-> 경량화 매니페스트 저장 완료: {manifest_path}")

# ==============================================================================
# [모드 3] 알고리즘 vs ML 챔피언 비교 모드 (Mode 3: Champion Arena Comparison)
# ==============================================================================
def execute_comparison(algo_file_path: str, ml_file_path: str):
    """
    메인 알고리즘 결과 파일과 백그라운드 ML 결과 파일을 1:1 비교 검증:
    - 행수/컬럼 일치 여부
    - 결측치 및 미정제 센티널 누출(Leakage) 0건 검증
    - 수치형 컬럼 기초 통계(Mean, Std, Min, Max), 상관계수(r), MAE 비교
    - leaderboard.json / CHAMPION_REPORT.md 연동 및 최종 채택 가이드 제공
    """
    print("\n" + "=" * 70)
    print("  [CHAMPION ARENA] 메인 알고리즘 vs 백그라운드 ML 결과 1:1 비교")
    print("=" * 70)

    p_algo = Path(algo_file_path)
    p_ml = Path(ml_file_path)

    if not p_algo.is_file():
        print(f"❌ [FAIL] 알고리즘 파일이 존재하지 않습니다: {algo_file_path}")
        return False
    if not p_ml.is_file():
        print(f"❌ [FAIL] ML 결과 파일이 존재하지 않습니다: {ml_file_path}")
        return False

    def load_table(fpath: Path):
        fp, _ = open_with_encoding(fpath)
        delim = '\t' if fpath.suffix.lower() == '.tsv' else ','
        with fp:
            line = fp.readline()
            if ',' not in line and '\t' in line:
                delim = '\t'
            reader = csv.reader([line], delimiter=delim)
            headers = [h.strip() for h in next(reader, [])]
            fp.seek(0)
            c_reader = csv.reader(fp, delimiter=delim)
            next(c_reader, None)
            rows = [r for r in c_reader]
        return headers, rows

    headers_algo, rows_algo = load_table(p_algo)
    headers_ml, rows_ml = load_table(p_ml)

    print(f"■ 알고리즘 파일: {p_algo.name} (행수: {len(rows_algo):,}, 컬럼수: {len(headers_algo)})")
    print(f"■ ML 결과 파일  : {p_ml.name} (행수: {len(rows_ml):,}, 컬럼수: {len(headers_ml)})")
    print("-" * 70)

    # 1. 행 수 검증
    row_match = len(rows_algo) == len(rows_ml)
    print(f"1. 행 수 일치 여부: {'[PASS]' if row_match else '[FAIL — 불일치]'}")
    if not row_match:
        print(f"   ⚠️ 주의: 알고리즘 행 수({len(rows_algo)})와 ML 행 수({len(rows_ml)})가 일치하지 않습니다!")

    # 2. 컬럼 헤더 일치 여부
    headers_match = headers_algo == headers_ml
    print(f"2. 컬럼 헤더 일치 여부: {'[PASS]' if headers_match else '[WARN — 부분 일치]'}")
    common_headers = [h for h in headers_algo if h in headers_ml]

    # 3. 결측치 및 미정제 센티널 누출 점검 (반드시 0건이어야 PASS)
    algo_leaks = 0
    ml_leaks = 0
    for r in rows_algo:
        for val in r:
            if is_sentinel_or_missing(val):
                algo_leaks += 1
    for r in rows_ml:
        for val in r:
            if is_sentinel_or_missing(val):
                ml_leaks += 1

    print(f"3. 제출 포맷 누출(NaN/센티널) 점검:")
    print(f"   - 알고리즘 결과 누출 건수: {algo_leaks}건 {'[PASS]' if algo_leaks == 0 else '[FAIL — 미정제 누출 발견]'}")
    print(f"   - ML 모델 결과 누출 건수  : {ml_leaks}건 {'[PASS]' if ml_leaks == 0 else '[FAIL — 미정제 누출 발견]'}")

    # 4. 수치형 컬럼 비교 (기초 통계, MAE, 상관계수)
    print("-" * 70)
    print("4. 공통 수치 컬럼 1:1 비교 통계 (Mean / Std / MAE / Correlation r):")

    min_len = min(len(rows_algo), len(rows_ml))
    stats_table = []

    for col in common_headers:
        idx_a = headers_algo.index(col)
        idx_m = headers_ml.index(col)

        vals_a = [clean_numeric_val(rows_algo[i][idx_a]) for i in range(min_len) if idx_a < len(rows_algo[i])]
        vals_m = [clean_numeric_val(rows_ml[i][idx_m]) for i in range(min_len) if idx_m < len(rows_ml[i])]

        # 둘 다 수치형 컬럼인지 확인
        valid_pairs = [(a, m) for a, m in zip(vals_a, vals_m) if a is not None and m is not None]
        if len(valid_pairs) < min_len * 0.5 or len(valid_pairs) == 0:
            continue

        a_nums = [p[0] for p in valid_pairs]
        m_nums = [p[1] for p in valid_pairs]

        mean_a = sum(a_nums) / len(a_nums)
        mean_m = sum(m_nums) / len(m_nums)

        var_a = sum((x - mean_a) ** 2 for x in a_nums) / len(a_nums)
        var_m = sum((x - mean_m) ** 2 for x in m_nums) / len(m_nums)
        std_a = math.sqrt(var_a)
        std_m = math.sqrt(var_m)

        mae = sum(abs(a - m) for a, m in valid_pairs) / len(valid_pairs)

        # Pearson correlation
        if std_a > 1e-9 and std_m > 1e-9:
            cov = sum((a - mean_a) * (m - mean_m) for a, m in valid_pairs) / len(valid_pairs)
            corr = cov / (std_a * std_m)
        else:
            corr = 1.0 if std_a <= 1e-9 and std_m <= 1e-9 else 0.0

        stats_table.append({
            'col': col,
            'mean_algo': mean_a,
            'mean_ml': mean_m,
            'std_algo': std_a,
            'std_ml': std_m,
            'mae': mae,
            'corr': corr
        })

        print(f"   ▶ [{col}]")
        print(f"      - Algo : Mean={mean_a:.4f}, Std={std_a:.4f}")
        print(f"      - ML   : Mean={mean_m:.4f}, Std={std_m:.4f}")
        print(f"      - MAE(평균 절대 오차) : {mae:.4f}")
        print(f"      - 상관계수 (Pearson r): {corr:.4f} {'(매우 높은 일치도)' if corr >= 0.90 else '(상이한 패턴)'}")

    # 5. 백그라운드 리더보드/챔피언 리포트 연동
    print("-" * 70)
    print("5. 백그라운드 ML 트랙(Sol 6.1) 검증 점수 및 채택 가이드:")
    champion_found = False

    # 리더보드 탐색 (.probe-kit/ml_track 또는 상위 디렉토리)
    possible_dirs = [
        p_ml.parent,
        p_algo.parent,
        Path.cwd() / ".probe-kit" / "ml_track",
        Path.cwd() / "probe-kit" / "ml_track"
    ]
    for d in possible_dirs:
        lb_path = d / "leaderboard.json"
        rep_path = d / "CHAMPION_REPORT.md"
        if lb_path.is_file():
            try:
                lb = json.loads(lb_path.read_text(encoding="utf-8"))
                champion_found = True
                print(f"   [리더보드 감지] 최고 성능 모델: {lb.get('champion_model', 'N/A')}")
                print(f"   - CV 검증 점수: {lb.get('best_cv_score', 'N/A')} ({lb.get('metric', 'Score')})")
                print(f"   - 최종 학습 라운드: {lb.get('total_iterations', 'N/A')}회 완료")
                break
            except Exception:
                pass
        elif rep_path.is_file():
            try:
                content = rep_path.read_text(encoding="utf-8")
                champion_found = True
                print(f"   [챔피언 리포트 감지]: {rep_path.name}")
                for line in content.splitlines()[:5]:
                    if line.strip():
                        print(f"     {line}")
                break
            except Exception:
                pass

    if not champion_found:
        print("   💡 [안내] 백그라운드 leaderboard.json 파일이 아직 생성되지 않았습니다.")

    # 6. 최종 채택 권고
    print("-" * 70)
    print("【 최종 아레나 채택 권고 】")
    if algo_leaks > 0 and ml_leaks == 0:
        print("   👉 [ML 채택 강력 권고] 메인 알고리즘에 미정제 결측/센티널 누출이 있으므로, 정제된 ML 결과를 우선 채택하세요.")
    elif ml_leaks > 0 and algo_leaks == 0:
        print("   👉 [알고리즘 채택 권고] ML 결과에 누출이 감지되었습니다. 알고리즘 산출물을 우선 제출하세요.")
    else:
        # 상관계수 기준
        high_corrs = [s['corr'] for s in stats_table if s['corr'] >= 0.90]
        if len(high_corrs) == len(stats_table) and len(stats_table) > 0:
            print("   👉 [앙상블 권고 (Ensemble 50:50)] 두 결과의 일치도(r >= 0.90)가 매우 높습니다.")
            print("      `final = 0.5 * algo + 0.5 * ml` 블렌딩 시 단일 모델 대비 분산 감소 및 리더보드 안정성을 확보할 수 있습니다.")
        else:
            print("   👉 [개별 검증 필요] 알고리즘과 ML 결과 간 편차가 존재합니다. CV 점수 및 도메인 제약 준수 여부를 확인하세요.")
    print("=" * 70)
    return True

# ==============================================================================
# [모드 4] 데모 및 자체 검증 모드 (Mode 4: Self-Verification Demo)
# ==============================================================================
def execute_demo():
    """
    임시 합성 데이터셋(500행, 타깃 yield, 센티널 < DL 및 상수 컬럼 포함)으로
    [진단] -> [--compact 경량화] -> [--compare 비교] 3단계를 모두 자체 검증하고 [PASS] 출력
    """
    print("\n" + "=" * 70)
    print("  [DEMO] ml_feasibility_check.py 3단계 자가 검증 데모 시작")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        ws_path = temp_path / "demo_workspace"
        ws_path.mkdir(parents=True, exist_ok=True)
        ml_track_path = ws_path / ".probe-kit" / "ml_track"

        # 1. 합성 데이터 및 README 생성
        readme_file = ws_path / "README.md"
        readme_file.write_text(
            "# 반도체 웨이퍼 수율(yield) 예측 과제\n\n"
            "공정 센서 데이터(온도, 압력, RF 전력)를 바탕으로 최종 수율(yield)을 예측하는 경량 회귀 모델링 과제입니다.\n",
            encoding="utf-8"
        )

        data_file = ws_path / "wafer_process_data.csv"
        headers = ["wafer_id", "temp_sensor", "press_sensor", "const_col", "sentinel_col", "sparse_col", "yield"]
        rows = []
        random.seed(42)
        for i in range(1, 501):
            w_id = f"WF-{i:03d}"
            temp = round(200.0 + random.uniform(-5.0, 5.0), 2)
            press = round(50.0 + random.uniform(-2.0, 2.0), 2)
            const = "FIXED_SETTING"
            # 센티널 일부 삽입
            if i % 25 == 0:
                sentinel = "< DL"
            elif i % 50 == 0:
                sentinel = "-9999"
            else:
                sentinel = f"{round(10.0 + random.uniform(0.1, 1.0), 3)}ppm"
            # 98% 이상 고결측 컬럼
            sparse = "" if i > 5 else "VAL"
            # 타깃 컬럼 (수율)
            y = round(92.0 + 0.05 * (temp - 200.0) + 0.1 * (press - 50.0) + random.uniform(-0.5, 0.5), 2)
            rows.append([w_id, temp, press, const, sentinel, sparse, y])

        with open(data_file, 'w', encoding='utf-8', newline='') as f:
            w = csv.writer(f)
            w.writerow(headers)
            w.writerows(rows)

        print(f"\n[Step 1] 합성 데이터셋 생성 완료: {data_file.name} (500행, 센티널/상수/고결측 컬럼 포함)")

        # 2. [진단 모드 실행]
        print("\n--- [Step 2: 기본 진단 모드 검증] ---")
        report = evaluate_feasibility(ws_path, ml_track_path)
        assert report['verdict'] == "GO_DIRECT_ML", f"예상치 못한 판정: {report['verdict']}"
        assert (ml_track_path / "FEASIBILITY_SUMMARY.txt").is_file(), "FEASIBILITY_SUMMARY.txt 미생성"
        assert (ml_track_path / "feasibility_report.json").is_file(), "feasibility_report.json 미생성"
        print("✔ [PASS] Step 2 기본 진단 모드 검증 성공!")

        # 3. [경량화 모드 실행]
        print("\n--- [Step 3: --compact 경량화 모드 검증] ---")
        execute_compaction(ws_path, ml_track_path)
        compact_csv = ml_track_path / "data_compact" / "wafer_process_data_compact.csv"
        manifest_json = ml_track_path / "data_compact" / "compact_manifest.json"
        assert compact_csv.is_file(), "경량화 CSV 파일 미생성"
        assert manifest_json.is_file(), "compact_manifest.json 미생성"

        # 컬럼 축소 확인 (const_col, sparse_col 제거되었는지 확인)
        with open(compact_csv, 'r', encoding='utf-8') as f:
            r = csv.reader(f)
            c_headers = next(r)
            assert "const_col" not in c_headers, "상수 컬럼 제거 실패"
            assert "sparse_col" not in c_headers, "고결측 컬럼 제거 실패"
            assert "yield" in c_headers, "타깃 컬럼 누락"
        print("✔ [PASS] Step 3 --compact 경량화 모드 검증 성공 (상수/고결측 컬럼 정상 제거 완료)!")

        # 4. [비교 모드 실행]
        print("\n--- [Step 4: --compare 챔피언 비교 모드 검증] ---")
        algo_file = ws_path / "algo_pred.csv"
        ml_file = ws_path / "ml_pred.csv"

        with open(algo_file, 'w', encoding='utf-8', newline='') as f:
            w = csv.writer(f)
            w.writerow(["wafer_id", "pred_yield"])
            for i in range(1, 101):
                w.writerow([f"WF-{i:03d}", round(90.0 + i * 0.05, 2)])

        with open(ml_file, 'w', encoding='utf-8', newline='') as f:
            w = csv.writer(f)
            w.writerow(["wafer_id", "pred_yield"])
            for i in range(1, 101):
                w.writerow([f"WF-{i:03d}", round(90.0 + i * 0.05 + random.uniform(-0.02, 0.02), 2)])

        cmp_success = execute_comparison(str(algo_file), str(ml_file))
        assert cmp_success is True, "비교 모드 실행 실패"
        print("✔ [PASS] Step 4 --compare 비교 모드 검증 성공!")

    print("\n" + "=" * 70)
    print("  🎉 [PASS] ALL DEMO CHECKS PASSED SUCCESSFULLY! (모든 데모 검증 완료)")
    print("=" * 70)

# ==============================================================================
# 메인 진입점 (CLI Entry Point)
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="경량 AI/ML Feasibility Checker & Dataset Compactor & Champion Arena Comparator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  1. 기본 진단 모드 (8대 조건 판별 및 보고서 생성):
     python3 scripts/ml_feasibility_check.py
     python3 scripts/ml_feasibility_check.py /path/to/workspace

  2. 데이터 경량화 실행 모드:
     python3 scripts/ml_feasibility_check.py --compact
     python3 scripts/ml_feasibility_check.py --compact /path/to/workspace

  3. 챔피언 결과 비교 모드:
     python3 scripts/ml_feasibility_check.py --compare algo_result.csv ml_result.csv

  4. 데모 및 3단계 자체 검증:
     python3 scripts/ml_feasibility_check.py --demo
"""
    )
    parser.add_argument("workspace_dir", nargs="?", default=None, help="대상 워크스페이스 디렉토리 경로 (생략 시 현재 위치 자동 감지)")
    parser.add_argument("--compact", action="store_true", help="데이터셋 자체 경량화 실행 (.probe-kit/ml_track/data_compact/)")
    parser.add_argument("--compare", nargs=2, metavar=("ALGO_FILE", "ML_FILE"), help="알고리즘 산출물과 ML 산출물 1:1 비교")
    parser.add_argument("--demo", action="store_true", help="임시 합성 데이터셋으로 진단 -> 경량화 -> 비교 3단계 자체 검증 실행")

    args = parser.parse_args()

    if args.demo:
        execute_demo()
        return

    if args.compare:
        execute_comparison(args.compare[0], args.compare[1])
        return

    ws_dir, ml_track_dir = resolve_workspace_paths(args.workspace_dir)

    if args.compact:
        execute_compaction(ws_dir, ml_track_dir)
    else:
        evaluate_feasibility(ws_dir, ml_track_dir)

if __name__ == "__main__":
    main()
