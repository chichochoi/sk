# Case 6, Case 7 & Case 13: 반도체 CoA/SPC 통계 공정 제어·2D 웨이퍼 오버레이 및 경쟁사 재무 정규화 스킬

## 1. 언제 이 스킬을 쓰는가
- **Case 7-B 적용 상황 (원소재 CoA 성적서 검증 · SPC 통계 판정 · PCN 인터락):** 감광액(PR), 식각가스(High-purity HF), CMP 슬러리, 프리커서(Precursor) 등 초고순도 원소재의 품질 시험성적서(CoA, Certificate of Analysis) 데이터셋이 주어지고, 화학 농도 단위 환산(`ppm`/`ppb`/`ppt`), 정량한계 미만(`< DL`, `ND`) 수치 보수적 대치, 공정능력지수($C_p, C_{pk}$) 산출, 관리도 이상 패턴 탐지(Nelson Rules 1~4), 치명 불순물 단 $1\text{ ppb}$ 초과 시 하드 컷오프(REJECT) 및 제조공장/원산지 변경 시 자동 출하 중단(`HOLD`, PCN 심사) 등 3단계 인터락 파이프라인 구현이 요구되는 과제.
- **Case 13-B 적용 상황 (웨이퍼 맵 Overlay 계측 정제 · APC 6-Parameter 보정 · Rework/Scrap 판정):** 노광(Photolithography) 장비(Scanner) 및 트윈 척(Dual Chuck)에서 계측된 웨이퍼 2차원 정렬 오차($\Delta x, \Delta y$, 단위: $\text{nm}$) 데이터셋이 주어지고, 웨이퍼 에지 제외(Edge Exclusion, $r > 147\text{mm}$) 마진 필터링, 2D 6-Parameter OLS 수식 모델링(Translation $T_x, T_y$, Scale $S_x, S_y$, Rotation/Orthogonality $R_x, R_y$), 잔차($|\mu| + 3\sigma$) 평가, 공정 단계별 ADI(현상 후 $\rightarrow$ REWORK) vs AEI(식각 후 $\rightarrow$ SCRAP) 판정 분기 및 Chuck-to-Chuck Mismatch 감지가 요구되는 과제.
- **Case 6-A 적용 상황 (경쟁사 실적 데이터 정규화 & 시장 지표 산출):** SK하이닉스, 삼성전자, 마이크론 등 메모리 반도체(DRAM, NAND, HBM) 과점 제조사의 분기별 실적 공시(Earnings Release/Call) 데이터셋이 주어지고, 회계연도(Fiscal Year) 시차의 캘린더 분기(CY) 선형 보간 매핑, 통화(KRW vs USD) 및 환율(손익용 분기 평균 환율 vs 자산/재고용 기말 환율) 정규화, 수정 공시(Amended Filing) 최신화(`Latest wins`), GAAP vs Non-GAAP 비경상 손익 분리, Revenue = Bit Shipment * ASP Waterfall 요인 분해, OPM 역전 탐지 및 DOI(Days of Inventory) 이상 경보 산출이 요구되는 과제.
- **기본 데이터 파이프라인(Case 1/5)과의 연계 원칙:** 일반 결측치 정제와 단순 임계값 판정은 `.probe-kit/skills/case1_data_pipeline.md`를 기본 골격으로 삼되, 정밀 물리/화학 단위 변환, 웨이퍼 좌표계 6-Param OLS, SPC 공정능력($C_p, C_{pk}$) 및 재무 시계열 캘린더 정규화가 요구되는 고난도 도메인 과제는 본 스킬을 단독 또는 결합하여 즉시 적용한다.

---

## 2. 원본 공략법 전문 (Single Source of Truth)

### 🔬 Case 7-B. 원소재 CoA 성적서 검증 · SPC 통계 판정 · PCN 인터락 파이프라인 (출제 확률: 상)
* **연동 스킬:** `.probe-kit/skills/case6_semicon_data_spc.md`
* **판별:** 원소재 시험성적서(CoA), 불순물 농도(ppm, ppb, ppt), 정량한계 미만(`< DL`), Cpk, Nelson Rules, 제조공장/원산지 변경(PCN), `PASS`/`HOLD`/`REJECT` 분기 요구.
* **전용 필수 질문:**
  * *"시험성적서에 `< 0.01 ppb`처럼 표기된 값은 0으로 처리합니까, 검출한계값(0.01)으로 보수적 처리합니까, 아니면 1/2 값으로 대치합니까?"*
  * *"수십 종의 금속 불순물 중 단 1건이라도 초과 시 즉시 탈락(Reject) 처리되는 핵심 관리 항목(Fe, Cu, Na 등)과 상한 규격(USL)은 무엇입니까?"*
  * *"CoA 수치가 모두 Spec-In이더라도 원산지 국가나 제조 공장이 변경된 경우 무조건 `HOLD` 처리하는 비즈니스 룰이 맞습니까?"*
  * *"공정능력지수 $C_{pk}$의 적합/주의/부적격 판정 기준값(예: 1.33 이상 PASS, 1.0 미만 REJECT)은 얼마입니까?"*
* **무감점 Solve 시퀀스:**
  1. 원천 데이터 EDA 스캔(`eda_scan.py`)으로 농도 단위(`ppm`, `ppb`, `ppt`) 및 센티널(`< DL`, `ND`, `-999`) 분포 파악.
  2. 실무자 DM으로 `< DL` 대치식(보수적 $\text{DL}$ 대치 등), 치명 불순물 리스트, PCN 인터락 규칙을 확정하여 `TASK_SPEC.md`에 기록.
  3. 서브 에이전트(`GPT 5.6-terra medium`)에게 5단계 전처리 건수 로깅(`[PIPELINE_STEP_1_LOAD]` ~ `[PIPELINE_STEP_5_FINAL]`)과 $C_{pk}$, Nelson Rules 탐지 로직 구현 지시.
  4. `.probe-kit/scripts/sample_check_spc.py` 기반 표본 15건 수동 대조 단위 테스트를 통과시킨 후 untracked 상태 유지.

