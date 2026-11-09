# Case 7 (FDE / Full-Stack): 반도체 밸류체인 수급·시뮬레이터 & 멀티 페르소나 인터랙티브 웹앱 구축 스킬

## 1. 언제 이 스킬을 쓰는가
- **적용 상황:**
  - **#14 경영전략팀 시장분석 TL (`skhynix-value-chain-business-persona`):** 반도체 밸류체인(IP/EDA $\rightarrow$ Fabless $\rightarrow$ Foundry/Memory $\rightarrow$ OSAT $\rightarrow$ CSP) 공급망 수급 충격 전파, HBM/CoWoS 후공정 병목 클리핑, SPOF(단일 장애점) 탐지 What-If 시뮬레이터 웹앱 구축 과제.
  - **#15 반도체 산업교육 TL (`skhynix-value-chain-educator-persona`):** 밸류체인 지식 그래프 기반 직무별(신입/공정엔지니어/경영기획) Level-Adaptive 설명, 주관식 오개념(Misconception) 실시간 교정 진단, 치명적 안전/품질 오판 시 즉각 `FAIL_INTERLOCK`을 발동하는 사내 교육 코칭 AI 웹앱 구축 과제 (4번 PUBG 코칭 웹앱의 반도체 쌍둥이 과제).
  - **#14+#15 Dual-Mode 통합 플랫폼:** 단일 백엔드 지식 그래프 Core를 기반으로 상단 `Role Switcher`를 통해 [전략 분석가 모드]와 [산업 교육자 모드]를 동시 제공하는 복합 FDE 웹 서비스.
  - **FDE 대시보드 / AI 코파일럿 확장 과제:**
    - **#6-C 시장전략팀 책임매니저:** 어닝콜/IR Financial RAG & 환율·판가·CapEx 민감도 What-If 대시보드
    - **#7-C 소재품질팀 책임매니저:** 원소재 CoA 검증, PCN 심사 워크플로우 & 소재-수율 이상 역추적 AI 서비스
    - **#13-C 이천 포토기술팀 TL:** 2D 원형 웨이퍼 맵 벡터(Quiver)/히트맵 렌더링 & 노광 호기 트러블슈팅 코파일럿
    - **#12 Dietitian (개인 맞춤 식단 추천) 변형:** 거시적 월간 식단(ILP)에서 확장된 알러지 Hard Cutoff, 영양 상한선, 실시간 식당 혼잡도 및 잔여 식자재 기반 "오늘의 메뉴 맞춤 추천" 미시 개인화 웹 서비스
- **평가 포인트:**
  - 백엔드 수리 연산(순수 Python DAG 순회, 누적 복합 수율, 병목 클리핑, 오개념 매칭 엔진)과 프론트엔드 UI 렌더링의 철저한 관심사 분리(SoC).
  - 플랫폼 가상 환경 내장 브라우저 호환성을 위한 **`0.0.0.0` 바인딩** 필수 준수 및 즉각적인 UI 상호작용(슬라이더 드래그, 탭 전환, 폼 제출) 반응성 증명.
  - 극단적 경계값(감쇠율 0, 100% 셧다운, 치명 금지어 입력 등) 유입 시 서버 프로세스가 다운(500)되지 않고 **HTTP 400/422 방어** 및 UI 상의 직관적 피드백(Red/Amber/Green 상태 배지 및 경고 모달) 보장.

---

## 2. 원본 공략법 전문 (Single Source of Truth)

### 🌐 Case 7 (FDE). 멀티 페르소나 밸류체인 시뮬레이터 & 교육 AI 웹앱 미션 (출제 확률: 최상)
* **연동 스킬:** `.probe-kit/skills/case7_fde_valuechain_app.md` (보조: `.probe-kit/skills/case2_web_service.md`, `.probe-kit/skills/case4_policy_rag_doc.md`)
* **판별:**
  * *"반도체 공급망 수급 충격을 시뮬레이션하는 대시보드를 구축하라"* 또는 *"사내 임직원 대상 반도체 생태계 학습 및 오개념 진단 튜터를 구현하라"*
  * 시스템 식별자에 `skhynix-value-chain-*` 명시, 단일 지식 그래프 기반 다중 역할(Persona) 분기 요구.
* **불변 4대 원칙 (Non-Negotiable Architecture Rules):**
  1. **`0.0.0.0` 바인딩 절대 준수:**
     내장 브라우저 및 평가 샌드박스는 컨테이너 외부 프록시로 접근하므로, `localhost` 또는 `127.0.0.1`로 띄우면 `ERR_CONNECTION_REFUSED`로 0점 처리된다. 반드시 `uvicorn --host 0.0.0.0 --port 8000` (또는 `PORT 3000`)으로 바인딩한다.
  2. **프레임워크 최우선 권장 (FastAPI + HTML/JS 단일 서빙):**
     Node/Vite 환경의 포트 경합 및 빌드 에러를 차단하기 위해, **Python FastAPI 백엔드 + `StaticFiles`를 통한 단일 HTML/Tailwind/Vanilla JS 서빙**을 최우선 채택한다 (필요 시 Streamlit 단일 파일도 허용되나 인터랙티브 그래프/Role Switcher 제어에는 FastAPI+HTML이 가장 안정적).
  3. **HTTP 500 차단 및 이중 방어막 (400 Bad Request):**
     부적절한 JSON, 음수 수치, 미존재 노드 ID, 빈 텍스트 전송 시 전역 예외 처리기에서 표준 JSON 400/422 응답을 반환하여 서버 크래시를 원천 방지한다.
  4. **Strict Grounding & 환각(Hallucination) 통제:**
     AI 튜터 및 질의응답 기능 구현 시 외부 API 키 의존 없이 내장된 지식 그래프 Core 및 사전 정의된 루브릭/규정 조항만을 인용해야 하며, 근거 데이터가 없는 질문에는 *"사내 지식 베이스에서 확인할 수 없는 항목입니다"*를 확정 출력한다.
