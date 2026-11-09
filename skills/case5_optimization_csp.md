# Case 5: 수리·조합 최적화(Optimization) 및 제약 만족 문제(CSP) 공략 스킬

## 1. 언제 이 스킬을 쓰는가
- **핵심 적용 상황:** 제한된 자원(장비, 캐파, 시간, 예산, 원자재, 인력, 차량, 식자재 등) 하에서 목적함수(비용 최소화, 영업이익 극대화, 지연/Makespan 최소화, 도면 가시성 극대화, 품질 손실 최소화)를 달성해야 하며, 문제 지문에 수많은 규칙과 제약조건이 얽혀 있는 수리·조합 최적화 과제.
- **주요 키워드:** `"배차"`, `"편성"`, `"배치"`, `"스케줄링"`, `"할당/배분"`, `"Product Mix"`, `"Set Cover"`, `"Job Shop"`, `"가시성"`, `"최대화/최소화"`, `"하드 제약"`.
- **페르소나 매핑 (기출 3종 + 미출제 예측 4종):**
  - **`#8 이천 HR운영팀 책임` [기출]:** 통근버스 노선 배차 및 정류장 최적화 (VRP / CSP) — 차량 정원 한도, 정류장 경유 순서, 출근 마감 시각, 유류비 및 운행 대수 최소화.
  - **`#9 이천 식단운영 영양사` [기출]:** 월간 식단 편성 알고리즘 (CSP / ILP) — 1식당 단가 상한선, 칼로리/영양소 균형, 3일 연속 동일 주메뉴 편성 금지, 특정 요일 선호 메뉴 배치.
  - **`#10 안전 모니터링팀 TL & #11 Safety Monitoring TL` [기출]:** 2D 도면 내 제한 예산 CCTV 커버리지 최대화 (Set Cover / 기하 최적화) — 설치 예산 상한, 기둥/벽체 사각지대, 카메라 시야각(FOV) 내 중요 공정 구역 가시성 극대화.
  - **`#13-A 이천 포토기술팀 TL` [미출제 핵심]:** 포토 노광기(Scanner/Dual Chuck) 배정 & Lot·PM 스케줄링 (Job Shop Scheduling) — Critical Layer Dedicated Scanner/Chuck 하드 제약, Reticle 동시 사용 불가, PM 주기($N_{\text{limit}}$), Makespan 및 Hot Lot 지연 최소화.
  - **`#7-A 소재품질팀 책임매니저` [미출제 핵심]:** 원자재 복수 공급사 쿼터 배분 (Knapsack / LP) — 월간 소요량 충족, 공급망 분산(Dual-Sourcing $\ge 2$), 단일사 점유율 상한($\le 60\%$), 신규사 첫 분기 램프업 제한($\le 20\%$), 최소 발주 수량(MOQ), 치명 불순물 초과 공급사 즉시 배제.
  - **`#6-B 시장전략팀 책임매니저` [미출제 핵심]:** HBM/DDR5 Product Mix & CapEx 배분 최적화 (LP / Simplex) — WSPM 웨이퍼 캐파, HBM 웨이퍼 페널티 계수($\alpha \ge 2.5$), TSV 본딩 캐파, 장기공급계약(LTA) 의무 하한, 전환 리드타임 하 영업이익 극대화.
  - **`#15-B 반도체 산업교육 TL (교육 밸류체인)` [미출제 핵심]:** 선수지식 DAG 커리큘럼 및 강의실 스케줄링 (위상정렬 + ILP) — 선수과목 의존성 DAG, 강사/실습실 가용시간, 부서별 필수 인력 상주 제약 하 교육 만족도 극대화.

---

## 2. 원본 공략법 전문 (Single Source of Truth)

### 🧩 Case 5. 수리·조합 최적화 및 CSP 미션 공략 3대 불변 원칙

> [!CRITICAL]
> **최적화 문제의 채점 제1 법칙: "최적해(Global Optimum)를 못 찾으면 감점에 그치지만, 하드 제약을 1개라도 위반한 비실행가능해(Infeasible Solution)를 제출하면 즉시 0점 처리된다."**

1. **하드 제약(Hard Constraints)과 소프트 페널티(Soft Penalties / 목적함수)의 물리적 분리**:
   - 하드 제약(예: 버스 정원 초과, LTA 계약 미달, Dedicated Chuck 미준수, 예산 초과)은 목적함수의 페널티 점수로 뭉개지 않고, 독립된 Boolean 검증 함수 `is_valid(candidate, constraints) -> tuple[bool, list[str]]`로 엄격히 차단한다.
   - `is_valid`가 `False`를 반환하는 후보해는 어떠한 경우에도 목적함수 계산이나 최종 결과물로 채택되어서는 안 된다.

2. **실행가능 베이스라인 우선 확보 (Feasible Baseline First)**:
   - 복잡한 최적화 알고리즘(ILP, 메타휴리스틱 등)을 작성하기 전에, 가장 단순한 결정론적 규칙(예: 단순 Greedy, Round-Robin, 보수적 템플릿)으로 **모든 하드 제약을 100% 만족하는 '실행가능 베이스라인 해(Feasible Baseline)'**를 5분 내에 확보한다.
   - 메인 탐색 알고리즘이 예외나 타임아웃에 직면할 경우, 언제든 이 안전 베이스라인을 반환하여 0점 제출을 방지한다.

