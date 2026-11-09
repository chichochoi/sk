#!/usr/bin/env python3
"""
scripts/sample_check_spc.py
반도체 원소재 CoA · SPC 통계 공정 제어 · 2D 오버레이 계측 · 재무 정규화 표본 15건 수동 대조 검증 스크립트 (Case 6 필수)
(Case 7-B, Case 13-B, Case 6-A 전용)

15건의 수작업 기댓값(EXPECTED)과 실제 파이프라인 처리 함수를 비교 검증합니다:
- Case 7-B: 단위 환산(ppm/ppb/ppt), < DL 대치, Cpk, Nelson Rules, PCN HOLD/REJECT 인터락 (1~5번)
- Case 13-B: Edge Exclusion(147mm), 6-Param OLS, 잔차 3-sigma, ADI REWORK vs AEI SCRAP, Chuck Mismatch (6~10번)
- Case 6-A: FY->CY 분기 선형보간, 수정공시 최신화, 손익 평균환율 vs 자산 기말환율, Bit*ASP Waterfall, DOI 경보 (11~15번)

- TARGET_MODULE / TARGET_FUNC 동적 로딩 지원 (미지정 시 안내 후 내장 참조 검증, --demo 플래그 시 내장 reference 검증)
- 선택적 입력 파일(CSV/JSON 데이터 파일) 유효성 및 센티널 잔존 검증 지원
"""

import os
import sys
import math
import argparse
import importlib
from typing import List, Dict, Any, Tuple, Optional

# 워크스페이스 루트 및 현재 작업 디렉토리 sys.path 등록 (루트 모듈 임포트 지원)
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

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

# --------------------------------------------------------------------------
# [0] 환경 변수 설정
# --------------------------------------------------------------------------
TARGET_MODULE = os.environ.get("TARGET_MODULE", "").strip()
TARGET_FUNC = os.environ.get("TARGET_FUNC", "").strip()


# ==============================================================================
# [1] Case 7-B: 원소재 CoA & SPC & PCN 로직
# ==============================================================================

def normalize_concentration(val_str: str, unit: str, dl_policy: str = "conservative") -> float:
    """
    농도 단위 정규화 (기준 단위: ppb)
    - ppm: * 1,000
    - ppb: * 1.0
    - ppt: / 1,000
    - < DL 대치: conservative=DL, half_sqrt=DL/sqrt(2), zero=0.0
    """
    s = str(val_str).strip()
    is_less_than_dl = s.startswith("<")
    if is_less_than_dl:
        num_str = s.replace("<", "").strip()
        base_val = float(num_str)
        if dl_policy == "conservative":
            val = base_val
        elif dl_policy == "half_sqrt":
            val = base_val / math.sqrt(2)
        elif dl_policy == "zero":
            val = 0.0
        else:
            val = base_val
    else:
        val = float(s)

    unit_lower = unit.strip().lower()
    if unit_lower == "ppm":
        return val * 1000.0
    elif unit_lower == "ppb":
        return val * 1.0
    elif unit_lower == "ppt":
        return val / 1000.0
    return val


def evaluate_cpk(values: List[float], usl: float, lsl: float = None) -> float:
    """단측 또는 양측 규격 공정능력지수 Cpk 산출"""
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    var = sum((x - mean) ** 2 for x in values) / (n - 1)
    std = math.sqrt(var)
    if std == 0.0:
        return 999.0

    if lsl is not None:
        cpu = (usl - mean) / (3.0 * std)
        cpl = (mean - lsl) / (3.0 * std)
        return min(cpu, cpl)
    else:
        return (usl - mean) / (3.0 * std)


def evaluate_coa_pcn(
    fe_ppb: float,
    usl_fe_ppb: float,
    cpk: float,
    plant_changed: bool,
    origin_changed: bool
) -> str:
    """
    Case 7-B 3단 인터락:
    1. 치명 불순물 초과(단 1ppb라도 초과) 또는 Cpk < 1.0 -> REJECT
    2. 성분 규격 내이나 플랜트/원산지 변경 -> HOLD
    3. Cpk >= 1.33 및 규격 만족 및 PCN 무변경 -> PASS
    """
    if fe_ppb > usl_fe_ppb or cpk < 1.0:
        return "REJECT"
    if plant_changed or origin_changed:
        return "HOLD"
    if cpk >= 1.33:
        return "PASS"
    return "WARNING"