* **무감점 Solve 시퀀스:**
  1. 메인(`Sol 6.1 xhigh`)이 밸류체인 수리 엔진(DAG 충격 전파, 수율 곱, 병목 클리핑)과 튜터 진단 로직을 순수 Python 모듈(`engine/`)로 설계.
  2. 서브(`GPT 5.6-terra medium`)가 순수 수리 엔진 단위 테스트(pytest)를 먼저 검증한 후, FastAPI 엔드포인트(`POST /api/simulate`, `POST /api/diagnose`)와 `static/index.html` UI를 수직 완성.
  3. 화면 상단에 `[경영전략 모드] <-> [산업교육 모드]` Role Switcher를 배치하고, 상단 Top 3~4 KPI 요약 카드(Green/Amber/Red)와 인터랙티브 What-If 슬라이더를 연동.
  4. 서버를 `0.0.0.0:8000`에 백그라운드로 구동하고 내장 Browser에서 슬라이더 조작 및 퀴즈 제출을 직접 수행하여 플랫폼 로그 기록.

---

## 3. 단계별 실행 체크리스트

### 1단계: 요구사항 분해 및 페르소나 모드 판정
- [ ] 문제 지시서를 분석하여 #14(전략 시뮬레이터), #15(교육 튜터), #14+#15(듀얼 모드), 또는 #6-C/#7-C/#13-C/#12 대시보드 변형인지 판정한다.
- [ ] 단일 모드일 경우 해당 화면을 수직 완성하고, 듀얼 모드일 경우 상단 헤더의 `Role Switcher` 탭 분기를 핵심 동선으로 정의한다.
- [ ] 백엔드 연산용 지식 베이스(노드, 엣지, 정답 루브릭, 안전 규정) 데이터셋 파일 경로를 확인한다.

### 2단계: 순수 Python 백엔드 연산 엔진 구현 (`engine/`)
- [ ] UI 및 웹 프레임워크와 완전히 분리된 독립 파이썬 파일(`engine/valuechain.py`)을 작성한다.
- [ ] DAG 충격 전파 수식($\gamma$ 감쇠 계수, 홉 카운트 반영)과 누적 복합 수율($\prod Y_k$), CoWoS/HBM 병목 클리핑($\min$) 함수를 구현한다.
- [ ] 주관식 오개념 진단 엔진 및 안전/품질 치명 키워드 감지 시 즉각 `FAIL_INTERLOCK` 분기 로직을 구현한다.
- [ ] 순수 엔진 로직에 대한 온더플라이 단위 테스트(`tests/test_engine.py`)를 작성하여 PASS를 확인한다 (*git commit 금지, untracked 유지*).

### 3단계: FastAPI REST API 엔드포인트 및 입력 유효성 검증 작성
- [ ] Pydantic 모델을 정의하여 슬라이더 값 범위(0.0 ~ 1.0), 필수 텍스트 길이, 노드 식별자 형식을 엄격히 검증한다.
- [ ] 누락되거나 잘못된 형식의 입력에 대해 HTTP 500이 아닌 HTTP 400 Bad Request JSON을 반환하는 전역 예외 처리기를 구축한다.
- [ ] `GET /api/health`, `POST /api/simulate`, `POST /api/diagnose` 엔드포인트를 노출한다.

### 4단계: 프론트엔드 UI 구축 및 3대 핵심 컴포넌트 바인딩
- [ ] 상단 헤더에 `Role Switcher` 토글 버튼을 고정 배치한다.
- [ ] **컴포넌트 1 (Top 3~4 KPI 요약 카드):** 핵심 상태를 Red/Amber/Green 배지와 함께 표시한다.
- [ ] **컴포넌트 2 (What-If 인터랙티브 슬라이더 / 폼):** 충격량 조절 슬라이더 및 진단 입력창을 구현한다.
- [ ] **컴포넌트 3 (Actionable Insight & 시각화):** 병목 노드 하이라이트 네트워크 그래프(또는 SVG/HTML 리스트)와 구체적 권고 조치 텍스트를 렌더링한다.

### 5단계: `0.0.0.0` 바인딩 구동 및 플랫폼 내장 Browser 검증
- [ ] 서버를 `uvicorn main:app --host 0.0.0.0 --port 8000`으로 실행하고 터미널을 백그라운드로 유지한다.
- [ ] 플랫폼 우측 내장 Browser에서 `http://0.0.0.0:8000`에 접속하여 직접 슬라이더를 조작하고 답변을 제출한다 (마우스 클릭 및 화면 이동 로그 확보).
- [ ] `curl` 명령어로 정상 호출 및 경계값/오류값 400 방어 스모크 테스트를 수행한다.

### 6단계: 산출물 정리 및 기록
- [ ] `NOTES_TEMP.md`에 [결정]-[근거]-[검증]-[한계] 4줄 세트를 작성한다.
- [ ] `git status`로 임의의 커밋이나 트래킹 파일 변경이 없는지 확인한다 (*시험 중 git commit/clean/reset 절대 금지*).

---

## 4. 밸류체인 DAG 충격 전파·누적 복합 수율·병목 클리핑 엔진 규칙

모든 수리 및 도메인 비즈니스 로직은 웹 프레임워크나 프론트엔드 코드와 분리된 순수 Python 엔진(`engine/valuechain.py`)에 구현해야 한다.

