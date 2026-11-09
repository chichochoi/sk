#!/usr/bin/env python3
"""
scripts/eda_scan.py
무토큰 초고속 워크스페이스 EDA 스캐너 & [CASE_SIGNAL] 자동 감지기 (표준 라이브러리 전용)
- 최상단: 문제 유형(Case 1~7), 추천 스킬, DM 질문 섹션, 추정 페르소나 [CASE_SIGNAL] 배너 출력 (< 10줄)
- 테스트 파일 목록 자동 탐지
- CSV / TSV / JSON / JSONL 스키마, 행 수, 결측치, 중복행, 3행 샘플, 수치 min/max 요약
- 반도체 및 제조 도메인 센티널(< DL, < 0.xx, ND, -9999 등) 및 단위 마커(ppm, ppb, ppt, nm) 자동 탐지
- 수치 min/max 연산 시 단위 접미사 정제 및 센티널 왜곡 방지
- 최대 200,000행 보호 제한 및 다중 인코딩(utf-8-sig, utf-8, cp949, euc-kr, latin-1) 폴백 지원
- argparse 기반 --help / -h 지원 및 positional target_path 호환성 100% 보장
"""

import os
import sys
import csv
import json
import math
import re
import argparse
from collections import Counter
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
    '', 'null', 'none', 'nan', 'na', 'n/a', '-999', '-999.0',
    '-9999', '-9999.0', 'nd', 'not detected', '< dl', '<dl'
}

UNIT_RE = re.compile(r'(?i)(?:^|(?<=[0-9\s_(\[/\-]))(ppm|ppb|ppt|nm)(?:$|(?=[\s_)\]/:\-_]))')

MAX_ROWS = 200000
MAX_JSON_FILE_SIZE = 10 * 1024 * 1024  # 10MB 초과 대용량 JSON OOM 안전 가드

# ==============================================================================
# 1. 반도체 / 제조 도메인 센티널 및 결측치 감지
# ==============================================================================

def check_domain_sentinel(val):
    """
    반도체/제조 도메인 센티널 및 검출한계 미만(< DL, < 0.xx, ND, -9999 등) 감지.
    감지 시 표준화된 토큰 문자열(예: '< DL', 'ND', '-9999', '< 0.xx') 반환, 아니면 None.
    """
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    s_lower = s.lower()
    if s_lower in ('-9999', '-9999.0'):
        return '-9999'
    if s_lower in ('-999', '-999.0'):
        return '-999'
    if s_lower in ('nd', 'not detected'):
        return 'ND'
    if s_lower in ('< dl', '<dl'):
        return '< DL'
    if s_lower.startswith('<'):
        if 'dl' in s_lower:
            return '< DL'
        if any(ch.isdigit() for ch in s_lower):
            token = s.split()[0] if ' ' in s else s
            return token[:12]
    return None

def is_missing(val):
    if val is None:
        return True
    s = str(val).strip().lower()
    if s in MISSING_TOKENS:
        return True
    if check_domain_sentinel(val) is not None:
        return True
    return False

def try_float(val):
    """
    수치 변환 함수:
    - 결측치 및 도메인 센티널(-9999, < DL 등)은 None 반환으로 min/max 왜곡 방지
    - 단위 마커 접미사(ppm, ppb, ppt, nm 등) 제거 후 순수 수치 파싱
    """
    if is_missing(val):
        return None
    s = str(val).strip().replace(',', '')
    s = re.sub(r'(?i)\s*(ppm|ppb|ppt|nm)$', '', s).strip()
    try:
        f = float(s)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (ValueError, TypeError):
        return None

# ==============================================================================
# 2. 인코딩 안전 파일 리더
# ==============================================================================

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

    has_non_ascii = any(b >= 128 for b in raw_sample)
    if not has_non_ascii:
        return open(filepath, 'r', encoding='utf-8', newline='', errors='replace'), 'utf-8'

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

# ==============================================================================
# 3. [CASE_SIGNAL] 문제 유형 및 페르소나 자동 감지 휴리스틱 분류기
# ==============================================================================