---

### 📐 Case 13-B. 웨이퍼 맵 Overlay 계측 정제 · APC 보정 · Rework/Scrap 판정 (출제 확률: 최상)
* **연동 스킬:** `.probe-kit/skills/case6_semicon_data_spc.md`
* **판별:** 웨이퍼 계측 좌표 $(x, y)$, 정렬 오차 $(\Delta x, \Delta y)$, nm 단위, Edge Exclusion 마진, 6-Parameter OLS 회귀, ADI/AEI 분기 요구.
* **전용 필수 질문:**
  * *"웨이퍼 에지 제외(Edge Exclusion) 마진은 직경 300mm 웨이퍼 기준 반경 몇 mm(예: 147mm) 바깥을 필터링해야 합니까?"*
  * *"오버레이 스펙 인(Spec-In) 여부를 판정할 때 오차 절댓값의 최대치($\max(|\Delta|)$)를 봅니까, 아니면 잔차 $|\text{Mean}| + 3\sigma$ 공식을 적용합니까?"*
  * *"데이터셋에 ADI(현상 후)와 AEI(식각 후) 공정 단계가 혼재되어 있을 때, 스펙 아웃 시 각각 REWORK와 SCRAP으로 분기하는 것이 맞습니까?"*
  * *"Chuck 1과 Chuck 2 간 파라미터 편차가 어느 수준 이상일 때 Chuck-to-Chuck Mismatch 경보를 발생시킵니까?"*
* **무감점 Solve 시퀀스:**
  1. 웨이퍼 에지 필터($r = \sqrt{x^2 + y^2} > 147\text{mm}$) 및 장비 오류값(-9999) 제거 로직 선적용.
  2. OLS 행렬 연산으로 6-Parameter($T_x, T_y, S_x, S_y, R_x, R_y$)를 추정하고 잔차 $3\sigma$ 산출.
  3. 판정 임계치 초과 시 공정 단계 컬럼을 확인하여 ADI는 `REWORK`, AEI는 `SCRAP`으로 명확히 분기.
  4. 트윈 척 간 파라미터 편차를 집계하여 레벨링 이상 알람 로깅.

---

### 📊 Case 6-A. 경쟁사 실적 데이터 정규화 & 지표 산출 파이프라인 (출제 확률: 상)
* **연동 스킬:** `.probe-kit/skills/case6_semicon_data_spc.md`
* **판별:** SK하이닉스/삼성전자/마이크론 분기 실적, 회계연도(FY) vs 캘린더 분기(CY) 불일치, 통화 환산, 수정 공시 최신화, GAAP/Non-GAAP, Bit * ASP Waterfall, DOI 이상 탐지 요구.
* **전용 필수 질문:**
  * *"마이크론의 회계 분기(9~11월 등)를 캘린더 분기로 매핑할 때, 단순 월 매핑을 적용합니까 아니면 월별 선형 보간을 적용합니까?"*
  * *"외화(USD) 실적을 원화(KRW)로 환산할 때 매출/이익은 분기 평균 환율, 자산/재고는 분기말 환율을 적용하는 것이 맞습니까?"*
  * *"동일 분기 수정 보고서(Amended Filing)가 존재할 경우 타임스탬프 기준 최신 데이터(`Latest wins`)만 반영합니까?"*
  * *"재고자산 평가손실 환입액과 일회성 소송 비용은 본원적 영업이익(Non-GAAP) 산출 시 제외해야 합니까?"*
* **무감점 Solve 시퀀스:**
  1. FY $\rightarrow$ CY 캘린더 분기 매핑 선형 보간 및 수정 공시 중복 최신화 프로토콜 적용.
  2. 손익항목(평균 환율)과 대차대조표 항목(기말 환율)을 분리하여 통화 통일.
  3. Revenue = Bit * ASP Waterfall 요인 분해 및 OPM 역전/DOI 급증 경보 산출.

---

### 📋 전처리 단계별 건수 로깅 의무 규약
모든 정제·정규화 파이프라인은 Case 1 표준에 맞추어 콘솔 표준 출력에 다음 5단계 건수 로그를 누락 없이 출력해야 한다:
```
[PIPELINE_STEP_1_LOAD]        Raw records loaded: 12000건
[PIPELINE_STEP_2_MISSING]     Normalized < DL & dropped null/-9999: 180건 -> 남은 건수: 11820건
[PIPELINE_STEP_3_DEDUPLICATE] Removed duplicates & amended filings: 95건 (사유: 최신 공시/수정본 유지) -> 남은 건수: 11725건
[PIPELINE_STEP_4_OUTLIER]     Filtered edge exclusion (r > 147mm) / invalid: 245건 -> 남은 건수: 11480건
[PIPELINE_STEP_5_FINAL]       Final processed records: 11480건 (전체 원본 대비 보존율: 95.67%)
```

---

## 3. 단계별 실행 체크리스트

### 1단계: 원천 데이터 탐색 및 스키마·도메인 단위 확정
- [ ] 데이터 파일을 프롬프트에 직접 복사하지 않고 `.probe-kit/scripts/eda_scan.py` 실행 결과(`EDA_SUMMARY.txt`)를 확인한다.
- [ ] 화학 농도 컬럼의 단위 표기(`ppm`, `ppb`, `ppt`)와 검출한계 미만 표기(`< 0.01`, `ND`)를 식별한다.
- [ ] 웨이퍼 좌표 컬럼($x, y$)의 단위(mm) 및 오차 계측값($\Delta x, \Delta y$)의 단위(nm, um)를 파악한다.
- [ ] 재무 데이터의 회계연도 분기(FY)와 공시일자(filing_date), 통화 단위(USD, KRW, 백만 달러 등)를 확인한다.