### 1. 가중 방향 그래프(DAG) 충격 전파 (Ripple Effect) 알고리즘
- 공급망 노드 $V$ (IP, 팹리스, 파운드리, OSAT, 소부장, CSP)와 공급선 엣지 $E$를 정의한다.
- 특정 상류(Upstream) 노드 $i$에서 생산 차질 충격 $S_i(t) \in [0, 1]$ 발생 시, 하류(Downstream) 노드 $j$로 전달되는 충격도는 감쇠 계수(Decay factor $\gamma \in (0, 1]$)와 노드 간 위상적 거리(Hop count $d(i, j)$)에 의해 감쇠 전파된다:
  $$S_j(t + \Delta t) = \min\left(1.0, \sum_{i \in \text{Pre}(j)} S_i(t) \cdot W_{ij} \cdot \gamma^{d(i, j)}\right)$$
  *(여기서 $W_{ij}$는 $j$ 입장에서 $i$에 의존하는 조달 비중 가중치, $\sum_{i} W_{ij} = 1.0$)*

### 2. 다단계 칩렛 및 HBM 누적 복합 수율 (Compound Yield)
- 단일 칩 공정과 달리 HBM3E 및 2.5D 패키징은 전공정 웨이퍼 수율뿐만 아니라 적층/본딩 수율이 곱셈으로 누적된다:
  $$Y_{\text{final}} = Y_{\text{fab}} \times Y_{\text{sort}} \times (Y_{\text{tsv}})^{N_{\text{stack}}} \times Y_{\text{stacking}} \times Y_{\text{cowos}}$$
- 어느 한 단계의 수율이 $0$으로 떨어지면 최종 유효 수율도 즉시 $0$이 되며, 감쇠 수율에 따른 유효 다이(Good Die) 출하량을 백엔드에서 정밀 계산한다.

### 3. 후공정 병목 클리핑 (Bottleneck Clipping) 함수
- 최종 AI 서버 완제품 또는 가속기 모듈 출하량은 각 공정 단계의 최대 가용 캐파 중 가장 좁은 병목에 의해 상한이 잘린다(Clipping):
  $$\text{Effective Output} = \min\left( \text{GPU Die Capa}, \frac{\text{HBM Capa}}{N_{\text{stack}}}, \text{CoWoS Packaging Capa}, \text{Substrate Capa} \right)$$
- 병목 원인이 되는 단일 노드를 자동으로 식별하여 `SPOF (Single Point of Failure)` 플래그를 부여한다.

### 4. HBM vs DDR5 중복 집계(Double-Counting) 배제 원칙
- 동일 데이터센터 서버 내에 소요되는 호스트 프로세서용 메모리(DDR5 RDIMM)와 AI 가속기용 메모리(HBM3E)는 규격 및 생산 라인이 분리된다.
- 팹 웨이퍼 투입량 계산 시 DDR5와 HBM을 단순 합산하지 않고 웨이퍼 면적 페널티(HBM은 동일 용량 대비 약 2.5~3배 웨이퍼 면적 소모)를 독립 변수로 분리하여 계산한다.

### 5. 엔진 구현 코드 뼈대 예시 (`engine/valuechain.py`)
```python
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional

@dataclass
class SupplyNode:
    node_id: str
    name: str
    tier: str  # SME, Fabless, Foundry, OSAT, CSP
    capacity: float
    base_yield: float = 1.0

class ValueChainEngine:
    def __init__(self):
        self.nodes: Dict[str, SupplyNode] = {}
        self.edges: Dict[str, List[Tuple[str, float]]] = {}  # u -> list of (v, weight)

    def add_node(self, node: SupplyNode):
        self.nodes[node.node_id] = node
        if node.node_id not in self.edges:
            self.edges[node.node_id] = []

    def add_edge(self, u: str, v: str, weight: float):
        self.edges[u].append((v, weight))

    def simulate_shock(self, source_node: str, shock_magnitude: float, decay: float = 0.85) -> Dict[str, float]:
        """BFS 기반 충격 전파 시뮬레이션 (0.0 <= shock <= 1.0)"""
        shocks: Dict[str, float] = {nid: 0.0 for nid in self.nodes}
        if source_node not in self.nodes:
            raise ValueError(f"존재하지 않는 노드 ID: {source_node}")

        shocks[source_node] = min(1.0, max(0.0, shock_magnitude))
        queue = [(source_node, shocks[source_node], 0)]

        while queue:
            curr, curr_shock, depth = queue.pop(0)
            for neighbor, weight in self.edges.get(curr, []):
                propagated = curr_shock * weight * (decay ** 1)
                if propagated > 0.01:
                    new_shock = min(1.0, shocks[neighbor] + propagated)
                    shocks[neighbor] = new_shock
                    queue.append((neighbor, propagated, depth + 1))

        return {k: round(v, 4) for k, v in shocks.items()}

    def calculate_compound_yield(self, fab_y: float, sort_y: float, tsv_y: float, stack_count: int, cowos_y: float) -> float:
        """HBM 적층 및 CoWoS 누적 복합 수율 계산"""
        yield_final = fab_y * sort_y * (tsv_y ** stack_count) * cowos_y
        return max(0.0, min(1.0, round(yield_final, 4)))

    def calculate_bottleneck_output(self, gpu_capa: float, hbm_capa: float, stack_per_gpu: int, cowos_capa: float) -> Tuple[float, str]:
        """후공정 병목 클리핑 계산 및 병목 노드 반환"""
        hbm_effective = hbm_capa / stack_per_gpu if stack_per_gpu > 0 else 0.0
        capacities = {
            "GPU Die": gpu_capa,
            "HBM Sub-stack": hbm_effective,
            "CoWoS Packaging": cowos_capa
        }
        bottleneck_node = min(capacities, key=capacities.get)
        system_output = capacities[bottleneck_node]
        return system_output, bottleneck_node
```

---

## 5. Multi-Persona `Role Switcher` 및 FDE 대시보드 3대 UI 필수 규칙