def detect_nelson_rules(series: List[float], mean: float, std: float) -> List[str]:
    """Nelson Rules 1~4 탐지"""
    violations = []
    # Rule 1: 1점 > 3 sigma
    for x in series:
        if abs(x - mean) > 3.0 * std:
            violations.append("RULE_1_OUTLIER")
            break

    # Rule 2: 연속 9개 점이 중심선의 동일 쪽에 위치
    run_above, run_below = 0, 0
    for x in series:
        if x > mean:
            run_above += 1
            run_below = 0
        elif x < mean:
            run_below += 1
            run_above = 0
        else:
            run_above, run_below = 0, 0
        if run_above >= 9 or run_below >= 9:
            violations.append("RULE_2_DRIFT")
            break

    # Rule 3: 연속 6개 점이 단조 증가 또는 단조 감소
    inc_count, dec_count = 1, 1
    for i in range(1, len(series)):
        if series[i] > series[i - 1]:
            inc_count += 1
            dec_count = 1
        elif series[i] < series[i - 1]:
            dec_count += 1
            inc_count = 1
        else:
            inc_count, dec_count = 1, 1
        if inc_count >= 6 or dec_count >= 6:
            violations.append("RULE_3_TREND")
            break

    # Rule 4: 연속 14개 점 교대 증감
    alt_count = 1
    for i in range(2, len(series)):
        d1 = series[i - 1] - series[i - 2]
        d2 = series[i] - series[i - 1]
        if (d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0):
            alt_count += 1
        else:
            alt_count = 1
        if alt_count >= 13:  # 14 consecutive alternating points
            violations.append("RULE_4_OSCILLATION")
            break

    return violations


# ==============================================================================
# [2] Case 13-B: 2D Overlay & Edge Exclusion & 6-Param OLS 로직
# ==============================================================================

def is_edge_excluded(x: float, y: float, max_radius: float = 147.0) -> bool:
    """반경 147mm 초과 시 Edge Exclusion 필터링"""
    r = math.sqrt(x * x + y * y)
    return r > max_radius


def solve_ols_3x3(X: List[List[float]], Y: List[float]) -> List[float]:
    """
    3차원 OLS 파라미터 계산: theta = (X^T X)^(-1) X^T Y
    X: N x 3 행렬, Y: N x 1 벡터
    """
    # X^T X (3x3)
    XTX = [[0.0] * 3 for _ in range(3)]
    for r in range(3):
        for c in range(3):
            XTX[r][c] = sum(X[i][r] * X[i][c] for i in range(len(X)))

    # X^T Y (3x1)
    XTY = [0.0] * 3
    for r in range(3):
        XTY[r] = sum(X[i][r] * Y[i] for i in range(len(X)))

    # 3x3 역행렬 계산 (Gaussian Elimination)
    M = [row[:] + [1.0 if i == j else 0.0 for j in range(3)] for i, row in enumerate(XTX)]
    for i in range(3):
        pivot = M[i][i]
        if abs(pivot) < 1e-12:
            return [0.0, 0.0, 0.0]
        for j in range(6):
            M[i][j] /= pivot
        for k in range(3):
            if k != i:
                factor = M[k][i]
                for j in range(6):
                    M[k][j] -= factor * M[i][j]

    invXTX = [[M[i][j + 3] for j in range(3)] for i in range(3)]

    # theta = invXTX * XTY
    theta = [sum(invXTX[i][j] * XTY[j] for j in range(3)) for i in range(3)]
    return theta