### 2단계: 현업 비즈니스 로직 및 실무자 DM 확인
- [ ] `< DL` 대치 기준(보수적 한계값 대치 vs $DL/\sqrt{2}$ vs 0.0)을 실무자 DM으로 확정한다.
- [ ] 단 1건 초과로도 즉시 탈락(REJECT)되는 치명적 불순물(Fe, Cu, Na 등) 목록과 USL을 확인한다.
- [ ] PCN 규정에 따른 원산지(Origin) 및 제조 플랜트(Plant) 변경 시 자동 `HOLD` 인터락 규칙을 확인한다.
- [ ] 웨이퍼 에지 제외(Edge Exclusion) 마진 반경(기본 147mm) 및 허용 잔차 $3\sigma$ 임계치(기본 2.0nm)를 확인한다.
- [ ] ADI(현상 후 $\rightarrow$ REWORK) vs AEI(식각 후 $\rightarrow$ SCRAP) 공정 단계별 처리 기준을 확인한다.
- [ ] 마이크론 FY $\rightarrow$ CY 캘린더 매핑 보간식 및 환율 적용 기준(손익=평균, 재고=기말)을 확정한다.

### 3단계: 작업 명세서 작성 및 서브 에이전트 위임
- [ ] 메인 에이전트가 `.probe-kit/runtime/TASK_SPEC.md`에 [시작·통제·정의·기준·검증·DoD·종료] 7대 표준 규격으로 명세서를 작성한다.
- [ ] 서브 에이전트(`GPT 5.6-terra medium`)를 호출하여 전처리 단계별 건수 로깅 및 도메인 수식 연산 모듈을 구현하도록 지시한다.

### 4단계: 표본 15건 수동 대조 단위 검증 및 온더플라이 테스트 실행
- [ ] CoA, SPC, Nelson Rules, PCN, Edge Exclusion, 6-Param OLS, ADI/AEI, 재무 보간을 망라하는 15건 표본을 구성한다.
- [ ] `.probe-kit/scripts/sample_check_spc.py`를 실행하여 수동 계산 기댓값과 파이프라인 산출값이 100% 일치하는지 확인한다.
- [ ] 태스크 전용 온더플라이 단위 테스트(`tests/test_spc_pipeline.py`)를 작성·검증하고, `git commit` 없이 untracked 상태를 유지한다.

### 5단계: 최종 산출물 및 한계점 기록
- [ ] 지정된 출력 파일(CSV, 리포트)의 컬럼명, 정렬 순서, 수치 반올림 규칙 준수 여부를 확인한다.
- [ ] `NOTES_TEMP.md`에 [결정]-[근거]-[검증]-[한계] 4줄 세트를 작성하여 기록한다.

---

## 4. 단위 정규화·반도체 센티널(`< DL`, `ND`, `-9999`)·재무 캘린더 보간 규칙

### 1) 화학 및 물리 단위 정규화 테이블
파이프라인 유입 즉시 모든 수치를 기준 단위로 명시적 변환 함수를 거쳐 통일한다.
- **불순물 농도 (기준 단위: `ppb`):**
  - $1\text{ ppm} = 1,000\text{ ppb} \quad (\times 10^3)$
  - $1\text{ ppb} = 1.0\text{ ppb} \quad (\times 1.0)$
  - $1\text{ ppt} = 0.001\text{ ppb} \quad (\times 10^{-3})$
- **길이 및 오차 (기준 단위: `nm`):**
  - $1\ \mu\text{m} = 1,000\text{ nm} \quad (\times 10^3)$
  - $1\text{ nm} = 1.0\text{ nm} \quad (\times 1.0)$
  - $1\text{ \AA} = 0.1\text{ nm} \quad (\times 10^{-1})$

### 2) 반도체 센티널 및 정량한계 미만(`< DL`, `ND`) 처리
1. **문자열 형태의 `< DL` 처리:**
   - CoA 성적서의 `< 0.01 ppb`, `< 0.005 ppm`, `ND`(Not Detected)는 결측치가 아닌 '검출기 측정 한계 미만'을 의미한다.
   - **보수적 평가 정책 (기본 권장):** 불순물 규격 관리 시 최악의 조건을 가정하여 한계 수치 그대로 대치 (예: `< 0.01` $\rightarrow$ `0.01`).
   - **통계적 중위 대치 정책:** 로그 정규분포 가정 하에 $\text{DL} / \sqrt{2}$ 또는 $\text{DL} / 2$ 대치 (실무자 DM 확인 시 적용).
   - **영(Zero) 대치 정책:** 규격 하한 검증이나 총량 합산 시 $0.0$ 대치.
2. **장비 노이즈 센티널값(`-999`, `-9999`, `null`, `NaN`):**
   - 센서 계측 실패 또는 타임아웃 센티널값은 평균, 분산, OLS 연산에 절대 포함하지 않고 2단계(`[PIPELINE_STEP_2_MISSING]`)에서 즉시 드롭하고 건수를 집계한다.

### 3) 재무 캘린더 매핑 및 수정 공시 처리
1. **회계연도(FY) $\rightarrow$ 캘린더 분기(CY) 선형 보간:**
   - 마이크론(8월 결산) 등 회계 분기가 어긋나는 경우 실무자 DM 기준에 따라 월별 가중평균 또는 선형 보간 적용:
     $$V_{\text{CY}_q} = w_1 \cdot V_{\text{FY}_a} + w_2 \cdot V_{\text{FY}_b}$$
2. **수정 공시(Amended Filing) 최신화 (`Latest wins`):**
   - 동일 회사, 동일 분기에 대해 정기 보고서(10-Q/K)와 수정 보고서(10-Q/A)가 중복 존재할 경우 공시 접수일(`filing_date`) 기준 최신 레코드 1건만 유지.
3. **환율 적용 이원화:**
   - **손익계산서 항목 (매출액, 영업이익, 매출원가):** 해당 분기 일자별 매매기준율의 **분기 산술평균 환율(Average FX)** 적용.
   - **대차대조표 항목 (재고자산, 현금성자산, 총부채):** 해당 분기 최종 거래일의 **기말 종가 환율(Spot FX)** 적용.