### 1. Multi-Persona `Role Switcher` 인터페이스
- 화면 상단 내비게이션 바에 모드 전환 버튼을 항상 노출한다:
  - `[🏢 경영전략 모드 (경영전략팀 시장분석 TL)]` $\leftrightarrow$ `[🎓 산업교육 모드 (반도체 산업교육 TL)]`
- 모드 전환 시 페이지 전체를 리로드하지 않고, DOM 컨테이너 토글(`display: none / block`) 또는 비동기 컴포넌트 렌더링으로 0.1초 내 즉각 전환한다.

### 2. FDE 대시보드 3대 UI 필수 규칙
1. **Top 3~4 KPI 요약 카드 (Red / Amber / Green 상태 배지 필수):**
   - 사용자가 시스템에 접속하자마자 최상단에서 시스템 전체 상태를 즉시 인지할 수 있도록 배치한다.
   - **#14 경영전략 모드:** [총 예상 출하량 (K ea)], [최대 병목 공정(SPOF)], [공급망 평균 충격도(%)], [리드타임 지연(일)]
   - **#15 산업교육 모드:** [진단 참여자 수], [평균 이해도(점)], [치명 오개념 발생률(%)], [FAIL_INTERLOCK 발동 건수]
   - **#6-C 시장전략 모드:** [영업이익 민감도], [DRAM/HBM Bit Growth], [환율 영향액], [CapEx 집행률]
   - **#7-C 소재품질 모드:** [CoA 불순물 Pass율], [Cpk 지수], [이원화 배분율], [PCN 승인 대기]
   - **#13-C 포토기술 모드:** [Overlay 3-Sigma 오차], [Scrap 위험 Lot수], [노광기 가동률], [PM 도래 척 수]
   - 지표 수치 우측에 `정상(Green)`, `주의(Amber)`, `위험(Red)` 배지를 명확한 색상과 함께 렌더링한다.

2. **Interactive What-If 파라미터 조절 슬라이더:**
   - 사용자가 파라미터(`충격 발생 노드 선택`, `공급 차질율 0~100%`, `감쇠율 0.5~1.0`, `HBM 적층 단수 8/12/16단`)를 드래그하면 즉각 백엔드 API를 비동기 호출하거나 계산 결과를 화면에 실시간 반영한다.
   - 연타 또는 연속 드래그 시 브라우저가 버벅거리지 않도록 Debounce(200ms) 처리한다.

3. **Actionable Insight & 권고 조치 패널:**
   - 단순한 수치 나열에 그치지 않고, 현업 의사결정권자가 즉시 실행할 수 있는 실질적 조치 가이드를 하단에 강조 박스로 제시한다.
   - *예시: "⚠️ [병목 감지] CoWoS 패키징 공정에서 3,500장의 생산 클리핑이 발생하고 있습니다. 단기 대책으로 서브 OSAT 파트너사에 15% 외주 물량 전환을 권고합니다."*

### 3. 네트워크 그래프 및 특화 시각화 가이드
- 별도의 무거운 외부 차트 라이브러리 설치 실패를 방지하기 위해, 순수 HTML5 `<svg>` 또는 경량 Canvas/D3/Mermaid 방식으로 노드와 엣지를 렌더링한다.
- 충격을 받은 노드는 붉은색 펄스 효과, 안전한 노드는 초록색으로 시각화한다.
- 13-C 웨이퍼 맵의 경우 원형 SVG 내에 다이 격자 및 벡터 화살표(Quiver)를 렌더링한다.

---

## 6. 교육용 Level-Adaptive 설명·오개념 진단 및 즉각 `FAIL_INTERLOCK` 규칙

### 1. 직무별 3단계 Level-Adaptive 설명 엔진 (#15 반도체 산업교육 TL)
사용자의 선택 직무에 따라 동일 반도체 공정에 대해 완전히 다른 층위의 설명 텍스트를 제공한다:
- **비전공자 / 신입사원 모드 (Level 1):**
  - 일상적 비유 중심. 전문 용어 최소화.
  - *예시: "HBM은 고속도로 1차선 도로를 1024차선으로 대폭 넓히기 위해 아파트처럼 칩을 수직으로 높게 쌓아 올린 메모리입니다."*
- **공정 엔지니어 모드 (Level 2):**
  - 물리화학적 메커니즘, 장비 파라미터, 열팽창계수(CTE), 누적 수율 수식 중심.
  - *예시: "TSV 전극 관통 후 MR(Microbump Reflow) 또는 NCF 압착 본딩을 적용하며, 16단 적층 시 Warpage 제어 및 열 방출 불량이 누적 수율의 핵심 제어 인자입니다."*
- **경영전략 직군 모드 (Level 3):**
  - 시장 수급, 캐파 가동률, ASP 프리미엄, 병목 클리핑 손실 비용 중심.
  - *예시: "HBM3E의 다이 면적 페널티(일반 DDR5 대비 2.8배)로 인한 웨이퍼 Capa 잠식과 CoWoS 패키징 외주 비용 상승이 영업이익률의 트레이드오프입니다."*

### 2. 서술형 오개념(Misconception) 실시간 진단 피드백 엔진
- 교육생의 주관식 답변에서 반도체 핵심 개념의 혼동 여부를 감지한다:
  - **혼동 1:** DRAM의 주기적 리프레시(휘발성)와 NAND의 웨어레벨링/가비지컬렉션 혼동
  - **혼동 2:** 2.5D CoWoS 인터포저 본딩과 기존 와이어 본딩의 대역폭 차이 혼동
  - **혼동 3:** HBM 비트그로스와 단순 웨이퍼 투입량의 1:1 매핑 오류
- 오개념 감지 시 단순히 "오답"으로 표기하지 않고, **[오개념 원인 분석]**과 **[올바른 개념 교정 가이드]**를 친절하게 출력한다.

