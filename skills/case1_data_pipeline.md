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
  3. 서브(`GPT 5.6-terra medium`)에게 각 전처리 단계별 필터링 건수를 로그로 출력하도록 코드 구현 지시.
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
  2. Case 1(데이터 정제) 프로토콜 적용 + 판정 구간(정상/주의/위험) 로직을 서브(`GPT 5.6-terra medium`)가 구현 및 표본 검증.
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
- [ ] 서브 에이전트(`GPT 5.6-terra medium`)를 호출하여 전처리 단계별 건수 로깅 로직을 구현하도록 지시한다.
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

## 8. 서브 에이전트(`GPT 5.6-terra medium`)에게 넘길 TASK_SPEC 예시

메인 에이전트(`Sol 6.1 xhigh`)는 아래 규격의 명세서를 작성하여 서브 에이전트에게 구현을 위임한다.

```markdown
# TASK_SPEC: 데이터 정제 및 이상 판정 파이프라인 구현

## 1. 작업 개요
- 대상 파일: `data/wafer_sensor_raw.csv`
- 산출 파일: `output/wafer_quality_report.csv`
- 담당 역할: 서브 에이전트 (GPT 5.6-terra medium)

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


---

## 🚨 [CCTV / Safety Vision AI 특화] 객체 탐지·행동 판단 시공간(Spatio-Temporal) 파이프라인 공략

> **만약 CCTV(Safety Vision AI / 침입·쓰러짐·추락·화재 감지 / 24시간 모니터링)에 관련된 문제라면, 위 기존의 단순 단일 행(Row) 수치 임계값(웨이퍼/온도 400도 등) 및 일반 주문 집계 내용이 아니라, 아래 새로 만든 [CCTV 시공간(Spatio-Temporal) 사고 판정 및 쿨다운 병합 파이프라인] 내용을 참고하세요.**

---

### 1. CCTV 비전 AI 데이터 파이프라인 특성 및 핵심 평가 포인트
- CCTV 및 스마트 안전관제 도메인은 단순 정적 수치(1행 1판정)와 달리 **공간(Spatial) 위치·형상**과 **시간(Temporal) 연속성**을 동시에 만족해야 유효 사고로 확정됩니다.
- **공간(Spatial) 판정**: 객체의 BBox 중심점/발끝 좌표가 위험구역(ROI) 내부인지, 쓰러짐/추락의 경우 종횡비(Aspect Ratio)가 정상 보행자 범위(0.3~0.6)를 벗어나 전도 상태(>= 1.2 등)인지 판정합니다.
- **시간(Temporal) 판정**: 작업자 보행 중 스쳐지나감이나 카메라 깜빡임 등의 단발성 노이즈(1~2프레임)를 제거하기 위해 최소 지속시간(`min_duration_sec`) 이상 유지되어야 하며, 영상 프레임 드롭이나 가림(Occlusion) 발생 시 짧은 공백(`max_gap_sec`)은 끊어지지 않은 동일 사건으로 이어붙여야 합니다.
- **쿨다운(Cooldown / Deduplication)**: 동일 현장에서 1초에 수십 프레임씩 반복 탐지되는 건을 단일 사고(Incident)로 압축 및 쿨다운 병합하여 관제 피로도(Alert Fatigue)를 방지합니다.

---

### 2. 공간(Spatial) 판정 패턴 및 Python 표준 라이브러리 레퍼런스

#### (1) BBox 좌표 및 지표 계산 함수
```python
def extract_bbox_features(bbox, fmt="xyxy"):
    """
    bbox: [x1, y1, x2, y2] (fmt="xyxy") 또는 [x, y, w, h] (fmt="xywh")
    반환: 중심점 (cx, cy), 하단 발끝 좌표 (fx, fy), 너비 w, 높이 h, 종횡비 aspect_ratio (w / h)
    """
    if fmt == "xywh":
        x, y, w_raw, h_raw = bbox
        x1, y1 = float(x), float(y)
        w = max(0.0, float(w_raw))
        h = max(0.0, float(h_raw))
        x2, y2 = x1 + w, y1 + h
    else:
        x1, y1, x2, y2 = [float(v) for v in bbox]
        w = max(0.0, x2 - x1)
        h = max(0.0, y2 - y1)
    
    cx = (x1 + x2) / 2.0
    cy = (y1 + y2) / 2.0
    
    # 작업자 위치 및 구역 진입 판정: 지면 접촉점인 하단 발끝(Bottom-Center) 좌표 기준
    fx = cx
    fy = float(y2)
    
    # 쓰러짐 판정: 가로가 세로보다 현저히 크면(aspect_ratio >= 1.2 등) 쓰러짐 의심
    # ZeroDivision 완전 방어 (1e-6)
    aspect_ratio = w / max(h, 1e-6)
    
    return {
        "center": (cx, cy),
        "foot": (fx, fy),
        "width": w,
        "height": h,
        "aspect_ratio": aspect_ratio
    }