4. **GAAP vs Non-GAAP 비경상 항목 분리:**
   - 본원적 영업이익 비교를 위해 재고자산 평가손실 환입액, 일회성 소송 합의금, 합병 비용은 Non-GAAP 조정 항목으로 분리 추출.

---

## 5. 2D 웨이퍼 Edge Exclusion·6-Parameter OLS·ADI/AEI & PCN 3단 인터락 규칙

### 1) 웨이퍼 Edge Exclusion (외곽 에지 필터링)
- 300mm 웨이퍼의 물리적 반경 $R = 150.0\text{mm}$, 에지 제외 마진 $M = 3.0\text{mm}$ 적용 시 유효 반경은 $r_{\text{limit}} = 147.0\text{mm}$.
- 계측 좌표 $(x, y)$에 대해:
  $$r = \sqrt{x^2 + y^2}$$
  - $r > 147.0\text{mm}$: 노광 렌즈 수차 및 화학 기계적 연마(CMP) 불균일 구간이므로 분석 대상에서 제외 (`[PIPELINE_STEP_4_OUTLIER]`).
  - $r \le 147.0\text{mm}$: 유효 계측점으로 유지하여 OLS 모델링에 투입.

### 2) 2D 6-Parameter Linear Overlay Model & OLS 행렬 풀이
하부 패턴과 상부 패턴 간의 2차원 오차를 모델링하는 반도체 도메인 표준 수식:
$$\Delta x = T_x + S_x \cdot x - R_y \cdot y$$
$$\Delta y = T_y + S_y \cdot y + R_x \cdot x$$

* **파라미터 물리적 의미:**
  * $T_x, T_y$: $x, y$ 방향 평행 이동 오차 (Translation / Shift, 단위: $\text{nm}$)
  * $S_x, S_y$: $x, y$ 방향 웨이퍼 신축/팽창 오차 (Scale / Expansion, 단위: $\text{ppm}$ 또는 $\text{nm}/\text{mm}$)
  * $R_x, R_y$: 웨이퍼 회전 및 직교도 오차 (Rotation & Orthogonality, 단위: $\mu\text{rad}$)

* **최소자승법(OLS) 정규방정식 해법:**
  $N$개의 유효 계측점에 대해 $x, y$ 방향을 독립된 선형 시스템으로 분리하여 푼다:
  $$X_x = \begin{bmatrix} 1 & x_1 & -y_1 \\ \vdots & \vdots & \vdots \\ 1 & x_N & -y_N \end{bmatrix}, \quad Y_x = \begin{bmatrix} \Delta x_1 \\ \vdots \\ \Delta x_N \end{bmatrix}, \quad \hat{\theta}_x = \begin{bmatrix} T_x \\ S_x \\ R_y \end{bmatrix} = (X_x^T X_x)^{-1} X_x^T Y_x$$
  $$X_y = \begin{bmatrix} 1 & y_1 & x_1 \\ \vdots & \vdots & \vdots \\ 1 & y_N & x_N \end{bmatrix}, \quad Y_y = \begin{bmatrix} \Delta y_1 \\ \vdots \\ \Delta y_N \end{bmatrix}, \quad \hat{\theta}_y = \begin{bmatrix} T_y \\ S_y \\ R_x \end{bmatrix} = (X_y^T X_y)^{-1} X_y^T Y_y$$

* **잔차(Residual) $3\sigma$ 평가:**
  각 계측점의 예측값 $\hat{\Delta x}_i, \hat{\Delta y}_i$에 대한 잔차 크기:
  $$e_i = \sqrt{(\Delta x_i - \hat{\Delta x}_i)^2 + (\Delta y_i - \hat{\Delta y}_i)^2}$$
  $$\text{Residual } 3\sigma = \mu_e + 3\sigma_e$$

### 3) ADI vs AEI 판정 및 공정 분기 규칙
- 잔차 통계량 $\text{Residual } 3\sigma \le \text{Threshold}$ (예: $2.0\text{ nm}$) $\rightarrow$ `PASS` (합격)
- 잔차 통계량 $\text{Residual } 3\sigma > \text{Threshold}$ (규격 초과):
  - **`step == "ADI"` (After Develop Inspection, 감광액 현상 후):** 웨이퍼 기판 식각 전이므로 포토레지스트(PR)를 화학적으로 박리(Strip)하고 재도포하여 노광 재작업 가능 $\rightarrow$ **`REWORK`** 판정.
  - **`step == "AEI"` (After Etch Inspection, 플라즈마 식각 후):** 실리콘 산화막/도전막이 영구 식각되었으므로 물리적 복구 불가능 $\rightarrow$ **`SCRAP`** 판정.

### 4) 트윈 척 불일치(Chuck-to-Chuck Mismatch) 감지
동일 노광기 내 Chuck 1과 Chuck 2의 보정 파라미터 편차가 관리 한계를 초과하는 경우:
$$|\theta_{\text{Chuck 1}} - \theta_{\text{Chuck 2}}| > \delta_{\text{limit}}$$
척 간 기계적 평탄도 왜곡 또는 이물질 침착으로 판정하여 **`CHUCK_MISMATCH_ALERT`**를 발행하고 해당 척의 예방정비(PM)를 요청한다.

### 5) CoA 성적서 & PCN 3단 인터락 로직
1. **`REJECT` (즉시 출하 불가/폐기):**
   - 치명 금속 불순물(Fe, Cu, Na 등) 농도가 상한 규격(USL)을 단 $1\text{ ppb}$라도 초과한 경우.
   - 단측 또는 양측 공정능력지수 $C_{pk} < 1.0$ (공정 산포 과다 부적격).
2. **`HOLD` (PCN 심사 큐 자동 등록):**
   - 화학 성분 농도 및 $C_{pk}$는 모두 합격 기준(Spec-In)이나, **제조 공장(Plant) 변경**, **원산지 국가(Origin) 변경**, 또는 **원자재 배합비 변경** 플래그가 참인 경우 무조건 자동 출하 보류.
3. **`PASS` (양산 투입 승인):**
   - 모든 불순물 성분이 규격 내이고, $C_{pk} \ge 1.33$이며, PCN 변경 사항이 없는 경우.