CASE5_KEYWORD_MAP = {
    'bus': ('#8', '윤서영 책임(통근버스 배차)'),
    'route': ('#8', '윤서영 책임(통근버스 배차)'),
    'stop': ('#8', '윤서영 책임(통근버스 배차)'),
    'shuttle': ('#8', '윤서영 책임(통근버스 배차)'),
    '통근버스': ('#8', '윤서영 책임(통근버스 배차)'),
    '배차': ('#8', '윤서영 책임(통근버스 배차)'),
    '정류장': ('#8', '윤서영 책임(통근버스 배차)'),
    'diet': ('#9', '이하린 영양사 / #12 Sarah(식단편성)'),
    'menu': ('#9', '이하린 영양사 / #12 Sarah(식단편성)'),
    'calorie': ('#9', '이하린 영양사 / #12 Sarah(식단편성)'),
    '식단': ('#9', '이하린 영양사 / #12 Sarah(식단편성)'),
    '영양': ('#9', '이하린 영양사 / #12 Sarah(식단편성)'),
    'cctv': ('#10', '정유진 TL / #11 Jordan(CCTV 배치)'),
    'camera': ('#10', '정유진 TL / #11 Jordan(CCTV 배치)'),
    'grid': ('#10', '정유진 TL / #11 Jordan(CCTV 배치)'),
    'floorplan': ('#10', '정유진 TL / #11 Jordan(CCTV 배치)'),
    'coverage': ('#10', '정유진 TL / #11 Jordan(CCTV 배치)'),
    '사각지대': ('#10', '정유진 TL / #11 Jordan(CCTV 배치)'),
    '도면': ('#10', '정유진 TL / #11 Jordan(CCTV 배치)'),
    'scanner': ('#13-A', '이도윤 TL(노광기 배정·PM)'),
    'reticle': ('#13-A', '이도윤 TL(노광기 배정·PM)'),
    'pm_schedule': ('#13-A', '이도윤 TL(노광기 배정·PM)'),
    '노광기': ('#13-A', '이도윤 TL(노광기 배정·PM)'),
    'quota': ('#7-A', '박서연 책임(조달 쿼터 LP)'),
    'moq': ('#7-A', '박서연 책임(조달 쿼터 LP)'),
    '조달': ('#7-A', '박서연 책임(조달 쿼터 LP)'),
    '쿼터': ('#7-A', '박서연 책임(조달 쿼터 LP)'),
    'product_mix': ('#6-B', '김현우 책임(Product Mix)'),
    'wspm': ('#6-B', '김현우 책임(Product Mix)'),
    'curriculum': ('#15-B', '윤지안 TL(교육 커리큘럼)'),
    'prerequisite': ('#15-B', '윤지안 TL(교육 커리큘럼)'),
    '선수과목': ('#15-B', '윤지안 TL(교육 커리큘럼)')
}

CASE6_KEYWORD_MAP = {
    'wafer': ('#13-B/#7-B', '반도체 데이터 분석'),
    '웨이퍼': ('#13-B/#7-B', '반도체 데이터 분석'),
    'overlay': ('#13-B', '이도윤 TL(2D Overlay OLS)'),
    '오버레이': ('#13-B', '이도윤 TL(2D Overlay OLS)'),
    'dx': ('#13-B', '이도윤 TL(2D Overlay OLS)'),
    'dy': ('#13-B', '이도윤 TL(2D Overlay OLS)'),
    'chuck': ('#13-B', '이도윤 TL(2D Overlay OLS)'),
    'adi': ('#13-B', '이도윤 TL(2D Overlay OLS)'),
    'aei': ('#13-B', '이도윤 TL(2D Overlay OLS)'),
    'coa': ('#7-B', '박서연 책임(원소재 CoA/SPC)'),
    'ppm': ('#7-B', '박서연 책임(원소재 CoA/SPC)'),
    'ppb': ('#7-B', '박서연 책임(원소재 CoA/SPC)'),
    'ppt': ('#7-B', '박서연 책임(원소재 CoA/SPC)'),
    'cpk': ('#7-B', '박서연 책임(원소재 CoA/SPC)'),
    'usl': ('#7-B', '박서연 책임(원소재 CoA/SPC)'),
    'lsl': ('#7-B', '박서연 책임(원소재 CoA/SPC)'),
    'pcn': ('#7-B', '박서연 책임(원소재 CoA/SPC)'),
    'nelson': ('#7-B', '박서연 책임(원소재 CoA/SPC)'),
    '시험성적서': ('#7-B', '박서연 책임(원소재 CoA/SPC)'),
    '성적서': ('#7-B', '박서연 책임(원소재 CoA/SPC)'),
    'bit_growth': ('#6-A', '김현우 책임(경쟁사 실적 정규화)'),
    'asp': ('#6-A', '김현우 책임(경쟁사 실적 정규화)'),
    'doi': ('#6-A', '김현우 책임(경쟁사 실적 정규화)'),
    'fiscal': ('#6-A', '김현우 책임(경쟁사 실적 정규화)'),
    'opm': ('#6-A', '김현우 책임(경쟁사 실적 정규화)'),
    'ebitda': ('#6-A', '김현우 책임(경쟁사 실적 정규화)'),
    '경쟁사': ('#6-A', '김현우 책임(경쟁사 실적 정규화)')
}

