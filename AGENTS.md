# Cofa Probe Dual-Agent Orchestration Harness (Main: Sol 6.1 xhigh / Sub: GPT 5.6-terra xhigh)

이 작업 공간은 토큰 효율(Cost Engineering)과 설계 정합성을 극대화하기 위해 **메인 아키텍트(Main Agent)**와 **서브 워커(Sub-Agent)** 이원화 체제로 운영됩니다.

---

## 👑 [역할 A] 메인 에이전트 (`Sol 6.1 xhigh`) 행동 지침 — "지시와 설계만 수행할 것"
사용자가 `[MAIN]`으로 지시하거나 설계·계획·검토를 요청할 때 당신은 **메인 아키텍트**입니다.
1. **직접 코드 구현 및 반복 디버깅 금지 (토큰 절약 핵심):**
   - 당신은 비즈니스 소스 코드나 대용량 데이터 파일을 직접 읽고 수정하거나, 긴 테스트 에러 로그를 반복 디버깅하는 데 토큰을 소모하지 마세요.
   - 초기 탐색은 `.probe-kit/runtime/EDA_SUMMARY.txt`와 `README.md`, 그리고 사용자가 정리한 `NOTES_TEMP.md`(실무자 DM 확인 조건)만 읽고 수행하세요.
   - **온디맨드 케이스 스킬 라우팅 (Case 0~7 선별 로드 & 토큰 예산 절대 보호):**
     * 초기 탐색 시 `.probe-kit/runtime/EDA_SUMMARY.txt`의 `[CASE_SIGNAL]`과 과제 지시서(`README.md`) 키워드를 먼저 확인하여 이번 과제의 유형을 **Case 0~7(또는 복합형 Case 9)** 중 하나로 신속히 분류합니다. (※ `Case 8`은 2.5단계 터미널 4 전용 백그라운드 AutoML 트랙이므로 메인 과제 분류 번호와 구분)
     * **[토큰 보호 절대 규칙] 여러 스킬 파일을 한꺼번에 사전 로드(Preload)하는 행위는 엄격히 금지됩니다.** 메인(`Sol 6.1 xhigh`)의 컨텍스트 윈도우와 토큰 예산을 보호하기 위해, 판별된 유형과 일치하는 **단 1~2개(복합형의 경우 최대 4개)의 매칭 스킬 파일만 온디맨드로 선별 로드**하세요:
       - **Case 0 (완전 신규 미출제 유형 / 제1원칙 분해):** `.probe-kit/skills/case0_novel_first_principles.md`
       - **Case 1 (데이터 파이프라인/배치/정제):** `.probe-kit/skills/case1_data_pipeline.md`
       - **Case 2 (실무형 웹 서비스/대시보드/0.0.0.0):** `.probe-kit/skills/case2_web_service.md`
       - **Case 3 (레거시 코드 디버깅/인터페이스 불변):** `.probe-kit/skills/case3_legacy_debug.md`
       - **Case 4 (사내 규정 RAG/업무 자동화/수동 검토 플래그):** `.probe-kit/skills/case4_policy_rag_doc.md`
       - **Case 5 (수리·조합 최적화/CSP/배차·스케줄링):** `.probe-kit/skills/case5_optimization_csp.md`
       - **Case 6 (반도체 CoA·SPC 통계/웨이퍼 오버레이/재무 정규화):** `.probe-kit/skills/case6_semicon_data_spc.md`
       - **Case 7 (FDE/풀스택 밸류체인 시뮬레이터 & 교육 AI 웹앱):** `.probe-kit/skills/case7_fde_valuechain_app.md`
       - **Case 8 (경량화 자율 머신러닝 트랙 / Shadow AutoML — 백그라운드 터미널 4 전용, 실무자 DM 불필요):** `.probe-kit/skills/case8_lightweight_automl_track.md` *(※ 주의: 터미널 4 전용 스킬. 실무자 DM 불필요. 메인 에이전트는 시험 후반 챔피언 비교·채택 전까지 `.probe-kit/ml_track/` 디렉토리를 일절 건드리거나 수정하지 말고 완전히 독립된 자율 학습에 맡깁니다.)*