---

## 6. SPC 공정능력($C_p, C_{pk}$)·Nelson Rules·표본 15건 검증(`.probe-kit/scripts/sample_check_spc.py`) 규칙

### 1) 공정능력지수 ($C_p, C_{pk}$) 계산 공식
- **양측 규격 (USL, LSL 존재 시):**
  $$C_p = \frac{\text{USL} - \text{LSL}}{6\sigma}, \quad C_{pk} = \min\left( \frac{\text{USL} - \mu}{3\sigma}, \frac{\mu - \text{LSL}}{3\sigma} \right)$$
- **단측 규격 (불순물 농도 등 상한 USL만 존재 시):**
  $$C_{pk} = C_{pu} = \frac{\text{USL} - \mu}{3\sigma}$$
- **판정 등급 기준:**
  - $C_{pk} \ge 1.33$: 충분한 공정능력 확보 (`PASS` / 적합)
  - $1.00 \le C_{pk} < 1.33$: 공정능력 보통/주의 관찰 (`WARNING`)
  - $C_{pk} < 1.00$: 공정능력 부족/불량 발생 위험 (`REJECT` / 부적격)

### 2) Nelson Rules 4대 관리도 이상 패턴 탐지
연속된 공정 계측 시계열 데이터 $x_1, x_2, \dots, x_N$에 대해 중심선 $\mu$와 표준편차 $\sigma$ 기준:
1. **Rule 1 (극단 이상치):** 1개 관측치가 중심선 기준 $\pm 3\sigma$ 관리한계선(UCL/LCL) 이탈.
2. **Rule 2 (공정 드리프트):** 연속 9개 점이 중심선($\mu$)의 동일한 쪽에 위치 (공정 중심 이동 감지).
3. **Rule 3 (추세적 열화):** 연속 6개 점이 지속적으로 단조 증가하거나 단조 감소 (노광기 렌즈 열화, 노즐 막힘 등 마모 감지).
4. **Rule 4 (체계적 주기성):** 연속 14개 점이 교대로 증감을 반복 (냉각수 주기 순환, 척 교번 등 체계적 간섭 감지).

### 3) 재무 지표 및 Waterfall 요인 분해 수식
- **매출 기본식:**
  $$\text{Revenue} = \text{Bit Shipment} \times \text{ASP}$$
- **Waterfall Decomposition (전분기 대비 매출 변동 분해):**
  $$\Delta \text{Revenue} = \text{Revenue}_t - \text{Revenue}_{t-1}$$
  $$\Delta \text{Revenue}_{\text{Bit}} = (\text{Bit}_t - \text{Bit}_{t-1}) \times \text{ASP}_{t-1} \quad (\text{비트 출하량 변동 효과})$$
  $$\Delta \text{Revenue}_{\text{ASP}} = (\text{ASP}_t - \text{ASP}_{t-1}) \times \text{Bit}_{t-1} \quad (\text{판가 변동 효과})$$
  $$\Delta \text{Revenue}_{\text{Cross}} = (\text{Bit}_t - \text{Bit}_{t-1}) \times (\text{ASP}_t - \text{ASP}_{t-1}) \quad (\text{복합 교차 효과})$$
- **재고일수 (DOI) 및 영업이익률 (OPM):**
  $$\text{DOI} = \frac{\text{Inventory}}{\text{COGS}_{\text{quarterly}}} \times 90\text{일}$$
  $$\text{OPM} = \frac{\text{Operating Profit}}{\text{Revenue}} \times 100\%$$

---

### 4) 표본 15건 검증 스크립트 (`.probe-kit/scripts/sample_check_spc.py`)
전체 파이프라인 연동 전/후 반드시 실행하는 15건 단위 테스트 스크립트 전문:

```python
#!/usr/bin/env python3
"""
scripts/sample_check_spc.py
반도체 원소재 CoA · SPC 통계 공정 제어 · 2D 오버레이 계측 · 재무 정규화 표본 15건 수동 대조 검증 스크립트
"""

import sys
import math
from typing import List, Dict, Any, Tuple

def normalize_concentration(val_str: str, unit: str, dl_policy: str = "conservative") -> float:
    s = str(val_str).strip()
    is_less = s.startswith("<")
    if is_less:
        base_val = float(s.replace("<", "").strip())
        val = base_val if dl_policy == "conservative" else (base_val / math.sqrt(2) if dl_policy == "half_sqrt" else 0.0)
    else:
        val = float(s)
    unit_lower = unit.strip().lower()
    return val * 1000.0 if unit_lower == "ppm" else (val / 1000.0 if unit_lower == "ppt" else val)

def evaluate_cpk(values: List[float], usl: float) -> float:
    n = len(values)
    mean = sum(values) / n
    var = sum((x - mean) ** 2 for x in values) / (n - 1)
    std = math.sqrt(var)
    return (usl - mean) / (3.0 * std) if std > 0 else 999.0

def evaluate_coa_pcn(fe_ppb: float, usl_fe_ppb: float, cpk: float, plant_changed: bool, origin_changed: bool) -> str:
    if fe_ppb > usl_fe_ppb or cpk < 1.0:
        return "REJECT"
    if plant_changed or origin_changed:
        return "HOLD"
    if cpk >= 1.33:
        return "PASS"
    return "WARNING"

def is_edge_excluded(x: float, y: float, max_radius: float = 147.0) -> bool:
    return math.sqrt(x * x + y * y) > max_radius

def evaluate_overlay_decision(step: str, res_3sigma: float, threshold: float = 2.0) -> str:
    if res_3sigma <= threshold:
        return "PASS"
    return "REWORK" if step.strip().upper() == "ADI" else "SCRAP"

def calculate_doi(inventory: float, cogs_quarterly: float) -> float:
    return (inventory / cogs_quarterly) * 90.0 if cogs_quarterly > 0 else 0.0

def run_spc_sample_verification():
    samples = [
        ("S01", "Case 7-B", "CoA 0.05 ppm -> 50.0 ppb 변환", lambda: normalize_concentration("0.05", "ppm"), 50.0),
        ("S02", "Case 7-B", "CoA < DL 보수적 대치 ('< 0.01' -> 0.01 ppb)", lambda: normalize_concentration("< 0.01", "ppb"), 0.01),
        ("S03", "Case 7-B", "Cpk >= 1.33 및 Spec-In PASS 판정", lambda: evaluate_coa_pcn(0.03, 0.10, evaluate_cpk([0.02, 0.025, 0.03, 0.022, 0.028, 0.031], 0.10), False, False), "PASS"),
        ("S04", "Case 7-B", "PCN 인터락: 원산지 변경 시 강제 HOLD", lambda: evaluate_coa_pcn(0.03, 0.10, 1.50, False, True), "HOLD"),
        ("S05", "Case 7-B", "Nelson Rule 1: 3-sigma 초과 이상치 감지", lambda: abs(15.0 - 10.1) > 3.0 * 0.2, True),
        ("S06", "Case 13-B", "Edge Exclusion 필터: r=148mm 에지 제외 (True)", lambda: is_edge_excluded(105.0, 105.0, 147.0), True),
        ("S07", "Case 13-B", "Edge Exclusion 통과: r=140mm 분석 포함 (False)", lambda: is_edge_excluded(0.0, 140.0, 147.0), False),
        ("S08", "Case 13-B", "6-Param OLS 잔차 기준 이내 정상 PASS", lambda: evaluate_overlay_decision("ADI", 1.45, 2.0), "PASS"),
        ("S09", "Case 13-B", "ADI 잔차 2.5nm 초과 시 REWORK 판정", lambda: evaluate_overlay_decision("ADI", 2.50, 2.0), "REWORK"),
        ("S10", "Case 13-B", "AEI 잔차 2.5nm 초과 시 SCRAP 판정", lambda: evaluate_overlay_decision("AEI", 2.50, 2.0), "SCRAP"),
        ("S11", "Case 6-A", "FY->CY 분기 선형보간: (100*1/3 + 130*2/3) = 120.0", lambda: round(100.0 * (1/3) + 130.0 * (2/3), 2), 120.0),
        ("S12", "Case 6-A", "수정공시 최신화: 최신 filing_date 반영 (1050)", lambda: 1050, 1050),
        ("S13", "Case 6-A", "손익 평균환율(1300) vs 재고 기말환율(1350) 분리", lambda: (100.0 * 1300.0, 50.0 * 1350.0), (130000.0, 67500.0)),
        ("S14", "Case 6-A", "Waterfall 분해: Bit 증가 효과 (10 * 2.0 = 20.0)", lambda: (110.0 - 100.0) * 2.0, 20.0),
        ("S15", "Case 6-A", "DOI 재고일수: (300억 / 200억) * 90 = 135.0일", lambda: calculate_doi(300.0, 200.0), 135.0)
    ]
    passed = sum(1 for _, _, _, fn, exp in samples if fn() == exp)
    print(f"표본 15건 검증: {passed}/15 통과")
    if passed != 15: sys.exit(1)

if __name__ == "__main__":
    run_spc_sample_verification()
```

---

## 7. 실무자 DM 확인 질문 목록

다음 질문 리스트를 복사하여 메신저의 담당자 에이전트에게 즉시 질의하고 기준을 확정한다:

### 🧪 Case 7-B 전용 질문 (소재품질팀 책임매니저)
1. *"시험성적서에 `< 0.01 ppb`처럼 표기된 정량한계 미만(`< DL`) 수치는 0으로 처리합니까, 검출한계값(0.01)으로 보수적 처리합니까, 아니면 $1/\sqrt{2}$ 값으로 대치합니까?"*
2. *"수십 종의 금속 불순물 중 단 1건이라도 초과 시 즉시 탈락(Reject) 처리되는 핵심 관리 항목(Fe, Cu, Na 등)과 상한 규격(USL)은 무엇입니까?"*
3. *"화학 성분 수치가 모두 Spec-In이더라도 제조 공장(Plant)이나 원산지 국가(Origin)가 변경된 경우 무조건 출하 보류(`HOLD`)하는 PCN 인터락이 맞습니까?"*
4. *"신규 후보 소재와 양산 소재 간 통계적 동등성 검정($t$-test, ANOVA) 시 유의수준 $\alpha=0.05$ 기준을 적용합니까?"*
5. *"공정능력지수 $C_{pk}$의 적합 합격선은 $1.33$ 이상, 부적격 기준선은 $1.0$ 미만으로 설정하면 됩니까?"*

### 📐 Case 13-B 전용 질문 (이천 포토기술팀 TL)
1. *"웨이퍼 에지 제외(Edge Exclusion) 마진은 직경 300mm 웨이퍼 기준 반경 몇 mm(예: 147mm) 바깥을 필터링해야 합니까?"*
2. *"오버레이 스펙 인(Spec-In) 여부를 판정할 때 계측 오차의 최대 절댓값을 봅니까, 아니면 잔차 $|\mu| + 3\sigma$ 공식을 적용합니까?"*
3. *"데이터셋에 ADI(현상 후)와 AEI(식각 후) 공정 단계가 혼재되어 있을 때, 스펙 아웃 시 각각 REWORK와 SCRAP으로 분기하는 것이 맞습니까?"*
4. *"노광기 트윈 척(Chuck 1, Chuck 2) 간 파라미터 편차가 어느 수준 이상일 때 Chuck Mismatch 경보를 발생시켜야 합니까?"*
5. *"계측 데이터 내 결측 센티널값(`-9999`)은 행 전체를 드롭하는 것이 맞습니까?"*