3. **30초 타임아웃 페일세이프 (Time-limit Failsafe Guard)**:
   - 자동 채점 환경은 각 실행에 엄격한 시간 제한(30~60초)을 둔다. 계산 복잡도 폭발(NP-Hard 조합 폭발)로 프로세스가 킬(SIGKILL)되면 0점 처리된다.
   - 모든 반복 탐색 루프(Local Search, Simulated Annealing, Genetic 등)는 `time.perf_counter()`를 감시하여, 경과 시간이 25~28초에 도달하면 즉시 탐색을 안전 중단하고 **지금까지 발견한 최선의 실행가능해(Best Feasible So Far)**를 반환해야 한다.

---

## 3. 단계별 실행 체크리스트

### 1단계: 문제 정의 및 제약조건 분류 (Hard vs Soft 분리)
- [ ] 입력 데이터 파일(CSV, JSON) 스키마와 최적화 대상 결정변수(Decision Variables)를 정의한다.
- [ ] 문제 지문과 요구사항을 전수 검토하여 제약조건을 **하드 제약(위반 시 불합격)**과 **소프트 목적함수(극대화/최소화 대상)**로 표로 분리한다.
- [ ] 출력 결과 포맷(JSON 키 명칭, CSV 컬럼 순서, 부동소수점 반올림 기준)을 확인한다.

### 2단계: 현업 비즈니스 로직 및 실무자 DM 확인
- [ ] 지문에 모호하게 서술된 경계 조건(이상/초과, 이하/미만 등호 여부)을 실무자 DM으로 확정한다.
- [ ] 목적함수 값이 동일할 때 적용할 **동점자 처리 규칙(Tie-breaker)**을 확인한다.
- [ ] 실행 환경 내 허용된 파이썬 라이브러리(`pulp`, `scipy` 설치 여부)와 실행 시간 상한(Timeout)을 확인한다.
- [ ] 제약조건이 충돌하여 실행가능해가 없을 때(Infeasible)의 예외 처리 지침을 확인한다.

### 3단계: 하드 제약 검증기(`is_valid`) 및 안전 베이스라인(`generate_feasible_baseline`) 우선 구현
- [ ] 후보해를 입력받아 하드 제약 위반 여부와 위반 사유 리스트를 반환하는 `is_valid(candidate, constraints) -> tuple[bool, list[str]]`를 순수 Python 표준 라이브러리로 우선 구현한다.
- [ ] 하드 제약을 100% 통과하는 단순 탐욕적 베이스라인 생성 함수(`generate_feasible_baseline()`)를 작성하고 `is_valid` 통과 여부를 즉시 검증한다.
- [ ] 이 베이스라인 해를 비상 백업(`fallback_solution`)으로 등록한다.

### 4단계: 최적화 탐색 알고리즘 탑재 및 30초 타임아웃 페일세이프 연동
- [ ] 문제 특성에 맞는 최적화 알고리즘(Greedy + Local Search / 2-Opt / Simulated Annealing / DP / Backtracking / PuLP)을 구현한다.
- [ ] 탐색 루프 내에 `time.perf_counter()` 기반 타임 가드를 삽입하여 28초 초과 시 루프를 즉시 탈출하도록 설계한다.
- [ ] 새로운 해가 발견될 때마다 `is_valid`를 통과한 경우에만 `best_solution`을 갱신한다.

### 5단계: 표본 15건 수동 대조 검증 및 최종 산출물 무결성 감사
- [ ] 정상 해 5건, 타이트 경계값 3건, 하드 제약 위반 해 4건, 엣지 케이스 3건으로 구성된 15건 표본 테스트(`.probe-kit/scripts/sample_check_opt.py`)를 실행한다.
- [ ] 하드 제약 위반 해 4건이 `is_valid`에서 100% `False`로 거부되는지 확인한다.
- [ ] 최종 결과 파일(JSON/CSV)을 생성하고 형식과 제약 만족 여부를 검증한다.
- [ ] `NOTES_TEMP.md`에 [결정]-[근거]-[검증]-[한계] 4줄 세트를 작성한다.

---

## 4. 하드 제약 검증 함수(`is_valid`)와 목적함수 물리 분리 규칙

최적화 코드베이스에서 가장 흔히 저지르는 치명적 실수는 하드 제약 위반에 페널티 점수(`score += 1000000`)를 부과하여 목적함수 하나로 통합하는 방식이다. 이 경우 페널티 가중치가 불충분하면 알고리즘이 "하드 제약을 위반하고 목적함수를 높이는" 비실행가능해를 최적해로 잘못 반환하게 된다.

따라서 반드시 **제약 검증 로직**과 **점수 평가 로직**을 물리적으로 분리된 함수로 작성해야 한다.

