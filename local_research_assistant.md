좋습니다. 이 시스템을 **“내 PC 전체 문서에 질문하는 로컬 조사 비서”**로 보면, wiki에 올리는 시스템보다 훨씬 자연스럽습니다.

핵심은 이것입니다.

```text
질문 입력
-> Everything으로 PC 전체에서 관련 파일 검색
-> 상위 후보 파일만 내용 추출
-> Copilot으로 읽고 분석
-> 답변 + 근거 파일 경로 + 신뢰도 + 다음 액션 출력
```

즉, Obsidian에 저장하는 게 아니라 **그때그때 내 컴퓨터 문서를 조사해서 답하는 비서**입니다.

---

**1. 시스템 이름 아이디어**

작업명은 이렇게 잡을 수 있습니다.

```text
Local Research Assistant
PC Document Investigator
Everything Copilot Research
Local File Q&A
내 PC 조사 비서
```

내부 명령 이름은 이런 식이 좋습니다.

```powershell
python scripts\local_research_assistant.py ask "TR5 Pre-Op Gantt 최신 일정 요약해줘"
python scripts\local_research_assistant.py find-bundle "Globalmaritime MWS 13차 기성"
python scripts\local_research_assistant.py audit-folder "C:\HVDC_WORK\REPORTS\기성\GM202603"
python scripts\local_research_assistant.py brief --today
```

---

**2. 기본 사용 흐름**

사용자는 질문만 합니다.

예:

```text
TR5 Pre-Op Gantt 관련 최신 파일 찾아서 일정과 리스크 알려줘
```

시스템 내부 흐름:

```text
1. 질문 분석
2. Everything 검색어 생성
3. 후보 파일 수집
4. 파일 확장자/수정일/경로로 랭킹
5. 상위 5~10개 파일만 추출
6. Copilot에 조사 요청
7. 답변 생성
8. 근거 파일 경로 출력
```

출력 예:

```text
Answer
TR5 Pre-Op Gantt 관련 최신 파일은 2026-04-15 16:21 생성본으로 보입니다.
핵심 일정은 Pre-Op simulation, inspection, site readiness 순서로 정리됩니다.
현재 리스크는 일부 단계의 선후행 관계와 문서 버전 중복입니다.

Key Findings
- 최신 XLSM: C:\Users\SAMSUNG\Documents\TR5_PreOp_Gantt_20260415_162140.xlsm
- 관련 PDF: C:\tr_dash-main\work\TR5_PreOp_Gantt_20260415\docs\TR5_Pre-Op_Simulation_Gantt_A3.pdf
- v3, v5, v6, v7 PDF가 있어 버전 정리가 필요합니다.

Sources
1. ...
2. ...

Next Actions
- 최신본 기준 파일 1개를 확정
- PDF v7과 XLSM 162140 간 내용 차이 확인
```

---

**3. 핵심 기능 아이디어**

**A. Ask: 내 PC 문서 Q&A**

가장 기본 기능입니다.

```powershell
python scripts\local_research_assistant.py ask "UAE HVDC Globalmaritime MWS 13차 기성 문서 요약해줘"
```

시스템은 Everything으로 관련 파일을 찾습니다.

검색어 후보:

```text
UAE HVDC
Globalmaritime
MWS
13차
기성
Jopetwil
```

검색 대상:

```text
*.docx
*.pdf
*.xlsx
*.xlsm
*.md
*.txt
*.csv
*.json
```

Copilot이 하는 일:

```text
- 관련 파일들 중 어떤 것이 핵심 문서인지 판단
- 파일별 역할 구분
- 질문에 대한 답변 생성
- 근거 경로 제시
```

좋은 점:
- wiki 저장 없음
- 즉석 답변
- 파일 경로가 근거로 남음
- 반복 질문 가능

---

**B. Find Bundle: 관련 파일 묶음 찾기**

특정 업무/프로젝트/업체명을 넣으면 관련 파일들을 묶어줍니다.

```powershell
python scripts\local_research_assistant.py find-bundle "TR5 PreOp Gantt"
```

출력 예:

```text
Bundle: TR5 PreOp Gantt 2026-04-15

Likely Core Files
1. TR5_PreOp_Gantt_20260415_162140.xlsm
   Role: source schedule workbook

2. TR5_Pre-Op_Simulation_Gantt_A3.pdf
   Role: exported presentation/report

3. TR5_Pre-Op_Simulation_Gantt_A3_v7.pdf
   Role: likely latest PDF version

Duplicates / Versions
- v3, v5, v6, v7 PDF exist
- latest-looking PDF: v7
- latest-looking workbook: 162140

Suggested Action
Use XLSM 162140 as source of truth and compare against PDF v7.
```