```

#### (2) 위험구역(ROI) 침입 판정 (사각형 & 다각형 Ray-Casting & IoU)
```python
def is_point_in_rect(point, roi_rect, inclusive=True):
    """
    point: (x, y)
    roi_rect: [rx1, ry1, rx2, ry2]
    inclusive: 경계선 포함 여부 (<= vs <)
    """
    px, py = point
    rx1, ry1, rx2, ry2 = roi_rect
    if inclusive:
        return (rx1 <= px <= rx2) and (ry1 <= py <= ry2)
    return (rx1 < px < rx2) and (ry1 < py < ry2)

def _is_point_on_segment(px, py, x1, y1, x2, y2, eps=1e-9):
    """점 (px, py)가 선분 (x1, y1)-(x2, y2) 위에 존재하는지 판정"""
    cross = (px - x1) * (y2 - y1) - (py - y1) * (x2 - x1)
    if abs(cross) > eps:
        return False
    return (min(x1, x2) - eps <= px <= max(x1, x2) + eps) and (min(y1, y2) - eps <= py <= max(y1, y2) + eps)

def is_point_in_polygon(point, polygon, inclusive=True):
    """
    2D 다각형 위험구역 내부 판정 (경계선/꼭짓점 정확 판정 + Ray-Casting Algorithm)
    point: (x, y)
    polygon: [(x1, y1), (x2, y2), ..., (xn, yn)]
    inclusive: 다각형 경계선/꼭짓점 위의 점을 포함할지 여부 (<= vs <)
    """
    if not polygon or len(polygon) < 3:
        return False
    px, py = float(point[0]), float(point[1])
    n = len(polygon)

    # 1. 경계선(선분/꼭짓점) 위에 정확히 위치한 경우 우선 판정
    for i in range(n):
        x1, y1 = float(polygon[i][0]), float(polygon[i][1])
        x2, y2 = float(polygon[(i + 1) % n][0]), float(polygon[(i + 1) % n][1])
        if _is_point_on_segment(px, py, x1, y1, x2, y2):
            return inclusive

    # 2. Ray-Casting 내부 판정
    inside = False
    p1x, p1y = float(polygon[0][0]), float(polygon[0][1])
    for i in range(1, n + 1):
        p2x, p2y = float(polygon[i % n][0]), float(polygon[i % n][1])
        if (p1y > py) != (p2y > py):
            xinters = (py - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
            if px < xinters:
                inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def calculate_iou(boxA, boxB):
    """
    두 BBox [x1, y1, x2, y2] 간 IoU (Intersection over Union) 계산
    """
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0.0, xB - xA) * max(0.0, yB - yA)
    boxAArea = max(0.0, boxA[2] - boxA[0]) * max(0.0, boxA[3] - boxA[1])
    boxBArea = max(0.0, boxB[2] - boxB[0]) * max(0.0, boxB[3] - boxB[1])
    unionArea = boxAArea + boxBArea - interArea

    return interArea / max(unionArea, 1e-6)
```

---

### 3. 시간(Temporal) 연속 지속시간 판정 & 프레임 끊김 허용(Grace Period)

단발성 오탐(1~2프레임 노이즈)을 제거하고 유효한 연속 사고 세션만 추출하는 로직:

```python
from datetime import datetime
from collections import defaultdict

def parse_iso_or_timestamp(ts):
    if isinstance(ts, (int, float)):
        return float(ts)
    s = str(ts).strip()
    try:
        return float(s)
    except ValueError:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()