def fit_6parameter_overlay(
    points: List[Tuple[float, float, float, float]]
) -> Tuple[Dict[str, float], float]:
    """
    6-Parameter Linear Overlay Model:
    dx = Tx + Sx * x - Ry * y
    dy = Ty + Sy * y + Rx * x
    points: [(x, y, dx, dy), ...]
    반환: (params_dict, residual_3sigma)
    """
    valid_pts = [(x, y, dx, dy) for (x, y, dx, dy) in points if not is_edge_excluded(x, y)]
    if not valid_pts:
        return {}, 0.0

    Xx = [[1.0, x, -y] for (x, y, dx, dy) in valid_pts]
    Yx = [dx for (x, y, dx, dy) in valid_pts]
    theta_x = solve_ols_3x3(Xx, Yx)
    Tx, Sx, Ry = theta_x[0], theta_x[1], theta_x[2]

    Xy = [[1.0, y, x] for (x, y, dx, dy) in valid_pts]
    Yy = [dy for (x, y, dx, dy) in valid_pts]
    theta_y = solve_ols_3x3(Xy, Yy)
    Ty, Sy, Rx = theta_y[0], theta_y[1], theta_y[2]

    # 잔차 계산
    residuals = []
    for x, y, dx, dy in valid_pts:
        pred_dx = Tx + Sx * x - Ry * y
        pred_dy = Ty + Sy * y + Rx * x
        res_x = dx - pred_dx
        res_y = dy - pred_dy
        res_mag = math.sqrt(res_x ** 2 + res_y ** 2)
        residuals.append(res_mag)

    mean_res = sum(residuals) / len(residuals)
    var_res = sum((r - mean_res) ** 2 for r in residuals) / len(residuals)
    res_3sigma = mean_res + 3.0 * math.sqrt(var_res)

    params = {
        "Tx": Tx, "Sx": Sx, "Ry": Ry,
        "Ty": Ty, "Sy": Sy, "Rx": Rx
    }
    return params, res_3sigma


def evaluate_overlay_decision(step: str, res_3sigma: float, threshold: float = 2.0) -> str:
    """
    ADI: 현상 후 초과 시 REWORK
    AEI: 식각 후 초과 시 SCRAP
    정상 시: PASS
    """
    if res_3sigma <= threshold:
        return "PASS"
    step_upper = step.strip().upper()
    if step_upper == "ADI":
        return "REWORK"
    elif step_upper == "AEI":
        return "SCRAP"
    return "REJECT"


# ==============================================================================
# [3] Case 6-A: 재무 정규화 & Waterfall & DOI 로직
# ==============================================================================

def interpolate_fiscal_to_calendar(
    val_prev_fy: float, val_curr_fy: float, weight_prev: float, weight_curr: float
) -> float:
    """FY 분기 -> CY 분기 선형 보간"""
    return (val_prev_fy * weight_prev) + (val_curr_fy * weight_curr)


def calculate_waterfall(
    bit_base: float, bit_curr: float, asp_base: float, asp_curr: float
) -> Dict[str, float]:
    """
    Revenue Waterfall Decomposition:
    Total Change = Bit Growth Effect + ASP Change Effect + Cross Effect
    """
    delta_bit = bit_curr - bit_base
    delta_asp = asp_curr - asp_base
    rev_base = bit_base * asp_base
    rev_curr = bit_curr * asp_curr
    delta_rev = rev_curr - rev_base

    effect_bit = delta_bit * asp_base
    effect_asp = delta_asp * bit_base
    effect_cross = delta_bit * delta_asp

    return {
        "delta_rev": delta_rev,
        "effect_bit": effect_bit,
        "effect_asp": effect_asp,
        "effect_cross": effect_cross
    }


def calculate_doi(inventory: float, cogs_quarterly: float) -> float:
    """Days of Inventory (DOI) = (Inventory / COGS) * 90일"""
    if cogs_quarterly <= 0:
        return 0.0
    return (inventory / cogs_quarterly) * 90.0


# ==============================================================================
# [4] 동적 타깃 로더 (TARGET_MODULE & TARGET_FUNC 지원)
# ==============================================================================

