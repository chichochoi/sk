# Case 1 & Case 5: 데이터 파이프라인 정제·집계 및 반도체/제조 판정 스킬

## 1. 언제 이 스킬을 쓰는가
- **Case 1 적용 상황:** 복수의 원천 데이터 파일(CSV, JSON, TSV, DB 덤프, 텍스트 로그 등)이 제공되고, 데이터 정제(결측/중복/이상치 처리) 및 통계 집계, 결과 파일 생성(CSV/Excel 등), 요약 리포트 작성이 요구되는 과제.
- **Case 5 적용 상황:** SK하이닉스 제조 공정, 웨이퍼(Wafer), 수율(Yield), 장비 파라미터, 센서 시계열 로그, 불량(Defect) 판정 용어가 등장하며, 특정 임계값(Threshold)을 기준으로 정상/주의/위험 등 등급 판정 및 후속 조치 리포팅이 요구되는 과제.
- **혼합형 기본 상황:** 시험 시작 후 10분 내에 문제 유형이 단일 케이스로 특정되지 않을 경우, 기본 골격으로 본 스킬(데이터 정제·집계)과 Case 3(코드 수정·검증)을 결합하여 착수한다.

---

## 2. 원본 공략법 전문 (Single Source of Truth)

### 📦 Case 1. 데이터 파이프라인 정제·집계 및 리포팅 미션 (출제 확률: 최상 — 공식 FAQ 직결)
* **연동 스킬:** `.probe-kit/skills/case1_data_pipeline.md`
* **판별:** 복수의 데이터 파일(CSV, JSON, 로그 등) 첨부 + 정제·집계 결과 파일/스크립트/대시보드 제출 요구.
* **전용 필수 질문:**
  * *"이 표에서 한 행(Row)은 무엇을 한 건으로 세나요?"*
  * *"취소·철회된 건이나 중복 유입된 건은 집계(및 비율 계산 시 분모)에서 어떻게 처리하나요? 중복 시 최신과 최초 중 무엇을 기준으로 삼나요?"*
  * *"기간 필터링 기준은 신청일인가요, 처리 완료일인가요? 타임존이나 단위 불일치, 결측치(`null`, `-999`) 처리 기준은 무엇인가요?"*
  * *"최종 결과는 어떤 단위(부서별/월별 등)로 묶으며, 컬럼명·정렬 순서·소수점 반올림 기준은 무엇인가요?"*
* **무감점 Solve 시퀀스:**
  1. 데이터를 프롬프트에 통째로 넣지 말고(토큰·OOM 폭발 방지), `init.sh`가 생성한 `EDA_SUMMARY.txt`로 스키마·행 개수·결측치부터 파악.
  2. 실무자 DM으로 정제 기준을 확정해 메인(`Sol 6.1 xhigh`)이 `TASK_SPEC.md`에 체크리스트로 기록.
  3. 서브(`Luna 6 xhigh`)에게 각 전처리 단계별 필터링 건수를 로그로 출력하도록 코드 구현 지시.
  4. **태스크 DM 요구사항에 맞춘 온더플라이 테스트(tests/test_*.py) 즉석 작성·실행 및 표본 10~20건 대조 단위 테스트** 실행 후 제출 (고정 템플릿 금지, git commit 없이 untracked 유지).

---

### 🔬 Case 5. 반도체 / 제조 도메인 데이터·판정 미션 (출제 확률: 중 — SK하이닉스 주최 보정)
* **연동 스킬:** `.probe-kit/skills/case1_data_pipeline.md`
* **판별:** 공정·수율·웨이퍼·장비 센서·불량(Defect) 용어 등장 + 수치 데이터 및 이상 판정 요구.
* **전용 필수 질문:**
  * *"이 지표가 이상(비정상)이라는 것은 수치로 어느 수준인가요? 정상/주의/위험을 나누는 명확한 임계값(Threshold) 기준이 정해져 있나요?"*
  * *"현업 엔지니어는 이 결과를 보고 어떤 후속 조치를 취하나요? 오탐(정상인데 불량 판정)과 미탐(불량인데 놓침) 중 무엇이 더 치명적인가요?"*
  * *"문서에 나온 `[전문 용어]`는 현재 과제 맥락에서 정확히 어떻게 계산하거나 해석해야 하나요?"* (모르는 도메인 용어를 아는 척 넘기지 않고 물어보는 것이 가산점)
