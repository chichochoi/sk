#!/usr/bin/env python3
"""
scripts/sample_check_template.py
데이터 과제용 표본 수동 대조 단위 테스트 템플릿 (Case 1 & Case 5 필수)
- 12~20건의 정상, 중복, 취소, 결측, 경계값 표본 데이터 구성
- 수동 계산된 기댓값(EXPECTED)과 실제 처리 함수 출력값 정밀 비교
- 단계별(원본 -> 중복제거 -> 취소제외 -> 결측제외) 건수 추적 로깅
- 불일치 시 직관적인 diff 출력
- TARGET_MODULE / TARGET_FUNC 동적 로딩 지원 (미지정 시 Fail 보고, --demo 플래그 시 내장 reference_impl 검증)
"""

import os
import sys
import unittest
import importlib
import difflib
import json
from typing import List, Dict, Any

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
# [0] 실행 모드 확인 (--demo 플래그 또는 DEMO_MODE 환경변수)
#     - unittest.main() 인자 충돌 방지를 위해 sys.argv에서 사전 분리
# --------------------------------------------------------------------------
IS_DEMO = "--demo" in sys.argv or os.environ.get("DEMO_MODE", "0") == "1"
if "--demo" in sys.argv:
    while "--demo" in sys.argv:
        sys.argv.remove("--demo")

# --------------------------------------------------------------------------
# [1] 테스트 대상 모듈 및 함수 설정 (환경 변수 또는 코드 수정)
# --------------------------------------------------------------------------
TARGET_MODULE = os.environ.get("TARGET_MODULE", "").strip()
TARGET_FUNC = os.environ.get("TARGET_FUNC", "").strip()