CASE7_KEYWORD_MAP = {
    'value_chain': ('#14', '한서진 TL(밸류체인 수급 충격)'),
    'valuechain': ('#14', '한서진 TL(밸류체인 수급 충격)'),
    '밸류체인': ('#14', '한서진 TL(밸류체인 수급 충격)'),
    'dag': ('#14/#15', '한서진/윤지안 TL(DAG 시뮬레이터)'),
    'ripple': ('#14', '한서진 TL(밸류체인 수급 충격)'),
    'bottleneck': ('#14', '한서진 TL(밸류체인 병목 탐지)'),
    '병목': ('#14', '한서진 TL(밸류체인 병목 탐지)'),
    'cowos': ('#14', '한서진 TL(밸류체인 수급 충격)'),
    'hbm': ('#14', '한서진 TL(밸류체인 수급 충격)'),
    'educator': ('#15', '윤지안 TL(산업교육 AI 튜터)'),
    'misconception': ('#15', '윤지안 TL(산업교육 AI 튜터)'),
    '오개념': ('#15', '윤지안 TL(산업교육 AI 튜터)'),
    '튜터': ('#15', '윤지안 TL(산업교육 AI 튜터)'),
    'persona': ('#14/#15', '한서진/윤지안 TL(듀얼 페르소나)'),
    'role_switcher': ('#14/#15', '듀얼 페르소나 앱'),
    'what_if': ('#6-C/#7-C/#13-C', 'What-If 시뮬레이터'),
    'allergy': ('#12', 'Sarah Collins(오늘의 메뉴 맞춤추천)'),
    'today_menu': ('#12', 'Sarah Collins(오늘의 메뉴 맞춤추천)'),
    '알레르기': ('#12', 'Sarah Collins(오늘의 메뉴 맞춤추천)')
}

def extract_matches(text: str, kw_map: dict):
    if not text:
        return []
    text_clean = text.lower()
    text_norm = re.sub(r'[^a-z0-9가-힣_]+', ' ', text_clean)
    words = set(text_norm.split())
    words_no_sep = set(text_clean.replace('_', ' ').replace('-', ' ').split())
    all_words = words | words_no_sep

    hits = []
    for kw in kw_map:
        kw_lower = kw.lower()
        if '_' in kw_lower or '-' in kw_lower or ' ' in kw_lower:
            phrase = kw_lower.replace('_', ' ').replace('-', ' ')
            if phrase in text_clean or kw_lower in text_clean:
                hits.append(kw)
        else:
            if kw_lower in all_words:
                hits.append(kw)
    return hits