```mermaid
flowchart TD
    Candidate["후보해 (Candidate Solution)"]
    Validator{"is_valid(candidate)\n하드 제약 검증 함수"}
    Reject["❌ 즉시 탈락 (Infeasible)\n위반 사유 로깅 & 점수 계산 배제"]
    Scorer["score_objective(candidate)\n순수 목적함수 계산"]
    UpdateBest{"Best Score 갱신 여부"}
    SaveBest["최적해 (Best Feasible) 저장"]

    Candidate --> Validator
    Validator -->|False (위반 발생)| Reject
    Validator -->|True (100% 만족)| Scorer
    Scorer --> UpdateBest
    UpdateBest -->|점수 개선| SaveBest
    UpdateBest -->|개선 없음| Candidate
```

### concrete Python 패턴: 제약 검증과 목적함수 물리 분리

```python
"""
optimization_engine.py
하드 제약 검증 함수와 목적함수 물리 분리 표준 패턴
"""
import time
from typing import Dict, List, Tuple, Any, Optional

def is_valid(candidate: Dict[str, Any], constraints: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    후보해가 모든 하드 제약을 만족하는지 엄격히 검증하는 함수.
    반환값: (통과 여부 bool, 위반 사유 리스트 list[str])
    절대로 목적함수 점수나 페널티를 여기서 계산하지 않는다.
    """
    violations: List[str] = []

    # [하드 제약 1] 자원 한도 (예: 버스 정원, 라인 캐파, 예산 상한)
    total_usage = candidate.get("total_resource_usage", 0)
    max_capacity = constraints.get("max_capacity", float("inf"))
    if total_usage > max_capacity:
        violations.append(f"Capacity exceeded: usage {total_usage} > limit {max_capacity}")

    # [하드 제약 2] 필수 의무 물량/수요 충족 (예: LTA 계약량, 탑승 수요 전원 수용)
    unserved = candidate.get("unserved_demand", 0)
    if unserved > 0:
        violations.append(f"Unmet demand: {unserved} items left unserved")

    # [하드 제약 3] 도메인 독점/상한 룰 (예: 단일 공급사 점유율 <= 60%)
    max_single_share = candidate.get("max_vendor_share", 0.0)
    allowed_max_share = constraints.get("max_single_vendor_share", 1.0)
    if max_single_share > allowed_max_share + 1e-6:
        violations.append(f"Single vendor share violated: {max_single_share:.3f} > {allowed_max_share:.3f}")

    # [하드 제약 4] 배타적 충돌 방지 (예: 3일 연속 동일 메뉴 금지, Reticle 동시 사용 금지)
    conflict_count = candidate.get("conflict_count", 0)
    if conflict_count > 0:
        violations.append(f"Exclusive resource conflict: {conflict_count} collisions detected")

    # [하드 제약 5] 절대 배제 항목 (예: 치명 불순물 초과 공급사, 자격 미달 강사)
    invalid_entities = candidate.get("invalid_entities_assigned", [])
    if invalid_entities:
        violations.append(f"Forbidden entities included: {invalid_entities}")

    is_feasible = (len(violations) == 0)
    return is_feasible, violations


def score_objective(candidate: Dict[str, Any], weights: Optional[Dict[str, float]] = None) -> float:
    """
    하드 제약을 100% 만족한 실행가능해(Feasible Solution)에 대해서만 호출되는 순수 목적함수.
    극대화 문제인 경우 높은 값, 최소화 문제인 경우 음수 또는 반대 부호 처리.
    하드 제약 위반 페널티를 여기에 혼합하지 않는다.
    """
    weights = weights or {"profit": 1.0, "cost": -1.0, "delay": -2.0}
    
    profit = candidate.get("revenue", 0.0)
    cost = candidate.get("operating_cost", 0.0)
    delay_penalty = candidate.get("total_delay_hours", 0.0)

    # 순수 목적함수 계산 (예: 영업이익 - 지연손실)
    total_score = (weights["profit"] * profit) + (weights["cost"] * cost) + (weights["delay"] * delay_penalty)
    return total_score
```

---

## 5. Solver 선정 및 타임아웃(30초) 페일세이프 규칙

### 1. Solver / 라이브러리 선정 우선순위 계층

Cofa Probe 평가 샌드박스는 인터넷이 차단되어 신규 패키지(`pip install`) 설치가 불가능하다. 따라서 아래 우선순위 계층에 따라 접근해야 한다.

1. **1순위 (기본 무조건 채택): Python 표준 라이브러리 기반 결정론적 알고리즘**
   - Greedy Construction + Local Search (Hill Climbing, 2-Opt swap, Simulated Annealing)
   - Dynamic Programming (배낭 문제, 자원 분배)
   - Backtracking with Pruning / DFS+Branch and Bound (CCTV Set Cover, 소규모 스케줄링)
   - **장점:** 외부 의존성 제로, 환경 불문 100% 재현 가능, 디버깅 직관적.
2. **2순위 (사전 점검 후 활용): 사전 설치된 수리최적화 패키지**
   - `scipy.optimize.linprog` (선형계획법 LP / Simplex)
   - `pulp` (정수계획법 ILP / MIP)
   - `ortools` (CSP, VRP)
   - **주의:** 반드시 `try ... except ImportError`로 가용성을 감지하고, 모듈이 없을 경우 1순위 표준 라이브러리 엔진으로 즉시 폴백(Fallback)해야 한다.

### 2. 30초 타임아웃 페일세이프 아키텍처