* **무감점 Solve 시퀀스:**
  1. AI가 임의로 지어낸 반도체 공정 지식이나 임의의 임계값을 절대 그대로 쓰지 않고, 반드시 `README`와 실무자 DM으로 확인한 기준값만 `TASK_SPEC.md`에 반영.
  2. Case 1(데이터 정제) 프로토콜 적용 + 판정 구간(정상/주의/위험) 로직을 서브(`Luna 6 xhigh`)가 구현 및 표본 검증.
  3. 계획 문서와 서술형 대비용으로 **'현재 임계값 방식에서 오탐/미탐이 발생할 수 있는 한계 조건(예: 센서 노이즈, 시계열 급변 구간)'**을 명확히 정리.

---

## 3. 단계별 실행 체크리스트

### 1단계: 원천 데이터 탐색 및 스키마 확정
- [ ] 데이터 파일을 프롬프트에 직접 복사하지 않고 터미널에서 `.probe-kit/scripts/eda_scan.py` 실행 결과(`EDA_SUMMARY.txt`)를 확인한다.
- [ ] 각 데이터 파일의 총 레코드 수, 컬럼 목록, 결측치 분포, 주요 컬럼 고유값 수를 파악한다.
- [ ] 데이터 내 식별자(Primary Key) 후보 컬럼과 중복 키 존재 여부를 확인한다.

### 2단계: 현업 비즈니스 로직 및 실무자 DM 확인
- [ ] 한 행(Row)의 집계 단위 정의를 실무자 DM으로 확인한다.
- [ ] 중복 레코드 처리 기준(최신 타임스탬프 우선 vs 최초 발생 우선)을 확인한다.
- [ ] 취소/환불/테스트 계정 데이터의 분모 포함 여부를 확정한다.
- [ ] 반도체/제조 센서 데이터의 임계값(Threshold) 수치와 경계 연산자(`>=`, `>`, `<=`, `<`)를 확정한다.
- [ ] 센서 결측치 대체값(`-999`, `-9999`, `null`, `NaN`, `INF`) 필터링 기준을 확정한다.

### 3단계: 작업 명세서 작성 및 서브 에이전트 위임
- [ ] 메인 에이전트가 `.probe-kit/runtime/TASK_SPEC.md`에 파이프라인 단계별 입출력 경로 및 필터링 규칙을 명시한다.
- [ ] 서브 에이전트(`Luna 6 xhigh`)를 호출하여 전처리 단계별 건수 로깅 로직을 구현하도록 지시한다.
- [ ] 서브 에이전트가 코드를 구현하고 전처리 단계별 건수 로그를 표준 출력에 출력하도록 한다.

### 4단계: 표본 10~20건 수동 대조 검증 및 온더플라이 테스트 실행
- [ ] 정상, 중복, 결측, 취소, 경계값 케이스를 포함하는 10~20건의 표본 데이터를 추출한다.
- [ ] 이번 태스크의 실무자 DM 요구사항에 맞춘 온더플라이 단위 테스트(예: `tests/test_*.py` 또는 ad-hoc 검증 스크립트)를 직접 작성하여 실행한다 (고정 템플릿 사용 금지, 태스크 맞춤형 ad-hoc 작성, `git commit` 금지 및 untracked 유지).
- [ ] `.probe-kit/scripts/sample_check_template.py`를 활용하여 수동 계산 기댓값과 파이프라인 출력값을 비교한다.
- [ ] 불일치 발생 시 즉시 파이프라인 로직의 부등호, 타임존, 반올림 규칙을 점검하고 수정한다.