def process_spatio_temporal_events(detections, min_duration_sec=3.0, max_gap_sec=1.5):
    """
    detections: [
        {
            "camera_id": "CAM-01",
            "track_id": 101,          # 또는 object_id
            "event_type": "INTRUSION", # INTRUSION, FALL_DOWN, FIRE 등
            "timestamp": 1700000000.0,
            "confidence": 0.88,
            "bbox": [100, 200, 150, 320]
        }, ...
    ]
    """
    # 1. 정렬: 카메라 + 객체(트랙) + 사고유형 기준 타임스탬프 오름차순
    sorted_dets = sorted(detections, key=lambda d: (
        d["camera_id"],
        d.get("track_id", "GLOBAL"),
        d["event_type"],
        parse_iso_or_timestamp(d["timestamp"])
    ))

    # 2. 그룹별 연속 감지 세션 병합
    sessions = defaultdict(list)
    for det in sorted_dets:
        key = (det["camera_id"], det.get("track_id", "GLOBAL"), det["event_type"])
        t = parse_iso_or_timestamp(det["timestamp"])
        
        if not sessions[key]:
            sessions[key].append({
                "start_time": t,
                "end_time": t,
                "frame_count": 1,
                "max_confidence": det.get("confidence", 0.0),
                "samples": [det]
            })
        else:
            last_sess = sessions[key][-1]
            gap = t - last_sess["end_time"]
            
            if gap <= max_gap_sec:
                # 허용 간격(Grace Period) 이내이면 세션 연장
                last_sess["end_time"] = t
                last_sess["frame_count"] += 1
                last_sess["max_confidence"] = max(last_sess["max_confidence"], det.get("confidence", 0.0))
                last_sess["samples"].append(det)
            else:
                # 간격 초과 시 새로운 연속 감지 세션 시작
                sessions[key].append({
                    "start_time": t,
                    "end_time": t,
                    "frame_count": 1,
                    "max_confidence": det.get("confidence", 0.0),
                    "samples": [det]
                })

    # 3. 최소 지속 시간(min_duration_sec) 필터링
    valid_events = []
    for key, sess_list in sessions.items():
        cam_id, track_id, event_type = key
        for sess in sess_list:
            duration = sess["end_time"] - sess["start_time"]
            if duration >= min_duration_sec:
                valid_events.append({
                    "camera_id": cam_id,
                    "track_id": track_id,
                    "event_type": event_type,
                    "start_time": sess["start_time"],
                    "end_time": sess["end_time"],
                    "duration": round(duration, 2),
                    "frame_count": sess["frame_count"],
                    "confidence": sess["max_confidence"]
                })
                
    return valid_events
```

---

### 4. 24시간 모니터링 중복 알람 억제(Cooldown / Deduplication)

동일 현장·동일 객체에서 발생하는 중복 알람 폭주를 차단하는 상태 머신:

```python
def merge_with_cooldown(valid_events, cooldown_sec=60.0):
    """
    동일 카메라 + 동일 사고 유형에 대해 cooldown_sec 이내 연속 발생 건을
    단일 긴급 인시던트(Incident)로 병합
    """
    sorted_events = sorted(valid_events, key=lambda x: (x["camera_id"], x["event_type"], x["start_time"]))
    
    incidents = []
    active_incidents = {} # key: (camera_id, event_type) -> incident
    
    for ev in sorted_events:
        key = (ev["camera_id"], ev["event_type"])
        ev_start = ev["start_time"]
        ev_end = ev["end_time"]
        
        if key in active_incidents:
            curr = active_incidents[key]
            # 쿨다운 윈도우 판정: 이전 인시던트 종료 후 cooldown_sec 이내인가?
            if ev_start <= (curr["incident_end"] + cooldown_sec):
                # 기존 인시던트 갱신 병합
                curr["incident_end"] = max(curr["incident_end"], ev_end)
                curr["merged_event_count"] += 1
                curr["max_confidence"] = max(curr["max_confidence"], ev["confidence"])
                curr["total_duration"] = round(curr["incident_end"] - curr["incident_start"], 2)
                continue
            else:
                # 쿨다운 기간 경과 -> 이전 인시던트 종결 후 신규 등록
                incidents.append(curr)
                del active_incidents[key]

        # 신규 인시던트 생성
        new_inc = {
            "incident_id": f"INC-{ev['camera_id']}-{ev['event_type']}-{int(ev_start)}",
            "camera_id": ev["camera_id"],
            "event_type": ev["event_type"],
            "track_id": ev.get("track_id"),
            "incident_start": ev_start,
            "incident_end": ev_end,
            "total_duration": ev["duration"],
            "max_confidence": ev["confidence"],
            "merged_event_count": 1,
            "status": "DETECTED"
        }
        active_incidents[key] = new_inc

    # 남아있는 활성 인시던트 플러시
    for inc in active_incidents.values():
        incidents.append(inc)

    return sorted(incidents, key=lambda x: x["incident_start"])
```

---

### 5. CCTV 전용 5단계 전처리 건수 로깅 양식 (무감점 표준 출력)

파이프라인 실행 시 터미널과 채점 로그에 반드시 아래 5단계 필터링 통계를 순서대로 명확히 출력합니다:

```python
def print_cctv_pipeline_summary(raw_count, filter1_count, filter2_count, filter3_count, final_incidents_count):
    print("=" * 65)
    print(" [CCTV Safety Vision AI 시공간 파이프라인 단계별 처리 리포트]")
    print(f" 1단계 [RAW_FRAMES]:                  {raw_count:>6} 건 (원천 프레임 탐지 총합)")
    print(f" 2단계 [CONFIDENCE_AND_STATUS_FILTER]:{filter1_count:>6} 건 (점검중 카메라/저신뢰도 제외 잔여)")
    print(f" 3단계 [SPATIAL_ROI_MATCH]:            {filter2_count:>6} 건 (위험구역 내부 진입/특화 BBox 일치)")
    print(f" 4단계 [TEMPORAL_DURATION_FILTER]:     {filter3_count:>6} 건 (단발성 노이즈 제거 유효 지속 세션)")
    print(f" 5단계 [COOLDOWN_INCIDENT_MERGE]:      {final_incidents_count:>6} 건 (쿨다운 병합 최종 확정 사고)")
    retention_rate = (final_incidents_count / max(raw_count, 1)) * 100
    print(f" 최종 사고 보존 및 압축률:             {retention_rate:.2f}%")
    print("=" * 65)