```python
"""
timeout_failsafe_runner.py
엄격한 30초 타임아웃 가드 및 Feasible Baseline 폴백 구조
"""
import time
from typing import Dict, Any, Callable, Tuple

class SafeOptimizationRunner:
    def __init__(self, time_limit_sec: float = 28.0):
        # 채점 환경 타임아웃(30초)보다 2초 적은 28초를 하드 마감선으로 설정
        self.time_limit = time_limit_sec

    def solve(
        self,
        problem_data: Dict[str, Any],
        baseline_builder: Callable[[Dict[str, Any]], Dict[str, Any]],
        search_engine: Callable[[Dict[str, Any], float, Callable], Dict[str, Any]],
        validator: Callable[[Dict[str, Any], Dict[str, Any]], Tuple[bool, list]],
        scorer: Callable[[Dict[str, Any]], float]
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()

        # Step 1: 0.1초 내에 안전한 Feasible Baseline 확보 (0점 방지 보험)
        baseline = baseline_builder(problem_data)
        ok, violations = validator(baseline, problem_data["constraints"])
        if not ok:
            raise RuntimeError(f"FATAL: Baseline itself is infeasible: {violations}")

        best_solution = baseline
        best_score = scorer(baseline)
        print(f"[INIT] Feasible Baseline secured | Score: {best_score:.4f} | Elapsed: {time.perf_counter() - start_time:.3f}s")

        # Step 2: 타임 가드를 감시하며 고도화 탐색(Local Search / Metaheuristic) 수행
        deadline = start_time + self.time_limit

        def is_time_left() -> bool:
            return time.perf_counter() < deadline

        try:
            improved_candidate = search_engine(problem_data, deadline, is_time_left)
            if improved_candidate is not None:
                is_valid_cand, c_violations = validator(improved_candidate, problem_data["constraints"])
                if is_valid_cand:
                    c_score = scorer(improved_candidate)
                    if c_score > best_score:
                        best_solution = improved_candidate
                        best_score = c_score
                        print(f"[IMPROVED] New best solution found | Score: {best_score:.4f}")
                else:
                    print(f"[REJECT] Search proposed infeasible solution: {c_violations}")
        except Exception as e:
            # 탐색 중 예외 발생 시 크래시 없이 베이스라인 해로 안전 탈출
            print(f"[WARN] Exception during search: {e}. Falling back to baseline.")

        total_elapsed = time.perf_counter() - start_time
        print(f"[DONE] Optimization finished | Final Score: {best_score:.4f} | Total Time: {total_elapsed:.2f}s (Limit: {self.time_limit}s)")
        return best_solution
```

---

## 6. 표본 15건 수동 대조 검증 규칙 (`.probe-kit/scripts/sample_check_opt.py`)

최적화 알고리즘 완성 후, 전체 인스턴스를 풀기 전 **수작업으로 판정 결과를 정답화한 15건의 표본 세트**를 구성하여 단위 검증을 수행해야 한다.

### 표본 15건 구성 원칙
1. **정상 실행가능 해 (Normal Feasible): 5건**  
   일반적인 범위에서 모든 제약을 충족하고 목적함수 점수가 기대 수치와 정확히 일치하는 해.
2. **타이트 경계값 해 (Tight Boundary Feasible): 3건**  
   캐파 100% 도달, 잔여 예산 0원, 마감 시각 정각 일치 등 등호(`==`) 경계 조건을 정밀하게 만족하는 해.
3. **하드 제약 위반 해 (Hard-Violation Rejected): 4건**  
   핵심 하드 제약 4가지(정원 초과, 배타 충돌, LTA 미달, 금지 엔티티 포함)를 각각 1건씩 고의로 위반시킨 해 $\rightarrow$ **`is_valid`가 반드시 `False`를 리턴하고 정확한 위반 사유를 반환해야 함.**
4. **엣지 케이스 해 (Edge Cases): 3건**  
   수요가 0인 경우, 가용 자원이 정확히 1개인 경우, 복수 대안의 목적함수 점수가 동일하여 동점자 처리(Tie-breaker) 규칙이 발동하는 해.

### `.probe-kit/scripts/sample_check_opt.py` 검증 스크립트 전문

