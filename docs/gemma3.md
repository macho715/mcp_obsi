판정: **예. A안으로 고정합니다.** Cursor 스킬의 Gemma 4 호출은 **Ollama** 기준으로 설계하면 됩니다. Ollama는 현재 `gemma4` 모델을 제공하고, 기본 `/api/chat` API와 OpenAI 호환 API를 함께 제공합니다. ([ollama.com][1])

근거: Ollama 공식 라이브러리에는 `gemma4`, `gemma4:e2b`, `gemma4:e4b`, `gemma4:26b`, `gemma4:31b`가 올라와 있고, `gemma4:e4b`는 9.6GB·128K context, `gemma4:e2b`는 7.2GB·128K context로 표기됩니다. 또한 공식 예시는 `ollama run gemma4`와 `POST /api/chat` 형식을 직접 제시합니다. ([ollama.com][1])

다음행동: **Skill은 Ollama native 기준**, 단 **호출 인터페이스는 얇은 adapter 1개로 감싸서** 나중 교체 가능성만 남겨두면 됩니다. 기본값은 `gemma4:e4b`, 경량 작업은 `gemma4:e2b`로 나누는 구성이 적절합니다. ([ollama.com][1])

## 최종 고정안

### 1) 런타임

* **Provider:** Ollama
* **Base URL:** `http://localhost:11434`
* **Primary model:** `gemma4:e4b`
* **Light model:** `gemma4:e2b`

### 2) 호출 방식

* 기본: **`/api/chat`**
* 선택: OpenAI 호환 `/v1/chat/completions`

Ollama 공식 문서는 자체 API를 제공하고, 별도로 OpenAI compatibility도 제공합니다. ([docs.ollama.com][2])

### 3) Skill별 모델 배치

* `obsidian-ingest` → `gemma4:e4b`
* `obsidian-query` → `gemma4:e4b`
* `obsidian-lint` → `gemma4:e2b` 기본, 복잡 시 `e4b`
* `obsidian-watch` → `gemma4:e2b`

## AGENTS.md에 넣을 고정 문구

```md
## LLM Runtime Policy
- Local LLM provider is fixed to Ollama.
- Default endpoint is `http://localhost:11434`.
- Primary model is `gemma4:e4b`.
- Lightweight tasks may use `gemma4:e2b`.
- Skills should call Ollama through a thin adapter, not by scattering raw HTTP calls across multiple files.
- Default API style is Ollama native `/api/chat`.
- OpenAI-compatible mode is optional and secondary.
```

## 호출 템플릿

### curl

```bash
curl http://localhost:11434/api/chat \
  -d '{
    "model": "gemma4:e4b",
    "messages": [
      {"role": "system", "content": "You are a structured knowledge-base compiler."},
      {"role": "user", "content": "Summarize and extract entities."}
    ],
    "stream": false
  }'
```

Ollama의 Gemma 4 페이지는 이와 같은 `POST /api/chat` 예시를 제공합니다. ([ollama.com][1])

### Python adapter 형태

```python
def generate_ollama(messages, model="gemma4:e4b", base_url="http://localhost:11434"):
    import requests
    r = requests.post(
        f"{base_url}/api/chat",
        json={
            "model": model,
            "messages": messages,
            "stream": False,
        },
        timeout=300,
    )
    r.raise_for_status()
    data = r.json()
    return data["message"]["content"]