def detect_case_signal(root: Path, readme_text: str, all_rel_paths: list, headers_and_keys: list,
                       data_files: list, test_files: list, has_src: bool,
                       has_package_json: bool, has_requirements_txt: bool,
                       policy_doc_count: int) -> dict:
    """
    디렉토리 구조, README 앞부분, 파일명 및 컬럼 헤더를 종합 분석하여 문제 유형(Case 1~7) 추정
    """
    filenames_text = " ".join([p.name for p in all_rel_paths])
    headers_text = " ".join(headers_and_keys)

    scores = {}
    matched_kw_by_case = {}

    for case_num, kw_map in ((5, CASE5_KEYWORD_MAP), (6, CASE6_KEYWORD_MAP), (7, CASE7_KEYWORD_MAP)):
        r_hits = extract_matches(readme_text, kw_map)
        f_hits = extract_matches(filenames_text, kw_map)
        h_hits = extract_matches(headers_text, kw_map)
        score = len(r_hits) * 3 + len(f_hits) * 2 + len(h_hits) * 2
        scores[case_num] = score
        matched_kw_by_case[case_num] = (r_hits, f_hits, h_hits)

    best_case = max(scores, key=scores.get)
    best_score = scores[best_case]

    if best_score > 0:
        r_hits, f_hits, h_hits = matched_kw_by_case[best_case]
        all_hits = list(dict.fromkeys(r_hits + f_hits + h_hits))
        kw_map = {5: CASE5_KEYWORD_MAP, 6: CASE6_KEYWORD_MAP, 7: CASE7_KEYWORD_MAP}[best_case]
        suspects = [kw_map[h][1] for h in all_hits if h in kw_map]
        unique_suspects = list(dict.fromkeys(suspects))

        if best_case == 5:
            persona_str = ", ".join(unique_suspects[:3]) if unique_suspects else "#8/#9/#10/#13-A/#7-A/#6-B/#15-B (배차·식단·CCTV·노광·쿼터)"
            return {
                "title": "Case 5 (수리·조합 최적화 / CSP)",
                "skill": ".probe-kit/skills/case5_optimization_csp.md",
                "dm_section": ".probe-kit/dm_question.md (## Case 5. 수리·조합 최적화 / CSP)",
                "personas": persona_str,
                "audit_script": "bash .probe-kit/scripts/pre_submit_audit.sh"
            }
        elif best_case == 6:
            persona_str = ", ".join(unique_suspects[:3]) if unique_suspects else "#7-B/#13-B/#6-A (CoA/SPC·2D Overlay·재무 정규화)"
            return {
                "title": "Case 6 (반도체 CoA/SPC·2D Overlay·재무 정규화)",
                "skill": ".probe-kit/skills/case6_semicon_data_spc.md",
                "dm_section": ".probe-kit/dm_question.md (## Case 6. 반도체 CoA/SPC·2D Overlay·재무 정규화)",
                "personas": persona_str,
                "audit_script": "bash .probe-kit/scripts/pre_submit_audit.sh"
            }
        else:  # 7
            persona_str = ", ".join(unique_suspects[:3]) if unique_suspects else "#14/#15/#12/#6-C/#7-C/#13-C (밸류체인·교육 AI·시뮬레이터)"
            return {
                "title": "Case 7 (밸류체인 DAG·듀얼 페르소나·교육 AI/시뮬레이터)",
                "skill": ".probe-kit/skills/case7_fde_valuechain_app.md",
                "dm_section": ".probe-kit/dm_question.md (## Case 7. 밸류체인 DAG·듀얼 페르소나·교육 AI/시뮬레이터)",
                "personas": persona_str,
                "audit_script": "bash .probe-kit/scripts/pre_submit_audit.sh"
            }

    # Fallback 로직
    if (len(test_files) > 0 or any('tests' in p.parts or 'test' in p.parts for p in all_rel_paths)) and has_src:
        return {
            "title": "Case 3 (레거시 코드베이스 디버깅 및 신규 기능 확장)",
            "skill": ".probe-kit/skills/case3_legacy_debug.md",
            "dm_section": ".probe-kit/dm_question.md (## Case 3. 레거시 코드베이스 디버깅 및 신규 기능 확장)",
            "personas": "기존 코드베이스 디버깅 / 결함 분석 / 신규 인터페이스 확장",
            "audit_script": "bash .probe-kit/scripts/pre_submit_audit.sh"
        }
    if has_package_json or any(p.name.lower() in ('app.jsx', 'index.html', 'app.py', 'server.js') for p in all_rel_paths):
        return {
            "title": "Case 2 (실무형 웹 서비스 / 웹앱 구축)",
            "skill": ".probe-kit/skills/case2_web_service.md",
            "dm_section": ".probe-kit/dm_question.md (## Case 2. 실무형 웹 서비스 / 웹앱 구축)",
            "personas": "실무형 웹 서비스 / REST API / 웹앱 대시보드 구축",
            "audit_script": "bash .probe-kit/scripts/pre_submit_audit.sh"
        }
    if policy_doc_count > 0:
        return {
            "title": "Case 4 (사내 업무 자동화, 규정 색인·판정, RAG·분류기)",
            "skill": ".probe-kit/skills/case4_policy_rag_doc.md",
            "dm_section": ".probe-kit/dm_question.md (## Case 4. 사내 업무 자동화, 규정 색인·판정, RAG·분류기, 전략 대안 비교)",
            "personas": "사내 규정 색인·판정 / RAG / 정책 대안 비교 과제",
            "audit_script": "bash .probe-kit/scripts/pre_submit_audit.sh"
        }

    return {
        "title": "Case 1 (데이터 파이프라인 정제·집계 및 반도체/제조 판정)",
        "skill": ".probe-kit/skills/case1_data_pipeline.md",
        "dm_section": ".probe-kit/dm_question.md (## Case 1. 데이터 파이프라인 정제·집계 및 반도체/제조 판정)",
        "personas": "데이터 정제 및 집계 파이프라인 / 수율·품질 판정",
        "audit_script": "bash .probe-kit/scripts/pre_submit_audit.sh"
    }