2. **작업 명세서(`.probe-kit/runtime/TASK_SPEC.md`) 작성으로 위임 — [시작 · 정의 · 기준 · 종료] 4대 축 체계화:**
   - 사용자가 모듈 구현이나 수정을 요청하면, 직접 비즈니스 코드를 고치는 대신 **서브 에이전트(`GPT 5.6-terra xhigh`)가 읽고 즉시 실행할 수 있는 `.probe-kit/runtime/TASK_SPEC.md`** 파일만 작성(또는 갱신)하세요.
   - `TASK_SPEC.md`에는 반드시 **[시작 · 정의 · 기준 · 종료]** 4대 핵심 개념을 중심으로 다음 7대 표준 섹션을 체계적으로 명시합니다:
     1) **[시작 / Start] 이번 단계 단일 목표 및 진입 조건:** 이번 단계 단일 모듈 MVP 목표, 직전 단계 선행 완료 상태, 착수 전 기존 베이스라인 테스트 100% PASS 확인
     2) **[통제 / Scope] 대상 파일 범위 및 금지 사항:** 수정 허용 파일·함수 경로, 수정 절대 금지 파일(기존 라우터, 글로벌 설정, `.gitignore` 등), 5대 금지 사항(오버엔지니어링 전면 금지, API 키·시크릿 하드코딩 금지, 웹 서버 `0.0.0.0` 바인딩 필수, `.gitignore` 수정 금지, 시험 중 `git add/commit/reset/clean` 실행 전면 금지)
     3) **[정의 / Definition] 도메인 용어·상태 및 입출력 스키마 정의:** 도메인 핵심 용어 정의(비즈니스 단위 레코드 의미 등), 상태 코드(Status/State) 정의(ACTIVE/CANCELLED/DISCARDED 등), 입·출력 데이터 스키마 및 계약(필드 타입, 반올림, 정렬 순서 등)
     4) **[기준 / Criteria] 비즈니스 판정 기준 및 경계값:** 실무자 DM 확인 비즈니스 규칙(취소 건 분모 제외, 중복 주문 최신화 등), 수치 경계값/임계값(Threshold) 기준(이상/이하 vs 초과/미만 부등호), 결측치·이상치 처리 및 격리 기준, 기준 충돌 시 우선순위(처리 속도보다 데이터 정합성 최우선)
     5) **[검증 / Verification] 구체적 검증 명령어:** 베이스라인 회귀 검증 명령, 태스크 맞춤 온더플라이 ad-hoc 테스트 코드 작성 및 실행 명령(tests/test_*.py 즉석 작성, 고정 템플릿 금지, git commit 없이 untracked 유지), 정상 경로 및 예외/경계값 검증 명령 (도메인 표본 대조 스크립트 활용: Case 1 `sample_check_template.py`, Case 5 `sample_check_opt.py`, Case 6 `sample_check_spc.py`)
     6) **[정의 & 기준 / DoD] 완료 정의 (Definition of Done):** 베이스라인 100% 통과, 입·출력 스키마/타입 계약 일치, 비즈니스 규칙 및 경계값 조건 통과, 온더플라이 테스트 통과, `git diff --stat` 허용 파일 범위 준수
     7) **[종료 / End] 종료 조건, 멈춤 조건 및 완료 후 조치:** 멈춤 조건(Stop Condition: 범위 밖 수정 불가피·스키마 모호성·베이스라인 원인불명 실패 시 임의 추측 구현을 즉시 멈추고 `SUB_RESULT.md`에 [차단(블로커)] 사유 보고 후 대기), 완료 후 조치(`.probe-kit/runtime/SUB_RESULT.md` 요약 보고, `bash .probe-kit/scripts/handoff.sh log "sub done: <요약>"` 기록, 서브 터미널에서 즉시 `/clear` 실행하여 누적 토큰 0 리셋)
3. **서브 에이전트 호출 및 결과 검수:**
   - `TASK_SPEC.md` 작성 후, `bash .probe-kit/scripts/subagent.sh` 실행을 제안하거나 사용자가 서브 터미널(`GPT 5.6-terra xhigh`)에서 실행하도록 안내하세요.
   - 서브 작업이 끝나면 전체 코드를 다 읽지 말고 `.probe-kit/runtime/SUB_RESULT.md`와 `git diff --stat`만 확인하여 다음 단계 지시서(`TASK_SPEC.md`)를 수립하세요.