```

## 운영 메모

* **thinking 제어**가 필요하면 system prompt 쪽 제어를 고려합니다. Ollama의 Gemma 4 문서는 `<|think|>` 토큰 기반 thinking mode를 설명합니다. ([ollama.com][1])
* 멀티턴에서는 이전 turn의 thought를 history에 다시 넣지 말라는 주의가 있습니다. ([ollama.com][1])
* 이미지 입력도 가능하므로, 추후 문서 캡처/OCR 보조 ingest까지 확장 여지가 있습니다. ([ollama.com][1])

## 최종 문구

**확정:**

* **A안 채택**
* **Ollama 고정**
* **기본 모델 `gemma4:e4b`**
* **경량 작업 `gemma4:e2b`**
* **기본 호출 `/api/chat`**

[1]: https://ollama.com/library/gemma4 "gemma4"
[2]: https://docs.ollama.com/api "Introduction - Ollama"
판정: **예. A안으로 진행하면 됩니다.** 현재 목표가 `app/` 무수정, KB 스키마 분리, Skill 단위 독립 운영이라면 **`obsidian-ingest / obsidian-query / obsidian-lint` 3개 독립 Skill**이 가장 맞습니다. Cursor는 **Rules/AGENTS.md = 지속 규칙**, **Skills = 동적 workflow**로 분리하는 구조입니다. ([Cursor][1])

근거: Ollama는 로컬에서 `http://localhost:11434` API를 제공하고, `POST /api/chat`로 직접 호출할 수 있습니다. 또 `keep_alive`로 모델 상주 시간을 제어할 수 있어, Skill별 독립 호출 구조에서도 불필요한 reload 비용을 줄일 수 있습니다. ([docs.ollama.com][2])

다음행동: **A안 확정** 후 아래 4가지만 같이 고정하십시오.

1. Skill은 3개로 분리
2. Ollama 호출은 각 Skill 안에 흩뿌리지 말고 **공통 호출 블록/템플릿**으로 통일
3. `wiki` 직접 쓰기 + `save_memory`는 포인터만
4. 기본 호출은 `/api/chat`, 모델은 `gemma4:e4b` 기본, 경량은 `gemma4:e2b`

## 최종 확정안

### 채택

* **A — 3개 독립 Cursor Skills**

### 보완 조건

* “각 Skill이 Ollama를 직접 호출”은 맞지만, **프롬프트/HTTP 형식/오류 처리**는 공통 규약으로 묶으십시오.
* 즉, **독립 Skill**이되 **중복 로직은 최소화**가 맞습니다.

## 왜 A안이 맞나

* **구조 분리 유지**
  `app/`는 memory/MCP 층, Skills는 KB workflow 층으로 역할이 안 섞입니다. ([Cursor][3])
* **테스트 용이**
  ingest/query/lint를 각각 개별 검증할 수 있습니다.
* **나중 교체 쉬움**
  B안처럼 서버 계약을 바꾸지 않으므로 rollback이 쉽습니다.
* **현재 Ollama와 잘 맞음**
  Ollama는 단순한 로컬 REST 호출 구조라 Skill에서 직접 부르기 쉽습니다. ([docs.ollama.com][2])

## 바로 잠글 운영 규칙

```md
- KB workflows are implemented as 3 independent Cursor Skills:
  - obsidian-ingest
  - obsidian-query
  - obsidian-lint
- Skills call Ollama directly at http://localhost:11434.
- Default API is POST /api/chat.
- Canonical knowledge is written to vault/wiki/.
- save_memory stores only pointer + short summary, never the full canonical wiki note.
- Shared Ollama request schema, model names, timeout, and error handling must remain identical across all skills.
```

## 추가로 한 가지

Ollama는 OpenAI 호환도 제공하지만, **비상태형 중심**입니다. 지금처럼 Skill이 각 작업을 독립 실행하는 구조라면 오히려 native `/api/chat`이 더 단순합니다. ([docs.ollama.com][4])

**결론:**

* **A안으로 진행**
* 단, **“독립 Skill + 공통 Ollama 호출 규약”**으로 고정
* B안은 나중에 production 중앙화가 필요할 때만 검토
* C안은 지금 시점에서는 비추천

[1]: https://cursor.com/docs/skills?utm_source=chatgpt.com "Agent Skills | Cursor Docs"
[2]: https://docs.ollama.com/api/chat?utm_source=chatgpt.com "Generate a chat message"
[3]: https://cursor.com/blog/agent-best-practices?utm_source=chatgpt.com "Best practices for coding with agents"
[4]: https://docs.ollama.com/api/openai-compatibility?utm_source=chatgpt.com "OpenAI compatibility"