```


---

## 🚨 [최유력 3대 시나리오 특화] ① 24시간 관제 근무표 · ② 휴가 잔여일 계산 · ③ CCTV 대응자 배정 표준 구현 레퍼런스

> **만약 문제가 ① 24시간 안전 관제 인력 근무표 편성, ② 휴가 잔여일(연차·연중·장기근속·해피프라이데이) 계산, ③ CCTV 감지 이벤트 중복 묶기·우선순위·대응자 배정으로 나왔다면, 위 기존의 일반 예제 대신 아래 새로 만든 시나리오별 표준 알고리즘을 참고하여 구현하세요.**

---

### 시나리오 ①: 24시간 안전 관제 인력 근무표 편성 (Shift / Roster Scheduling)
- **핵심 제약 체크리스트**:
  1. **24시간 무결성**: 모든 날짜·모든 교대조(또는 시간 슬롯)에 최소 필수 인원(`min_staff`) 배치.
  2. **확실하게 쉬는 제약 (Hard Constraints)**:
     - 휴가자(`leave_dates`) 및 결근자 해당 일자 배정 절대 금지 (특히 **둘째 주 금요일 해피프라이데이** 결원 급증 주의).
     - **근무 사이 최소 휴식 시간 보장** (`min_rest_hours`, 예: 야간 근무 후 당일 주간/오후 연속 투입 금지, 최소 11~12시간 이상 간격).
     - **야간 연속 근무 상한** (`max_consecutive_nights`, 예: 연속 2~3일 초과 금지).
     - **연속 관제 시간 상한** (`max_continuous_watch_hours`, 예: 2시간 연속 모니터링 후 휴식/교대 슬롯 부여).
  3. **결정론적 공정 배정 (Tie-breaker)**: 가용 후보 중 `(누적 근무시간 오름차순, 야간 근무 횟수 오름차순, 사번 오름차순)`으로 정렬하여 항상 동일한 정답 근무표가 생성되게 보장.

```python
import calendar
from datetime import date, datetime, timedelta

def is_second_friday(d: date) -> bool:
    """해당 월의 둘째 주 금요일(해피프라이데이 등)인지 판정 (weekday 4 == Friday)"""
    return d.weekday() == 4 and 8 <= d.day <= 14

def build_watch_subslots(shift_start: int, shift_end: int, assigned_emp_ids: list, max_continuous_watch_hours: int = 2):
    """
    연속 관제 시간 상한(예: 2시간마다 교대/휴식)을 만족하도록 교대조 내부 모니터링 서브슬롯 생성
    배정된 인원들이 max_continuous_watch_hours 단위로 순환(Round-Robin)하며 집중 모니터링을 수행
    """
    subslots = []
    if not assigned_emp_ids:
        return subslots
    n_emps = len(assigned_emp_ids)
    step = max(1, int(max_continuous_watch_hours))
    slot_idx = 0
    for h in range(shift_start, shift_end, step):
        sub_end = min(h + step, shift_end)
        primary_watcher = assigned_emp_ids[slot_idx % n_emps]
        resting_or_sub = [eid for eid in assigned_emp_ids if eid != primary_watcher]
        subslots.append({
            "subslot_hours": f"{h % 24:02d}:00~{sub_end % 24:02d}:00",
            "duration_hours": sub_end - h,
            "active_monitor_emp_id": primary_watcher,
            "rotation_support_emp_ids": resting_or_sub
        })
        slot_idx += 1
    return subslots