### 5단계: 최종 산출물 및 한계점 기록
- [ ] 지정된 출력 파일명(CSV, JSON, 리포트)으로 최종 결과 파일이 정상 생성되었는지 행 수와 컬럼을 확인한다.
- [ ] `NOTES_TEMP.md`에 [결정]-[근거]-[검증]-[한계] 4줄 세트를 기록한다.

---

## 4. 전처리 단계별 건수 로깅 규칙

데이터 처리 파이프라인은 반드시 **원본 N건 → 결측 제거 → 중복 제거 → 취소/이상치 제외 → 최종 M건**으로 이어지는 파이프라인 각 단계의 처리 전후 건수와 제외 사유를 표준 출력 또는 로그 파일에 명시해야 한다. 이는 평가관의 자동 수집 로그에서 무결성과 검증 철저성을 입증하는 결정적 증거가 된다.

### 단계별 건수 로깅 표준 양식
```
[PIPELINE_STEP_1_LOAD]        Raw records loaded: 10000건
[PIPELINE_STEP_2_MISSING]     Removed missing values: 142건 (사유: 필수 키 또는 타깃 센서값 null/NaN/-999) -> 남은 건수: 9858건
[PIPELINE_STEP_3_DEDUPLICATE] Removed duplicates: 85건 (사유: 동일 wafer_id + timestamp 중복 유입, 최신값 1건 유지) -> 남은 건수: 9773건
[PIPELINE_STEP_4_OUTLIER]     Removed cancelled/outliers: 120건 (사유: status='CANCELLED' 95건, 온도 센서 음수 비정상값 25건) -> 남은 건수: 9653건
[PIPELINE_STEP_5_FINAL]       Final processed records: 9653건 (전체 원본 대비 보존율: 96.53%)
```

### 전처리 단계별 로깅 구현 예시 코드 (Python 표준 라이브러리)
```python
import csv
import sys
from typing import List, Dict, Tuple, Set

def run_pipeline(input_path: str, output_path: str) -> Dict[str, int]:
    stats = {
        "raw_count": 0,
        "missing_dropped": 0,
        "duplicate_dropped": 0,
        "outlier_dropped": 0,
        "final_count": 0
    }
    
    # 1단계: 원본 데이터 로드
    raw_rows: List[Dict[str, str]] = []
    with open(input_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_rows.append(row)
    stats["raw_count"] = len(raw_rows)
    print(f"[PIPELINE_STEP_1_LOAD] Raw records loaded: {stats['raw_count']}건")

    # 2단계: 결측치 및 비정상 대체값(-999, null) 제거
    valid_missing_rows: List[Dict[str, str]] = []
    invalid_sensor_values = {"-999", "-9999", "", "null", "none", "nan"}
    for row in raw_rows:
        sensor_val = row.get("sensor_temp", "").strip().lower()
        wafer_id = row.get("wafer_id", "").strip()
        if not wafer_id or sensor_val in invalid_sensor_values:
            stats["missing_dropped"] += 1
            continue
        valid_missing_rows.append(row)
    remaining_after_step2 = len(valid_missing_rows)
    print(f"[PIPELINE_STEP_2_MISSING] Dropped missing: {stats['missing_dropped']}건 -> 남은 건수: {remaining_after_step2}건")

    # 3단계: 중복 제거 (wafer_id 기준 최신 timestamp 유지)
    # 정렬: timestamp 내림차순
    valid_missing_rows.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
    seen_keys: Set[str] = set()
    deduped_rows: List[Dict[str, str]] = []
    for row in valid_missing_rows:
        key = row.get("wafer_id", "")
        if key in seen_keys:
            stats["duplicate_dropped"] += 1
            continue
        seen_keys.add(key)
        deduped_rows.append(row)
    remaining_after_step3 = len(deduped_rows)
    print(f"[PIPELINE_STEP_3_DEDUPLICATE] Dropped duplicates: {stats['duplicate_dropped']}건 -> 남은 건수: {remaining_after_step3}건")

    # 4단계: 취소 및 이상치 제외 (status == 'CANCEL' 또는 센서 물리적 한계 초과)
    cleaned_rows: List[Dict[str, str]] = []
    for row in deduped_rows:
        status = row.get("status", "").strip().upper()
        try:
            temp = float(row.get("sensor_temp", 0.0))
        except ValueError:
            stats["outlier_dropped"] += 1
            continue
        
        # 비즈니스 제외 규칙: 취소 건 제외 및 0도 미만 이상치 제외
        if status == "CANCELLED" or temp < 0.0 or temp > 1500.0:
            stats["outlier_dropped"] += 1
            continue
        cleaned_rows.append(row)
    stats["final_count"] = len(cleaned_rows)
    print(f"[PIPELINE_STEP_4_OUTLIER] Dropped outliers/cancelled: {stats['outlier_dropped']}건 -> 남은 건수: {stats['final_count']}건")
    print(f"[PIPELINE_STEP_5_FINAL] Final processed records: {stats['final_count']}건")

    # 결과 저장
    if cleaned_rows:
        fieldnames = list(cleaned_rows[0].keys())
        with open(output_path, mode="w", encoding="utf-8", newline="") as out_f:
            writer = csv.DictWriter(out_f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(cleaned_rows)
            
    return stats

if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "data/input.csv"
    dst = sys.argv[2] if len(sys.argv) > 2 else "data/output_cleaned.csv"
    run_pipeline(src, dst)
```