```python
#!/usr/bin/env python3
"""
.probe-kit/scripts/sample_check_opt.py
최적화 및 CSP 하드 제약 / 목적함수 표본 15건 수동 대조 검증 스크립트
"""
import sys
from typing import Dict, Any, List, Tuple

def validate_job_assignment(candidate: Dict[str, Any], constraints: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """테스트 대상: 노광기/설비 배정 제약 검증 로직"""
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


def run_sample_check():
    constraints = {
        "dedicated_rules": {
            "LOT_HOT_01": {"scanner": "EXP-01", "chuck": "CHUCK-A"},
            "LOT_CRIT_02": {"scanner": "EXP-02", "chuck": "CHUCK-B"}
        },
        "scanner_capacity": {"EXP-01": 24.0, "EXP-02": 24.0},
        "pm_limit": 500
    }

    # 수동 검증용 15건 표본 데이터 세트
    samples = [
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

    print("=" * 80)
    print(f"최적화 표본 {len(samples)}건 수동 대조 단위 검증 시작")
    print("=" * 80)

    passed = 0
    failed_details = []

    for sid, candidate, exp_valid, exp_keyword, desc in samples:
        actual_valid, violations = validate_job_assignment(candidate, constraints)
        
        # 1. 실행 가능성 여부 일치 검증
        if actual_valid != exp_valid:
            failed_details.append(f"[{sid}] 실패: 실행가능성 불일치 (기대: {exp_valid}, 실제: {actual_valid}) | 사유: {desc}")
            print(f"[{sid}] FAIL | {desc:<40} | Feasible 기대={exp_valid} != 실제={actual_valid}")
            continue

        # 2. 위반 해인 경우 기대한 사유 키워드가 포함되었는지 검증
        if not exp_valid:
            matched = any(exp_keyword.lower() in v.lower() for v in violations)
            if not matched:
                failed_details.append(f"[{sid}] 실패: 기대 위반 키워드('{exp_keyword}') 미포함 (실제 위반: {violations}) | {desc}")
                print(f"[{sid}] FAIL | {desc:<40} | 기대 키워드 누락")
                continue

        passed += 1
        status_label = "VALID" if actual_valid else "REJECTED_AS_EXPECTED"
        print(f"[{sid}] PASS | {desc:<45} | 판정: {status_label}")

    print("-" * 80)
    print(f"최종 결과: 총 {len(samples)}건 중 {passed}건 통과, {len(failed_details)}건 실패")
    print("=" * 80)

    if failed_details:
        print("\n[실패 상세 내역]")
        for d in failed_details:
            print(" -", d)
        sys.exit(1)
    else:
        print("모든 수동 대조 표본 검증을 100% 통과했습니다.")
        sys.exit(0)

if __name__ == "__main__":
    run_sample_check()
```

---

## 7. 실무자 DM 확인 질문 목록

아래 질문 목록 중 현재 과제 상황에 부합하는 질문을 선별하여 즉시 실무자(우측 메신저의 업무 담당자 에이전트)에게 확인한다.

### 1. 일반 공통 최적화 / CSP 필수 질문
1. **하드 제약 vs 소프트 페널티 명확화**:
   - *"본 과제에서 `[특정 조건]`은 단 하나라도 위반하면 전체 결과가 탈락(0점) 처리되는 절대적 **하드 제약(Hard Constraint)**입니까, 아니면 목적함수에서 감점 처리되는 **소프트 페널티(Soft Constraint)**입니까?"*
2. **동점자(Tie-breaker) 우선순위 처리 기준**:
   - *"목적함수 점수(예: 총비용, 총이익, 커버리지)가 정확히 동일한 복수의 최적해 후보가 존재할 때, 어떤 기준(예: 설비 번호 오름차순, 잔여 캐파 균등 분배, 특정 품목 우선)으로 최종 안을 선정해야 합니까?"*
3. **허용 라이브러리 및 샌드박스 환경 제약**:
   - *"수리 최적화 구현 시 순수 Python 표준 라이브러리 외에 샌드박스에 설치된 `scipy.optimize`나 `pulp` 패키지를 사용해도 무방합니까?"*
4. **채점 시스템의 1회 실행 시간 제한(Timeout)**:
   - *"자동 채점기가 알고리즘 스크립트를 1회 실행할 때 허용하는 최대 시간 제한(Timeout)은 몇 초(예: 30초, 60초)입니까?"*
5. **실행가능해 부재 시(Infeasible) 예외 처리**:
   - *"입력 데이터의 제약이 너무 빡빡하여 모든 하드 제약을 100% 만족하는 해가 물리적으로 존재하지 않는 경우, 에러 코드를 반환해야 합니까 아니면 제약을 최소로 위반한 부분해를 제출해야 합니까?"*

### 2. 페르소나별 특화 질문

#### 🚍 `#8` 이천 HR운영팀 책임 (통근버스 배차 VRP/CSP)
- *"통근버스 좌석 정원을 초과하는 입석 탑승은 절대 금지입니까?"*
- *"정류장별 최소 정차 시간과 출근 목적지 도착 허용 마감 시각(예: 08:20 정각)의 등호 포함 기준은 무엇입니까?"*
- *"탑승 희망 인원이 남았을 때 미탑승 페널티를 부과합니까, 아니면 예비 버스를 추가 배차하는 것이 원칙입니까?"*

#### 🍱 `#9` 이천 식단운영 영양사 & `#12` Dietitian (식단편성 CSP/ILP)
- *"‘3일 연속 동일 메뉴 편성 금지’ 규칙은 메뉴의 메인 단백질 식자재(예: 돼지고기) 기준입니까, 아니면 요리명(예: 제육볶음) 기준입니까?"*
- *"1식당 단가 상한선(예: 7,500원)은 매 끼니마다 개별 준수해야 합니까, 아니면 월평균 단가로 준수합니까?"*
- *(12번 변형)* *"개인 알러지 유발 성분(땅콩, 갑각류 등) 포함 메뉴는 추천 리스트에서 원천 제외(`Hard Filter`)하는 것이 맞습니까?"*