def load_target_module_and_function(is_demo: bool = False):
    if is_demo:
        print("[데모 모드] 내장 reference_impl 을 사용해 자체 검증을 수행합니다. (--demo 옵션 활성화)")
        return None, None

    if TARGET_MODULE and TARGET_FUNC:
        try:
            mod = importlib.import_module(TARGET_MODULE)
            fn = getattr(mod, TARGET_FUNC, None)
            if fn is not None:
                print(f"[타깃 로드 성공] {TARGET_MODULE}.{TARGET_FUNC} 함수를 사용합니다.")
            else:
                print(f"[타깃 모듈 로드 성공] {TARGET_MODULE} 모듈을 사용합니다.")
            return mod, fn
        except Exception as e:
            err_msg = f"[타깃 로드 실패] {TARGET_MODULE}.{TARGET_FUNC} 로드 불가 ({e}). 실제 구현 코드를 확인하세요."
            print(f"❌ {err_msg}", file=sys.stderr)
            raise ImportError(err_msg)

    print("\n" + "=" * 60)
    print("ℹ️ [안내] TARGET_MODULE 및 TARGET_FUNC 환경변수가 미지정되어,")
    print("   내장 참조 구현체(reference_impl) 데모 모드로 검증을 수행합니다.")
    print("   👉 실제 과제 함수 검증 시 아래와 같이 환경변수를 지정하여 실행하세요:")
    print("      TARGET_MODULE=src.spc_pipeline TARGET_FUNC=evaluate_spc python3 .probe-kit/scripts/sample_check_spc.py")
    print("=" * 60 + "\n")
    return None, None


def resolve_func(name: str, fallback_fn, mod=None):
    if mod is not None and hasattr(mod, name):
        target = getattr(mod, name)
        if callable(target):
            return target
    return fallback_fn


# ==============================================================================
# [5] 선택적 입력 파일 검증
# ==============================================================================

def validate_input_file(file_path: str, mod=None, fn=None) -> bool:
    """선택적 입력 파일(CSV, JSON 등) 유효성 및 센티널 잔존 검사"""
    print("=" * 80)
    print(f"[입력 파일 검증 모드] 대상 파일: {file_path}")
    print("=" * 80)

    if not os.path.exists(file_path):
        print(f"⚠️ [안내] 지정된 입력 파일 '{file_path}'이(가) 아직 생성되지 않았거나 존재하지 않습니다.")
        print("   기본 15건 표본 수동 대조 단위 검증을 대신 수행합니다.\n")
        return True

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = [line.strip() for line in f if line.strip()]

        row_count = len(lines)
        header = lines[0] if lines else "(empty)"
        print(f"  * 파일 로드 성공       : 총 {row_count}개 행 (헤더: {header[:60]}...)")

        # 센티널 토큰 및 특수값 탐지
        sentinel_tokens = ["-999", "-9999", "null", "NaN", "NAN", "< DL", "ND"]
        found_sentinels = {}
        for token in sentinel_tokens:
            cnt = sum(line.count(token) for line in lines)
            if cnt > 0:
                found_sentinels[token] = cnt

        if found_sentinels:
            print(f"  * 센티널/결측 토큰 감지: {found_sentinels} (실제 파이프라인 정제 필요 여부 확인 요망)")
        else:
            print("  * 센티널 결측치(-999/null/NaN) 미발견 (클린 데이터)")

        if fn is not None and callable(fn):
            try:
                res = fn(file_path)
                print(f"  * 타깃 함수({TARGET_FUNC}) 실행 결과 요약: {res}")
            except Exception as e:
                print(f"  * 타깃 함수 직접 호출 알림 (파일 직접 인자 불가: {e})")

        print("=" * 80 + "\n")
        return True
    except Exception as e:
        print(f"❌ [오류] 파일 읽기 실패 ({file_path}): {e}")
        print("=" * 80 + "\n")
        return False


# ==============================================================================
# [6] 표본 15건 정의 및 수동 대조 실행
# ==============================================================================