def schedule_24h_safety_roster(
    dates,                  # ["2026-11-01", ...]
    shifts,                 # [{"id": "DAY", "start": 6, "end": 14, "min_staff": 2}, {"id": "EVENING", "start": 14, "end": 22, "min_staff": 2}, {"id": "NIGHT", "start": 22, "end": 30, "min_staff": 2}]
    employees,              # [{"emp_id": "E001", "name": "김하이", "role": "SENIOR"}, ...]
    leave_set,              # {("E001", "2026-11-13"), ...} (취소/반려 제외된 확정 휴가)
    min_rest_hours=11,
    max_consecutive_nights=2,
    max_weekly_hours=52,
    max_continuous_watch_hours=2
):
    # 직원별 상태 추적: 누적 시간, 주간별 시간, 야간 횟수, 마지막 근무일/종료시각, 연속 야간 일수
    emp_stats = {
        e["emp_id"]: {
            "total_hours": 0,
            "weekly_hours": {},
            "night_count": 0,
            "last_work_day_idx": -999,
            "last_end_abs_hour": -999,
            "consec_nights": 0,
            "last_night_day_idx": -999,
            "info": e
        }
        for e in employees
    }
    roster = []
    warnings = []

    for day_idx, d_str in enumerate(dates):
        base_abs_hour = day_idx * 24
        week_idx = day_idx // 7
        for sh in shifts:
            sh_id = sh["id"]
            sh_start = base_abs_hour + sh["start"]
            sh_end = base_abs_hour + sh["end"]
            duration = sh["end"] - sh["start"]
            needed = sh["min_staff"]

            # 가용 후보 필터링
            candidates = []
            for emp_id, st in emp_stats.items():
                # 1. 휴가자 제외
                if (emp_id, d_str) in leave_set:
                    continue
                # 2. 동일 일자 중복 배정 금지 (1일 최대 1개 교대조)
                if st["last_work_day_idx"] == day_idx:
                    continue
                # 3. 최소 휴식 시간 보장 (직전 근무 종료 후 min_rest_hours 이상 경과)
                if (sh_start - st["last_end_abs_hour"]) < min_rest_hours:
                    continue
                # 4. 주당 최대 근무시간(예: 52시간) 상한 체크
                if st["weekly_hours"].get(week_idx, 0) + duration > max_weekly_hours:
                    continue
                # 5. 야간 연속 근무 상한 체크
                if sh_id == "NIGHT":
                    consec = st["consec_nights"] if st["last_night_day_idx"] == (day_idx - 1) else 0
                    if consec >= max_consecutive_nights:
                        continue
                candidates.append(emp_id)

            # 결정론적 정렬: 누적 근무시간 적은 순 -> 야간 횟수 적은 순 -> 사번 오름차순
            candidates.sort(key=lambda eid: (
                emp_stats[eid]["total_hours"],
                emp_stats[eid]["night_count"],
                eid
            ))

            assigned = candidates[:needed]
            if len(assigned) < needed:
                warnings.append({
                    "date": d_str,
                    "shift": sh_id,
                    "required": needed,
                    "assigned": len(assigned),
                    "reason": "SHORTAGE_DUE_TO_LEAVE_OR_REST_CONSTRAINT"
                })

            for eid in assigned:
                st = emp_stats[eid]
                st["total_hours"] += duration
                st["weekly_hours"][week_idx] = st["weekly_hours"].get(week_idx, 0) + duration
                st["last_work_day_idx"] = day_idx
                st["last_end_abs_hour"] = sh_end
                if sh_id == "NIGHT":
                    st["night_count"] += 1
                    if st["last_night_day_idx"] == (day_idx - 1):
                        st["consec_nights"] += 1
                    else:
                        st["consec_nights"] = 1
                    st["last_night_day_idx"] = day_idx

            roster.append({
                "date": d_str,
                "shift": sh_id,
                "assigned_emp_ids": assigned,
                "watch_rotation": build_watch_subslots(sh["start"], sh["end"], assigned, max_continuous_watch_hours),
                "is_full": len(assigned) == needed
            })

    return {"roster": roster, "warnings": warnings, "emp_summary": emp_stats}
```

---

### 시나리오 ②: 휴가 잔여일 계산 (연차·연중·장기근속·해피프라이데이) 및 동시 휴가 제한 검증
- **핵심 경계값 체크리스트**:
  1. **근속연수(`service_years`) 계산**: 기준일(`ref_date`) 대비 만 근속연수 (윤년 2월 29일 입사자 안전 처리).
  2. **기본 연차(Annual Leave)**: 1년 이상 기본 15일 + 매 2년 초과(`(years - 1) // 2`)마다 1일 가산, **최대 25일 상한(`min(25, 15 + (years - 1) // 2)`)**.
  3. **장기근속 휴가(Long-Service Leave)**: 5년차·10년차 등 부여 시 **10년차에 5년·10년 중복 부여 여부(`long_service_mode="tier" | "exact_year" | "cumulative"`)**를 DM 확인 결과에 따라 파라미터로 즉시 제어.
  4. **차감 제외 및 소수점**: `HAPPY_FRIDAY`(해피프라이데이), 공휴일, `CANCELLED`/`REJECTED` 상태는 연차 차감에서 제외. 반차(`0.5`), 반반차(`0.25`) 정확히 차감.
  5. **팀별 동시 휴가 제한**: 같은 날짜·같은 팀(`team`)의 휴가 인원이 최소 근무 인원(`min_team_working`)을 침범하는지 검증.

