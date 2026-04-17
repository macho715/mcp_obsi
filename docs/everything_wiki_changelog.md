지금까지 한 일을 쉽게 말하면, **내 컴퓨터 파일들을 찾아서 Obsidian 스타일의 지식 wiki로 바꾸는 “첫 번째 안전한 파이프라인”을 만든 상태**입니다.

**1. 목표를 정리했습니다**
처음에는 Everything 검색과 AI 답변을 연결하는 이야기였는데, 중간에 목표를 정확히 바꿨습니다.

최종 목표는 이것입니다.

```text
내 로컬 컴퓨터 파일들
-> Everything으로 빠르게 찾기
-> 안전한 파일만 골라서 읽기
-> PDF/Word/Excel/텍스트 내용을 추출하기
-> vault/wiki 안에 지식 노트로 저장하기
```

저장 위치는 repo 내부 테스트 wiki로 정했습니다.

```text
C:\Users\SAMSUNG\Downloads\mcp_obsi-main\vault\wiki
```

**2. 설계 문서를 만들었습니다**
설계 문서에는 전체 구조와 안전 규칙을 적었습니다.

파일:
[2026-04-16-local-computer-knowledge-wiki-design.md](C:/Users/SAMSUNG/Downloads/mcp_obsi-main/docs/superpowers/specs/2026-04-16-local-computer-knowledge-wiki-design.md)

핵심 내용:
- Everything HTTP는 파일 검색만 담당
- 파일 본문은 ingest 단계에서만 읽음
- 원본 파일은 절대 수정하지 않음
- `.pdf`, `.docx`, `.xlsx`, `.xlsm`, `.md`, `.txt`, `.csv`, `.json`, `.log` 지원
- `.doc`, `.xls`, OCR PDF는 일단 제한 지원
- 결과는 `vault/wiki/sources`에 draft note로 저장

**3. 구현 계획 문서를 만들었습니다**
실제로 어떤 파일을 만들고, 어떤 테스트를 할지 단계별 계획을 작성했습니다.

파일:
[2026-04-16-local-computer-knowledge-wiki-implementation.md](C:/Users/SAMSUNG/Downloads/mcp_obsi-main/docs/superpowers/plans/2026-04-16-local-computer-knowledge-wiki-implementation.md)

처음 계획에는 Everything HTTP가 꺼져 있다고 적혀 있었지만, 사용자가 설정을 켠 뒤 최신 상태로 문서를 수정했습니다.

현재 Everything 설정은 통과했습니다.

```text
HTTP server: 켜짐
bind: 127.0.0.1
port: 8080
file download: 꺼짐
```

**4. Everything HTTP 연결을 확인했습니다**
Everything이 실제로 검색 API처럼 동작하는지 확인했습니다.

성공한 상태:
```text
http://127.0.0.1:8080/?search=*.md&json=1...
```

결과:
- HTTP 200
- JSON 검색 결과 반환
- `127.0.0.1:8080`에서만 listen
- 파일 다운로드 허용 꺼짐

즉, Everything은 이제 **로컬 전용 검색 엔진**으로 안전하게 쓸 수 있습니다.

**5. 실제 코드 5개를 만들었습니다**
이번 기능의 핵심 코드입니다.

1. [local_wiki_everything.py](C:/Users/SAMSUNG/Downloads/mcp_obsi-main/scripts/local_wiki_everything.py)  
Everything HTTP에 연결해서 파일 검색 결과를 가져옵니다.

2. [local_wiki_inventory.py](C:/Users/SAMSUNG/Downloads/mcp_obsi-main/scripts/local_wiki_inventory.py)  
내 PC에서 wiki 후보 파일 목록을 만듭니다. 이 단계는 파일 내용은 읽지 않고, 이름/경로/크기/수정일 같은 메타데이터만 봅니다.

3. [local_wiki_extract.py](C:/Users/SAMSUNG/Downloads/mcp_obsi-main/scripts/local_wiki_extract.py)  
선택된 파일의 내용을 읽습니다. PDF, Word, Excel, 텍스트 파일을 처리합니다.

4. [local_wiki_writer.py](C:/Users/SAMSUNG/Downloads/mcp_obsi-main/scripts/local_wiki_writer.py)  
추출한 내용을 `vault/wiki/sources/*.md` 형태의 wiki 노트로 저장합니다.