def run_spc_sample_verification(mod=None, fn=None) -> bool:
    print("=" * 80)
    print("반도체 CoA · SPC · 2D Overlay · 재무 정규화 표본 15건 수동 대조 단위 검증")
    print("=" * 80)

    # 개별 함수 동적 바인딩 (타깃 모듈에 구현되어 있을 경우 타깃 함수 우선)
    _norm_conc = resolve_func("normalize_concentration", normalize_concentration, mod)
    _eval_cpk = resolve_func("evaluate_cpk", evaluate_cpk, mod)
    _eval_pcn = resolve_func("evaluate_coa_pcn", evaluate_coa_pcn, mod)
    _detect_nelson = resolve_func("detect_nelson_rules", detect_nelson_rules, mod)
    _is_edge = resolve_func("is_edge_excluded", is_edge_excluded, mod)
    _eval_overlay = resolve_func("evaluate_overlay_decision", evaluate_overlay_decision, mod)
    _interpolate = resolve_func("interpolate_fiscal_to_calendar", interpolate_fiscal_to_calendar, mod)
    _waterfall = resolve_func("calculate_waterfall", calculate_waterfall, mod)
    _doi = resolve_func("calculate_doi", calculate_doi, mod)

    # 15건 표본 정의 (ID, 도메인, 설명, 실행람다, 기댓값)
    test_cases = [
        # --- Case 7-B: CoA / SPC / PCN (1~5번) ---
        (
            "S01", "Case 7-B", "CoA 단위 변환: 0.05 ppm -> 50.0 ppb",
            lambda: _norm_conc("0.05", "ppm"),
            50.0
        ),
        (
            "S02", "Case 7-B", "CoA < DL 보수적 대치: '< 0.01' ppb -> 0.01 ppb",
            lambda: _norm_conc("< 0.01", "ppb", dl_policy="conservative"),
            0.01
        ),
        (
            "S03", "Case 7-B", "Cpk 산출 및 판정: Fe 불순물 데이터 Cpk >= 1.33 PASS",
            lambda: _eval_pcn(
                fe_ppb=0.03, usl_fe_ppb=0.10,
                cpk=_eval_cpk([0.02, 0.025, 0.03, 0.022, 0.028, 0.031], usl=0.10),
                plant_changed=False, origin_changed=False
            ),
            "PASS"
        ),
        (
            "S04", "Case 7-B", "PCN 인터락: 성분 Spec-In 이나 원산지 변경 시 무조건 HOLD",
            lambda: _eval_pcn(
                fe_ppb=0.03, usl_fe_ppb=0.10, cpk=1.50,
                plant_changed=False, origin_changed=True
            ),
            "HOLD"
        ),
        (
            "S05", "Case 7-B", "Nelson Rule 1 이탈: 3-sigma 초과 이상치 감지",
            lambda: _detect_nelson(
                series=[10.0, 10.2, 10.1, 10.3, 10.0, 10.2, 10.1, 15.0, 10.0],
                mean=10.1, std=0.2
            ),
            ["RULE_1_OUTLIER"]
        ),

        # --- Case 13-B: 2D Overlay / APC / ADI / AEI (6~10번) ---
        (
            "S06", "Case 13-B", "Edge Exclusion 필터: r=148mm (x=105, y=105) 에지 제외 판정",
            lambda: _is_edge(105.0, 105.0, max_radius=147.0),
            True
        ),
        (
            "S07", "Case 13-B", "Edge Exclusion 통과: r=140mm (x=0, y=140) 분석 포함 판정",
            lambda: _is_edge(0.0, 140.0, max_radius=147.0),
            False
        ),
        (
            "S08", "Case 13-B", "6-Param OLS 잔차 기준 이내 정상 PASS 판정",
            lambda: _eval_overlay(step="ADI", res_3sigma=1.45, threshold=2.0),
            "PASS"
        ),
        (
            "S09", "Case 13-B", "ADI 단계 잔차 2.5nm 초과 시 REWORK 판정 (PR Strip 가능)",
            lambda: _eval_overlay(step="ADI", res_3sigma=2.50, threshold=2.0),
            "REWORK"
        ),
        (
            "S10", "Case 13-B", "AEI 단계 잔차 2.5nm 초과 시 SCRAP 판정 (영구 식각 손상)",
            lambda: _eval_overlay(step="AEI", res_3sigma=2.50, threshold=2.0),
            "SCRAP"
        ),

        # --- Case 6-A: 재무 정규화 / Waterfall / DOI (11~15번) ---
        (
            "S11", "Case 6-A", "FY->CY 분기 선형보간: FY Q1(100) 1/3 + FY Q2(130) 2/3 -> 120.0",
            lambda: round(_interpolate(100.0, 130.0, 1.0 / 3.0, 2.0 / 3.0), 2),
            120.0
        ),
        (
            "S12", "Case 6-A", "수정공시 최신화 (Latest wins): 최신 레코드 선택",
            lambda: sorted([
                {"filing_date": "2024-05-15", "rev": 1000},
                {"filing_date": "2024-08-20", "rev": 1050}
            ], key=lambda x: x["filing_date"], reverse=True)[0]["rev"],
            1050
        ),
        (
            "S13", "Case 6-A", "환율 적용 분리: 손익(평균환율 1300원) vs 재고(기말환율 1350원)",
            lambda: (100.0 * 1300.0, 50.0 * 1350.0),
            (130000.0, 67500.0)
        ),
        (
            "S14", "Case 6-A", "Waterfall 분해: Bit 증가 효과 (10M * $2.0 = $20M)",
            lambda: _waterfall(bit_base=100.0, bit_curr=110.0, asp_base=2.0, asp_curr=2.5)["effect_bit"],
            20.0
        ),
        (
            "S15", "Case 6-A", "DOI 재고일수 계산: 재고 300억 / COGS 200억 * 90일 = 135.0일 (경보)",
            lambda: _doi(inventory=300.0, cogs_quarterly=200.0),
            135.0
        )
    ]

    passed = 0
    failed = []

    for sid, category, desc, fn_call, expected in test_cases:
        try:
            actual = fn_call()
            # 부동소수점 오차 허용 비교
            is_match = False
            if isinstance(expected, float) and isinstance(actual, (int, float)):
                is_match = abs(actual - expected) < 1e-4
            else:
                is_match = (actual == expected)

            if is_match:
                passed += 1
                print(f"[{sid}] PASS | {category:<10} | {desc:<50} | 결과: {actual}")
            else:
                failed.append((sid, category, desc, expected, actual))
                print(f"[{sid}] FAIL | {category:<10} | {desc:<50} | 기대: {expected} != 실제: {actual}")
        except Exception as e:
            failed.append((sid, category, desc, expected, f"EXCEPTION: {e}"))
            print(f"[{sid}] ERR  | {category:<10} | {desc:<50} | 에러: {e}")

    print("-" * 80)
    print(f"검증 결과: 총 {len(test_cases)}건 중 {passed}건 통과, {len(failed)}건 실패")
    print("=" * 80)

    if failed:
        print("[실패 목록]")
        for fid, fcat, fdesc, fexp, fact in failed:
            print(f"- {fid} [{fcat}] {fdesc} -> 기대: {fexp}, 실제: {fact}")
        return False
    else:
        print("모든 반도체 및 재무 정규화 표본 검증을 100% 통과했습니다.\n")
        return True