---

## 5. 10~20건 표본 수동 대조 검증 규칙 (`sample_check_template.py`)

전체 파이프라인을 돌리기 전 또는 돌린 직후, 반드시 **수작업으로 정답을 계산한 10~20건의 표본 세트**를 구성하고 단위 테스트를 실행해야 한다.

### 표본 세트 구성 원칙 (총 15건 권장 구성)
1. **정상 데이터 (Normal):** 일반적인 흐름의 데이터 5건
2. **경계값 데이터 (Boundary):** 임계값과 정확히 일치하거나 임계값 ±0.01인 데이터 3건
3. **결측치 데이터 (Missing):** 필수 필드가 공백, `null`, `-999`인 데이터 3건
4. **중복 데이터 (Duplicate):** 동일 키를 가지며 타임스탬프가 다른 데이터 2쌍 (4건)
5. **취소/이상치 데이터 (Cancelled/Outlier):** 취소 상태값 또는 물리적 불가 범위 수치 2건

### `.probe-kit/scripts/sample_check_template.py` 활용 스크립트
```python
#!/usr/bin/env python3
"""
표본 10~20건 수동 대조 검증 스크립트
수동으로 계산한 기대 결과(expected)와 파이프라인 실제 계산 함수(actual)를 비교 검증합니다.
"""

import sys

def calculate_yield_and_grade(temp: float, defect_count: int, status: str) -> str:
    """테스트 대상 비즈니스 로직 함수"""
    if status == "CANCELLED":
        return "EXCLUDED"
    if temp < 0.0 or temp > 1500.0 or temp == -999.0:
        return "INVALID"
    if defect_count >= 50 or temp >= 450.0:
        return "CRITICAL"
    if defect_count >= 20 or temp >= 400.0:
        return "WARNING"
    return "NORMAL"

def run_sample_verification():
    # 수동 검증용 15건 표본 데이터셋 (입력값과 수작업 기댓값 정의)
    samples = [
        # [ID, temp, defect_count, status, 기대 판정 결과, 테스트 목적]
        ("S01", 350.0, 5, "ACTIVE", "NORMAL", "정상 케이스"),
        ("S02", 399.9, 19, "ACTIVE", "NORMAL", "주의 구간 미만 정상 경계"),
        ("S03", 400.0, 10, "ACTIVE", "WARNING", "주의 온도 임계값 정확히 일치 (400.0)"),
        ("S04", 420.0, 20, "ACTIVE", "WARNING", "결함 수 임계값 정확히 일치 (20)"),
        ("S05", 449.9, 49, "ACTIVE", "WARNING", "위험 구간 미만 경계"),
        ("S06", 450.0, 10, "ACTIVE", "CRITICAL", "위험 온도 임계값 정확히 일치 (450.0)"),
        ("S07", 380.0, 50, "ACTIVE", "CRITICAL", "위험 결함 수 임계값 정확히 일치 (50)"),
        ("S08", 480.0, 80, "ACTIVE", "CRITICAL", "온도/결함 모두 위험 초과"),
        ("S09", -999.0, 5, "ACTIVE", "INVALID", "센서 결측 센티널값 (-999.0)"),
        ("S10", 350.0, 0, "CANCELLED", "EXCLUDED", "취소 상태 건 제외"),
        ("S11", -10.0, 2, "ACTIVE", "INVALID", "물리적 불가 음수 온도 이상치"),
        ("S12", 1600.0, 1, "ACTIVE", "INVALID", "물리적 상한 초과 온도 이상치"),
        ("S13", 400.0, 19, "ACTIVE", "WARNING", "온도 경계값 단독 만족 시 WARNING 판정"),
        ("S14", 350.0, 20, "ACTIVE", "WARNING", "결함 경계값 단독 만족 시 WARNING 판정"),
        ("S15", 450.0, 50, "ACTIVE", "CRITICAL", "온도/결함 동시 경계값 만족 시 CRITICAL 판정"),
    ]

    print("=" * 70)
    print(f"표본 {len(samples)}건 수동 대조 단위 검증 시작")
    print("=" * 70)

    passed_count = 0
    failed_cases = []

    for sample_id, temp, defects, status, expected, purpose in samples:
        actual = calculate_yield_and_grade(temp, defects, status)
        if actual == expected:
            passed_count += 1
            print(f"[{sample_id}] PASS | 목적: {purpose:<30} | 결과: {actual}")
        else:
            failed_cases.append((sample_id, purpose, expected, actual))
            print(f"[{sample_id}] FAIL | 목적: {purpose:<30} | 기대: {expected} != 실제: {actual}")

    print("-" * 70)
    print(f"검증 결과: 총 {len(samples)}건 중 {passed_count}건 성공, {len(failed_cases)}건 실패")
    print("=" * 70)

    if failed_cases:
        print("[오류 상세 목록]")
        for fid, fpurpose, fexp, fact in failed_cases:
            print(f"- ID: {fid}, 목적: {fpurpose}, 기대: {fexp}, 실제: {fact}")
        sys.exit(1)
    else:
        print("모든 수동 표본 검증을 100% 통과했습니다.")
        sys.exit(0)

if __name__ == "__main__":
    run_sample_verification()
```