5. [local_wiki_ingest.py](C:/Users/SAMSUNG/Downloads/mcp_obsi-main/scripts/local_wiki_ingest.py)  
전체 흐름을 연결합니다.

```text
inventory 후보
-> 파일 추출
-> credential/secret hard-stop 검사
-> wiki note 작성
```

**6. 테스트도 만들었습니다**
각 코드 파일마다 테스트를 만들었습니다.

- Everything 연결 테스트
- inventory 생성 테스트
- 문서 추출 테스트
- wiki writer 테스트
- ingest 흐름 테스트

초기 deterministic pipeline 시점의 local-wiki 테스트 결과:

```text
24 passed
```

**7. dry-run까지 성공했습니다**
실제 wiki에 쓰기 전에 안전하게 미리 실행하는 dry-run을 했습니다.

Inventory dry-run:
```powershell
python scripts\local_wiki_inventory.py --dry-run --limit-per-extension 5
```

결과:
```text
queued=21 total=55
```

뜻:
- Everything으로 후보 파일 55개를 찾음
- 그중 안전 필터를 통과한 파일 21개가 ingest 후보가 됨
- 이 단계에서는 파일 본문을 읽지 않음

Ingest dry-run:
```powershell
python scripts\local_wiki_ingest.py --dry-run --limit 1
```

결과:
```text
would write wiki note
```

뜻:
- 실제로 쓰지는 않았지만
- 지금 실행하면 PDF 하나를 wiki note로 만들 수 있다는 것까지 확인함

**8. Python 개발 환경도 만들었습니다**
처음에는 `.venv`가 없어서 테스트/ruff가 제대로 안 됐습니다.

