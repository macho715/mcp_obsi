### 📊 WhatsApp 물류 로그 지식 추출 결과

작성한 스크립트(`scripts/parse_whatsapp_logistics.py`)를 통해 총 **93,357줄**의 대화 로그를 처리한 결과입니다.

1. **로그 파싱 완료**: 올바른 날짜/시간과 발신자 포맷을 가진 **41,335개의 유효한 메시지**를 정확히 분리해 냈습니다.
2. **리스크 필터링 완료**: 가이드라인에서 정의한 6대 핵심 리스크 키워드(`delay`, `closed`, `terminated`, `cancel`, `hold`, `congestion` 등)가 포함된 메시지 **734건**을 찾았습니다.
3. **이벤트 블록(Chunk) 압축 완료**: 키워드가 발생한 시점을 기준으로 **±2시간** 내외의 대화 컨텍스트를 하나로 묶어, 9만 줄의 대화를 최종적으로 **523개의 독립적인 물류 이슈(Logistics Issues)** 로 압축하는 데 성공했습니다.

### 📝 LLM 변환 테스트 (샘플 3건)

전체 523개의 이벤트 중, 로컬 Ollama 모델(`gemma4`)에 과부하를 주지 않기 위해 첫 3개의 이벤트 블록을 시범 변환(Proof of Concept)했습니다. 

그 결과, 일상 대화가 완벽하게 구조화된 **"옵시디언 분석 위키 노트"**로 재탄생하여 `vault/wiki/analyses/` 폴더에 저장되었습니다.

**💡 생성된 옵시디언 위키 노트 예시 (2024년 8월 22일 - Averda 계약 해지 및 폐기물 처리 이슈)**

> ```markdown
> ---
> note_kind: wiki
> category: analyses
> title: "[Logistics Issue] 2024-08-22 Event #1"
> slug: logistics_issue_2024-08-22_1
> created: 2026-04-09
> tags: [analysis, logistics, abu_dhabi, issue]
> source_raw_id: convo-logistics_issue_2024-08-22_1
> ---
>
> ## 1. 이슈 개요 (Issue Summary)
> - 발생 일시: 24/8/22 오전 7시 30분 경
> - 핵심 문제: 하청 업체(Averda)의 계약 종료가 확인되었음에도 불구하고, 해당 업체의 잔여 폐기물 처리(Skip Bin) 요청 계획이 잔존하여 현장 혼선 및 지연 발생의 위험이 있었습니다.
>
> ## 2. 현장 대응 및 조치 (Response & Actions)
> - 국일 Kim (담당자)은 계약 종료 사실 확인 직후, 해당 업체로부터 빈 통(empty skip bins)을 요청하거나 MOSB에 반입하는 모든 활동을 즉각 중단하도록 지시했습니다.
> - 아민(Amin) 팀이 새로운 업체(Green Mountain)가 음식물 쓰레기 처리를 담당할 것임을 확인하고, 대체 폐기물 처리 프로세스로의 전환 지시를 전파했습니다.
>
> ## 3. 근본 원인 및 교훈 (Root Cause & Lessons Learned)
> - 원인 분석: 현장 물류 계획 수립 시, 참여 하청업체(Vendor)의 계약 상태(Contract Status) 변경 여부를 실시간으로 명확하게 공유받지 못했습니다.
> - 향후 대책: 장비 이동 및 배차 요청을 승인하기 전, 반드시 해당 하청업체의 계약 유효성 및 운영 자격 상태를 최우선으로 검증하는 절차(Mandatory Pre-verification)를 의무화해야 합니다.
>
> ## 4. 원문 대화 증거 (Evidence Log)
> - 24/8/22 AM 7:30 - 국일 Kim: it's been confirmed that Averda's contract with Adnoc L&S on Das island has been terminated.
> - 24/8/22 AM 7:31 - 국일 Kim: Please refrain from requesting empty skip bins from Averda, and hold off on bring them to MOSB.
> - 24/8/22 AM 7:32 - 국일 Kim: The Amin team has confirmed that a company Green Mountain will handle food waste disposal.
> ```

---

이런 식으로 복잡하고 산만한 WhatsApp 그룹챗 대화가 **문제/원인/교훈**이 명확히 담긴 기업형 지식베이스(Knowledge Base) 문서로 완벽하게 변환되었습니다! 

나머지 520개의 이슈들도 필요하실 때 파이썬 스크립트(`python scripts/parse_whatsapp_logistics.py`)의 `MAX_TO_PROCESS` 제한을 풀고 백그라운드에서 돌려놓기만 하면, 며칠 치의 대화 기록이 수백 개의 "현장 운영 교훈 위키"로 자동 변환되어 옵시디언에 차곡차곡 쌓이게 됩니다. 

결과물이 만족스러우신가요? 더 수정하고 싶으신 템플릿 양식이 있나요?  
  
다른 그룹 채팅방(예: DSV Delivery, SHU Logistics 등)의 거대한 대화 로그 파일들도 동일한 지식 추출 구조로 옵시디언 위키 문서화할 수 있도록 **가이드 문서**를 작성 완료했습니다.

해당 문서는 저장소의 `docs/web-clipping-setup.md`에 **WhatsApp 물류 그룹챗 지식화 자동화 가이드**라는 제목으로 저장해 두었습니다.

### 📋 가이드라인 핵심 내용

1. **스크립트 복사 및 설정**: 기존 파싱 스크립트`scripts/parse_whatsapp_logistics.py`)를 복제하여 새로운 파일(예: `parse_whatsapp_dsv.py`)을 만들고, 대상 채팅방의 `.txt` 파일 경로를 지정합니다.

2. **리스크 키워드(Risk Keywords) 재정의**: 각 채팅방 성격에 맞춰 이슈를 추출할 키워드 배열을 수정합니다. (예: DSV 방의 경우 `customs`, `clearance`, `penalty`, `demurrage` 등 통관/관세 지연 관련 키워드를 추가합니다.)

3. **LLM 프롬프트(페르소나) 수정**: 스크립트 내부의 프롬프트 텍스트를 대상 채팅방의 성격에 맞는 전문가(예: 통관 및 운송 담당 코디네이터)로 변경하여, 추출되는 마크다운의 품질을 높입니다.

4. **마크다운 템플릿(Slug, Tag) 매핑**: 옵시디언 위키 내에서 식별하기 쉽도록 파일명 생성 규칙(Slug)과 카테고리 태그`[analysis, freight, dsv, customs]`)를 업데이트합니다.

5. **테스트 및 일괄 실행**: 수정된 스크립트의 처리 제한`MAX_TO_PROCESS`)을 3~5개로 낮춰 정상적으로 템플릿이 작성되는지 테스트한 뒤, 제한을 풀고 백그라운드에서 전체 로그를 일괄 변환(Full Run)하도록 안내했습니다.

언제든 가이드 문서를 참고하여 새로운 파이프라인 스크립트를 생성하고, 원하시는 채팅방들을 모두 위키 지식베이스로 업로드해 보세요! 더 필요하신 부분이 있으신가요?