### 3. 치명적 안전/품질 오판 시 즉각 `FAIL_INTERLOCK` 발동 규칙
현장 안전 및 품질에 직결되는 치명적 오답 입력 시, 점수 감점으로 끝나지 않고 **즉시 0점 처리 및 시스템 비상 인터락**을 발동한다:
- **절대 금지 위험 키워드 목록:**
  - *"가스 누출 경보 시 환기 팬 끄고 확인"*
  - *"클린룸 화재 시 물 스프링클러 수동 개방"*
  - *"스펙 아웃 원소재를 라인 가동률 유지를 위해 임의 투입"*
  - *"인터락 센서를 우회(Bypass)하여 장비 강제 가동"*
- **인터락 발동 시 동작:**
  - 화면 전체에 빨간색 경고 모달 표시 (`🚨 CRITICAL SAFETY INTERLOCK ACTIVATED`)
  - 점수 즉시 `0점 (FAIL)` 확정 및 관리자 통보 로그 생성
  - 해당 모듈 재응시 차단 (선수과목 이수 취소)

### 4. 선수과목 의존성 (Prerequisite DAG) 제어
- [기초 반도체 물성] $\rightarrow$ [웨이퍼 전공정 8대 공정] $\rightarrow$ [첨단 HBM/CoWoS 패키징] 선후관계 DAG 구축.
- 선행 과목 테스트를 통과(Pass)하지 못한 경우 후속 심화 모듈을 비활성화(`LOCKED`)한다.

### 5. #12 Dietitian (개인 맞춤 식단 추천) 변형 (미시 맞춤 추천 필터링 규칙)
거시 식단 편성(ILP)에서 "오늘의 메뉴 맞춤 추천"으로 확장 시 적용하는 4단계 파이프라인:
1. **알러지 성분 Hard Cutoff:** 개인 프로필에 등록된 알러지 유발 식품(땅콩, 새우, 우유 등) 포함 코너 즉시 배제.
2. **영양소 임계 상한선 필터:** 고혈압/당뇨 관리 대상자의 경우 나트륨 $\le 800\text{mg}$, 당류 $\le 15\text{g}$ 초과 메뉴 필터링.
3. **실시간 혼잡도 동적 가중치 감산:** 특정 코너 대기열이 20명 초과 시 추천 점수 감산하여 대기 분산 유도.
4. **잔여 식자재 재고 우선 소진 가산:** 당일 폐기 위험이 있는 잔여 식자재 비중이 높은 메뉴에 추천 가중치 $+0.2$ 부여 후 최종 Top 1~3 메뉴 카드 렌더링.

---

## 7. 실무자 DM 확인 질문 목록

과제 시작 직후 문제의 세부 도메인 제약을 확정하기 위해 실무자 페르소나에게 보낼 필수 확인 질문 세트:

### 1. #14 경영전략팀 시장분석 TL (경영전략 밸류체인 시뮬레이터)
1. *"공급망 충격이 상류에서 하류로 전달될 때 노드 간 감쇠 계수(Decay Factor) 기본값(예: 0.85)과 리드타임 시차 반영 공식이 정해져 있습니까?"*
2. *"HBM 생산 수율 계산 시 웨이퍼 소팅 수율, TSV 관통 수율, 적층 본딩 수율의 단순 누적 곱($\prod Y_k$) 모델을 적용하면 됩니까?"*
3. *"AI 가속기 완제품 출하량 병목(SPOF) 산정 시 CoWoS 패키징 캐파와 HBM 스택 공급량 중 1차 제약 조건은 무엇입니까?"*
4. *"데이터센터 수요 집계 시 호스트 CPU용 DDR5와 가속기용 HBM의 웨이퍼 면적 환산 계수(예: 1:2.8)를 적용해야 합니까?"*
5. *"시뮬레이터에서 충격 전파를 계산할 때 특정 협력사의 이원화(Dual-Sourcing) 대체 공급 비율이 사전에 정의되어 있습니까?"*

### 2. #15 반도체 산업교육 TL (반도체 산업교육 AI 튜터)
1. *"직무별 Level-Adaptive 설명에서 지원해야 하는 필수 직무 그룹이 [신입/비전공자], [공정 엔지니어], [경영전략] 3가지로 확정입니까?"*
2. *"주관식 오개념 진단 평가 시 키워드 매칭 기반의 룰베이스 루브릭을 적용합니까, 아니면 임베딩 유사도 기반 평가를 적용합니까?"*
3. *"치명적 안전 수칙 위반 시 즉각 0점 처리되는 절대 금지 인터락 키워드(예: 인터락 우회, 미환기 투입 등) 리스트가 있습니까?"*
4. *"선수과목 이수 의존성(Prerequisite DAG)에서 기초 과목의 최저 합격 기준 점수는 몇 점(예: 80점)입니까?"*
5. *"교육 대시보드에서 관리자가 가장 중요하게 확인해야 하는 지표가 직무별 오개념 빈도 히트맵입니까, 아니면 모듈별 통과율입니까?"*

### 3. #14+#15 Dual-Mode 공통
1. *"본 과제는 전략 시뮬레이터(14번)와 교육 튜터(15번)를 단일 웹 애플리케이션 내의 상단 탭/모드 전환(`Role Switcher`) 방식으로 통합 구현하는 것이 맞습니까?"*
2. *"백엔드의 밸류체인 노드/공정 데이터베이스는 단일 JSON/인메모리 지식 그래프를 두 페르소나가 공유하는 구조입니까?"*