# --------------------------------------------------------------------------
# [2] 내장 참조 구현체 (Reference Implementation)
#     - 비즈니스 로직:
#       1) order_id 기준 중복 제거 (최초 발생 건 유지)
#       2) status == 'cancelled' (대소문자 무관) 제외
#       3) amount 결측치(None, "", -999, NaN) 제외
#       4) customer_id별 유효 주문 금액(amount) 합산
# --------------------------------------------------------------------------
def reference_impl(orders: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    주문 목록 정제 및 고객별 금액 합산 참조 함수
    단계별 필터링 카운트를 표준 출력으로 기록합니다.
    """
    total_raw = len(orders)

    # 1. 중복 order_id 제거 (최초 주문 유지)
    seen_order_ids = set()
    deduped_orders = []
    dup_count = 0
    for order in orders:
        oid = order.get("order_id")
        if oid in seen_order_ids:
            dup_count += 1
            continue
        seen_order_ids.add(oid)
        deduped_orders.append(order)

    # 2. 취소 상태(cancelled) 제외
    active_orders = []
    cancelled_count = 0
    for order in deduped_orders:
        status = str(order.get("status", "")).strip().lower()
        if status in ("cancelled", "cancel"):
            cancelled_count += 1
            continue
        active_orders.append(order)

    # 3. amount 결측치 제외
    valid_orders = []
    missing_amount_count = 0
    missing_tokens = {None, "", "none", "nan", "null", "-999", "-999.0", -999, -999.0}

    for order in active_orders:
        amt_raw = order.get("amount")
        if amt_raw in missing_tokens:
            missing_amount_count += 1
            continue
        try:
            amt = float(amt_raw)
            if amt in (-999.0,):
                missing_amount_count += 1
                continue
            valid_orders.append((order["customer_id"], amt))
        except (ValueError, TypeError):
            missing_amount_count += 1
            continue

    # 단계별 건수 로깅 출력
    print("\n" + "=" * 60)
    print("[파이프라인 단계별 처리 건수 로깅]")
    print(f"  1. 원본 데이터 수              : {total_raw}건")
    print(f"  2. 중복 order_id 제거 후       : {len(deduped_orders)}건 (중복 제거: {dup_count}건)")
    print(f"  3. 취소 상태(cancelled) 제외 후  : {len(active_orders)}건 (취소 제외: {cancelled_count}건)")
    print(f"  4. amount 결측치 제외 후 유효 건수: {len(valid_orders)}건 (결측 제외: {missing_amount_count}건)")
    print("=" * 60)

    # 4. 고객별 합계 집계
    result: Dict[str, float] = {}
    for cid, amt in valid_orders:
        result[cid] = round(result.get(cid, 0.0) + amt, 2)

    return result

# --------------------------------------------------------------------------
# [3] 표본 데이터 (정상 7 + 중복 2 + 취소 3 + 결측 3 + 경계값 포함 = 총 15건)
# --------------------------------------------------------------------------
SAMPLES: List[Dict[str, Any]] = [
    # --- [정상 건: 6건] ---
    {
        "order_id": "ORD_001",
        "customer_id": "CUST_001",
        "amount": 10000.0,
        "status": "COMPLETED",
        "timestamp": "2026-10-28 09:00:00"
    },
    {
        "order_id": "ORD_002",
        "customer_id": "CUST_001",
        "amount": 25000.0,
        "status": "CONFIRMED",
        "timestamp": "2026-10-28 09:15:00"
    },
    {
        "order_id": "ORD_003",
        "customer_id": "CUST_002",
        "amount": 5000.0,
        "status": "COMPLETED",
        "timestamp": "2026-10-28 09:30:00"
    },
    {
        "order_id": "ORD_004",
        "customer_id": "CUST_002",
        "amount": 150000.0,  # 정상 대용량 금액
        "status": "SHIPPED",
        "timestamp": "2026-10-28 10:00:00"
    },
    {
        "order_id": "ORD_005",
        "customer_id": "CUST_003",
        "amount": 0.0,       # 경계값: 0원 결제 (이벤트 무료 주문, 결측치 아님)
        "status": "COMPLETED",
        "timestamp": "2026-10-28 10:30:00"
    },
    {
        "order_id": "ORD_006",
        "customer_id": "CUST_003",
        "amount": 7700.50,   # 경계값: 소수점 포함 금액
        "status": "COMPLETED",
        "timestamp": "2026-10-28 11:00:00"
    },

    # --- [중복 유입 건: 2건] (이미 유입된 order_id 재유입 -> 제외되어야 함) ---
    {
        "order_id": "ORD_001",  # ORD_001 중복 (금액이 달라도 최초 건 유지 원칙)
        "customer_id": "CUST_001",
        "amount": 99999.0,
        "status": "COMPLETED",
        "timestamp": "2026-10-28 11:15:00"
    },
    {
        "order_id": "ORD_003",  # ORD_003 동일 내용 네트워크 재전송 중복
        "customer_id": "CUST_002",
        "amount": 5000.0,
        "status": "COMPLETED",
        "timestamp": "2026-10-28 11:20:00"
    },

    # --- [취소 상태 건: 3건] (status == cancelled / cancel -> 집계 제외) ---
    {
        "order_id": "ORD_007",
        "customer_id": "CUST_001",
        "amount": 50000.0,
        "status": "CANCELLED",  # 대문자 CANCELLED
        "timestamp": "2026-10-28 11:30:00"
    },
    {
        "order_id": "ORD_008",
        "customer_id": "CUST_002",
        "amount": 30000.0,
        "status": "cancelled",  # 소문자 cancelled
        "timestamp": "2026-10-28 11:45:00"
    },
    {
        "order_id": "ORD_011",
        "customer_id": "CUST_002",
        "amount": 42000.0,
        "status": "cancel",     # 약어 cancel 필터링 검증
        "timestamp": "2026-10-28 12:30:00"
    },

    # --- [결측치 건: 3건] (amount가 None, "", 센티널 -999 -> 집계 제외) ---
    {
        "order_id": "ORD_009",
        "customer_id": "CUST_001",
        "amount": None,         # Null / None 결측
        "status": "COMPLETED",
        "timestamp": "2026-10-28 12:00:00"
    },
    {
        "order_id": "ORD_010",
        "customer_id": "CUST_003",
        "amount": -999.0,       # 시스템 센티널 결측 표기 (-999)
        "status": "COMPLETED",
        "timestamp": "2026-10-28 12:15:00"
    },
    {
        "order_id": "ORD_012",
        "customer_id": "CUST_001",
        "amount": "",           # 공백 문자열("") 결측치
        "status": "COMPLETED",
        "timestamp": "2026-10-28 12:45:00"
    },

    # --- [추가 정상 및 경계값 건: 1건] (CUST_003 소수점 가산 검증) ---
    {
        "order_id": "ORD_013",
        "customer_id": "CUST_003",
        "amount": 1299.50,      # 경계값: 소수점 부동소수점 합산 정밀도 검증 (7700.50 + 1299.50 = 9000.0)
        "status": "COMPLETED",
        "timestamp": "2026-10-28 13:00:00"
    },
]

# --------------------------------------------------------------------------
# [4] 수동 검산 기댓값 (EXPECTED)
#     - 계산 근거:
#       * CUST_001: ORD_001(10,000) + ORD_002(25,000) = 35,000.0
#                   (ORD_001 중복 제외, ORD_007 취소 제외, ORD_009 결측 제외, ORD_012 공백결측 제외)
#       * CUST_002: ORD_003(5,000) + ORD_004(150,000) = 155,000.0
#                   (ORD_003 중복 제외, ORD_008 취소 제외, ORD_011 약어 cancel 제외)
#       * CUST_003: ORD_005(0.0) + ORD_006(7,700.50) + ORD_013(1,299.50) = 9,000.0
#                   (ORD_010 센티널 -999 결측 제외)
# --------------------------------------------------------------------------
EXPECTED: Dict[str, float] = {
    "CUST_001": 35000.0,
    "CUST_002": 155000.0,
    "CUST_003": 9000.0,
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
    print("      TARGET_MODULE=src.pipeline.aggregator TARGET_FUNC=clean_orders python scripts/sample_check_template.py")
    print("=" * 60 + "\n")
    return reference_impl

# --------------------------------------------------------------------------
# [6] 단위 테스트 케이스 및 불일치 diff 출력
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
                f"원인 점검: 중복 제거 누락, 취소 상태 필터 누락, 결측치(-999/None) 처리 누락 확인 요망"
            )

        # 각 고객별 개별 검증
        for cust_id, exp_val in EXPECTED.items():
            self.assertIn(cust_id, actual, f"고객 ID {cust_id} 누락")
            self.assertAlmostEqual(
                actual[cust_id], exp_val, places=2,
                msg=f"고객 {cust_id} 집계 금액 불일치: 실제 {actual[cust_id]} != 기댓값 {exp_val}"
            )

        print("\n[검증 통과] 15건 표본(정상/중복/취소/결측/경계값) 수동 기댓값과 100% 일치합니다!\n")

if __name__ == "__main__":
    unittest.main(verbosity=2)