이건 실제 업무에서 매우 유용합니다. 폴더가 지저분할 때 “이 건의 파일 세트가 뭐냐”를 바로 알 수 있습니다.

---

**C. Audit: 첨부/증빙 누락 검사**

집행 문서, 기성 문서, 인보이스, 첨부 목록 검사용입니다.

```powershell
python scripts\local_research_assistant.py audit "Globalmaritime MWS 13차 기성"
```

Copilot에게 시키는 일:

```text
- 집행의 건 문서에서 첨부 목록 추출
- 같은 폴더 또는 관련 경로에서 실제 파일 존재 여부 확인
- 금액/업체명/차수/문서 제목 일치 여부 확인
- 누락 가능성 보고
```

출력 예:

```text
Audit Result: Globalmaritime MWS 13차 기성

Found
- 집행의 건 DOCX
- 관련 MWS 문서
- Jopetwil 71 언급

Potential Missing Evidence
- invoice PDF not found
- signed approval PDF not found
- cost breakdown Excel not found

Risk
Medium

Recommended Next Step
Search invoice/globalmaritime/jopetwil/71 in adjacent folders.
```

wiki보다 이런 감사 리포트가 더 실무적입니다.

---

**D. Folder Brief: 폴더 요약**

폴더 하나를 지정하면 그 안의 파일들이 무슨 업무인지 요약합니다.

```powershell
python scripts\local_research_assistant.py brief-folder "C:\HVDC_WORK\PIPELINE\PP1030\data\raw"
```

출력 예:

```text
Folder Brief

This folder appears to contain raw warehouse and case list data for SIMENSE / HVDC pipeline work.

Important Files
- HVDC WAREHOUSE_SIMENSE(SIM).xlsm
- Case List_Simense.xlsm

Likely Purpose
- warehouse status tracking
- case list management
- logistics or material movement monitoring

Suggested Questions
- Which cases are delayed?
- Which warehouse entries have missing status?
- Are there duplicate case IDs?
```

이건 “폴더 열었는데 뭐가 뭔지 모르겠다”를 해결합니다.

---

**E. Excel Investigator: 엑셀 파일 해석기**

Everything으로 엑셀 파일을 찾고 Copilot에게 구조 해석을 시킵니다.

```powershell
python scripts\local_research_assistant.py inspect-excel "SIMENSE warehouse"
```

출력 예:

```text
Excel Investigation

File
C:\HVDC_WORK\PIPELINE\PP1030\data\raw\HVDC WAREHOUSE_SIMENSE(SIM).xlsm

Sheets
- Summary
- Warehouse
- Case List

Likely Important Columns
- Case No
- Package
- Status
- ETA
- Location
- Remarks

Possible Checks
- blank status rows
- duplicated case numbers
- overdue ETA
- mismatch between Case List and Warehouse sheet
```

다음 단계로 자동 QA도 가능합니다.

```text
빈 Status 찾기
중복 Case No 찾기
ETA 지난 건 찾기
수량 합계 검산
```

---

**F. Version Resolver: 최신본/중복본 판별**

Everything은 버전 파일 찾기에 좋습니다.

```powershell
python scripts\local_research_assistant.py versions "TR5_Pre-Op_Simulation_Gantt_A3"
```

출력 예:

```text
Detected Versions
- TR5_Pre-Op_Simulation_Gantt_A3.pdf
- TR5_Pre-Op_Simulation_Gantt_A3_v3.pdf
- TR5_Pre-Op_Simulation_Gantt_A3_v5.pdf
- TR5_Pre-Op_Simulation_Gantt_A3_v6.pdf
- TR5_Pre-Op_Simulation_Gantt_A3_v7.pdf

Likely Latest
TR5_Pre-Op_Simulation_Gantt_A3_v7.pdf

But
Base file has later modified time than v7, verify before archiving.

Recommended Keep
- source XLSM
- latest PDF
- final exported PDF

Recommended Review
- v3/v5/v6
```

실제 삭제는 하지 않고, “정리 제안”만 합니다.

---

**G. Today Brief: 오늘 작업 요약**

오늘 수정된 파일을 Everything으로 찾고 Copilot이 브리핑합니다.

```powershell
python scripts\local_research_assistant.py brief --today
```

출력 예:

```text
Today Brief

Major Work Areas
1. TR5 Pre-Op Gantt
2. Desktop organizer reports
3. Local wiki / Copilot integration
4. HVDC warehouse data

Notable Files
- ...
- ...

Suggested Follow-up
- decide source of truth for TR5 schedule
- review desktop organizer output
- avoid duplicate PDF versions
```

이건 매일 업무 마감/시작 보고서처럼 쓸 수 있습니다.

---

**H. Risk Scanner: 위험 신호 스캐너**

최근 문서 중 위험 키워드를 포함하는 파일을 찾습니다.

키워드:

```text
delay
claim
urgent
overdue
missing
damage
hold
penalty
shortage
지연
클레임
누락
미입고
손상
보류
기성
```

명령:

```powershell
python scripts\local_research_assistant.py risk --recent 14
```

출력:

```text
High Risk
- Case List_Simense.xlsm
  Reason: missing status and delayed ETA hints

Medium Risk
- TR5_PreOp_Gantt_20260415_162140.xlsm
  Reason: multiple versioned outputs exist

Low Risk
- desktop organizer logs
```

---

**I. Rename Suggestion: 파일명 정리 제안**

지저분한 파일명을 내용 기반으로 바꾸는 제안서를 만듭니다.

```powershell
python scripts\local_research_assistant.py suggest-names "C:\Users\SAMSUNG\Downloads"
```

출력 CSV:

```csv
current_path,suggested_name,reason
C:\...\$IDA2386.docx,20260412_UAE-HVDC_Globalmaritime_MWS-13_Execution.docx,content indicates execution approval
```

실제 rename은 하지 않습니다.

---

**J. Handoff Builder: 인수인계 초안 생성**

특정 프로젝트명으로 관련 파일을 찾고 인수인계 문서를 만듭니다.

```powershell
python scripts\local_research_assistant.py handoff "UAE HVDC SIMENSE warehouse"
```

출력:

```text
Project Handoff: UAE HVDC SIMENSE Warehouse

Current Files
- HVDC WAREHOUSE_SIMENSE(SIM).xlsm
- Case List_Simense.xlsm

Known Data
- warehouse status
- case list
- package movement

Unknowns
- latest update owner
- final approved report
- missing status rows

Next Actions
- verify latest workbook
- check blank status
- reconcile case list vs warehouse
```

---

**4. 결과 저장 위치**

Obsidian/wiki에 저장하지 않는 조건이므로 결과는 `runtime` 아래가 좋습니다.

```text
runtime/research/
runtime/research/answers/
runtime/research/bundles/
runtime/research/audits/
runtime/research/excel/
runtime/research/briefs/
runtime/research/risks/
```

예:

```text
runtime/research/answers/20260416-153000-tr5-preop-answer.md
runtime/research/audits/20260416-globalmaritime-mws-13.md
runtime/research/excel/20260416-simense-warehouse-analysis.json
```

이렇게 하면:
- 원본 파일 수정 없음
- wiki 업로드 없음
- 결과를 나중에 지우기 쉬움
- 재실행 로그 관리 쉬움

---

**5. 답변 형식**

모든 기능의 출력은 같은 구조가 좋습니다.

```markdown
# Local Research Result

## Question
사용자 질문

## Short Answer
짧은 결론

## Findings
- 핵심 발견 1
- 핵심 발견 2

## Sources
1. 파일 경로
   - 이유
   - 수정일
   - 파일 크기

## Evidence Snippets
- 필요한 짧은 근거만

## Risks / Gaps
- 확인 안 된 점
- 누락 가능성

## Next Actions
- 다음에 할 일
```

중요한 점은 **항상 source path를 보여주는 것**입니다.  
AI 답변만 있으면 믿기 어렵고, 파일 경로가 있어야 실무에서 쓸 수 있습니다.

---

**6. 내부 아키텍처**

구성은 이렇게 나누면 됩니다.

```text
local_research_assistant.py
  CLI entrypoint

local_research_search.py
  Everything 검색어 생성/검색 실행

local_research_rank.py
  후보 파일 랭킹

local_research_extract.py
  기존 local_wiki_extract 재사용

local_research_copilot.py
  Copilot 분석 요청

local_research_report.py
  Markdown/JSON 결과 출력
```

기존 코드 재사용:

```text
scripts/local_wiki_everything.py
scripts/local_wiki_extract.py
scripts/local_wiki_copilot.py
```

새로 만들 부분:

```text
질문 -> 검색어 생성
파일 랭킹
조사 모드별 프롬프트
보고서 출력
```