그래서 새로 만들었습니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,mcp]"
```

그 결과:
- `pytest`
- `ruff`
- `pyshacl`
- `pypdf`
- `python-docx`
- `openpyxl`
- `pandas`

등 필요한 개발 의존성이 설치됐습니다.

**9. 전체 테스트는 통과했습니다**
전체 pytest 결과:

```text
.\.venv\Scripts\python.exe -m pytest -q
PASS
```

즉, 이번 기능 때문에 기존 테스트가 깨지지는 않았습니다.

**10. ruff는 두 종류로 나눠 봐야 합니다**
새로 만든 local-wiki 파일만 검사하면 통과합니다.

```text
local-wiki focused ruff: PASS
local-wiki focused format: PASS
```

하지만 repo 전체 ruff는 실패합니다.

이 실패는 이번에 만든 파일 때문이 아니라 기존 파일 때문입니다.

예:
- `Logi ontol core doc\_giseong_to_json.py`
- `scripts\build_dashboard_graph_data.py`
- `scripts\vault_dedup.py`
- `local-rag\app\retrieval.py`

당시 제가 추천한 선택은:

```text
기존 ruff debt는 이번 작업 범위 밖으로 두고,
one-note live ingest만 승인해서 진행
```

**당시 상태를 한 줄로 말하면**
**초기 deterministic 코드는 준비됐고, 테스트도 통과했고, Everything 연결도 안전하게 됐습니다. 이후 Copilot proxy, credential guard, compact packet, cleaner candidate, fallback-continue가 추가됐습니다.**

아직 실행하지 않은 명령:

```powershell
.\.venv\Scripts\python.exe scripts\local_wiki_ingest.py --limit 1
```

이 명령을 실행하면 실제로:

```text
vault/wiki/sources/*.md
vault/wiki/index.md
vault/wiki/log.md
```

가 생성되거나 갱신됩니다.

즉, 다음 단계는 **실제 지식 wiki에 첫 번째 노트를 저장하는 것**입니다.

---

## 2026-04-16 추가 반영: Copilot proxy normalizer 구현 및 검증

이전 기록은 deterministic local-wiki 파이프라인까지의 상태였습니다. 이후 `standalone-package`의 Copilot proxy를 선택적으로 쓰는 normalizer 경로가 추가됐습니다.

**추가/변경된 파일**

1. [local_wiki_copilot.py](C:/Users/SAMSUNG/Downloads/mcp_obsi-main/scripts/local_wiki_copilot.py)  
   Standalone `/api/ai/chat`용 packet 생성, Copilot 요청 생성, JSON 응답 검증, fallback 오류 처리를 담당합니다.

2. [local_wiki_ingest.py](C:/Users/SAMSUNG/Downloads/mcp_obsi-main/scripts/local_wiki_ingest.py)  
   `--normalizer deterministic|copilot` 옵션이 추가됐습니다. Copilot 실패 시 deterministic normalization으로 fallback하고 이유를 결과에 남깁니다.

3. [test_local_wiki_copilot.py](C:/Users/SAMSUNG/Downloads/mcp_obsi-main/tests/test_local_wiki_copilot.py)  
   Copilot packet, `secret` sensitivity 거부, JSON 파싱, fallback 오류 테스트가 추가됐습니다.

4. [test_local_wiki_ingest.py](C:/Users/SAMSUNG/Downloads/mcp_obsi-main/tests/test_local_wiki_ingest.py)  
   Copilot normalizer 주입과 fallback 동작 테스트가 추가됐습니다.

**Standalone 확인 결과**

검증된 standalone 경로:

```text
C:\Users\SAMSUNG\Downloads\mcp_obsi-main\standalone-package-20260311T084247Z-1-001\standalone-package
```

검증된 서버:

```text
http://127.0.0.1:3010
```

확인된 내용:

- `GET /api/ai/health` -> HTTP 200
- service: `myagent-copilot-standalone`
- auth mode: `shared`
- chat smoke: route `copilot`, sensitivity `internal`, DLP `allow`, model `gpt-5-mini`
- 한 세션에서 확인된 node process PID: `47956`  
  단, PID는 세션별 증거라 재시작하면 바뀝니다.

**Standalone 실행 caveat**

처음에는 standalone dependency 상태가 불완전했습니다.

```powershell
pnpm install --frozen-lockfile
```

위 명령은 비대화형 환경에서 TTY 문제로 실패했습니다. 실제 복구에 성공한 명령은 다음입니다.

```powershell
$env:CI="true"; pnpm install --frozen-lockfile
```

또한 다음 명령은 standalone token 명령이 아니라 package-manager registry token 명령으로 동작했습니다.

```powershell
pnpm token --json
```

실제로 검증된 token warm-up 명령은 다음입니다. 토큰 값은 출력하거나 문서에 남기면 안 됩니다.

```powershell
node dist\cli.js token --json
```

검증된 서버 시작 명령:

```powershell
node dist\cli.js serve --host 127.0.0.1 --port 3010
```

**Copilot dry-run 결과**

실행한 명령:

```powershell
.\.venv\Scripts\python.exe scripts\local_wiki_ingest.py --normalizer copilot --dry-run --limit 1
```

당시 결과:

- 명령 자체는 성공했습니다.
- 현재 첫 번째 PDF 후보에서 standalone proxy가 `422 Unprocessable Entity`를 반환했습니다.
- ingest는 crash하지 않고 deterministic fallback을 사용했습니다.
- 따라서 이 결과는 “Copilot normalization 성공”이 아니라 **fallback 경로 검증 성공**입니다.

다음 live Copilot ingest 전에 할 일:

```text
Copilot packet을 더 작게 만들거나,
DLP/validation에 걸리지 않는 cleaner candidate로 dry-run을 다시 통과시킨 뒤 live ingest를 실행한다.
```

**최신 테스트/검증 상태**

Copilot + ingest focused tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_local_wiki_copilot.py tests\test_local_wiki_ingest.py -q
```

결과:

```text
14 passed
```

전체 local-wiki focused tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_local_wiki_everything.py tests\test_local_wiki_inventory.py tests\test_local_wiki_extract.py tests\test_local_wiki_writer.py tests\test_local_wiki_copilot.py tests\test_local_wiki_ingest.py -q
```

당시 결과:

```text
32 passed
```

전체 pytest:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

결과:

```text
PASS
```

Focused ruff/format:

```text
new local-wiki files: PASS
```

Repo-wide ruff/format:

```text
ruff check .: FAIL, 기존 unrelated debt 14건
ruff format --check .: FAIL, 기존 unrelated 파일 10개 format 필요
```

Git metadata 확인:

```powershell
git rev-parse --show-toplevel
```

결과:

```text
fatal: not a git repository
```

**당시 상태를 다시 한 줄로 말하면**

Everything 기반 deterministic wiki 파이프라인은 준비됐고, Copilot proxy 경로도 코드와 테스트는 준비됐습니다. 당시 첫 PDF 후보는 standalone `422`로 fallback됐고, 이 문제는 아래 compact packet 및 cleaner candidate 패치로 해결됐습니다.

---

## 2026-04-16 추가 반영: Copilot 422 완화 패치

Standalone `422` 가능성을 줄이기 위해 Copilot 입력을 더 작게 만들고, PDF보다 깨끗한 후보를 먼저 보내도록 바꿨습니다.

변경:

- Copilot excerpt 기본 상한을 `12,000`자에서 `4,000`자로 낮췄습니다.
- `MAX_EXCERPT_CHARS = 4_000`, `MAX_STRUCTURE_HINTS = 10`으로 구현했습니다.
- `structure_hints`는 최대 10개만 보냅니다.
- standalone 요청의 user message JSON은 pretty-print 대신 compact JSON으로 보냅니다.
- `--normalizer copilot` 모드에서는 후보 우선순위를 적용합니다.
- `order_candidates_for_copilot()`로 cleaner candidate ordering을 적용합니다.
- `.codex`, `.cursor`, `$Recycle.Bin` 같은 도구 설정/휴지통 경로는 일반 문서 후보 뒤로 보냅니다.
- Copilot dry-run에서 한 후보가 `422` 등으로 fallback되면 다음 후보를 계속 시도합니다.

Copilot 후보 우선순위:

```text
.md, .txt
-> .csv, .json, .log
-> .docx
-> .xlsx, .xlsm
-> .pdf
```

의도:

```text
처음부터 거친 PDF 추출물을 보내지 않고,
짧고 깨끗한 텍스트 계열 후보로 Copilot-normalized dry-run 성공률을 높인다.
한 파일의 422가 dry-run 전체를 실패처럼 보이게 만들지 않도록 다음 후보를 시도한다.
```

재검증 결과:

```powershell
.\.venv\Scripts\python.exe scripts\local_wiki_ingest.py --normalizer copilot --dry-run --limit 1
```

결과:

```text
status: dry-run
reason: would write wiki note; normalizer=copilot
path: C:\HVDC_WORK\REPORTS\기성\GM202603\260412_UAE HVDC_(Globalmaritime)_MWS 기성(13차) 집행의 건.docx
```

즉, compact packet과 cleaner candidate 재시도 이후에는 `422` fallback 없이 Copilot-normalized dry-run이 통과했습니다.

이 패치의 최신 focused 검증:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_local_wiki_copilot.py tests\test_local_wiki_ingest.py -q
.\.venv\Scripts\python.exe -m ruff check scripts\local_wiki_copilot.py scripts\local_wiki_ingest.py tests\test_local_wiki_copilot.py tests\test_local_wiki_ingest.py
.\.venv\Scripts\python.exe -m ruff format --check scripts\local_wiki_copilot.py scripts\local_wiki_ingest.py tests\test_local_wiki_copilot.py tests\test_local_wiki_ingest.py
```

결과:

```text
21 passed
All checks passed!
4 files already formatted
```

---

## 2026-04-16 추가 반영: local-wiki credential guard 분리

보안 정책을 전부 끄는 대신, local-wiki ingest에서 다음처럼 분리했습니다.

```text
개인/업무 민감정보: 사용자 승인 후 Copilot proxy 전송 허용
credential/secret: 항상 hard skip
```

코드 변경:

- [local_wiki_ingest.py](C:/Users/SAMSUNG/Downloads/mcp_obsi-main/scripts/local_wiki_ingest.py)에 `local_wiki_has_credential_pattern()`을 추가했습니다.
- 기존 skip reason `sensitive pattern`을 `credential pattern`으로 바꿨습니다.
- 전역 MCP 저장용 sanitize 정책은 변경하지 않았습니다.

테스트 변경:

- [test_local_wiki_ingest.py](C:/Users/SAMSUNG/Downloads/mcp_obsi-main/tests/test_local_wiki_ingest.py)에 credential guard 테스트를 추가했습니다.
- `api_key=...`, `Bearer ...`는 차단합니다.
- 전화번호, 내부 예산, 고객 미팅 메모 같은 일반 개인/업무 민감 텍스트는 local-wiki credential guard에서 차단하지 않습니다.
- credential guard 검증은 최신 focused pytest `21 passed`에 포함되어 있습니다.
- 실제 live write는 아직 실행하지 않았습니다. 최신 성공 결과는 dry-run이며, repo-local `vault/wiki/sources` 출력은 아직 관측되지 않았습니다.
- `copilot_metadata`는 client 응답에 포함될 수 있지만 아직 wiki note나 `vault/wiki/log.md`에 persist하지 않습니다.