def print_case_signal_banner(case_info: dict):
    print("=" * 65)
    print(f"[CASE_SIGNAL] 감지: {case_info['title']}")
    print(f"- 추천 스킬: {case_info['skill']}")
    print(f"- 추천 DM 질문: {case_info['dm_section']}")
    print(f"- 추정 페르소나: {case_info['personas']}")
    print(f"- 보조 점검: {case_info['audit_script']}")
    print("=" * 65)

# ==============================================================================
# 4. 빠른 헤더 및 파일 발췌 유틸리티
# ==============================================================================

def peek_headers(file_path: Path):
    try:
        fp, enc = open_with_encoding(file_path)
        with fp:
            line = fp.readline()
            if not line:
                return []
            delim = '\t' if file_path.suffix.lower() == '.tsv' else ','
            if ',' not in line and '\t' in line:
                delim = '\t'
            elif '\t' not in line and ';' in line:
                delim = ';'
            reader = csv.reader([line], delimiter=delim)
            headers = next(reader, [])
            return [h.strip() for h in headers if h.strip()]
    except Exception:
        return []

def peek_json_keys(file_path: Path):
    try:
        fp, enc = open_with_encoding(file_path)
        with fp:
            if file_path.suffix.lower() == '.jsonl':
                line = fp.readline()
                if line:
                    obj = json.loads(line)
                    if isinstance(obj, dict):
                        return list(obj.keys())[:30]
            else:
                chunk = fp.read(4096)
                if not chunk:
                    return []
                keys = re.findall(r'"([a-zA-Z0-9_\-]+)"\s*:', chunk)
                return keys[:30]
    except Exception:
        return []
    return []

def read_readme_preview(root: Path) -> str:
    candidates = ['README.md', 'README.en.md', 'readme.md', 'Readme.md', 'README.txt']
    read_texts = []
    seen_paths = set()
    for c in candidates:
        p = root / c
        if p.exists() and p.is_file() and p.resolve() not in seen_paths:
            seen_paths.add(p.resolve())
            try:
                fp, enc = open_with_encoding(p)
                with fp:
                    lines = [fp.readline() for _ in range(60)]
                    read_texts.append("".join(lines))
            except Exception:
                pass
    return "\n".join(read_texts)

# ==============================================================================
# 5. 테이블 및 데이터 분석 엔진
# ==============================================================================