```python
from datetime import date
from collections import defaultdict

def calc_full_years(join_date: date, ref_date: date) -> int:
    """입사일로부터 기준일까지의 정확한 만 근속연수 계산 (윤년 2/29 안전 처리)"""
    if ref_date < join_date:
        return 0
    years = ref_date.year - join_date.year
    # 평년 2월 28일에 2월 29일 입사자 비교 방어
    try:
        anniv = join_date.replace(year=ref_date.year)
    except ValueError:
        anniv = date(ref_date.year, 2, 28)
    if ref_date < anniv:
        years -= 1
    return max(0, years)

def calculate_employee_leave_balance(
    emp,                        # {"emp_id": "E01", "join_date": "2016-05-01", "team": "T1"}
    usage_rows,                 # [{"emp_id": "E01", "date": "2026-06-12", "type": "HALF_AM", "category": "ANNUAL", "status": "APPROVED"}, ...]
    ref_date=date(2026, 11, 4),
    mid_year_grant=3.0,         # 연중 리프레시 휴가 기본 부여일
    long_service_mode="tier",   # "tier"(구간별 대체: 5~9년 5일, 10년+ 10일) | "exact_year"(5년차/10년차 당해만) | "cumulative"(5년+10년 중복 합산 15일)
    long_service_overlap=False  # 하위 호환 플래그 (True이면 "cumulative"와 동일)
):
    join_d = date.fromisoformat(emp["join_date"])
    years = calc_full_years(join_d, ref_date)

    # 1. 기본 연차 (상한 25일 Cap)
    if years < 1:
        # 1년 미만: 개근 개월 수 (최대 11일)
        months = (ref_date.year - join_d.year) * 12 + (ref_date.month - join_d.month)
        if ref_date.day < join_d.day:
            months -= 1
        annual_grant = float(max(0, min(11, months)))
    else:
        annual_grant = float(min(25, 15 + (years - 1) // 2))

    # 2. 장기근속 휴가 (예: 5년 5일, 10년 10일 - DM 기준에 맞게 모드/수치 조정)
    mode = "cumulative" if long_service_overlap else long_service_mode
    long_grant = 0.0
    if mode == "cumulative":
        if years >= 5:
            long_grant += 5.0
        if years >= 10:
            long_grant += 10.0
    elif mode == "exact_year":
        if years == 5:
            long_grant = 5.0
        elif years == 10:
            long_grant = 10.0
    else:  # "tier" (가장 일반적인 구간별 부여: 5~9년 5일, 10년 이상 10일)
        if 5 <= years < 10:
            long_grant = 5.0
        elif years >= 10:
            long_grant = 10.0

    # 3. 사용 일수 차감 (취소/반려 및 해피프라이데이 제외)
    TYPE_WEIGHT = {
        "FULL": 1.0,
        "ANNUAL": 1.0,
        "HALF": 0.5,
        "HALF_AM": 0.5,
        "HALF_PM": 0.5,
        "QUARTER": 0.25,
        "HAPPY_FRIDAY": 0.0,  # 해피프라이데이는 연차 미차감 (DM 확인 시 1.0 전환 가능)
    }

    used_annual = 0.0
    used_mid = 0.0
    used_long = 0.0
    seen_emp_date_type = set()

    for r in usage_rows:
        if r.get("emp_id") != emp["emp_id"]:
            continue
        if str(r.get("status", "APPROVED")).upper() in ("CANCELLED", "REJECTED"):
            continue
        l_type = str(r.get("type", "FULL")).upper()
        if l_type == "HAPPY_FRIDAY" or str(r.get("category", "")).upper() == "HAPPY_FRIDAY":
            continue  # 해피프라이데이 차감 제외

        dedup_key = (r["emp_id"], r["date"], l_type)
        if dedup_key in seen_emp_date_type:
            continue
        seen_emp_date_type.add(dedup_key)

        days = float(r.get("days", TYPE_WEIGHT.get(l_type, 1.0)))
        cat = str(r.get("category", "ANNUAL")).upper()
        if cat == "LONG_SERVICE":
            used_long += days
        elif cat == "MID_YEAR":
            used_mid += days
        else:
            used_annual += days

    return {
        "emp_id": emp["emp_id"],
        "service_years": years,
        "annual_grant": annual_grant,
        "annual_used": used_annual,
        "annual_remained": round(annual_grant - used_annual, 2),
        "mid_year_remained": round(mid_year_grant - used_mid, 2),
        "long_service_remained": round(long_grant - used_long, 2),
        "total_remained": round((annual_grant - used_annual) + (mid_year_grant - used_mid) + (long_grant - used_long), 2)
    }

def validate_team_concurrent_leave(employees, usage_rows, min_team_working=2, count_half_as_absent=False):
    """
    같은 날 한 팀에서 너무 많이 쉬면 안 된다는 최소 근무 인원(동시 휴가 상한) 위반 일자/팀 검출
    """
    team_members = defaultdict(set)
    emp_to_team = {}
    for e in employees:
        t = e.get("team", "DEFAULT")
        team_members[t].add(e["emp_id"])
        emp_to_team[e["emp_id"]] = t

    # (team, date) -> 휴가자 사번 집합
    team_date_leaves = defaultdict(set)
    for r in usage_rows:
        if str(r.get("status", "APPROVED")).upper() in ("CANCELLED", "REJECTED"):
            continue
        l_type = str(r.get("type", "FULL")).upper()
        if not count_half_as_absent and l_type in ("HALF", "HALF_AM", "HALF_PM", "QUARTER"):
            continue
        eid = r.get("emp_id")
        if eid in emp_to_team:
            team_date_leaves[(emp_to_team[eid], r["date"])].add(eid)

    violations = []
    for (team, d_str), absent_ids in sorted(team_date_leaves.items()):
        total_size = len(team_members[team])
        working_count = total_size - len(absent_ids)
        if working_count < min_team_working:
            violations.append({
                "team": team,
                "date": d_str,
                "team_size": total_size,
                "absent_count": len(absent_ids),
                "working_count": working_count,
                "min_required_working": min_team_working,
                "absent_emp_ids": sorted(absent_ids)
            })
    return violations
```