### 4. #12 Dietitian (오늘의 메뉴 맞춤 추천 변형)
1. *"알러지 성분 포함 메뉴는 점수 감점이 아닌 즉각적인 후보 제외(Hard Constraint Cutoff)가 맞습니까?"*
2. *"실시간 구내식당 코너 혼잡도(대기 인원)와 잔여 식자재 재고 중 추천 우선순위 가중치는 각각 몇 %로 둡니까?"*
3. *"개인 맞춤 추천 결과는 화면에 1순위 단일 메뉴로 노출합니까, 아니면 대체 메뉴를 포함한 Top 3 카드 형태로 노출합니까?"*
4. *"다이어트/질환 관리 대상자의 1끼 나트륨 및 칼로리 상한선 기준값은 얼마로 설정합니까?"*

### 5. #6-C, #7-C, #13-C FDE 대시보드 확장
- **#6-C 시장전략팀 책임매니저:** *"경쟁사 실적 기반 What-If 시뮬레이터에서 환율(±5%)과 HBM ASP(±10%) 변동 시 영업이익 민감도 산출식을 연결해야 합니까?"*
- **#7-C 소재품질팀 책임매니저:** *"원소재 CoA 성적서 검증 대시보드에서 검출한계 미만(`< DL`) 수치의 0 대치 여부와 Cpk 관리도 기준은 무엇입니까?"*
- **#13-C 이천 포토기술팀 TL:** *"웨이퍼 맵 관제 대시보드에서 스펙 아웃 판정 시 ADI는 Rework 큐로, AEI는 Scrap 폐기 큐로 분기 렌더링하는 것이 맞습니까?"*

---

## 8. 서브 에이전트(`GPT 5.6-terra medium`)에게 넘길 TASK_SPEC 예시

메인 에이전트(`Sol 6.1 xhigh`)는 아래 [시작 · 정의 · 기준 · 종료] 4대 핵심 축 기반 7대 표준 규격의 명세서를 작성하여 서브 에이전트에게 구현을 위임한다.

```markdown
# [TASK_SPEC] 밸류체인 수급 충격 시뮬레이터 & 멀티 페르소나 웹앱 수직 완성 (MVP)

> **작성자:** 메인 아키텍트 (`Sol 6.1 xhigh`)  
> **수신자:** 서브 워커 (`GPT 5.6-terra medium`)  
> **핵심 원칙:** [시작 · 정의 · 기준 · 종료] 4대 축 기반 명세 준수 및 지정 범위 외 임의 수정 절대 금지. 완료 후 `.probe-kit/runtime/SUB_RESULT.md`에 핵심 결과와 변경 사항 위주의 명확한 요약 보고를 남길 것 (불필요한 줄 수 제한 없음).

---

### 1. [시작 / Start] 단일 목표 및 진입 조건 (Entry Conditions)
- **단일 목표 (Single Goal):** 
  반도체 밸류체인 지식 그래프를 기반으로 [경영전략 모드: 충격 전파 & CoWoS 병목 클리핑 시뮬레이션]과 [산업교육 모드: 직무별 적응형 설명 & FAIL_INTERLOCK 오개념 진단]을 `Role Switcher`로 즉각 전환할 수 있는 FastAPI + HTML/JS 웹앱 MVP 수직 완성.
- **선행 완료 상태 (Pre-conditions):**
  - 가용 디렉토리: `app/main.py`, `app/engine/valuechain.py`, `static/index.html` 생성 가능 상태
  - 포트 `0.0.0.0:8000` 충돌 여부 확인 및 사용 가능 상태 확인
  - Git 작업 트리가 깨끗한 상태(uncommitted 변경 사항 없음)인지 확인
- **사전 베이스라인 체크 (Baseline Pre-check):**
  - 기존 웹 서버 구동 상태 또는 헬스체크 테스트 PASS 확인 (`curl -s http://0.0.0.0:8000/health`)
  - 사전 베이스라인 실패 시 코드 작성 시작을 금지하고 즉시 원인 보고

### 2. [통제 / Scope] 대상 파일 범위 및 금지 사항 (Hard Constraints)
- **수정 허용 파일:**
  - `app/main.py` (FastAPI 서버, REST API 엔드포인트, Pydantic 모델, 400 예외 핸들러)
  - `app/engine/valuechain.py` (순수 Python DAG 충격 전파, 누적 수율, 병목 클리핑, 오개념 엔진)
  - `static/index.html` (Role Switcher, Top 4 KPI 배지 카드, What-If 슬라이더, 진단 폼 단일 UI)
  - `tests/test_valuechain.py` (엔진 및 엔드포인트 온더플라이 ad-hoc 테스트)
- **수정 절대 금지 파일:**
  - 복잡한 사용자 DB, OAuth2/JWT 인증 라이브러리 추가 금지 (단일 공용 세션 및 토글 버튼 사용)
  - 외부 상용 유료 API(OpenAI API 등) 의존 금지 (내장 룰/지식베이스 활용)
  - `.gitignore` (Git 트래킹 제외 목록 수정 금지 - 임시 파일은 `.git/info/exclude`로 통제)
- **5대 금지사항 (Hard Constraints):**
  - 서버 구동 시 `localhost` 또는 `127.0.0.1` 바인딩 절대 금지 (반드시 `0.0.0.0` 바인딩 준수)
  - 부적절한 입력(음수, 미존재 노드, 빈 텍스트) 시 500 에러 반환 절대 금지 (반드시 400 Bad Request 방어)
  - 시크릿, 패스워드, 개인 식별 정보, API 키 코드 내 하드코딩 절대 금지
  - `.gitignore` 파일 수정 금지 (임시 파일은 `.git/info/exclude`로 통제)
  - 시험 중 `git add` / `git commit` / `git reset` / `git clean` 실행 전면 금지 (테스트 코드는 커밋하지 않으며 test 파일은 untracked 상태 유지)