def analyze_tabular(headers, rows, file_label, truncated=False):
    num_cols = len(headers)
    num_rows = len(rows)

    print(f"  * 컬럼 수({num_cols}개): {headers}")
    trunc_note = f" (최대 {MAX_ROWS:,}행 제한 적용)" if truncated else ""
    print(f"  * 총 행 수(헤더 제외): {num_rows:,}행{trunc_note}")

    if num_rows == 0:
        print("  * 데이터가 비어 있습니다.")
        return

    # 결측치 집계 (컬럼별 & 전체) 및 도메인 센티널/단위 마커 감지
    col_missing = [0] * num_cols
    total_missing = 0
    col_numerics = [[] for _ in range(num_cols)]

    seen_rows = set()
    dup_count = 0

    domain_sentinels = Counter()
    detected_units = {}

    # 1. 헤더 단위 마커 탐지
    for idx, name in enumerate(headers):
        m = UNIT_RE.search(name)
        if m:
            detected_units[name] = m.group(1).lower()

    for r in rows:
        # 중복 행 체크
        r_tuple = tuple(r)
        if r_tuple in seen_rows:
            dup_count += 1
        else:
            seen_rows.add(r_tuple)

        for col_idx in range(num_cols):
            val = r[col_idx] if col_idx < len(r) else ""
            sentinel = check_domain_sentinel(val)
            if sentinel:
                domain_sentinels[sentinel] += 1

            if is_missing(val):
                col_missing[col_idx] += 1
                total_missing += 1
            else:
                fv = try_float(val)
                if fv is not None:
                    col_numerics[col_idx].append(fv)

    # 2. 값(Value) 단위 마커 샘플링 탐지 (상위 200행 대상)
    for col_idx in range(num_cols):
        col_name = headers[col_idx]
        if col_name not in detected_units:
            for r in rows[:200]:
                if col_idx < len(r):
                    val = str(r[col_idx]).strip()
                    m = UNIT_RE.search(val)
                    if m and not check_domain_sentinel(val):
                        detected_units[col_name] = m.group(1).lower()
                        break

    print(f"  * 중복 행 수: {dup_count:,}행 ({dup_count/num_rows*100:.2f}%)")
    print(f"  * 총 결측 셀 수: {total_missing:,}개 (전체 {num_rows * num_cols:,}셀 중 {total_missing/(num_rows*num_cols)*100:.2f}%)")

    # 도메인 센티널 및 단위 마커 요약
    if domain_sentinels:
        sentinel_details = [f"'{k}': {cnt:,}건" for k, cnt in domain_sentinels.most_common(4)]
        print(f"  * 도메인 센티널/한계미만값 감지: 총 {sum(domain_sentinels.values()):,}건 ({', '.join(sentinel_details)})")
    if detected_units:
        unit_details = [f"{col}({u})" for col, u in list(detected_units.items())[:6]]
        if len(detected_units) > 6:
            unit_details.append(f"...외 {len(detected_units) - 6}개")
        print(f"  * 도메인 단위 마커 감지: {', '.join(unit_details)}")

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

# ==============================================================================
# 6. 워크스페이스 스캔 메인 루틴
# ==============================================================================

def scan_workspace(root_path: str):
    root = Path(root_path).resolve()
    if not root.exists():
        print(f"[오류] 경로가 존재하지 않습니다: {root}")
        sys.exit(1)

    data_files = []
    test_files = []
    all_rel_paths = []
    headers_and_keys = []
    has_src = False
    has_package_json = (root / "package.json").exists()
    has_requirements_txt = (root / "requirements.txt").exists()
    policy_doc_count = 0

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and not d.startswith('.')]
        rel_dir = Path(dirpath).relative_to(root)
        if rel_dir.parts and rel_dir.parts[0].lower() == 'src':
            has_src = True

        for f in sorted(filenames):
            rel_p = rel_dir / f if str(rel_dir) != '.' else Path(f)
            all_rel_paths.append(rel_p)
            f_lower = f.lower()

            if is_test_file(rel_p):
                test_files.append(rel_p)

            if f_lower.endswith(('.csv', '.tsv', '.json', '.jsonl')):
                data_files.append(rel_p)
                full_p = root / rel_p
                if f_lower.endswith(('.csv', '.tsv')):
                    headers_and_keys.extend(peek_headers(full_p))
                elif f_lower.endswith(('.json', '.jsonl')):
                    headers_and_keys.extend(peek_json_keys(full_p))

            if f_lower.endswith('.pdf') or any(kw in f_lower for kw in ('policy', 'manual', '규정', '가이드', 'guideline')):
                policy_doc_count += 1

    readme_text = read_readme_preview(root)

    # 1. 최상단 [CASE_SIGNAL] 배너 출력 (10줄 이내)
    case_info = detect_case_signal(
        root=root,
        readme_text=readme_text,
        all_rel_paths=all_rel_paths,
        headers_and_keys=headers_and_keys,
        data_files=data_files,
        test_files=test_files,
        has_src=has_src,
        has_package_json=has_package_json,
        has_requirements_txt=has_requirements_txt,
        policy_doc_count=policy_doc_count
    )
    print_case_signal_banner(case_info)

    # 2. EDA SCAN 본문 출력
    print("=" * 65)
    print(f"[EDA SCAN] 워크스페이스 구조 및 데이터 무토큰 요약")
    print(f"   루트 경로: {root}")
    print("=" * 65)

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

def parse_args():
    parser = argparse.ArgumentParser(
        description="무토큰 초고속 워크스페이스 EDA 스캐너 & [CASE_SIGNAL] 자동 감지 도구 (표준 라이브러리 전용)"
    )
    parser.add_argument(
        "target_path",
        nargs="?",
        default=".",
        help="스캔할 워크스페이스 루트 경로 (기본값: .)"
    )
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    scan_workspace(args.target_path)