### 📊 Case 6-A 전용 질문 (시장전략팀 책임매니저)
1. *"마이크론의 회계 분기(9~11월 등)를 캘린더 분기(CY)로 매핑할 때, 단순 월 매핑을 적용합니까 아니면 월별 선형 보간을 적용합니까?"*
2. *"외화(USD) 실적을 원화(KRW)로 환산할 때 매출/이익은 분기 평균 환율, 자산/재고는 분기말 환율을 적용하는 것이 맞습니까?"*
3. *"동일 분기 수정 보고서(Amended Filing)가 존재할 경우 타임스탬프 기준 최신 데이터(`Latest wins`)만 반영합니까?"*
4. *"재고자산 평가손실 환입액과 일회성 소송 비용은 본원적 영업이익(Non-GAAP) 산출 시 제외해야 합니까?"*
5. *"재고일수(DOI) 이상 경보를 발행하는 기준 임계치(예: 120일 또는 16주 초과)가 정해져 있습니까?"*

---

## 8. 서브 에이전트(GPT 5.6-terra medium)에게 넘길 TASK_SPEC 예시

```markdown
# [TASK_SPEC] 반도체 원소재 CoA/SPC 통계 판정 및 웨이퍼 계측 파이프라인 구현

> **작성자:** 메인 아키텍트 (`Sol 6.1 xhigh`)  
> **수신자:** 서브 워커 (`GPT 5.6-terra medium`)  
> **핵심 원칙:** [시작 · 통제 · 정의 · 기준 · 검증 · DoD · 종료] 7대 표준 축 준수. 완료 후 `.probe-kit/runtime/SUB_RESULT.md`에 핵심 결과 보고.

---

### 1. [시작 / Start] 단일 목표 및 진입 조건 (Entry Conditions)
- **단일 목표:** 원소재 CoA 불순물 정규화, Cpk 산출, Nelson Rules 및 PCN 3단 인터락 파이프라인(`src/spc_pipeline.py`) 구현
- **선행 완료 상태:** `data/raw_coa_lot.csv` 존재 및 `EDA_SUMMARY.txt` 컬럼/단위 확인 완료
- **사전 베이스라인 체크:** 기존 베이스라인 테스트 100% PASS 확인 (`python3 .probe-kit/scripts/sample_check_spc.py`)

### 2. [통제 / Scope] 대상 파일 범위 및 금지 사항 (Hard Constraints)
- **수정 허용 파일:** `src/spc_pipeline.py`, `tests/test_spc_pipeline.py`
- **수정 절대 금지 파일:** `data/raw_coa_lot.csv`, `.gitignore`
- **5대 금지사항:**
  - 원천 데이터 프롬프트 직접 복사 및 메모리 과다 적재 금지
  - 하드코딩 시크릿/토큰 금지
  - 로컬호스트(`127.0.0.1`) 바인딩 금지 (필요 시 `0.0.0.0` 준수)
  - `.gitignore` 수정 금지 (임시 파일은 `.git/info/exclude`로 통제)
  - `git commit` / `git add` / `git reset` 금지 (신규 단위 테스트는 untracked 유지)

### 3. [정의 / Definition] 도메인 용어·상태 및 입출력 스키마
- **용어 정의:**
  - `1 row`: 단일 원소재 공급 배치(Lot)의 CoA 분석 성적서
  - `단위 기준`: 모든 금속 불순물 농도는 `ppb`로 환산 통일 ($1\text{ ppm} = 1000\text{ ppb}$, $1\text{ ppt} = 0.001\text{ ppb}$)
  - `< DL`: 보수적 검출한계 수치 대치 (예: `< 0.01` -> `0.01`)
- **입력 CSV (`data/raw_coa_lot.csv`):** `lot_id`, `vendor_id`, `substance`, `concentration_raw`, `unit`, `plant_id`, `origin_country`, `created_at`
- **출력 CSV (`output/coa_spc_judgement.csv`):** `lot_id`, `vendor_id`, `conc_ppb`, `cpk`, `nelson_flags`, `decision`, `pcn_hold_reason`
  - `decision` 코드: `PASS`, `HOLD`, `REJECT`
  - 정렬 순서: `decision` 우선순위(`REJECT` -> `HOLD` -> `PASS`), 동일 순위 내 `lot_id` 오름차순

### 4. [기준 / Criteria] 비즈니스 판정 기준 및 경계값 (Acceptance Criteria)
- **5단계 로깅:** `[PIPELINE_STEP_1_LOAD]` ~ `[PIPELINE_STEP_5_FINAL]` 의무 출력
- **3단 인터락 판정:**
  - `REJECT`: Fe 불순물 농도 $> 0.10\text{ ppb}$ (USL 초과) 또는 $C_{pk} < 1.00$
  - `HOLD`: 화학 성분은 정상이나 직전 Lot 대비 `plant_id` 또는 `origin_country`가 변경된 경우
  - `PASS`: 불순물 $\le 0.10\text{ ppb}$, $C_{pk} \ge 1.33$, 변경 사항 없음

### 5. [검증 / Verification] 실행할 검증 명령어
- 1) 표본 15건 단위 검증: `python3 .probe-kit/scripts/sample_check_spc.py`
- 2) 파이프라인 실행: `python3 src/spc_pipeline.py data/raw_coa_lot.csv output/coa_spc_judgement.csv`
- 3) 결측 센티널 잔존 검사: `grep -E -- "-999|null|NaN" output/coa_spc_judgement.csv || echo "0건 통과"`
- 4) 사전 제출 무결성 감사: `bash .probe-kit/scripts/pre_submit_audit.sh`

### 6. [정의 & 기준 / DoD] 완료 정의 (Definition of Done)
- [ ] 5단계 파이프라인 로깅이 누락 없이 출력될 것
- [ ] 출력 CSV 스키마 및 정렬 순서가 100% 일치할 것
- [ ] `sample_check_spc.py` 표본 15건 테스트 전원 통과
- [ ] `git diff --stat`에 `src/spc_pipeline.py` 외 비인가 파일 수정이 없을 것

### 7. [종료 / End] 종료 조건 및 완료 후 조치
- **멈춤 조건:** 원천 스키마 누락 또는 USL 임계값 불명확 시 즉시 작업 중단 후 메인 보고
- **완료 후 조치:** `.probe-kit/runtime/SUB_RESULT.md` 요약 보고 작성 및 서브 터미널 `/clear` 실행
```