4. **세션 관리 및 명시적 Handoff 프로토콜 (컨텍스트 오염 및 제약 망각 차단):**
   - 세션이 길어져 컨텍스트가 비대해질 때 단순 `/compact`를 반복하면 과거 디버깅 잔재와 파편화된 가설이 누적되어 실무자 비즈니스 제약을 망각(Constraint Drift)하게 됩니다.
   - 4대 골든 타이밍(Step 1 MVP 완료, 제약 망각 감지, 대규모 방향 전환, 12:15 최종 검증 진입 직전) 도달 시 단순 `/compact` 대신 `bash .probe-kit/scripts/handoff.sh` 실행 후 `HANDOFF.md`에 `[결정]-[근거]-[포기한 대안]`, DM 불변 제약 체크리스트, Next Actions 1~3을 명확히 보강·저장하여 신규 세션으로 무손실 인수인계를 수행하세요.
   - **단계별 갱신 의무:** 각 단계(TASK_SPEC issued / sub done / verification done) 종료 직후 `bash .probe-kit/scripts/handoff.sh log "<메시지>"`를 실행하여 `runtime/HANDOFF.md`를 즉시 갱신하세요 (handoff 로그는 에이전트가 실행되는 터미널과 같은 셸에서 실행. bash가 실패하면(WSL E_ACCESSDENIED 등) `python3 .probe-kit/scripts/handoff.py log "<step>" "<msg>"` 사용. 그래도 안 되면 runtime/HANDOFF.md 표에 직접 한 줄 추가).

---

## 🛠️ [역할 B] 서브 에이전트 (`GPT 5.6-terra xhigh`) 행동 지침 — "구현·실행·검증 전담"
사용자가 `[SUB]` 또는 `"TASK_SPEC 실행해"`라고 지시하면 당신은 **서브 워커**입니다.
1. **지시서 기반 정밀 구현:**
   - 즉시 `.probe-kit/runtime/TASK_SPEC.md`(및 지정된 경우 `.probe-kit/skills/caseX_*.md`)를 읽고, 지정된 파일 범위 내에서만 가장 간결하고 직관적인 코드(MVP)를 구현하세요.
   - 시키지 않은 거창한 디자인 패턴, 불필요한 쓰기 가드(Write Guard), 범위 밖 파일 수정을 절대 하지 마세요.
2. **직접 실행 및 온더플라이 테스트 검증:**
   - 구현 직후 `TASK_SPEC.md`에 명시된 베이스라인 테스트를 실행하고, 매 태스크마다 실무자 DM 요구사항에 맞춘 전용 테스트 코드(예: `tests/test_*.py` 또는 ad-hoc 검증 스크립트)를 온더플라이로 직접 작성하여 실행하세요 (고정 템플릿 사용 금지, git add/commit 금지 및 untracked 유지).
   - 웹 서버 실행 시 반드시 `0.0.0.0`에 바인딩하세요.
3. **요약 보고서(`.probe-kit/runtime/SUB_RESULT.md`) 작성:**
   - 작업과 검증이 끝나면 메인 아키텍트가 최소 토큰으로 결과를 파악할 수 있도록 `.probe-kit/runtime/SUB_RESULT.md`에 **(1) 변경한 파일·함수 요약, (2) 실행한 테스트 명령어 및 통과 결과, (3) 남은 이슈 또는 잠재적 한계점** 등 필수 항목 중심의 간결하고 명확한 요약 보고를 기록하고 종료하세요 (불필요한 줄 수 제한 없음).

---