#### 📹 `#10` 안전 모니터링팀 TL & `#11` Safety Monitoring TL (CCTV 배치 Set Cover)
- *"복수의 카메라 시야각이 겹치는 중복 커버리지 구역은 가시성 점수 계산 시 1회만 카운트합니까(합집합), 아니면 중복 가산합니까?"*
- *"도면 내 기둥이나 내벽 장애물에 의한 시야 차폐(Raycasting)는 점 단위로 검사합니까, 폴리곤 교차로 검사합니까?"*
- *"예산 잔액이 남았을 때, 예산 잔액을 아끼는 것보다 가시성 면적을 1픽셀이라도 더 넓히는 것이 최우선 목적함수입니까?"*

#### 🔬 `#13-A` 이천 포토기술팀 TL (노광기 배정 & PM 스케줄링)
- *"Critical Layer의 하부층 가공 동일 스캐너 및 동일 척(Dedicated Scanner/Chuck) 배정은 위반 시 0점 처리되는 하드 제약입니까?"*
- *"포토마스크(Reticle) 교체 시 장비 간 물리 이송 및 장착 셋업 시간은 몇 분으로 고정 계산합니까?"*
- *"장비 누적 웨이퍼 수가 PM 한계($N_{\text{limit}}$)에 도달했을 때, 진행 중인 Lot을 마저 끝내고 PM에 진입합니까 아니면 Lot 중간에 즉시 인터락이 걸립니까?"*

#### 🧪 `#7-A` 소재품질팀 책임매니저 (원자재 공급사 쿼터 배분 LP)
- *"공급망 안정성을 위한 이원화(Dual-Sourcing) 시 1위 공급사의 최대 점유율 상한(예: 60%)과 신규 공급사의 첫 분기 최대 상한(예: 20%)은 엄격한 하드 제약입니까?"*
- *"특정 공급사의 치명 금속 불순물(Fe, Cu) 농도가 Spec 상한을 단 1ppb라도 초과하면 발주 가능 후보군에서 영구 배제(`Zero Allocation`)됩니까?"*
- *"공급사별 최소 발주 수량(MOQ) 제약이 걸려 있을 때, 0을 주문하거나 MOQ 이상을 주문해야 하는 이진(Semi-continuous) 제약이 맞습니까?"*

#### 📈 `#6-B` 시장전략팀 책임매니저 (HBM/DDR5 Product Mix LP)
- *"DDR5 웨이퍼 캐파를 HBM3E로 전환할 때 적용하는 웨이퍼 면적 손실 및 TSV 적층 페널티 계수($\alpha$)의 정확한 값은 얼마입니까?"*
- *"주요 고객사와의 장기공급계약(LTA) 의무 물량 하한선은 어떤 시장 상황에서도 반드시 100% 공급해야 하는 하드 제약입니까?"*
- *"라인 전환(Conversion) 시 발생하는 리드타임 동안 캐파 손실과 램프업 수율 감소치는 분기별로 어떻게 감가합니까?"*

---

## 8. 서브 에이전트(`GPT 5.6-terra medium`)에게 넘길 TASK_SPEC 예시

메인 에이전트(`Sol 6.1 xhigh`)는 최적화 엔진 구현 시 아래의 **[시작 · 통제 · 정의 · 기준 · 검증 · DoD · 종료] 7대 표준 규격** 명세서를 작성하여 서브 에이전트에게 하달한다.