---

**7. 검색 전략**

질문 하나를 그대로 Everything에 넣으면 약합니다.  
Copilot 또는 deterministic parser가 질문을 검색어 세트로 바꿔야 합니다.

예:

```text
질문:
Globalmaritime MWS 13차 기성 관련 문서 찾아줘
```

검색어 생성:

```text
Globalmaritime
MWS
13차
기성
Jopetwil
UAE HVDC
```

Everything query:

```text
Globalmaritime ext:docx
Globalmaritime ext:pdf
MWS ext:xlsx
기성 ext:docx
Jopetwil
```

후보 랭킹 기준:

```text
점수 =
파일명 매칭
+ 경로 매칭
+ 최근 수정일
+ 확장자 신뢰도
+ 파일 크기 적정성
+ 질문 키워드 포함
- 휴지통/도구 폴더
- 너무 큰 파일
- 중복 버전 낮은 점수
```

---

**8. Copilot 프롬프트 전략**

wiki용 프롬프트와 다르게 해야 합니다.

wiki 프롬프트는:

```text
노트로 정리해라
```

조사 비서 프롬프트는:

```text
질문에 답해라.
답을 모르면 모른다고 말해라.
반드시 source file을 근거로 써라.
추측과 확인된 사실을 분리해라.
```

프롬프트 예:

```text
You are a local document research assistant.
Answer the user's question using only the provided extracted file packets.
Do not invent facts.
Separate confirmed findings from assumptions.
Always cite source_path for each finding.
Return JSON with:
- short_answer
- findings[]
- sources[]
- gaps[]
- next_actions[]
```

---

**9. 안전 규칙**

wiki 업로드는 제외하지만, 여전히 안전 규칙은 필요합니다.

```text
- 원본 파일 수정 금지
- 삭제/이동/rename 금지
- credential/secret hard skip
- Everything HTTP는 localhost만
- 결과는 runtime/research에만 저장
- 파일 전문을 결과에 복사하지 않음
- source path와 짧은 snippet만 저장
```

민감정보 정책은 지금처럼:

```text
개인/업무 민감정보: 사용자 승인 범위에서 Copilot 분석 허용
credential/secret: hard skip
```

---

**10. 3가지 구현 접근**

**Approach A: CLI 우선**

명령줄 도구로 시작합니다.

```powershell
python scripts\local_research_assistant.py ask "질문"
```

장점:
- 가장 빠르게 구현 가능
- 현재 코드 재사용 쉬움
- 테스트 쉬움
- 위험 낮음

단점:
- UI는 단순함

추천도: 보류

---

**Approach B: HTML 리포트 생성기**

질문하면 HTML 보고서를 만듭니다.

```text
runtime/research/reports/20260416-answer.html
```

장점:
- 읽기 좋음
- 파일 링크 클릭 가능
- 표/섹션 정리 좋음

단점:
- HTML 렌더링/링크 처리 추가 필요

추천도: 보류

---

**Approach C: 로컬 웹 UI**

브라우저에서 질문 입력하고 결과를 봅니다.

```text
http://127.0.0.1:8090
```

장점:
- 사용성 좋음
- 검색 결과 클릭/필터 가능

단점:
- 서버/UI 추가
- CLI보다 테스트 범위가 넓음

추천도: 최종 선택

---

**11. MVP 범위 결정: 로컬 웹 UI 기반 ask + find-bundle**

첫 버전은 사용자가 최종 선택한 대로 **Approach C: 로컬 웹 UI**로 잡습니다. 기능 범위는 `ask`와 `find-bundle` 두 가지로 유지하고, `brief-folder`, `inspect-excel`, `versions`, `risk`, `suggest-names`, `handoff`, `audit`는 다음 단계로 미룹니다.

```text
Local Research Assistant Web UI
```

접속 위치:

```text
http://127.0.0.1:8090
```

지원 모드:

```text
Ask
Find Bundle
```

**MVP 1: ask**

```text
웹 UI에서 Ask 선택 후 질문 입력:
TR5 Pre-Op Gantt 최신 파일과 리스크 알려줘
```

목적:

```text
질문에 답한다.
Everything으로 관련 파일을 찾는다.
상위 후보를 추출한다.
Copilot이 답변을 생성한다.
항상 source path를 근거로 보여준다.
```

출력:

```text
runtime/research/answers/<timestamp>-answer.md
runtime/research/answers/<timestamp>-answer.json
```

**MVP 2: find-bundle**