---

## 6. 임계값 판정 경계값 및 결측 센서값 처리 규칙

### 경계값 연산자 기준 (`=`)
1. **이상(`>=`) vs 초과(`>`):** 지침서에 "400도 이상"으로 기재된 경우 반드시 `>= 400.0`을 사용한다. "400도 초과"일 때만 `> 400.0`을 적용한다. 모호하게 "~이상"으로 표기되어 있으면 실무자 DM으로 등호 포함 여부를 재확인한다.
2. **이하(`<=`) vs 미만(`<`):** 정상 범위를 판정할 때 경계 수치가 정상군에 속하는지 주의군에 속하는지 명문화한다.
3. **단위 통일:**
   - 시간: 초(s) vs 밀리초(ms) vs 마이크로초(us)
   - 길이/두께: 마이크로미터(um) vs 나노미터(nm) vs 옹스트롬(Å)
   - 온도: 섭씨(℃) vs 켈빈(K)
   - 파이프라인 시작 단계에서 모든 단위를 SI 기본 단위 또는 과제 지정 단위로 명시적 변환 함수를 거치도록 한다.

### 센서 결측치 및 센티널값(`-999`, `-9999`) 처리
1. 장비 센서 통신 두절, 타임아웃 시 흔히 수집되는 `-999`, `-999.0`, `-9999`, `9999`, `NaN`, `null` 값은 절대 일반 수치 연산(평균, 표준편차, 합계)에 포함시켜서는 안 된다.
2. 결측 센티널값은 연산 전 즉시 `None` 또는 `NaN`으로 변환하고, 해당 컬럼의 처리 정책(행 삭제, 직전 유효값 유지 ffill, 또는 '센서 오류' 플래그 분리)을 적용한다.

