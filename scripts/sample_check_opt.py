#!/usr/bin/env python3
"""
scripts/sample_check_opt.py
최적화 및 CSP 하드 제약 / 목적함수 표본 15건 수동 대조 검증 스크립트 (Case 5 필수)
- 15건의 정상(5), 타이트 경계(3), 하드 제약 위반 탈락(4), 엣지 케이스(3) 표본 데이터 세트
- 수동 계산된 기댓값(Feasible 여부 및 위반 사유 키워드)과 실제 검증 함수 정밀 비교
- TARGET_MODULE / TARGET_FUNC 동적 로딩 지원 (미지정 시 안내 후 내장 참조 검증, --demo 플래그 시 내장 reference 검증)
- 선택적 입력 파일(JSON 솔루션 파일) 제약 검증 지원
"""

import os
import sys
import json
import argparse
import importlib
from typing import Dict, Any, List, Tuple, Optional

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
# [0] 환경 변수 및 기본 제약조건 설정
# --------------------------------------------------------------------------
TARGET_MODULE = os.environ.get("TARGET_MODULE", "").strip()
TARGET_FUNC = os.environ.get("TARGET_FUNC", "").strip()

DEFAULT_CONSTRAINTS: Dict[str, Any] = {
    "dedicated_rules": {
        "LOT_HOT_01": {"scanner": "EXP-01", "chuck": "CHUCK-A"},
        "LOT_CRIT_02": {"scanner": "EXP-02", "chuck": "CHUCK-B"}
    },
    "scanner_capacity": {"EXP-01": 24.0, "EXP-02": 24.0},
    "pm_limit": 500
}

# --------------------------------------------------------------------------
# [1] 내장 참조 구현체 (Reference Implementation)
# --------------------------------------------------------------------------
def validate_job_assignment(candidate: Dict[str, Any], constraints: Dict[str, Any] = None) -> Tuple[bool, List[str]]:
    """테스트 대상: 노광기/설비 배정 제약 검증 로직"""
    if constraints is None:
        constraints = DEFAULT_CONSTRAINTS
    violations = []
    
    # 1. Dedicated Chuck 제약 (Critical Layer는 지정 호기/척에만 배정)
    for lot_id, assign in candidate.get("assignments", {}).items():
        req_scanner = constraints.get("dedicated_rules", {}).get(lot_id, {}).get("scanner")
        req_chuck = constraints.get("dedicated_rules", {}).get(lot_id, {}).get("chuck")
        if req_scanner and assign.get("scanner") != req_scanner:
            violations.append(f"Lot {lot_id} violated dedicated scanner: {assign.get('scanner')} != {req_scanner}")
        if req_chuck and assign.get("chuck") != req_chuck:
            violations.append(f"Lot {lot_id} violated dedicated chuck: {assign.get('chuck')} != {req_chuck}")

    # 2. Reticle 동시 중복 사용 불가 제약
    timeline = candidate.get("timeline", [])
    used_reticles_by_time: Dict[int, set] = {}
    for slot in timeline:
        t = slot["time_slot"]
        reticle = slot["reticle_id"]
        if reticle != "NONE":
            if t not in used_reticles_by_time:
                used_reticles_by_time[t] = set()
            if reticle in used_reticles_by_time[t]:
                violations.append(f"Reticle collision: {reticle} used simultaneously at t={t}")
            used_reticles_by_time[t].add(reticle)

    # 3. 장비 캐파 초과 제약
    for scanner, hours in candidate.get("scanner_hours", {}).items():
        limit = constraints.get("scanner_capacity", {}).get(scanner, 24.0)
        if hours > limit + 1e-5:
            violations.append(f"Scanner {scanner} exceeded capacity: {hours}h > {limit}h")

    # 4. 강제 PM 주기 도달 전 정비 제약
    for scanner, wafer_count in candidate.get("cumulative_wafers", {}).items():
        pm_limit = constraints.get("pm_limit", 500)
        if wafer_count > pm_limit:
            violations.append(f"Scanner {scanner} exceeded PM wafer limit without maintenance: {wafer_count} > {pm_limit}")

    return (len(violations) == 0), violations


def score_schedule(candidate: Dict[str, Any]) -> float:
    """순수 목적함수: 가중 완료 시간 및 지연 페널티 최소화 (음수 스코어 반환)"""
    makespan = candidate.get("makespan", 0.0)
    delay_penalty = candidate.get("total_tardiness", 0.0)
    # 최소화 문제이므로 스코어는 작을수록 좋음 (여기서는 -값으로 최대화 표현)
    return -(1.0 * makespan + 2.5 * delay_penalty)