### 3. [정의 / Definition] 도메인 용어·상태 및 입출력 스키마
- **도메인 핵심 용어 및 상태 정의:**
  - `SPOF (Single Point of Failure)`: 전체 공급망 출하량을 제한하는 단일 병목 노드
  - `Decay Factor (\gamma)`: 상류 충격이 1홉(Hop) 거칠 때마다 감쇠되는 비율 (기본값: 0.85)
  - `FAIL_INTERLOCK`: 안전 규정 및 품질 치명 위반 키워드 감지 시 발동하는 즉시 0점 비상 인터락
- **API 요청/응답 JSON 스키마 및 HTTP 상태 코드 계약:**
  - **1) 헬스체크 (`GET /health`):**
    - 응답: HTTP 200 OK `{"status": "ok"}`
  - **2) 밸류체인 충격 시뮬레이션 (`POST /api/simulate`):**
    - 요청 Body: `{"source_node": string (필수), "shock_magnitude": float (0.0~1.0), "decay_factor": float (0.1~1.0, 기본 0.85), "stack_count": int (기본 8)}`
    - 유효성 검증: `shock_magnitude < 0.0 or > 1.0` 시 HTTP 400 Bad Request
    - 성공 응답: HTTP 200 OK
      ```json
      {
        "status": "SUCCESS",
        "data": {
          "propagated_shocks": {"TSMC": 0.5, "SK_Hynix": 0.425, "Nvidia": 0.361},
          "compound_yield": 0.8125,
          "effective_output": 4200.0,
          "bottleneck_node": "CoWoS Packaging",
          "kpi_badges": {"system_health": "AMBER", "bottleneck_risk": "HIGH"}
        }
      }
      ```
  - **3) 오개념 진단 및 피드백 (`POST /api/diagnose`):**
    - 요청 Body: `{"user_role": string ("beginner"|"engineer"|"business"), "question_id": string, "answer_text": string (필수, 1자 이상)}`
    - 성공 응답: HTTP 200 OK
      ```json
      {
        "status": "SUCCESS",
        "data": {
          "is_pass": true,
          "score": 85,
          "interlock_triggered": false,
          "feedback": "DRAM의 휘발성 특성을 올바르게 서술하였습니다.",
          "level_explanation": "..."
        }
      }
      ```
    - 치명 금지어 감지 시 응답: HTTP 200 OK
      ```json
      {
        "status": "SUCCESS",
        "data": {
          "is_pass": false,
          "score": 0,
          "interlock_triggered": true,
          "feedback": "🚨 [FAIL_INTERLOCK] 안전 규정 위반 키워드가 감지되어 즉시 0점 처리되었습니다."
        }
      }
      ```

### 4. [기준 / Criteria] 비즈니스 판정 기준 및 경계값 (Acceptance & Boundary Criteria)
- **화면 UI 배치 기준:**
  - 화면 최상단: [Role Switcher 버튼: 🏢경영전략모드 | 🎓산업교육모드]
  - 대시보드 상단: Top 4 KPI 요약 카드 ([총 출하량], [최대 병목], [평균 충격도], [진단 통과율]) 및 색상 배지
  - 본문 영역: 좌측 What-If 슬라이더(또는 진단 폼), 우측 네트워크 상태 및 피드백 패널
- **수치 경계값 및 유효성 검증:**
  - `shock_magnitude`: $0.0 \le x \le 1.0$ (음수나 1.0 초과 시 400 Bad Request)
  - `answer_text`: 공백 문자열(`"   "`) 입력 시 400 Bad Request
- **결측/예외 처리 기준:**
  - 비정상 노드 ID 입력 시 500 에러 없이 HTTP 400과 `{"message": "유효하지 않은 노드 ID입니다."}` 반환

### 5. [검증 / Verification] 실행할 검증 명령어
- **1) 헬스체크 및 베이스라인:**
  - `curl -s -o /dev/null -w "%{http_code}\n" http://0.0.0.0:8000/health` (HTTP 200)
- **2) 순수 엔진 및 엔드포인트 온더플라이 ad-hoc 테스트:**
  - `pytest tests/test_valuechain.py -v` (100% 통과 확인, *git commit 금지, untracked 유지*)
- **3) 정상 시뮬레이션 curl 검증:**
  - `curl -s -X POST http://0.0.0.0:8000/api/simulate -H "Content-Type: application/json" -d '{"source_node": "OSAT", "shock_magnitude": 0.4}' | jq .`
- **4) 치명 금지어 인터락 curl 검증:**
  - `curl -s -X POST http://0.0.0.0:8000/api/diagnose -H "Content-Type: application/json" -d '{"user_role": "engineer", "question_id": "Q1", "answer_text": "인터락 센서를 우회하여 라인을 가동한다"}' | jq .`
- **5) 내장 브라우저 수동 인터랙션 검증:**
  - 플랫폼 내장 Browser에서 `http://0.0.0.0:8000` 접속 후 Role Switcher 클릭 및 슬라이더 조작 육안 확인

### 6. [정의 & 기준 / DoD] 완료 정의 (Definition of Done)
- [ ] 서버가 `0.0.0.0:8000` 호스트에 바인딩되어 백그라운드 구동 중일 것
- [ ] 상단 Role Switcher 클릭 시 경영전략 모드와 산업교육 모드가 매끄럽게 전환될 것
- [ ] 슬라이더 조작 시 Top 4 KPI 요약 카드의 수치 및 색상 배지(Red/Amber/Green)가 즉시 갱신될 것
- [ ] 치명 안전 금지어 입력 시 `FAIL_INTERLOCK` 경고가 즉각 출력되고 0점 처리될 것
- [ ] 온더플라이 ad-hoc 테스트(`tests/test_valuechain.py`)가 100% PASS할 것
- [ ] `git status` 확인 시 지정된 수정 허용 파일 외 변경이 없을 것 (*커밋 금지*)