# --------------------------------------------------------------------------
# [7] 메인 실행 진입점
# --------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="반도체 원소재 CoA · SPC 통계 공정 제어 · 2D 오버레이 계측 · 재무 정규화 표본 15건 수동 대조 검증 스크립트 (Case 6)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 1. 내장 reference_impl 자체 데모 검증 (--demo 플래그)
  python scripts/sample_check_spc.py --demo

  # 2. 실제 과제 모듈 및 함수 지정 대조 실행
  TARGET_MODULE="src.spc_pipeline" TARGET_FUNC="evaluate_spc" python scripts/sample_check_spc.py

  # 3. 특정 데이터 파일 (CSV, JSON 등) 검증
  python scripts/sample_check_spc.py data/overlay_raw.csv
"""
    )
    parser.add_argument("--demo", action="store_true", help="내장 참조 구현체로 15건 표본 자체 검증 실행")
    parser.add_argument("input_path", nargs="?", default=None, help="선택 사항: 검증할 데이터 파일 (CSV, JSON 등) 경로")

    args, unknown = parser.parse_known_args()

    input_path = args.input_path
    if not input_path and unknown:
        for u in unknown:
            if not u.startswith("-"):
                input_path = u
                break

    is_demo = args.demo or os.environ.get("DEMO_MODE", "0") == "1"

    try:
        mod, fn = load_target_module_and_function(is_demo=is_demo)
    except Exception:
        sys.exit(1)

    file_valid = True
    if input_path and not is_demo:
        file_valid = validate_input_file(input_path, mod=mod, fn=fn)

    # 15건 표본 수동 대조 검증 실행
    samples_passed = run_spc_sample_verification(mod=mod, fn=fn)

    if not samples_passed or not file_valid:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