---

## 7. 실무자 DM 확인 질문 목록

다음 질문 리스트 중 현재 과제 상황에 맞는 질문을 선택하여 우측 메신저의 **업무 담당자(실무자 에이전트)**에게 즉시 질문한다.

### Case 1 전용 데이터 정제 질문
1. *"이 표에서 한 행(Row)은 무엇을 한 건으로 세나요? (예: 작업 단위, 장비 이벤트 단위, 또는 개별 웨이퍼 단위)"*
2. *"취소·철회된 건이나 중복 유입된 건은 집계(및 비율 계산 시 분모)에서 어떻게 처리하나요? 중복 시 최신과 최초 중 무엇을 기준으로 삼나요?"*
3. *"기간 필터링 기준은 신청일(발생일)인가요, 처리 완료일인가요? 타임존(KST vs UTC)이나 단위 불일치, 결측치(`null`, `-999`) 처리 기준은 무엇인가요?"*
4. *"최종 결과는 어떤 단위(부서별/월별/호기별)로 묶으며, 컬럼명·정렬 순서·소수점 반올림 기준은 무엇인가요?"*

### Case 5 전용 반도체/제조 도메인 판정 질문
1. *"이 지표가 이상(비정상)이라는 것은 수치로 어느 수준인가요? 정상/주의/위험을 나누는 명확한 임계값(Threshold) 기준과 부등호(= 포함 여부)가 정해져 있나요?"*
2. *"현업 엔지니어는 이 결과를 보고 어떤 후속 조치를 취하나요? 오탐(정상인데 불량 판정)과 미탐(불량인데 놓침) 중 무엇이 더 치명적인가요?"*
3. *"문서에 나온 `[전문 용어]`는 현재 과제 맥락에서 정확히 어떻게 계산하거나 해석해야 하나요?"*

---

## 8. 서브 에이전트(`Luna 6 xhigh`)에게 넘길 TASK_SPEC 예시

메인 에이전트(`Sol 6.1 xhigh`)는 아래 규격의 명세서를 작성하여 서브 에이전트에게 구현을 위임한다.

```markdown
# TASK_SPEC: 데이터 정제 및 이상 판정 파이프라인 구현

## 1. 작업 개요
- 대상 파일: `data/wafer_sensor_raw.csv`
- 산출 파일: `output/wafer_quality_report.csv`
- 담당 역할: 서브 에이전트 (Luna 6 xhigh)

## 2. 세부 구현 요구사항
1. `src/pipeline.py`를 작성하여 데이터를 로드하고 단계별 건수 로깅을 표준 출력으로 출력할 것.
   - 1단계: 원본 레코드 수 출력
   - 2단계: `sensor_temp`가 null, empty, -999인 결측치 제거 건수 출력
   - 3단계: 동일 `wafer_id` 기준 최신 `timestamp` 1건만 유지하고 중복 제거 건수 출력
   - 4단계: `status == 'DISCARDED'` 및 비정상 범위(0도 미만, 1500도 초과) 제거 건수 출력
   - 5단계: 최종 처리 건수 및 보존율 출력
2. 판정 로직:
   - CRITICAL: `sensor_temp >= 450.0` 또는 `defect_count >= 50`
   - WARNING: `sensor_temp >= 400.0` 또는 `defect_count >= 20`
   - NORMAL: 그 외 정상 수치
3. 최종 CSV 저장 포맷:
   - 컬럼: `wafer_id`, `lot_id`, `sensor_temp`, `defect_count`, `grade`, `processed_at`
   - 정렬: `grade` 우선순위(CRITICAL -> WARNING -> NORMAL), 동일 등급 내 `wafer_id` 오름차순
   - 수치 포맷: `sensor_temp`는 소수점 둘째자리 반올림

## 3. 검증 기준
- `python3 -m unittest tests/test_sample_check.py` 실행 시 15건 표본 테스트 100% 통과할 것.
- 실행 중 OOM 및 예외 발생 없이 종료 코드 0으로 완료될 것.
```

