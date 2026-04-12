# WhatsApp 물류 그룹챗 지식화 자동화 가이드 (WhatsApp Logistics to Obsidian Wiki)

이 문서는 여러 방대한 WhatsApp 물류 그룹 채팅 로그를 지능적으로 파싱하고(Filtering), 핵심 물류 이슈만 추출하여, 옵시디언 지식베이스(Knowledge Base)의 구조화된 위키 노트(Lesson Learned)로 일괄 변환하는 파이프라인의 적용 가이드입니다.

---

## 1. 개요 (Overview)
*   **목적**: 수만 줄에 달하는 단답형/일상 대화 속에서 "이슈 발생 및 해결 과정"을 가진 의미 있는 대화 스레드를 추출하여, 옵시디언 위키의 **운영 판단용 자산(Analyses)**으로 자동 전환합니다.
*   **핵심 파이프라인**: 
    1. 정규식을 통한 로그 파싱 (시간 및 발신자 분리)
    2. 리스크 키워드 매칭 (이슈 발생 여부 판단)
    3. ±2시간 단위 청킹 (문맥 보존)
    4. 로컬 LLM(Ollama - `gemma4`)을 통한 마크다운 문서 자동 생성

---

## 2. 필수 준비 사항 (Prerequisites)
1. **WhatsApp 대화 내보내기 (Export Chat)**
   * 스마트폰 또는 WhatsApp Web에서 대상 그룹 채팅방을 열고 `대화 내보내기 (미디어 제외)`를 선택하여 `.txt` 파일로 다운로드합니다.
2. **로컬 LLM (Ollama) 실행**
   * 위키 문서를 작성해 줄 로컬 AI 모델이 켜져 있어야 합니다. 백그라운드에서 `Ollama` 앱을 실행하고, 모델(`gemma4:e4b`)이 다운로드되어 있는지 확인하세요.
3. **작업 폴더 이동**
   * 다운로드 받은 `.txt` 파일을 `whatsapp groupchat/대화/` 폴더 안으로 이동시킵니다.

---

## 3. 다른 그룹 채팅방에 파이프라인 적용하는 방법

파이썬 스크립트(`scripts/parse_whatsapp_logistics.py`)를 각 채팅방의 특성에 맞게 **살짝 수정**한 뒤 실행하면 됩니다. 

### Step 1: 스크립트 복사 및 설정값 변경
기존 스크립트(`scripts/parse_whatsapp_logistics.py`)를 복사하여 새로운 이름으로 저장합니다. (예: `parse_whatsapp_dsv.py`)

파일의 상단 설정 부분(Configuration)을 타겟 채팅방에 맞게 수정합니다:

```python
# 1. 처리할 카카오톡/WhatsApp 대화 로그 파일 경로 지정
LOG_FILE = r"whatsapp groupchat\대화\새로운 그룹챗 대화 파일명.txt"

# 2. 해당 그룹 채팅방 성격에 맞는 리스크 키워드 재정의 (Risk Keywords)
# 예: DSV Delivery 방이라면 통관, 관세, 운송 지연 관련 키워드 추가
RISK_KEYWORDS = [
    r"delay", r"customs", r"clearance", r"inspection", r"rejected", r"damage", 
    r"penalty", r"demurrage", r"detention", r"urgent", r"hold", r"problem", r"issue"
]

# 3. WhatsApp 날짜 포맷 확인 (LOG_PATTERN)
# 만약 파일의 날짜 형식이 다르다면 이 정규식을 수정해야 합니다. 
# (기본값은 '24/8/21 PM 4:13 - 이름: 내용' 형태를 지원합니다)
LOG_PATTERN = re.compile(r"^(\d{2}/\d{1,2}/\d{1,2})\s+(AM|PM|오전|오후)\s+(\d{1,2}:\d{2})\s+-\s+([^:]+):\s+(.*)$")
```

### Step 2: LLM 프롬프트(템플릿) 역할 커스터마이징
해당 채팅방의 **페르소나**에 맞게 스크립트 내부의 `prompt` 부분을 수정합니다. 

```python
    prompt = [
        {
            "role": "system",
            "content": (
                # 이 부분을 타겟 그룹챗의 성격으로 바꿉니다.
                "You are an expert customs clearance and freight forwarding coordinator for the UAE HVDC project. "
                "Extract the logistics issue, response, root cause, and lessons learned from the provided chat excerpt. "
                "Output MUST be in Markdown matching this template exactly:\n\n"
                "## 1. 이슈 개요 (Issue Summary)\n- 발생 일시: <date>\n- 핵심 문제: <summary>\n\n"
                "## 2. 현장 대응 및 조치 (Response & Actions)\n- <Action 1>\n- <Action 2>\n\n"
                "## 3. 근본 원인 및 교훈 (Root Cause & Lessons Learned)\n- 원인 분석: <Cause>\n- 향후 대책: <Lesson>\n\n"
                "## 4. 원문 대화 증거 (Evidence Log)\n- <3-5 lines of key original chat>\n\n"
                "Use Korean language. Keep it concise and professional."
            )
        },
        ...
```

### Step 3: 슬러그(Slug) 및 태그 변경
저장될 옵시디언 위키 문서의 이름(Slug)과 검색용 태그(Tag)를 변경합니다.

```python
    # 예: DSV_Delivery 방인 경우
    slug = f"dsv_issue_{start_date}_{index}"
    raw_id = f"convo-{slug}"

    # 태그 업데이트
    wiki_frontmatter = f"""---
note_kind: wiki
category: analyses
title: "[DSV Delivery Issue] {start_date} Event #{index}"
slug: {slug}
created: {datetime.now().strftime("%Y-%m-%d")}
tags: [analysis, freight, dsv, customs, issue]
source_raw_id: {raw_id}
---
"""
```

---

## 4. 파이프라인 실행 및 전체 자동화 (Execution)

### 테스트 실행 (소량 샘플링)
처음에는 9만 줄을 한 번에 다 돌리지 말고, 스크립트 하단 `main()` 함수의 `MAX_TO_PROCESS` 값을 작게(예: `3`) 설정하여 정상적으로 마크다운 문서가 만들어지는지 테스트합니다.

```bash
python scripts/parse_whatsapp_dsv.py
```
테스트 완료 후 `vault/wiki/analyses/` 폴더에 마크다운이 제대로 생성되었다면 다음으로 넘어갑니다.

### 전체 자동화 실행 (Full Run)
모든 설정이 완벽하다면 `MAX_TO_PROCESS` 제한을 해제(코드를 주석 처리하거나 매우 큰 값으로 변경)하고 백그라운드에서 스크립트를 실행해 둡니다. 

Ollama 모델의 사양과 대화량에 따라 **수십 분에서 수 시간**이 소요될 수 있으며, 작업이 끝나면 해당 그룹 채팅방의 과거 몇 년 치 주요 문제 해결 과정이 수백 개의 "현장 운영 교훈 위키"로 옵시디언 앱에 완벽히 정렬됩니다.