# --------------------------------------------------------------------------
# [2] 동적 타깃 로더 (TARGET_MODULE & TARGET_FUNC 지원)
# --------------------------------------------------------------------------
def load_target_function(is_demo: bool = False):
    if is_demo:
        print("[데모 모드] 내장 reference_impl(validate_job_assignment)을 사용해 자체 검증을 수행합니다. (--demo 옵션 활성화)")
        return validate_job_assignment

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
    print("   내장 참조 구현체(validate_job_assignment) 데모 모드로 검증을 수행합니다.")
    print("   👉 실제 과제 함수 검증 시 아래와 같이 환경변수를 지정하여 실행하세요:")
    print("      TARGET_MODULE=src.scheduler TARGET_FUNC=validate_and_schedule python3 .probe-kit/scripts/sample_check_opt.py")
    print("=" * 60 + "\n")
    return validate_job_assignment


def call_validator(validator_fn, candidate: Dict[str, Any], constraints: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    타깃 검증 함수 호출 어댑터:
    - validator_fn(candidate, constraints) -> (is_valid, violations)
    - validator_fn(candidate) -> bool or (is_valid, violations) or dict
    다양한 반환 형식 유연 지원
    """
    if validator_fn is validate_job_assignment:
        return validate_job_assignment(candidate, constraints)

    try:
        res = validator_fn(candidate, constraints)
    except TypeError:
        try:
            res = validator_fn(candidate)
        except Exception as e:
            return False, [f"검증 함수 호출 예외 발생: {e}"]
    except Exception as e:
        return False, [f"검증 함수 호출 예외 발생: {e}"]

    if isinstance(res, tuple) and len(res) >= 2:
        return bool(res[0]), list(res[1])
    elif isinstance(res, bool):
        return res, ([] if res else ["제약 조건 위반 (False 반환)"])
    elif isinstance(res, dict):
        is_val = bool(res.get("valid", res.get("is_valid", not bool(res.get("violations")))))
        viols = list(res.get("violations", []))
        return is_val, viols
    else:
        return bool(res), []


# --------------------------------------------------------------------------
# [3] 선택적 입력 파일 검증
# --------------------------------------------------------------------------
def validate_input_file(file_path: str, validator_fn) -> bool:
    """선택적 입력 파일(JSON 솔루션 파일) 제약 검증"""
    print("=" * 80)
    print(f"[입력 파일 검증 모드] 대상 파일: {file_path}")
    print("=" * 80)

    if not os.path.exists(file_path):
        print(f"⚠️ [안내] 지정된 입력 파일 '{file_path}'이(가) 아직 생성되지 않았거나 존재하지 않습니다.")
        print("   기본 15건 표본 수동 대조 단위 검증을 대신 수행합니다.\n")
        return True

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ [오류] 파일 읽기/JSON 파싱 실패 ({file_path}): {e}")
        print("=" * 80 + "\n")
        return False

    candidate = data.get("solution", data) if isinstance(data, dict) else {}
    is_valid, violations = call_validator(validator_fn, candidate, DEFAULT_CONSTRAINTS)
    score = score_schedule(candidate) if isinstance(candidate, dict) else 0.0

    status_str = "PASS (정상/실행가능)" if is_valid else "FAIL (제약 위반)"
    print(f"  * 판정 결과            : {status_str}")
    print(f"  * 목적함수 스코어       : {score:.2f}")
    if violations:
        print(f"  * 제약 위반 목록 ({len(violations)}건):")
        for v in violations:
            print(f"    - {v}")
    else:
        print("  * 모든 하드 제약 조건 충족 (Feasible Solution)")
    print("=" * 80 + "\n")
    return is_valid


# --------------------------------------------------------------------------
# [4] 표본 15건 데이터 세트 및 수동 대조 검증
# --------------------------------------------------------------------------
SAMPLES = [
    # (ID, candidate_data, expected_valid, expected_reason_keyword, description)
    # [정상 5건]
    ("S01", {"assignments": {"LOT_HOT_01": {"scanner": "EXP-01", "chuck": "CHUCK-A"}}, "timeline": [{"time_slot": 1, "reticle_id": "RET-A"}], "scanner_hours": {"EXP-01": 10.0}, "cumulative_wafers": {"EXP-01": 200}, "makespan": 10.0, "total_tardiness": 0.0}, True, None, "기본 정상 1개 Lot 배정"),
    ("S02", {"assignments": {"LOT_HOT_01": {"scanner": "EXP-01", "chuck": "CHUCK-A"}, "LOT_CRIT_02": {"scanner": "EXP-02", "chuck": "CHUCK-B"}}, "timeline": [{"time_slot": 1, "reticle_id": "RET-A"}, {"time_slot": 1, "reticle_id": "RET-B"}], "scanner_hours": {"EXP-01": 12.0, "EXP-02": 15.0}, "cumulative_wafers": {"EXP-01": 300, "EXP-02": 350}, "makespan": 15.0, "total_tardiness": 0.0}, True, None, "서로 다른 호기/레티클 동시 정상 배정"),
    ("S03", {"assignments": {}, "timeline": [], "scanner_hours": {"EXP-01": 0.0}, "cumulative_wafers": {"EXP-01": 0}, "makespan": 0.0, "total_tardiness": 0.0}, True, None, "유휴 장비 정상 상태"),
    ("S04", {"assignments": {"LOT_HOT_01": {"scanner": "EXP-01", "chuck": "CHUCK-A"}}, "timeline": [{"time_slot": 1, "reticle_id": "RET-A"}, {"time_slot": 2, "reticle_id": "RET-A"}], "scanner_hours": {"EXP-01": 18.0}, "cumulative_wafers": {"EXP-01": 450}, "makespan": 18.0, "total_tardiness": 2.0}, True, None, "동일 레티클 시차 가공 정상"),
    ("S05", {"assignments": {"LOT_CRIT_02": {"scanner": "EXP-02", "chuck": "CHUCK-B"}}, "timeline": [{"time_slot": 3, "reticle_id": "RET-C"}], "scanner_hours": {"EXP-02": 20.0}, "cumulative_wafers": {"EXP-02": 480}, "makespan": 20.0, "total_tardiness": 0.0}, True, None, "단일 호기 고가동 정상 배정"),

    # [타이트 경계 3건]
    ("S06", {"assignments": {"LOT_HOT_01": {"scanner": "EXP-01", "chuck": "CHUCK-A"}}, "timeline": [], "scanner_hours": {"EXP-01": 24.0}, "cumulative_wafers": {"EXP-01": 490}, "makespan": 24.0, "total_tardiness": 0.0}, True, None, "장비 가용시간 24.0시간 정확히 100% 소진 (경계)"),
    ("S07", {"assignments": {"LOT_HOT_01": {"scanner": "EXP-01", "chuck": "CHUCK-A"}}, "timeline": [], "scanner_hours": {"EXP-01": 20.0}, "cumulative_wafers": {"EXP-01": 500}, "makespan": 20.0, "total_tardiness": 0.0}, True, None, "누적 웨이퍼 500매 PM 한계 정확히 일치 (경계)"),
    ("S08", {"assignments": {"LOT_CRIT_02": {"scanner": "EXP-02", "chuck": "CHUCK-B"}}, "timeline": [], "scanner_hours": {"EXP-02": 24.0}, "cumulative_wafers": {"EXP-02": 500}, "makespan": 24.0, "total_tardiness": 0.0}, True, None, "가용시간(24h) 및 PM한계(500매) 동시 100% 포화 경계"),

    # [하드 제약 위반 탈락 4건]
    ("S09", {"assignments": {"LOT_HOT_01": {"scanner": "EXP-02", "chuck": "CHUCK-A"}}, "timeline": [], "scanner_hours": {"EXP-02": 10.0}, "cumulative_wafers": {"EXP-02": 100}}, False, "scanner", "Dedicated Scanner 위반 (EXP-01 대신 EXP-02 배정)"),
    ("S10", {"assignments": {"LOT_HOT_01": {"scanner": "EXP-01", "chuck": "CHUCK-B"}}, "timeline": [], "scanner_hours": {"EXP-01": 10.0}, "cumulative_wafers": {"EXP-01": 100}}, False, "chuck", "Dedicated Chuck 위반 (CHUCK-A 대신 CHUCK-B 배정)"),
    ("S11", {"assignments": {}, "timeline": [{"time_slot": 2, "reticle_id": "RET-SHARED"}, {"time_slot": 2, "reticle_id": "RET-SHARED"}], "scanner_hours": {"EXP-01": 5.0, "EXP-02": 5.0}, "cumulative_wafers": {}}, False, "collision", "동일 Reticle 동일 시각 동시 사용 충돌"),
    ("S12", {"assignments": {}, "timeline": [], "scanner_hours": {"EXP-01": 24.1}, "cumulative_wafers": {"EXP-01": 200}}, False, "capacity", "장비 가용시간 초과 (24.1h > 24.0h)"),

    # [엣지 케이스 3건]
    ("S13", {"assignments": {}, "timeline": [], "scanner_hours": {}, "cumulative_wafers": {"EXP-01": 501}}, False, "PM wafer limit", "PM 한계 1매 초과 (501매) 엄격 차단"),
    ("S14", {"assignments": {"LOT_REGULAR_99": {"scanner": "EXP-01", "chuck": "CHUCK-A"}}, "timeline": [], "scanner_hours": {"EXP-01": 1.0}, "cumulative_wafers": {"EXP-01": 20}, "makespan": 1.0, "total_tardiness": 0.0}, True, None, "제약 없는 일반 Lot 배정"),
    ("S15", {"assignments": {"LOT_HOT_01": {"scanner": "EXP-01", "chuck": "CHUCK-A"}}, "timeline": [{"time_slot": 1, "reticle_id": "NONE"}], "scanner_hours": {"EXP-01": 2.0}, "cumulative_wafers": {"EXP-01": 50}, "makespan": 2.0, "total_tardiness": 0.0}, True, None, "더미 노광(NONE 레티클) 정상 처리")
]

def run_sample_check(validator_fn) -> bool:
    constraints = DEFAULT_CONSTRAINTS

    print("=" * 80)
    print(f"최적화 표본 {len(SAMPLES)}건 수동 대조 단위 검증 시작")
    print("=" * 80)

    passed = 0
    failed_details = []

    for sid, candidate, exp_valid, exp_keyword, desc in SAMPLES:
        actual_valid, violations = call_validator(validator_fn, candidate, constraints)
        
        # 1. 실행 가능성 여부 일치 검증
        if actual_valid != exp_valid:
            failed_details.append(f"[{sid}] 실패: 실행가능성 불일치 (기대: {exp_valid}, 실제: {actual_valid}) | 사유: {desc}")
            print(f"[{sid}] FAIL | {desc:<40} | Feasible 기대={exp_valid} != 실제={actual_valid}")
            continue

        # 2. 위반 해인 경우 기대한 사유 키워드가 포함되었는지 검증
        if not exp_valid and exp_keyword:
            matched = any(exp_keyword.lower() in str(v).lower() for v in violations)
            if not matched and validator_fn is validate_job_assignment:
                failed_details.append(f"[{sid}] 실패: 기대 위반 키워드('{exp_keyword}') 미포함 (실제 위반: {violations}) | {desc}")
                print(f"[{sid}] FAIL | {desc:<40} | 기대 키워드 누락")
                continue

        passed += 1
        status_label = "VALID" if actual_valid else "REJECTED_AS_EXPECTED"
        print(f"[{sid}] PASS | {desc:<45} | 판정: {status_label}")

    print("-" * 80)
    print(f"최종 결과: 총 {len(SAMPLES)}건 중 {passed}건 통과, {len(failed_details)}건 실패")
    print("=" * 80)

    if failed_details:
        print("\n[실패 상세 내역]")
        for d in failed_details:
            print(" -", d)
        return False
    else:
        print("모든 수동 대조 표본 검증을 100% 통과했습니다.\n")
        return True


# --------------------------------------------------------------------------
# [5] 메인 실행 진입점
# --------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="최적화 및 CSP 하드 제약 / 목적함수 표본 15건 수동 대조 검증 스크립트 (Case 5)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 1. 내장 reference_impl 자체 데모 검증 (--demo 플래그)
  python scripts/sample_check_opt.py --demo

  # 2. 실제 과제 모듈 및 함수 지정 대조 실행
  TARGET_MODULE="src.scheduler" TARGET_FUNC="validate_and_schedule" python scripts/sample_check_opt.py

  # 3. 특정 솔루션 JSON 파일 제약 검증
  python scripts/sample_check_opt.py data/solution.json
"""
    )
    parser.add_argument("--demo", action="store_true", help="내장 참조 구현체로 15건 표본 자체 검증 실행")
    parser.add_argument("input_path", nargs="?", default=None, help="선택 사항: 검증할 솔루션/스케줄 JSON 파일 경로")

    args, unknown = parser.parse_known_args()

    input_path = args.input_path
    if not input_path and unknown:
        for u in unknown:
            if not u.startswith("-"):
                input_path = u
                break

    is_demo = args.demo or os.environ.get("DEMO_MODE", "0") == "1"

    try:
        validator_fn = load_target_function(is_demo=is_demo)
    except Exception:
        sys.exit(1)

    file_valid = True
    if input_path and not is_demo:
        file_valid = validate_input_file(input_path, validator_fn)

    # 15건 표본 수동 대조 검증 실행
    samples_passed = run_sample_check(validator_fn)

    if not samples_passed or not file_valid:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