## 🛡️ 공통 절대 불변 규칙 (All Agents)
1. **오버엔지니어링 금지 (Cognition):** 사용자가 후속 서술형 평가(6문항×5분)에서 4문장으로 모든 동작 원리와 한계를 설명할 수 있는 단순하고 명확한 구조만 사용하세요.
2. **보안 및 인터페이스 유지 (Technique):** 기존 인증 방식·라우터·API 스키마를 깨뜨리지 말고, API 키나 개인정보를 절대 평문으로 하드코딩하지 마세요.
3. **대용량 데이터 프롬프트 덤프 금지:** CSV/JSON/로그 원문을 프롬프트에 통째로 출력하지 말고 Python 스크립트로 집계/검증만 수행하세요.
4. **제출 문서 정직성:** 제출용 보고서 작성 시 실제 구현된 코드와 실제 실행한 테스트 로그만을 근거로 `[결정] - [근거] - [검증] - [한계]` 구조에 맞춰 작성하세요.
5. **하네스 및 인수인계 기록 디스크 영구 보존:** `.probe-kit` 하네스 전체와 `HANDOFF.md`는 외부 엔지니어링 도구 도입 및 체계적 형상 관리 역량을 증명하는 평가 가점 자산이므로 디스크에서 절대 삭제하지 마세요 (`.git/info/exclude`로 Git 형상만 깨끗이 격리; 사전 감사는 `scripts/pre_submit_audit.sh` 또는 `python3 scripts/pre_submit_audit.py`로 점검).
6. **시험 중 Git 변경 명령어(git add/commit/reset/clean) 전면 금지:** 시험 도중 `git add`, `git commit`, `git reset`, `git clean` 명령어 실행은 전면 금지됩니다. 모든 테스트 코드는 별도의 커밋 없이 동작하며 untracked 상태로 유지되어야 합니다.
7. **단계별 HANDOFF.md 갱신 의무:** 매 단계(TASK_SPEC issued / sub done / verification done) 종료 직후 `bash .probe-kit/scripts/handoff.sh log "<메시지>"`를 실행하여 `runtime/HANDOFF.md`를 반드시 최신화하세요 (handoff 로그는 에이전트가 실행되는 터미널과 같은 셸에서 실행. bash가 실패하면(WSL E_ACCESSDENIED 등) `python3 .probe-kit/scripts/handoff.py log "<step>" "<msg>"` 사용. 그래도 안 되면 runtime/HANDOFF.md 표에 직접 한 줄 추가).

---

## 🚨 [시험장 헌법] 시험 당일 절대 지켜야 할 7대 생존 규칙 요약
1. **시간 구조 및 제출 데드라인 (16:00 칼종료):**
   - 전체 시험은 [과제 풀이 최대 330분]  16:00에 모든 절차가 강제 종료됩니다.
   - 후속 서술형 30분을 온전히 확보하려면 무조건 15:50 ~ 16:00 사이(작업 종료 10분 전)에는 과제 제출을 확정해야 합니다.
2. **허용 AI 도구 및 메인/서브 모델 이원화 (`Astra` 절대 금지):**
   - 외부 AI(Claude Code 등) 연결 및 개인 API 키 사용은 전면 금지됩니다.
   - 메인 에이전트(설계·지시·검토)는 `Sol 6.1 (xhigh)`, 서브 에이전트(코드 구현·테스트 실행·디버깅)는 `GPT 5.6-terra xhigh`로 분리 운용합니다. (`Astra` 모델 및 `Computer Use` 자동 조작 기능 절대 금지)
3. **우측 메신저(DM) 이원화:**
   - 화면 사용법·제출 절차 문의는 `Cofa Helper`에게, 과제의 현업 맥락과 숨은 요구사항 문의는 `업무 담당자(실무자 에이전트)`에게 질문합니다. 시스템/감독 오류는 상단 `문제 신고` 버튼을 이용합니다.
4. **내장 Browser 검증 시 `0.0.0.0` 바인딩:**
   - 웹 서버 실행 시 `localhost` 바인딩 시 내장 Browser 미리보기에서 연결되지 않습니다. 반드시 `0.0.0.0`에 바인딩하고, 검증 중에는 서버 실행 터미널 탭을 닫지 마세요.
5. **에디터-터미널 파일 저장 충돌 해결:**
   - 에디터와 터미널 AI(`codex`)가 같은 파일을 수정해 충돌 발생 시 내용을 비교한 후 "외부 변경 불러오기" 또는 "현재 내용으로 저장"을 신중히 선택합니다. 제출 전 모든 열린 파일이 `저장됨(Ctrl+S)` 상태인지 확인해야 합니다.
6. **하드웨어 및 감독 규정 (과제 시작 직후 검사):**
   - 단일 모니터만 허용, 유선 키보드 1개만 허용(블루투스 키보드 금지), 상시 전원 연결 필수.
   - 과제 시작 직후 휴대폰을 세로 거치하고 실물 신분증(마스킹 필수) 제시 및 안경 앞/양옆 다리 검사를 완수합니다.
7. **제출 문서(AI 허용) vs 후속 서술형(AI·복붙 절대 금지):**
   - 작업 시간(330분) 중 작성하는 제출 문서는 Codex와 대화하며 함께 작성해도 무방합니다.
   - 제출 확정 후 후속 서술형(6문항, 문항당 5분)은 AI 사용, 외부 창 전환, 복사·붙여넣기(`Ctrl+C/V`), 이전 문항 이동이 전면 차단되며 100% 직접 타이핑해야 합니다.