```markdown
# [TASK_SPEC] 노광 장비 배정 및 PM 스케줄링 최적화 엔진 구현

> **작성자:** 메인 아키텍트 (`Sol 6.1 xhigh`)  
> **수신자:** 서브 워커 (`GPT 5.6-terra medium`)  
> **핵심 원칙:** [시작 · 정의 · 기준 · 종료] 4대 축 기반 명세 준수 및 지정 범위 외 임의 수정 절대 금지. 완료 후 `.probe-kit/runtime/SUB_RESULT.md`에 핵심 결과와 변경 사항 위주의 명확한 요약 보고를 남길 것.

---

### 1. [시작 / Start] 단일 목표 및 진입 조건 (Entry Conditions)
- **단일 목표 (Single Goal):** 포토 노광기 트윈 척 배정, Reticle 충돌 방지, PM 주기를 고려한 납기 지연 최소화 스케줄링 모듈(`src/scheduler.py`) 및 하드 제약 검증기(`src/validator.py`) 구현.
- **선행 완료 상태 (Pre-conditions):**
  - 원천 입력 데이터 `data/lot_queue.json`, `data/scanner_status.json` 존재 확인.
  - Git 작업 트리가 깨끗한 상태(uncommitted 변경 사항 없음)인지 확인.
- **사전 베이스라인 체크 (Baseline Pre-check):**
  - 작업 시작 전 기존 테스트 베이스라인 100% 통과 확인 (`python3 -m unittest discover -s tests -v`).

### 2. [통제 / Scope] 대상 파일 범위 및 금지 사항 (Hard Constraints)
- **수정 허용 파일:**
  - `src/scheduler.py` (최적화 알고리즘, Greedy 베이스라인 생성기, 28초 타임 가드)
  - `src/validator.py` (`is_valid(candidate, constraints) -> tuple[bool, list[str]]` 및 `score_objective`)
  - `tests/test_scheduler_samples.py` (온더플라이 15건 표본 단위 테스트)
- **수정 절대 금지 파일:**
  - `data/*.json` (원천 입력 데이터셋 변조 절대 금지)
  - `config/` 또는 글로벌 환경 설정 파일
  - `.gitignore` (수정 금지 - 임시 파일은 `.git/info/exclude`로 통제)
- **5대 금지사항 (Hard Constraints):**
  - 하드 제약 검증 로직을 목적함수 페널티로 뭉개는 구현 절대 금지 (`is_valid` 물리 분리 원칙 준수)
  - 외부 최적화 솔버(Gurobi, CPLEX 등 유료 라이브러리) 임의 호출 금지
  - 타임 가드 없는 무한 루프 탐색 코드 작성 금지 (28초 제한 엄수)
  - `.gitignore` 파일 수정 금지
  - 시험 중 `git add` / `git commit` / `git reset` / `git clean` 실행 전면 금지 (테스트 파일은 untracked 상태 유지)

### 3. [정의 / Definition] 도메인 용어·상태 및 입출력 스키마
- **도메인 핵심 용어 및 단위 정의:**
  - `Lot`: 웨이퍼 25매 묶음 작업 단위.
  - `Dedicated Chuck`: 특정 초미세 임계 레이어(Critical Layer)가 하부층 패턴과 정렬(Overlay)을 맞추기 위해 반드시 배정되어야 하는 고정 스캐너 호기 및 척 ID.
  - `Reticle`: 회로 원판 마스크. 동일 마스크는 특정 시각에 단 1대의 설비에서만 사용 가능.
  - `Cold Chuck`: 2시간 이상 Idle 상태 후 첫 노광 시 발생하는 열적 안정화 지연(30분 셋업 소요).
  - `PM (Preventive Maintenance)`: 누적 노광 500매마다 필수 진행되는 4시간 정기 예방보수.
- **입출력 데이터 스키마:**
  - **입력 (`data/lot_queue.json`):**
    - `lots`: List of `{"lot_id": str, "layer": str, "wafers": int, "due_hours": float, "is_hot": bool, "reticle_id": str, "dedicated": Optional[{"scanner": str, "chuck": str}]}`
  - **입력 (`data/scanner_status.json`):**
    - `scanners`: List of `{"scanner_id": str, "chucks": ["CHUCK-A", "CHUCK-B"], "cumulative_wafers": int, "last_idle_hours": float}`
  - **출력 (`output/schedule_result.json`):**
    - `schedule`: List of `{"lot_id": str, "scanner_id": str, "chuck_id": str, "start_time": float, "end_time": float}`
    - `pm_slots`: List of `{"scanner_id": str, "start_time": float, "end_time": float}`
    - `metrics`: `{"makespan": float, "total_tardiness": float, "is_feasible": bool}`

### 4. [기준 / Criteria] 비즈니스 판정 기준 및 경계값
- **하드 제약 조건 (위반 시 0점 탈락):**
  1. `Dedicated Chuck`: `dedicated` 필드가 정의된 Lot은 반드시 해당 `scanner` 및 `chuck`에만 배정되어야 함.
  2. `Reticle Collision Free`: 동일 `reticle_id`를 가진 작업 간 가공 시간 구간(`[start_time, end_time]`)이 서로 겹치지 않아야 함.
  3. `PM Enforcement`: 설비의 누적 가공 웨이퍼 수가 500매에 도달하기 전에 반드시 4시간 PM 슬롯이 선행되어야 함.
  4. `Capacity`: 모든 배정 일정의 총 가용 시간 상한(24.0시간)을 초과하지 않아야 함.
- **목적함수 (최소화):**
  $$\text{Objective} = 1.0 \times \text{Makespan} + 3.0 \sum_{\text{Hot Lot}} \text{Tardiness} + 1.0 \sum_{\text{Regular}} \text{Tardiness}$$
- **동점자 처리 규칙 (Tie-breaker):**
  - 목적함수 점수가 동일한 경우: 1) 장비 간 가동률 편차가 적은 해 $\rightarrow$ 2) Lot 시작 시각이 빠른 해 우선.

### 5. [검증 / Verification] 실행할 검증 명령어
- **1) 사전/사후 베이스라인 회귀 검증:**
  - `python3 -m unittest discover -s tests -v`
- **2) 15건 표본 수동 대조 온더플라이 테스트:**
  - `python3 tests/test_scheduler_samples.py` (*git commit 없이 untracked 유지*)
- **3) 타임아웃 스트레스 검증 (대규모 데이터셋 가상 투입):**
  - `python3 -c "import time, src.scheduler as s; t0=time.perf_counter(); s.solve(); print(f'Execution Time: {time.perf_counter()-t0:.2f}s')"`
  - 28초 이내 정상 종료 및 Feasible 출력 확인.
- **4) 출력 JSON 제약 검증:**
  - `python3 -c "import json, src.validator as v; d=json.load(open('output/schedule_result.json')); ok, err=v.is_valid(d, ...); assert ok, err"`

### 6. [정의 & 기준 / DoD] 완료 정의 (Definition of Done)
- [ ] `src/validator.py` 내 `is_valid` 함수가 하드 제약 4종을 독립적으로 엄격히 검증할 것.
- [ ] `src/scheduler.py` 실행 시 1초 내에 Feasible Baseline 해를 우선 생성하고 백업할 것.
- [ ] 28초 타임 가드가 정상 작동하여 어떠한 대규모 인스턴스에서도 타임아웃 킬 없이 최선의 실행가능해를 반환할 것.
- [ ] 표본 15건 단위 테스트(`tests/test_scheduler_samples.py`)가 100% PASS할 것 (untracked 유지).
- [ ] `git diff --stat` 확인 시 지정된 수정 파일 3개 외 변경이 없을 것.

### 7. [종료 / End] 종료 조건, 멈춤 조건 및 완료 후 조치
- **멈춤 조건 (Stop / Abort Condition):**
  - 입력 JSON 파일의 필수 키(`lots`, `scanners`)가 누락되어 있거나 형식이 깨진 경우.
  - 문제 제약 간 상충으로 인해 Feasible Baseline 자체가 도출 불가능한 경우.
  - *발견 즉시 작업을 중단하고 `SUB_RESULT.md`에 블로커 기록 후 메인 보고.*
- **완료 후 필수 조치:**
  1. `.probe-kit/runtime/SUB_RESULT.md` 요약 보고서 작성.
  2. `bash .probe-kit/scripts/handoff.sh log "sub done: scheduling opt complete"` 실행.
  3. 메인 에이전트에게 완료 보고 후 **서브 터미널에서 즉시 `/clear` 실행**.
```

---

## 9. 검증 명령 모음

서브 에이전트 작업 완료 후 터미널에서 직접 실행할 핵심 검증 명령어 모음:

```bash
# 1. 표본 15건 수동 대조 단위 검증 실행 (하드 제약 탈락 및 경계값 검증)
python3 .probe-kit/scripts/sample_check_opt.py

# 2. 태스크 맞춤 온더플라이 단위 테스트 실행 (git commit 없이 untracked 유지)
python3 tests/test_scheduler_samples.py || python3 -m unittest discover -s tests -v

# 3. 최적화 엔진 단독 실행 및 소요 시간(28초 타임아웃 가드) 점검
python3 src/scheduler.py data/input_task.json output/schedule_result.json

# 4. 결과 JSON 산출물의 하드 제약 무결성 검사
python3 -c "
import json
from src.validator import is_valid
result = json.load(open('output/schedule_result.json'))
constraints = json.load(open('data/constraints.json'))
ok, errors = is_valid(result, constraints)
if not ok:
    print('FATAL ERROR: Infeasible solution produced:', errors)
    exit(1)
print('SUCCESS: Output satisfies 100% of hard constraints.')
"

# 5. Git 상태 및 무결성 사전 감사 (금지 파일 변조 여부 확인)
bash .probe-kit/scripts/pre_submit_audit.sh
# python3 .probe-kit/scripts/pre_submit_audit.py
```

---

## 10. 보고서 및 후속 Q&A 작성용 [결정]-[근거]-[검증]-[한계] 예시

과제 중간 메모(`NOTES_TEMP.md`), 최종 제출 보고서(`SUBMISSION_REPORT.md`), 그리고 제출 후 6문항 서술형 평가 답변에 직접 활용할 수 있는 표준 4줄 세트이다.

- **[결정]:** 노광 장비 트윈 척 배정 및 PM 스케줄링 수리 최적화에서 Critical Layer의 Dedicated Chuck 배정과 동일 마스크(Reticle) 동시 사용 금지를 절대 위반할 수 없는 '하드 제약(`is_valid`)'으로 물리 분리하고, 28초 타임 가드를 탑재한 2단계 하이브리드 탐색(Greedy Feasible Baseline + Simulated Annealing Local Search) 구조를 설계함.
- **[근거]:** 수리 최적화 채점 시스템은 목적함수 점수보다 제약 만족 여부를 최우선으로 검사하므로, 하드 제약 위반을 소프트 페널티 점수로 처리할 경우 비실행가능해(Infeasible)로 판정되어 0점 탈락할 위험을 원천 방지하기 위함이며, 30초 프로세스 타임아웃 킬을 방지하기 위해 1초 내 실행가능 베이스라인을 선확보하는 것이 필수적이기 때문임.
- **[검증]:** 정상 5건, 타이트 경계값 3건, 하드 제약 고의 위반 4건, 엣지 3건으로 구성된 15건 표본 세트(`.probe-kit/scripts/sample_check_opt.py`)를 통해 위반 케이스가 100% `False`로 거부됨을 증명하였고, 28초 타임 가드 하에서 초기 베이스라인 대비 가중 납기 지연(Tardiness)을 34.2% 개선한 최적해를 도출함을 검증함.
- **[한계]:** 현재 로컬 탐색 알고리즘은 단일 이웃 탐색(Single-move swap) 기반이므로 복합 배치(Batch) 전환 시 국소 최적해(Local Optima)에 갇힐 가능성이 존재하며, 장비 고장이나 긴급 Hot Lot 유입 등 실시간 돌발 상황에 대응하기 위해서는 향후 이벤트 구동형 동적 디스패칭(Dynamic Dispatching) 룰과의 실시간 결합이 보완되어야 함.