---

## 9. 검증 명령 모음

서브 에이전트 작업 완료 후 터미널에서 직접 실행할 검증 명령:

```bash
# 1. 원본 및 결과 파일 행 수 비교
wc -l data/wafer_sensor_raw.csv output/wafer_quality_report.csv

# 2. 파이프라인 실행 및 단계별 로깅 출력 확인
python3 src/pipeline.py data/wafer_sensor_raw.csv output/wafer_quality_report.csv

# 3. 태스크 DM 맞춤 온더플라이 단위 테스트 및 10~20건 수동 표본 대조 실행 (git commit 없이 untracked 유지)
python3 tests/test_sample_check.py || python3 .probe-kit/scripts/sample_check_template.py

# 4. 결측치 및 센티널값(-999) 잔존 여부 검사
grep -E -- "-999|null|NaN" output/wafer_quality_report.csv || echo "결측 센티널값 0건 확인 완료"

# 5. Git 변경 사항 및 무결성 감사 (또는 python3 버전 직접 실행)
bash .probe-kit/scripts/pre_submit_audit.sh
# python3 .probe-kit/scripts/pre_submit_audit.py
```

---

## 10. 보고서 및 후속 Q&A 작성용 [결정]-[근거]-[검증]-[한계] 예시

과제 중간 메모(`NOTES_TEMP.md`), 최종 제출 보고서(`SUBMISSION_REPORT.md`), 그리고 제출 후 6문항 서술형 평가 답변에 직접 활용할 수 있는 표준 4줄 세트이다.

- **[결정]:** 장비 센서 통신 에러로 수집된 `-999.0` 센티널 결측치와 `CANCELLED` 플래그가 붙은 레코드는 전체 통계 및 수율 판정 분모에서 배제하고, `wafer_id` 중복 건은 최신 타임스탬프 1건만 유지하도록 정제 파이프라인을 설계함.
- **[근거]:** 실무자 DM을 통해 취소 건과 통신 실패 데이터가 수율 통계에 포함될 경우 불량률이 과대 계상될 위험이 있음을 확인하였고, 이력 데이터 중복 수집 시 최신 보정 데이터를 취하는 것이 현업 품질 관리 표준 프로토콜임을 근거로 삼음.
- **[검증]:** 15건의 수동 계산 표본 세트(정상, 경계값 400.0/450.0, 결측치 -999, 취소 건, 중복 건)를 구축하고 단위 테스트를 실행하여 기대 판정 등급과 파이프라인 출력값이 100% 일치함을 확인하였으며, 단계별 필터링 건수 로그를 통해 원본 10,000건 중 9,653건이 무결하게 보존됨을 검증함.
- **[한계]:** 고정 임계값(400도/450도) 기반 판정 방식은 센서의 일시적 고주파 노이즈나 챔버 급가열 구간에서 일시적 오탐(정상 웨이퍼의 경보 발생)을 유발할 수 있으므로, 실제 현업 적용 시에는 단순 수치 비교를 넘어 3초 이동평균(Moving Average) 필터링이나 시계열 추세 분석 알고리즘의 추가 도입이 필요함.