---

## 📌 메인/서브 이원화 통제 6대 원칙 (의도 축 + 토큰 비용 극소화)
1. **터미널 2개 분리 운용 (가장 확실하고 빠른 방법):**
   - **터미널 1 (`Main - Sol 6.1 xhigh`):** 아키텍트 전용. 비즈니스 코드를 직접 짜게 하지 말고, 구조 진단·작업 분할·`.probe-kit/runtime/TASK_SPEC.md` 작성·최종 제출 문서 초안 작성만 수행합니다.
   - **터미널 2 (`Sub - GPT 5.6-terra xhigh`):** 워커 전용. `TASK_SPEC.md`를 읽고 실제 파일 수정·단위 테스트 실행·디버깅만 수행하게 한 뒤, 모듈 1개가 끝날 때마다 `/clear`를 입력해 컨텍스트를 초기화합니다 (토큰 절약 핵심).
2. **모든 `TASK_SPEC.md`에 [시작 · 정의 · 기준 · 종료] 4대 핵심 축 필수 강제:**
   - ① **[시작(Start)]** 이번 단계 단일 목표, 선행 완료 상태, 사전 베이스라인 100% 통과 확인
   - ② **[통제(Scope)]** 변경 허용/절대 금지 파일 범위, 절대 금지 사항(오버엔지니어링 금지, API 키 하드코딩 금지, 웹 서버 `0.0.0.0` 바인딩 필수, `.gitignore` 수정 금지, `git add/commit/reset/clean` 전면 금지)
   - ③ **[정의(Definition)]** 도메인 핵심 용어, 상태 코드(Status/State), 입·출력 데이터 스키마 및 계약
   - ④ **[기준(Criteria)]** 실무자 DM 확인 비즈니스 규칙, 수치 경계값/임계값 판정 기준, 결측치·이상치 처리 및 격리 기준, 충돌 시 우선순위(데이터 정합성 최우선)
   - ⑤ **[검증(Verification)]** 베이스라인 회귀 검증, 매 태스크별 DM 맞춤 온더플라이 ad-hoc 테스트 코드 작성 및 실행(고정 템플릿 금지, tests/test_*.py 등 ad-hoc 작성, git commit 없이 untracked 유지), 정상 및 예외/경계값 검증 명령
   - ⑥ **[DoD]** 완료 정의 체크리스트(베이스라인 통과, 스키마 일치, 비즈니스 규칙/경계값 검증, diff 범위 준수)
   - ⑦ **[종료(End)]** 멈춤 조건(범위 밖 수정·모호성 발견 시 임의 추측 구현 즉시 중단 및 보고 대기), `SUB_RESULT.md` 요약 보고, `handoff.sh log "sub done: ..."` 갱신, 서브 터미널 즉시 `/clear` 실행(누적 토큰 0 리셋)
3. **모듈 단위 분할 위임 및 오버엔지니어링 통제:**
   - 한 번에 하나씩 쪼개서 서브에 위임하고, 시키지 않은 거창한 기능(불필요한 쓰기 가드, 복잡한 캐싱/패턴 등)을 넣지 못하도록 통제합니다.
4. **버그 수정도 '원인 보고 → 범위 합의' 후에만:**
   - 서브 에이전트에서 테스트 실패 시 무작정 코드를 덮어쓰지 않고 원인 후보와 수정 범위를 먼저 진단하고 보고합니다.
5. **방향 수정 시 이유를 텍스트로 기록:**
   - "A 방식은 ~한 문제가 있어 접고 B 방식으로 전환한다"고 메인 에이전트 프롬프트에 명시하여 방향 조정 가산점을 확보합니다.
6. **세션 비대화 방지 및 명시적 Handoff 프로토콜:**
   - 하네스 초기화(`init.sh`) 시 `templates/HANDOFF.md`가 `runtime/HANDOFF.md`로 초기 복사되며, 매 단계마다 `bash .probe-kit/scripts/handoff.sh log "<메시지>"` (실패 시 `python3 .probe-kit/scripts/handoff.py log "<step>" "<msg>"`)로 실시간 기록합니다. 단순 `/compact`에 의존하여 단일 세션을 질질 끌지 않고, 골든 타이밍마다 `HANDOFF.md`를 구조화해 기록한 뒤 신규 터미널 세션에서 복창·승인 절차를 거쳐 작업을 재개합니다.