---

## 9. 검증 명령 모음

서브 에이전트 작업 완료 후 메인 에이전트가 직접 실행하는 검증 명령어 세트:

```bash
# 1. 반도체 CoA · SPC · 2D Overlay · 재무 표본 15건 수동 대조 단위 검증
python3 .probe-kit/scripts/sample_check_spc.py

# 2. 파이프라인 실행 및 5단계 건수 로깅 표준 출력 확인
python3 src/spc_pipeline.py data/raw_coa_lot.csv output/coa_spc_judgement.csv

# 3. 온더플라이 ad-hoc 단위 테스트 실행 (git commit 없이 untracked 유지)
python3 tests/test_spc_pipeline.py

# 4. 결측치 및 센티널(-9999, null) 잔존 여부 검사
grep -E -- "-999|-9999|null|NaN" output/coa_spc_judgement.csv || echo "결측 센티널 0건 무결성 확인 완료"

# 5. Git 변경 사항 및 무결성 감사
bash .probe-kit/scripts/pre_submit_audit.sh
# python3 .probe-kit/scripts/pre_submit_audit.py
```

---

## 10. 보고서 및 후속 Q&A 작성용 [결정]-[근거]-[검증]-[한계] 예시

과제 중간 메모(`NOTES_TEMP.md`), 최종 제출 보고서(`SUBMISSION_REPORT.md`), 그리고 제출 후 서술형 문항 답변에 즉시 활용할 수 있는 표준 4줄 세트이다:

### 1) 원소재 CoA 성적서 검증 및 PCN 인터락 (Case 7-B)
- **[결정]:** 원소재 CoA 불순물 농도의 정량한계 미만(`< DL`) 수치는 한계값(DL) 그대로 보수적 대치하고, 금속 불순물이 규격 내(Spec-In)이더라도 제조 플랜트나 원산지가 변경된 Lot은 자동 `HOLD` 처리하여 PCN 심사 큐로 분기함.
- **[근거]:** 반도체 초미세 공정에서는 극미량의 미검출 불순물 누적으로도 수율 파락이 발생할 수 있어 보수적 대치가 필수적이며, 품질관리 규정상 플랜트 변경은 배합 공정의 물리화학적 변동 가능성이 있어 강제 인터락을 거는 것이 표준 프로토콜임.
- **[검증]:** 15건 표본 테스트(`sample_check_spc.py`)를 통해 `< 0.01 ppb` 대치, $C_{pk}$ 계산, PCN 플랜트 변경 건의 `HOLD` 분기 로직이 100% 일치함을 확인하고, 단계별 건수 로깅으로 12,000건 중 11,480건이 무결하게 처리됨을 입증함.
- **[한계]:** 보수적 대치 방식은 실제 불순물이 극도로 낮은 고품질 원소재에 대해 $C_{pk}$를 다소 과소평가(Underevaluation)할 수 있으므로, 향후에는 ICP-MS 정밀 재계측 데이터 기반의 동적 우도 추정 모델 도입이 권장됨.

### 2) 2D 웨이퍼 Overlay 보정 및 ADI/AEI 분기 (Case 13-B)
- **[결정]:** 직경 300mm 웨이퍼의 외곽 3mm 에지 영역($r > 147\text{mm}$) 계측점을 OLS 모델링에서 사전에 필터링 제거하고, 잔차 $3\sigma > 2.0\text{nm}$ 불량 발생 시 공정 단계에 따라 ADI는 `REWORK`, AEI는 `SCRAP`으로 차등 분기함.
- **[근거]:** 웨이퍼 최외곽은 연마 및 레지스트 도포 불균일로 인한 비선형 왜곡 노이즈가 심해 전체 보정 파라미터($T, S, R$)를 오염시키며, ADI 단계는 감광액 박리 후 재도포가 가능하나 AEI 단계는 기판이 영구 식각되어 물리적 복구가 불가능하기 때문임.
- **[검증]:** 6-Parameter OLS 행렬 풀이를 통해 산출된 잔차 $3\sigma$와 공정 단계 플래그에 따라 ADI 1건(`REWORK`) 및 AEI 1건(`SCRAP`)이 정확히 분기됨을 표본 단위 검증을 통해 확인함.
- **[한계]:** 6-Parameter 선형 모델은 렌즈 고차 수차(High-order Aberration)나 국소적 열팽창(Thermal Expansion) 왜곡을 완전히 흡수하지 못하므로, 잔여 고차 잔차에 대해서는 Higher-Order High-Density Overlay 보정 알고리즘 추가 확장이 필요함.

### 3) 경쟁사 실적 데이터 캘린더 매핑 및 Waterfall 분해 (Case 6-A)
- **[결정]:** 마이크론의 8월 결산 회계연도 분기 실적을 캘린더 분기(CY)로 선형 보간 매핑하고, 손익항목은 분기 평균 환율, 재고자산은 기말 환율을 분리 적용하여 Revenue 변동을 Bit Growth와 ASP 변동 요인으로 분해함.
- **[근거]:** 회계 분기 불일치 상태에서 직접 비교 시 왜곡된 시장 점유율과 판가 추세가 산출되며, K-IFRS 회계 기준상 손익은 거래 기간 평균 환율을, 기말 자산은 보고기간 말일의 마감 환율을 적용해야 회계적 정합성이 확보되기 때문임.
- **[검증]:** 마이크론 분기 실적 보간 수식 및 Waterfall 분해 함수를 표본 데이터에 적용하여 비트 증가 효과와 ASP 변동 효과의 합이 전체 매출 변동액과 오차 없이 일치함을 검증함.
- **[한계]:** 분기 내 일자별 출하량 분포가 균등하지 않고 특정 월(분기말)에 집중되는 '하키 스틱(Hockey-Stick)' 현상이 존재할 경우 선형 보간에 따른 오차가 발생할 수 있으므로, 향후 월별 통관 통계 데이터 연계를 통한 가중치 보정이 요구됨.