---

### 시나리오 ③: CCTV 감지 이벤트 중복 묶기·우선순위·구역별 대응자 배정 및 에스컬레이션
- **핵심 비즈니스 규칙 체크리스트**:
  1. **같은 카메라 N분 내 반복 감지 묶기**: `(camera_id, event_type)` 기준 타임스탬프 정렬 후 $N$분(`window_sec = N * 60`) 이내 이벤트 병합 (`sliding` vs `fixed` 윈도우 모드 지원).
  2. **우선순위 산정 (화재 최우선)**: `FIRE(1순위) > FALL_OFF/FALL_DOWN(2순위) > INTRUSION(3순위) > PPE/NO_HELMET(4순위)`.
  3. **오탐 다발 카메라 필터링 & 화재 예외**: 오탐률이 높거나 낮은 신뢰도 이벤트는 억제/수동검토로 빼되, **`FIRE`(화재)는 오탐 이력과 무관하게 무조건 즉시 최우선 배정**.
  4. **구역별 대응자 배정 & 미응답 에스컬레이션**: 사건 구역(`zone_id`)의 가용(`AVAILABLE`) 대응자에게 배정하고, `ack_timeout_sec` 이내에 미응답(`status == 'ASSIGNED'`)이면 2순위 예비 대응자 또는 안전팀장(`MANAGER`)에게 자동 에스컬레이션.