```text
웹 UI에서 Find Bundle 선택 후 주제 입력:
Globalmaritime MWS 13차
```

목적:

```text
하나의 업무/프로젝트/업체명과 관련된 파일 묶음을 찾는다.
파일별 역할을 분류한다.
최신본/중복본/근거 파일 후보를 구분한다.
누락 가능성이 있는 첨부나 증빙 파일을 추정한다.
```

출력:

```text
runtime/research/bundles/<timestamp>-bundle.md
runtime/research/bundles/<timestamp>-bundle.json
```

**MVP에서 제외**

```text
brief-folder
inspect-excel
versions
risk
suggest-names
handoff
audit
HTML report
CLI-only workflow
```

출력은 모두:

```text
runtime/research/answers/*.md
runtime/research/answers/*.json
runtime/research/bundles/*.md
runtime/research/bundles/*.json
```

에 저장합니다.  
Obsidian/wiki에는 절대 쓰지 않습니다.
웹 UI도 결과를 `runtime/research` 아래에만 저장합니다.

---

**12. 성공 기준**

이 시스템이 쓸 만하다고 판단할 기준은 명확해야 합니다.

```text
1. 브라우저에서 Ask와 Find Bundle을 실행할 수 있다.
2. 질문 1개로 관련 파일 3~10개를 찾는다.
3. 답변에 source path가 반드시 포함된다.
4. Copilot 실패 시에도 검색 결과와 추출 요약은 남는다.
5. 원본 파일과 vault/wiki는 수정하지 않는다.
6. 결과는 runtime/research 아래에만 생긴다.
7. 5개 실제 질문 중 3개 이상은 실무적으로 쓸 만한 답을 준다.
```

---

**13. 예시 질문 세트**

테스트 질문은 이런 게 좋습니다.

```text
TR5 Pre-Op Gantt 최신 일정 파일 찾아서 핵심 리스크 알려줘
```

```text
Globalmaritime MWS 13차 기성 관련 파일 묶어줘
```

```text
SIMENSE warehouse 파일에서 중요한 시트와 컬럼 설명해줘
```

```text
오늘 수정된 HVDC 관련 파일 요약해줘
```

```text
GPTS PackingList FullSet 관련 문서들이 무엇인지 설명해줘
```

---

**14. 최종 추천**

내 추천은 이 순서입니다.

```text
1. scripts/local_research_service.py 생성
2. scripts/local_research_web.py 생성
3. 웹 UI에서 Ask 모드 구현
4. 웹 UI에서 Find Bundle 모드 구현
5. 결과는 runtime/research/answers/*.md + .json, runtime/research/bundles/*.md + .json
6. 실제 질문 5개로 품질 테스트
7. 그 다음 brief-folder / inspect-excel 확장
```

첫 구현 목표는 이것입니다.

```text
브라우저에서 내 PC 문서에 질문하면,
Everything으로 후보를 찾고,
Copilot으로 답하고,
근거 파일 경로를 보여주는 로컬 웹 도구

그리고 특정 업무명을 입력하면,
관련 파일 묶음을 찾아 역할/최신본/누락 가능성을 정리하는 로컬 웹 도구
```

한 줄로 말하면:

```text
Obsidian에 저장하는 지식화 시스템이 아니라,
내 PC 전체를 대상으로 하는 “근거 있는 문서 조사 챗봇”입니다.
```

다음 단계로 진행한다면, 첫 구현 계획은 **`Local Research Assistant Web UI ask + find-bundle MVP`**입니다.

---

**15. 구현 상태: Web UI MVP 1차 완료**

구현 파일:

```text
scripts/local_research_service.py
scripts/local_research_web.py
tests/test_local_research_service.py
tests/test_local_research_web.py
```

현재 실행 주소:

```text
http://127.0.0.1:8090
```

지원 API:

```text
GET  /
GET  /api/research/health
POST /api/research/ask
POST /api/research/find-bundle
```

확인된 동작:

```text
Everything HTTP가 켜져 있으면 실제 PC 파일 후보를 검색한다.
Copilot proxy가 켜져 있으면 Copilot 답변을 시도한다.
Copilot proxy가 꺼져 있거나 실패하면 검색/추출 기반 fallback 결과를 반환한다.
삭제되었거나 깨진 후보 파일이 섞여도 전체 요청은 중단하지 않는다.
save=false 요청은 runtime/research에도 쓰지 않는다.
기본 저장 대상은 runtime/research/answers 및 runtime/research/bundles다.
vault/wiki에는 쓰지 않는다.
```