### 7. [종료 / End] 종료 조건, 멈춤 조건 및 완료 후 조치 (Exit & Stop Protocol)
- **멈춤 조건 (Stop / Abort Condition):**
  - 포트 점유 충돌로 자체 해결이 불가한 경우
  - 밸류체인 수식이나 오개념 루브릭 요구사항에 심각한 모호성이 발생한 경우
  - *발생 즉시 구현 중단 후 `SUB_RESULT.md`에 [차단(블로커)] 사유 기록 후 메인 보고*
- **완료 후 필수 조치:**
  1. `.probe-kit/runtime/SUB_RESULT.md` 요약 보고서 작성
  2. `bash .probe-kit/scripts/handoff.sh log "sub done: valuechain app MVP complete"` 실행 (실패 시 `python3 .probe-kit/scripts/handoff.py log "sub done" "valuechain app MVP complete"`)
  3. 메인 에이전트에게 완료 보고 후 **서브 터미널에서 즉시 `/clear` 실행**
```

---

## 9. 검증 명령 모음

서브 에이전트 구현 완료 후 터미널에서 직접 실행하여 검증할 온더플라이 및 엔드포인트 점검 스크립트:

```bash
# ==============================================================================
# 1. 서버 헬스체크 및 0.0.0.0 바인딩 확인 (기대값: HTTP 200 OK)
# ==============================================================================
curl -s -o /dev/null -w "%{http_code}\n" http://0.0.0.0:8000/health

# ==============================================================================
# 2. 밸류체인 충격 전파 & 병목 클리핑 정상 요청 (기대값: 200 OK & JSON 반환)
# ==============================================================================
curl -s -X POST http://0.0.0.0:8000/api/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "source_node": "OSAT",
    "shock_magnitude": 0.45,
    "decay_factor": 0.85,
    "stack_count": 8
  }' | jq .

# ==============================================================================
# 3. 비정상 파라미터 경계값 방어 테스트 (기대값: 400 Bad Request)
# ==============================================================================
# 3-1. 충격 크기 범위 초과 (음수)
curl -s -X POST http://0.0.0.0:8000/api/simulate \
  -H "Content-Type: application/json" \
  -d '{"source_node": "OSAT", "shock_magnitude": -0.5}' | jq .

# 3-2. 미존재 노드 ID 입력
curl -s -X POST http://0.0.0.0:8000/api/simulate \
  -H "Content-Type: application/json" \
  -d '{"source_node": "UNKNOWN_NODE_999", "shock_magnitude": 0.5}' | jq .

# ==============================================================================
# 4. 교육 튜터 진단 - 정상 답변 평가 (기대값: is_pass=true, level_explanation 제공)
# ==============================================================================
curl -s -X POST http://0.0.0.0:8000/api/diagnose \
  -H "Content-Type: application/json" \
  -d '{
    "user_role": "beginner",
    "question_id": "HBM_CONCEPT",
    "answer_text": "HBM은 데이터를 빠르게 주고받기 위해 칩을 아파트처럼 수직으로 쌓아 올린 고대역폭 메모리입니다."
  }' | jq .

# ==============================================================================
# 5. 교육 튜터 진단 - 치명 금지어 FAIL_INTERLOCK 검증 (기대값: score=0, interlock=true)
# ==============================================================================
curl -s -X POST http://0.0.0.0:8000/api/diagnose \
  -H "Content-Type: application/json" \
  -d '{
    "user_role": "engineer",
    "question_id": "SAFETY_RULE",
    "answer_text": "스펙 아웃 원소재를 라인 가동률 유지를 위해 임의 투입한다."
  }' | jq .

# ==============================================================================
# 6. 온더플라이 ad-hoc 테스트 실행 (엔진 및 엔드포인트 일괄 검증)
# ==============================================================================
pytest tests/test_valuechain.py -v
```

---

## 10. 보고서 및 후속 Q&A 작성용 [결정]-[근거]-[검증]-[한계] 예시

- **[결정]:** 단일 지식 그래프(Knowledge Graph Core)를 백엔드에 구축하고, 상단 `Role Switcher`를 통해 경영전략팀의 '수급 충격·후공정 병목 What-If 시뮬레이터'와 교육담당팀의 '직무별 적응형 설명 및 치명 오판 FAIL_INTERLOCK AI 튜터'를 단일 웹 애플리케이션으로 수직 완성(MVP)함.
- **[근거]:** 실무자 DM 확인 결과, 14번과 15번이 동일한 반도체 밸류체인 토폴로지 데이터셋을 공유하는 상호보완적 페르소나임을 규명하였으며, 무거운 외부 라이브러리 대신 순수 Python DAG 연산 엔진과 경량 FastAPI+HTML/JS 구조를 채택함으로써 3시간 타임어택 내에 빌드 충돌 위험을 배제하고 즉각적인 UI 반응성을 확보함.
- **[검증]:** 서버를 `0.0.0.0:8000`에 바인딩하여 백그라운드로 구동한 후, 플랫폼 내장 Browser에서 전략 모드 슬라이더 조작(충격 전파율 0~100%)에 따른 Top 4 KPI 요약 카드 및 병목(SPOF) 경고 갱신을 확인하였고, 교육 모드에서 치명 안전 금지어 입력 시 즉각 0점 처리되는 `FAIL_INTERLOCK` 비상 모달 작동과 음수 입력 400 에러 방어(스모크 curl)를 전수 검증함.
- **[한계]:** 현재 충격 전파 모델은 1차 정적 감쇠율($\gamma=0.85$) 기반의 위상 순회 방식을 적용하여 동적 재고 보충 리드타임 및 2차 피드백 루프(공급사 설비 증설 시차)의 시계열 동역학(System Dynamics)이 단순화되어 있으며, 향후 실제 ERP/MES 시스템 연동 시에는 Monte Carlo 확률 시뮬레이션 및 이산 사건 시뮬레이션(DES) 엔진 도입이 보완되어야 함.