```python
PRIORITY_RANK = {
    "FIRE": 1,          # 화재 최우선
    "FALL_OFF": 2,      # 추락
    "FALL_DOWN": 2,     # 쓰러짐
    "FALL": 2,
    "INTRUSION": 3,     # 침입
    "NO_HELMET": 4,     # 보호구 미착용
    "OTHER": 5
}

def dedup_cctv_logs_within_n_minutes(
    raw_logs,                   # [{"camera_id": "CAM-01", "zone_id": "Z1", "event_type": "FIRE", "timestamp": 1700000000.0, "confidence": 0.91}, ...]
    window_minutes=5.0,
    window_mode="sliding",      # "sliding"(직전 감지 시각 기준 N분 연장) | "fixed"(최초 감지 시각 기준 N분 고정)
    false_alarm_cameras=None,   # 오탐 다발 카메라 집합 (예: {"CAM-99"})
    min_confidence=0.5,
    high_conf_for_noisy_cam=0.85
):
    """
    같은 카메라의 반복 감지를 N분 안에서 하나로 묶고, 오탐 다발 카메라 무시 경향을 방어하되
    화재(FIRE)는 어떠한 경우에도 최우선 통과시키는 전처리 함수
    """
    noisy_cams = set(false_alarm_cameras or [])
    window_sec = float(window_minutes) * 60.0

    # 1. 오탐/저신뢰도 필터링 (단, FIRE는 무조건 보존!)
    filtered = []
    for row in raw_logs:
        ev_type = str(row.get("event_type", "OTHER")).upper()
        conf = float(row.get("confidence", 1.0))
        cam_id = row["camera_id"]

        if ev_type != "FIRE":
            if conf < min_confidence:
                continue
            if cam_id in noisy_cams and conf < high_conf_for_noisy_cam:
                continue
        filtered.append(row)

    # 2. 카메라 + 이벤트 유형 + 시각 순 정렬
    sorted_logs = sorted(filtered, key=lambda r: (
        r["camera_id"],
        str(r.get("event_type", "OTHER")).upper(),
        parse_iso_or_timestamp(r["timestamp"])
    ))

    # 3. N분 이내 반복 감지 하나로 묶기
    merged_incidents = []
    active = {}  # key: (camera_id, event_type)

    for r in sorted_logs:
        cam_id = r["camera_id"]
        ev_type = str(r.get("event_type", "OTHER")).upper()
        t = parse_iso_or_timestamp(r["timestamp"])
        conf = float(r.get("confidence", 1.0))
        key = (cam_id, ev_type)

        if key in active:
            curr = active[key]
            ref_t = curr["incident_end"] if window_mode == "sliding" else curr["incident_start"]
            if (t - ref_t) <= window_sec:
                curr["incident_end"] = max(curr["incident_end"], t)
                curr["merged_count"] += 1
                curr["max_confidence"] = max(curr["max_confidence"], conf)
                continue
            else:
                merged_incidents.append(curr)
                del active[key]

        active[key] = {
            "incident_id": f"INC-{cam_id}-{ev_type}-{int(t)}",
            "camera_id": cam_id,
            "zone_id": r.get("zone_id", "DEFAULT"),
            "event_type": ev_type,
            "incident_start": t,
            "incident_end": t,
            "max_confidence": conf,
            "merged_count": 1,
            "status": "DETECTED",
            "excluded_responders": []
        }

    for inc in active.values():
        merged_incidents.append(inc)

    return merged_incidents

def assign_and_escalate_cctv_incidents(
    incidents,              # 병합된 사건 리스트
    responders,             # [{"resp_id": "R01", "zone_id": "Z1", "role": "STAFF", "status": "AVAILABLE", "assigned_count": 0}, ...]
    current_time_sec,
    ack_timeout_sec=180.0   # 3분 미응답 시 에스컬레이션
):
    # 1. 우선순위 정렬: 사고등급(화재 1순위) -> 높은 신뢰도 -> 최초 발생 시각 빠른 순 -> 사건 ID 순
    sorted_incidents = sorted(incidents, key=lambda inc: (
        PRIORITY_RANK.get(inc["event_type"], 99),
        -float(inc.get("max_confidence", 0.0)),
        float(inc["incident_start"]),
        inc["incident_id"]
    ))

    resp_map = {r["resp_id"]: r for r in responders}

    for inc in sorted_incidents:
        # JSON 직렬화 호환을 위해 list 형태로 관리
        excluded_list = list(inc.get("excluded_responders", []))

        # 이미 배정되었으나 미응답 타임아웃이 경과한 경우 -> 에스컬레이션!
        if inc.get("status") == "ASSIGNED" and not inc.get("acknowledged_at"):
            elapsed = current_time_sec - float(inc.get("assigned_at", current_time_sec))
            if elapsed >= ack_timeout_sec:
                prev_resp_id = inc.get("assigned_to")
                if prev_resp_id and prev_resp_id not in excluded_list:
                    excluded_list.append(prev_resp_id)
                inc["excluded_responders"] = excluded_list
                inc["escalation_count"] = inc.get("escalation_count", 0) + 1
                inc["status"] = "ESCALATED_PENDING"
                if prev_resp_id in resp_map:
                    resp_map[prev_resp_id]["status"] = "TIMEOUT_UNRESPONSIVE"

        # 신규 감지 또는 에스컬레이션 재배정 대상인 경우
        if inc.get("status") in ("DETECTED", "ESCALATED_PENDING"):
            excluded_set = set(inc.get("excluded_responders", []))
            target_zone = inc.get("zone_id")

            # 1차: 동일 구역 가용 대응자 탐색 (당일 배정 건수 적은 순 -> 사번 순)
            same_zone_cands = [
                r for r in responders
                if r["zone_id"] == target_zone
                and r["status"] == "AVAILABLE"
                and r["resp_id"] not in excluded_set
            ]
            same_zone_cands.sort(key=lambda r: (r.get("assigned_count", 0), r["resp_id"]))

            chosen = None
            if same_zone_cands:
                chosen = same_zone_cands[0]
            else:
                # 2차(에스컬레이션/가용 인원 부재 시): 안전팀장(MANAGER) 또는 타 구역 가용 예비 인력
                fallback_cands = [
                    r for r in responders
                    if r["status"] == "AVAILABLE" and r["resp_id"] not in excluded_set
                ]
                fallback_cands.sort(key=lambda r: (0 if r.get("role") == "MANAGER" else 1, r.get("assigned_count", 0), r["resp_id"]))
                if fallback_cands:
                    chosen = fallback_cands[0]

            if chosen:
                chosen["status"] = "BUSY"
                chosen["assigned_count"] = chosen.get("assigned_count", 0) + 1
                inc["assigned_to"] = chosen["resp_id"]
                inc["assigned_at"] = current_time_sec
                inc["status"] = "ASSIGNED"
            else:
                inc["status"] = "UNASSIGNED_QUEUE"

    return sorted_incidents
```
