# Local Computer Knowledge Wiki Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local-file knowledge wiki pipeline that discovers local files through Everything HTTP, optionally normalizes extracted content through the existing `standalone-package` Copilot proxy, and writes draft source notes into `vault/wiki`.

**Architecture:** Implement scripts first, not public server routes. `local_wiki_inventory.py` probes Everything HTTP and writes metadata-only inventory; `local_wiki_ingest.py` extracts queued files, calls deterministic or Copilot proxy normalization, and writes draft wiki notes through focused helper modules.

**Tech Stack:** Python 3.11+, `requests`, `PyYAML`, existing `openpyxl`/`pandas`, planned `pypdf` and `python-docx`, pytest, repo-local scripts, existing Node 22+ `standalone-package` Copilot proxy.

---

## Current Local Finding

- Process: `C:\Program Files\Everything\Everything.exe`
- Service: `Everything`, status `Running`, start type `Automatic`
- Config: `C:\Users\SAMSUNG\AppData\Roaming\Everything\Everything.ini`
- Current HTTP values after manual setup:
  - `http_server_enabled=1`
  - `http_server_bindings=127.0.0.1`
  - `http_server_port=8080`
  - `http_server_allow_file_download=0`
- Probe result: `http://127.0.0.1:8080/?search=*.md&json=1...` returns HTTP 200 with JSON results

Do not change Everything settings from code. The inventory command may query metadata from the loopback HTTP endpoint, but ingest remains the only step that reads file bodies.

## Current Standalone Finding

- Package path: `C:\Users\SAMSUNG\Downloads\mcp_obsi-main\standalone-package-20260311T084247Z-1-001\standalone-package`
- Endpoint: `POST http://127.0.0.1:3010/api/ai/chat`
- Health endpoint: `GET http://127.0.0.1:3010/api/ai/health`
- Default model: `github-copilot/gpt-5-mini`
- Auth source: GitHub Copilot device login or `MYAGENT_GITHUB_TOKEN` compatible environment token.
- Runtime token cache: `MYAGENT_HOME\cache\github-copilot.token.json` or OS temp fallback.
- Routing rule: `sensitivity: "secret"` requires local-only inference and must not be used because this computer will not run local LLMs.
- Copilot normalization rule: use `sensitivity: "internal"` and call Copilot only through standalone-package.
- Performance mode: user approved ignoring personal/business-data sensitivity for this workflow, so `MYAGENT_PROXY_ALLOW_SANITIZED_TO_COPILOT=1` may be used. Credential-like material remains a repo-local hard stop, and standalone high or critical DLP blocks still stop the request.
- Verified runtime caveat: `pnpm token` is not the standalone token helper in this environment; it calls the package-manager registry token command and failed with registry auth. After dependency repair, the verified command is `node dist\cli.js token --json` with token output suppressed.
- Verified dependency caveat: non-interactive `pnpm install --frozen-lockfile` required `$env:CI="true"` to avoid TTY prompts.
- Verified server command: `node dist\cli.js serve --host 127.0.0.1 --port 3010`.
- Current smoke evidence: `GET /api/ai/health` returned HTTP 200, and a small `/api/ai/chat` request routed to `copilot` with `sensitivity: "internal"` and DLP `allow`.
- Current Copilot dry-run evidence: `scripts\local_wiki_ingest.py --normalizer copilot --dry-run --limit 1` completed, but the first queued PDF candidate received standalone `422` and used deterministic fallback. This verifies the fallback path, not a successful Copilot-normalized note.
- Current mitigation update: Copilot packets now default to a 4,000-character excerpt and 10 structure hints, and Copilot mode orders cleaner `.md/.txt` candidates before `.csv/.json/.log`, `.docx`, spreadsheets, and `.pdf`.
- Current mitigation update: Copilot mode pushes `.codex`, `.cursor`, and `$Recycle.Bin` candidates behind normal documents, and Copilot dry-run tries the next candidate after a fallback so one noisy file does not consume the only dry-run slot.
- Current post-mitigation evidence: `scripts\local_wiki_ingest.py --normalizer copilot --dry-run --limit 1` completed without fallback and returned `reason="would write wiki note; normalizer=copilot"` for `C:\HVDC_WORK\REPORTS\기성\GM202603\260412_UAE HVDC_(Globalmaritime)_MWS 기성(13차) 집행의 건.docx`.

Do not add direct Copilot/GitHub API calls from the Python ingest code. The Python side talks only to the local standalone proxy.

## File Structure

- Create: `scripts/local_wiki_everything.py` - loopback-only Everything HTTP provider.
- Create: `scripts/local_wiki_inventory.py` - metadata-only discovery CLI.
- Create: `scripts/local_wiki_extract.py` - read-only document extraction.
- Create: `scripts/local_wiki_writer.py` - `vault/wiki` tree and draft note writer.
- Create: `scripts/local_wiki_copilot.py` - standalone-package Copilot proxy client, AI packet builder, JSON validator, and deterministic fallback adapter.
- Create: `scripts/local_wiki_ingest.py` - inventory-to-wiki orchestrator.
- Create: `tests/test_local_wiki_everything.py`
- Create: `tests/test_local_wiki_inventory.py`
- Create: `tests/test_local_wiki_extract.py`
- Create: `tests/test_local_wiki_writer.py`
- Create: `tests/test_local_wiki_copilot.py`
- Create: `tests/test_local_wiki_ingest.py`
- Modify: `pyproject.toml` - add `pypdf>=5.0` and `python-docx>=1.1`.
- Modify: `uv.lock` only if dependency tooling is run.

## Current Execution Evidence

This section records actual implementation status. The task checklist below remains as the original execution plan.

- Created: `scripts/local_wiki_everything.py`, `scripts/local_wiki_inventory.py`, `scripts/local_wiki_extract.py`, `scripts/local_wiki_writer.py`, `scripts/local_wiki_copilot.py`, `scripts/local_wiki_ingest.py`.
- Created or updated tests: `tests/test_local_wiki_everything.py`, `tests/test_local_wiki_inventory.py`, `tests/test_local_wiki_extract.py`, `tests/test_local_wiki_writer.py`, `tests/test_local_wiki_copilot.py`, `tests/test_local_wiki_ingest.py`.
- Copilot/ingest focused tests: `.\.venv\Scripts\python.exe -m pytest tests\test_local_wiki_copilot.py tests\test_local_wiki_ingest.py -q` -> PASS, `21 passed`.
- Full local-wiki focused tests: `.\.venv\Scripts\python.exe -m pytest tests\test_local_wiki_everything.py tests\test_local_wiki_inventory.py tests\test_local_wiki_extract.py tests\test_local_wiki_writer.py tests\test_local_wiki_copilot.py tests\test_local_wiki_ingest.py -q` -> PASS, `39 passed`.
- Focused ruff and format for changed local-wiki files -> PASS; `ruff check` reported `All checks passed!`, and `ruff format --check` reported `4 files already formatted`.
- Full pytest: `.\.venv\Scripts\python.exe -m pytest -q` -> PASS.
- Repo-wide ruff: `.\.venv\Scripts\python.exe -m ruff check .` -> FAIL due existing unrelated debt, not the local-wiki files; latest recorded count is 14 errors, 8 fixable.
- Repo-wide format: `.\.venv\Scripts\python.exe -m ruff format --check .` -> FAIL due existing unrelated files; latest recorded count is 10 files would be reformatted and 236 files already formatted.
- Git metadata: `git rev-parse --show-toplevel` -> FAIL, `.git` exists but git reports `fatal: not a git repository`.
- Standalone currently verified at `http://127.0.0.1:3010`; one observed running node process was PID `47956`, but PID is session-specific evidence only.
- `uv.lock` was not intentionally updated as part of this local-wiki implementation.
- TDD evidence for compact Copilot mitigation: RED failed on the old `12,000` character packet limit and missing candidate ordering; GREEN passed after setting `MAX_EXCERPT_CHARS = 4_000`, `MAX_STRUCTURE_HINTS = 10`, compact JSON serialization, cleaner candidate ordering, low-value path penalty, and fallback-continue dry-run behavior.
- Live Copilot ingest has not been run. The latest successful Copilot check is dry-run only; no repo-local `vault/wiki/sources` output was observed.

## Task 1: Everything HTTP Provider

**Files:** create `scripts/local_wiki_everything.py`; create `tests/test_local_wiki_everything.py`.

- [ ] **Step 1: Write failing tests**

Test loopback enforcement, URL construction, JSON parsing, and bad payload rejection.

```python
import pytest

from scripts.local_wiki_everything import (
    EverythingHttpError,
    build_everything_url,
    ensure_loopback_base_url,
    parse_everything_results,
)


def test_ensure_loopback_base_url_accepts_default_localhost():
    assert ensure_loopback_base_url("http://127.0.0.1:8080") == "http://127.0.0.1:8080"


def test_ensure_loopback_base_url_rejects_non_loopback():
    with pytest.raises(ValueError, match="loopback"):
        ensure_loopback_base_url("http://192.168.0.5:8080")


def test_build_everything_url_includes_required_columns():
    url = build_everything_url("http://127.0.0.1:8080", "*.pdf", 25)
    rendered = url.geturl()
    assert "search=%2A.pdf" in rendered
    assert "json=1" in rendered
    assert "path_column=1" in rendered
    assert "size_column=1" in rendered
    assert "date_modified_column=1" in rendered


def test_parse_everything_results_normalizes_full_path():
    payload = {"results": [{"name": "Report.pdf", "path": "C:\\Docs", "size": "120"}]}
    assert parse_everything_results(payload)[0]["path"] == "C:\\Docs\\Report.pdf"


def test_parse_everything_results_rejects_bad_payload():
    with pytest.raises(EverythingHttpError):
        parse_everything_results({"not_results": []})
```

- [ ] **Step 2: Run failing test**

Run: `.\.venv\Scripts\python.exe -m pytest tests\test_local_wiki_everything.py -q`

Expected: fail because module does not exist.

- [ ] **Step 3: Implement provider**

Implement `ensure_loopback_base_url`, `build_everything_url`, `parse_everything_results`, and `search_everything`. Use `EVERYTHING_HTTP_BASE_URL`, default `http://127.0.0.1:8080`, `requests.get(..., timeout=5)`, and raise `EverythingHttpError` on connection, HTTP, or JSON failures. Never accept non-loopback hosts.

- [ ] **Step 4: Verify provider**

Run: `.\.venv\Scripts\python.exe -m pytest tests\test_local_wiki_everything.py -q`

Expected: pass.

## Task 2: Metadata-Only Inventory

**Files:** create `scripts/local_wiki_inventory.py`; create `tests/test_local_wiki_inventory.py`.

- [ ] **Step 1: Write failing tests**

Test extension query generation, high-risk path exclusion, safe candidate queueing, and writing both `latest.json` and a timestamped run file.

```python
import json

from scripts.local_wiki_inventory import build_extension_queries, classify_candidate, write_inventory


def test_build_extension_queries_contains_requested_formats():
    assert "*.pdf" in build_extension_queries()
    assert "*.docx" in build_extension_queries()
    assert "*.xlsx" in build_extension_queries()
    assert "*.md" in build_extension_queries()


def test_classify_candidate_excludes_appdata():
    status = classify_candidate({"path": "C:\\Users\\SAMSUNG\\AppData\\x.txt", "extension": ".txt"})
    assert status == {"status": "excluded", "reason": "high-risk path"}


def test_classify_candidate_queues_safe_pdf():
    status = classify_candidate({"path": "C:\\Users\\SAMSUNG\\Documents\\a.pdf", "extension": ".pdf", "size": 100})
    assert status == {"status": "queued", "reason": "safe candidate"}


def test_write_inventory_outputs_latest_and_run(tmp_path):
    latest, run = write_inventory({"candidates": []}, output_root=tmp_path, timestamp="20260416-120000")
    assert latest.exists()
    assert run.exists()
    assert json.loads(latest.read_text(encoding="utf-8")) == {"candidates": []}
```

- [ ] **Step 2: Run failing test**

Run: `.\.venv\Scripts\python.exe -m pytest tests\test_local_wiki_inventory.py -q`

Expected: fail because module does not exist.

- [ ] **Step 3: Implement inventory CLI**

Implement:

- `SUPPORTED_EXTENSIONS = [".pdf", ".docx", ".doc", ".xlsx", ".xls", ".xlsm", ".md", ".txt", ".csv", ".json", ".log"]`
- `build_extension_queries()`
- `classify_candidate(candidate)`
- `write_inventory(payload, output_root=Path("runtime/local-wiki-inventory"), timestamp=None)`
- CLI flags: `--dry-run`, `--limit-per-extension`

Required exclusion defaults:

- `C:\Windows`
- `C:\Program Files`
- `C:\Program Files (x86)`
- `C:\Users\SAMSUNG\AppData`
- `.git`, `node_modules`, `.venv`, `dist`, `build`, `.cache`
- filename parts: `password`, `secret`, `token`, `apikey`, `private-key`

Size defaults:

- `.log`: 2 MB
- `.md`, `.txt`, `.csv`, `.json`: 5 MB
- `.pdf`, `.docx`, `.xlsx`, `.xlsm`: 20 MB
- `.doc`, `.xls`: excluded as legacy format

- [ ] **Step 4: Verify inventory tests**

Run: `.\.venv\Scripts\python.exe -m pytest tests\test_local_wiki_everything.py tests\test_local_wiki_inventory.py -q`

Expected: pass.

- [ ] **Step 5: Verify current local Everything state**

Run: `.\.venv\Scripts\python.exe scripts\local_wiki_inventory.py --dry-run --limit-per-extension 5`

Expected now: command writes an inventory file with queued and excluded candidates. It must not read document bodies.

## Task 3: Document Extraction

**Files:** create `scripts/local_wiki_extract.py`; create `tests/test_local_wiki_extract.py`; modify `pyproject.toml`.

- [ ] **Step 1: Add dependencies**

Modify `pyproject.toml` project dependencies to include:

```toml
"pypdf>=5.0",
"python-docx>=1.1",
```

- [ ] **Step 2: Write failing tests**

Test `.txt`, `.json`, `.xlsx`, and legacy `.doc` skip behavior.

```python
import json

from openpyxl import Workbook

from scripts.local_wiki_extract import extract_document


def test_extract_text_file(tmp_path):
    path = tmp_path / "note.txt"
    path.write_text("alpha\nbeta", encoding="utf-8")
    assert "alpha" in extract_document(path)["text"]


def test_extract_json_file(tmp_path):
    path = tmp_path / "data.json"
    path.write_text(json.dumps({"alpha": 1}), encoding="utf-8")
    assert '"alpha": 1' in extract_document(path)["text"]


def test_extract_xlsx_file(tmp_path):
    path = tmp_path / "book.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "SheetA"
    ws.append(["Name", "Qty"])
    ws.append(["Cable", 3])
    wb.save(path)
    result = extract_document(path)
    assert result["status"] == "ok"
    assert "SheetA" in result["text"]


def test_extract_legacy_doc_is_limited(tmp_path):
    path = tmp_path / "legacy.doc"
    path.write_bytes(b"fake")
    assert extract_document(path)["status"] == "limited"
```

- [ ] **Step 3: Run failing test**

Run: `.\.venv\Scripts\python.exe -m pytest tests\test_local_wiki_extract.py -q`

Expected: fail because module does not exist.

- [ ] **Step 4: Implement extractor**

Implement `extract_document(path: Path) -> dict` with:

- text read for `.md`, `.txt`, `.log`, encoding order `utf-8`, `utf-8-sig`, `cp949`, fallback replacement
- CSV first 30 rows
- JSON parsed and pretty-printed
- XLSX/XLSM via `openpyxl.load_workbook(read_only=True, data_only=True)`, first 25 sheets, first 30 rows, first 20 columns
- PDF via `pypdf.PdfReader`, first 20 pages, limited if no extractable text
- DOCX via `python-docx`, paragraphs and first 10 tables
- `.doc` and `.xls` return `{"status": "limited", "reason": "legacy binary format skipped", "text": ""}`
- cap returned text at 12,000 characters

- [ ] **Step 5: Verify extractor**

Run: `.\.venv\Scripts\python.exe -m pytest tests\test_local_wiki_extract.py -q`

Expected: pass after dependencies are installed.

## Task 4: Wiki Writer

**Files:** create `scripts/local_wiki_writer.py`; create `tests/test_local_wiki_writer.py`.

- [ ] **Step 1: Write failing tests**

Test slug hashing, array frontmatter, and creation of `sources`, `index.md`, and `log.md`.

```python
from scripts.local_wiki_writer import safe_slug, write_wiki_note


def test_safe_slug_adds_hash():
    slug = safe_slug("WH 종합 정리 분석보고서", "C:\\x.md")
    assert len(slug.split("-")[-1]) == 8


def test_write_wiki_note_creates_sources_index_and_log(tmp_path):
    note = write_wiki_note(
        vault_root=tmp_path,
        title="Example",
        source_path="C:\\file.txt",
        source_ext=".txt",
        source_size=10,
        source_modified_at="2026-04-16",
        summary="Short summary",
        key_facts=["Fact one"],
        extracted_structure=["Section one"],
        topics=["topic"],
        entities=[],
        projects=[],
        extraction_status="ok",
    )
    assert note.exists()
    assert (tmp_path / "wiki" / "sources").exists()
    assert (tmp_path / "wiki" / "index.md").exists()
    assert (tmp_path / "wiki" / "log.md").exists()
    assert "topics:" in note.read_text(encoding="utf-8")
```

- [ ] **Step 2: Run failing test**

Run: `.\.venv\Scripts\python.exe -m pytest tests\test_local_wiki_writer.py -q`

Expected: fail because module does not exist.

- [ ] **Step 3: Implement writer**

Implement:

- `safe_slug(title, source_path)` using ASCII slug plus 8-char SHA-256 source path hash
- `ensure_wiki_tree(vault_root)` creating `wiki/sources`, `wiki/concepts`, `wiki/entities`, `wiki/analyses`, `wiki/index.md`, `wiki/log.md`
- `write_wiki_note(...)` writing `vault/wiki/sources/<slug>.md`

Frontmatter must include:

```yaml
type: local_file_knowledge
status: draft
title: "<title>"
source_path: "<absolute source path>"
source_ext: "<extension>"
source_size: <int>
source_modified_at: "<value>"
ingested_at: "<today>"
topics: []
entities: []
projects: []
tags:
  - local-wiki
  - auto-ingest
```

- [ ] **Step 4: Verify writer**

Run: `.\.venv\Scripts\python.exe -m pytest tests\test_local_wiki_writer.py -q`

Expected: pass.

## Task 5: Standalone Copilot Proxy Normalizer

**Files:** create `scripts/local_wiki_copilot.py`; create `tests/test_local_wiki_copilot.py`; later modify `scripts/local_wiki_ingest.py`.

- [ ] **Step 1: Write failing tests**

Test packet building, request body shape, strict JSON extraction, fallback behavior, and `secret` sensitivity rejection.

```python
import pytest

from scripts.local_wiki_copilot import (
    CopilotNormalizationError,
    build_copilot_packet,
    build_copilot_request,
    parse_copilot_normalization,
)


def test_build_copilot_packet_keeps_bounded_excerpt():
    packet = build_copilot_packet(
        source_path="C:\\safe.txt",
        source_ext=".txt",
        extraction={"status": "ok", "text": "alpha " * 5000},
    )
    assert packet["source_ext"] == ".txt"
    assert len(packet["excerpt"]) <= 4000


def test_build_copilot_request_uses_internal_sensitivity():
    body = build_copilot_request({"source_ext": ".txt", "excerpt": "alpha"})
    assert body["model"] == "github-copilot/gpt-5-mini"
    assert body["sensitivity"] == "internal"


def test_build_copilot_request_rejects_secret_sensitivity():
    with pytest.raises(ValueError, match="secret"):
        build_copilot_request({"excerpt": "alpha"}, sensitivity="secret")


def test_parse_copilot_normalization_requires_json_object():
    parsed = parse_copilot_normalization('{"title":"A","summary":"B","topics":["local-file"]}')
    assert parsed["title"] == "A"


def test_parse_copilot_normalization_rejects_non_json():
    with pytest.raises(CopilotNormalizationError):
        parse_copilot_normalization("not json")
```

- [ ] **Step 2: Run failing test**

Run: `.\.venv\Scripts\python.exe -m pytest tests\test_local_wiki_copilot.py -q`

Expected: fail because module does not exist.

- [ ] **Step 3: Implement standalone proxy client**

Implement:

- `build_copilot_packet(source_path, source_ext, extraction, max_excerpt_chars=4000)`
- `build_copilot_request(packet, model="github-copilot/gpt-5-mini", sensitivity="internal")`
- `parse_copilot_normalization(text)`
- `normalize_with_copilot_proxy(packet, endpoint="http://127.0.0.1:3010/api/ai/chat", auth_token=None, timeout=120)`

Required behavior:

- Never send `sensitivity: "secret"`.
- Send `sensitivity: "internal"` by default.
- Keep default excerpt at or below 4,000 characters and `structure_hints` at or below 10 items to reduce standalone validation and DLP failures.
- Accept optional `LOCAL_WIKI_COPILOT_ENDPOINT`, defaulting to `http://127.0.0.1:3010/api/ai/chat`.
- Accept optional `LOCAL_WIKI_COPILOT_TOKEN` and pass it as `x-ai-proxy-token`.
- Prompt must require JSON only.
- The request packet should include source metadata, extracted structure hints, and bounded excerpts, not a full raw dump unless later explicitly approved.
- Parse only a JSON object response. Reject arrays, prose-only answers, and missing required fields.
- Normalize missing arrays to `[]` and tags to include `local-wiki` and `auto-ingest`.

- [ ] **Step 4: Verify standalone proxy client tests**

Run: `.\.venv\Scripts\python.exe -m pytest tests\test_local_wiki_copilot.py -q`

Expected: pass.

- [ ] **Step 5: Manual standalone performance setup**

In a separate PowerShell session:

```powershell
cd C:\Users\SAMSUNG\Downloads\mcp_obsi-main\standalone-package-20260311T084247Z-1-001\standalone-package
$env:MYAGENT_PROXY_HOST="127.0.0.1"
$env:MYAGENT_PROXY_PORT="3010"
$env:MYAGENT_PROXY_ALLOW_SANITIZED_TO_COPILOT="1"
$env:MYAGENT_PROXY_REQUIRE_PUBLIC_GUARDS="0"
$env:MYAGENT_PROXY_OPS_LOGS="1"
$env:CI="true"; pnpm install --frozen-lockfile
node dist\cli.js token --json
node dist\cli.js serve --host 127.0.0.1 --port 3010
```

Expected: token command succeeds without printing the token, server starts on `127.0.0.1:3010`, and `GET /api/ai/health` returns HTTP 200.

Observed caveat: do not use bare `pnpm token`; in this environment that command maps to the package-manager registry token command.

## Task 6: Ingest Orchestrator

**Files:** create `scripts/local_wiki_ingest.py`; create `tests/test_local_wiki_ingest.py`.

- [ ] **Step 1: Write failing tests**

Test queued candidate loading, deterministic normalization, and optional Copilot normalization injection.

```python
import json

from scripts.local_wiki_ingest import load_queued_candidates, normalize_extraction


def test_load_queued_candidates_filters_status(tmp_path):
    path = tmp_path / "latest.json"
    path.write_text(json.dumps({"candidates": [{"path": "C:\\safe.txt", "status": "queued"}, {"path": "C:\\bad.txt", "status": "excluded"}]}), encoding="utf-8")
    assert load_queued_candidates(path) == [{"path": "C:\\safe.txt", "status": "queued"}]


def test_normalize_extraction_creates_summary():
    result = normalize_extraction("C:\\safe.txt", "Alpha beta gamma\nSecond line", "ok")
    assert result["summary"].startswith("Alpha beta gamma")
    assert result["topics"] == ["local-file"]
```

- [ ] **Step 2: Run failing test**

Run: `.\.venv\Scripts\python.exe -m pytest tests\test_local_wiki_ingest.py -q`

Expected: fail because module does not exist.

- [ ] **Step 3: Implement orchestrator**

Implement CLI:

```powershell
.\.venv\Scripts\python.exe scripts\local_wiki_ingest.py --dry-run --limit 1
.\.venv\Scripts\python.exe scripts\local_wiki_ingest.py --limit 1
.\.venv\Scripts\python.exe scripts\local_wiki_ingest.py --normalizer copilot --dry-run --limit 1
```

Required behavior:

- Read `runtime/local-wiki-inventory/latest.json` by default.
- Only use candidates with `status == "queued"`.
- Skip missing files.
- Extract with `extract_document`.
- Stop wiki writing for a file if `local_wiki_has_credential_pattern(text)` is true. This is a credential/secret hard-stop, not a general personal/business sensitivity block.
- In `--dry-run`, do not write wiki notes.
- In live mode, write at most `--limit` notes through `write_wiki_note`.
- Use deterministic normalization first: title from filename stem, summary from first 300 normalized characters, topics `["local-file"]`.
- Add `--normalizer deterministic|copilot`, default `deterministic` until standalone smoke checks pass.
- In Copilot mode, prefer cleaner candidates before PDF: `.md/.txt`, `.csv/.json/.log`, `.docx`, `.xlsx/.xlsm`, then `.pdf`.
- In Copilot mode, push low-value tool/trash paths such as `.codex`, `.cursor`, and `$Recycle.Bin` after normal document candidates.
- In Copilot dry-run, when a candidate falls back because of `422` or another standalone error, continue to the next candidate until a Copilot-normalized candidate is found or all candidates have fallen back.
- When `--normalizer copilot` is selected, build a Copilot packet and call `normalize_with_copilot_proxy`.
- If Copilot returns invalid JSON, 401, 403, 409, 422, 429, 5xx, timeout, or connection error, fall back to deterministic normalization and record the fallback reason.
- Target behavior: if standalone returns a confirmed high or critical DLP block, skip Copilot normalization for that file and record the block. Current implementation treats standalone request failures such as `422` as Copilot failure and falls back to deterministic normalization; repo-local `local_wiki_has_credential_pattern(text)` still hard-skips token/password-like extracted text before wiki writing.
- Target behavior: log route/model/DLP/usage metadata when standalone returns it. Current implementation keeps fallback reason in `IngestResult.reason`; detailed Copilot metadata persistence into wiki/log output is deferred.

- [ ] **Step 4: Verify orchestrator**

Run: `.\.venv\Scripts\python.exe -m pytest tests\test_local_wiki_ingest.py -q`

Expected: pass.

## Task 7: End-To-End Verification

**Files:** no required code files unless tests reveal gaps.

- [ ] **Step 1: Run focused tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_local_wiki_everything.py tests\test_local_wiki_inventory.py tests\test_local_wiki_extract.py tests\test_local_wiki_writer.py tests\test_local_wiki_copilot.py tests\test_local_wiki_ingest.py -q
```

Expected: pass.

- [ ] **Step 2: Run current Everything dry-run**

Run:

```powershell
.\.venv\Scripts\python.exe scripts\local_wiki_inventory.py --dry-run --limit-per-extension 5
```

Expected with current settings: inventory file exists, queued candidates are present, excluded candidates have reasons, and no document bodies are read.

- [ ] **Step 3: Manual Everything HTTP checkpoint**

Manual configuration has already been completed and should remain:

```text
Enable HTTP Server
Bind/listen only on localhost if available
Port: 8080
Disable file download
```

Then verify:

```powershell
Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8080/?search=*.md&json=1&count=1&path_column=1&size_column=1&date_modified_column=1" -TimeoutSec 5
```

Expected: HTTP 200 with JSON results.

- [ ] **Step 4: Run live inventory**

Run:

```powershell
$env:EVERYTHING_HTTP_BASE_URL="http://127.0.0.1:8080"
.\.venv\Scripts\python.exe scripts\local_wiki_inventory.py --dry-run --limit-per-extension 20
```

Expected: `runtime/local-wiki-inventory/latest.json` contains queued and excluded candidates.

- [ ] **Step 5: Run one-note ingest**

Run:

```powershell
.\.venv\Scripts\python.exe scripts\local_wiki_ingest.py --dry-run --limit 1
.\.venv\Scripts\python.exe scripts\local_wiki_ingest.py --limit 1
```

Expected: one draft note under `vault/wiki/sources`, plus `vault/wiki/index.md` and `vault/wiki/log.md`.

- [ ] **Step 6: Run standalone proxy smoke**

Run while standalone is already running:

```powershell
Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:3010/api/ai/health" -TimeoutSec 5
```

Then run a small internal-sensitivity chat request:

```powershell
$body = @{
  model = "github-copilot/gpt-5-mini"
  sensitivity = "internal"
  messages = @(
    @{ role = "user"; content = "Return JSON only: {`"title`":`"Ping`",`"summary`":`"pong`",`"topics`":[`"local-file`"]}" }
  )
} | ConvertTo-Json -Depth 5

Invoke-WebRequest `
  -UseBasicParsing `
  -Method Post `
  -Uri "http://127.0.0.1:3010/api/ai/chat" `
  -ContentType "application/json; charset=utf-8" `
  -Body $body `
  -TimeoutSec 120
```

Expected: HTTP 200 and response route `copilot`.

- [ ] **Step 7: Run one-note Copilot-normalized dry run**

Run:

```powershell
$env:LOCAL_WIKI_COPILOT_ENDPOINT="http://127.0.0.1:3010/api/ai/chat"
.\.venv\Scripts\python.exe scripts\local_wiki_ingest.py --normalizer copilot --dry-run --limit 1
```

Expected: command completes. If standalone fails, the result must report deterministic fallback rather than crash.

Observed result before compact-packet mitigation: command completed for the current first PDF candidate, but standalone returned `422`, so deterministic fallback was used and recorded in the result reason.

Observed result after compact-packet and cleaner-candidate mitigation: command completed without fallback for `C:\HVDC_WORK\REPORTS\기성\GM202603\260412_UAE HVDC_(Globalmaritime)_MWS 기성(13차) 집행의 건.docx`; result reason was `would write wiki note; normalizer=copilot`.

- [ ] **Step 8: Run one-note Copilot-normalized ingest**

Run only after the dry run and smoke request pass:

```powershell
.\.venv\Scripts\python.exe scripts\local_wiki_ingest.py --normalizer copilot --limit 1
```

Expected: one draft note under `vault/wiki/sources` with Copilot-normalized summary when the proxy accepts the packet, or deterministic fallback status when it does not. After the observed `422` dry-run, compact-packet and cleaner-candidate mitigation must pass dry-run before treating live Copilot normalization as proven.

- [ ] **Step 9: Run repo checks**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
```

Expected: report exact pass/fail. Do not claim green if existing ruff issues remain.

Observed latest status: full pytest passed; repo-wide ruff and format checks failed on existing unrelated debt. New local-wiki files passed focused ruff and format checks.

## Self-Review

Spec coverage:

- Everything HTTP provider: Task 1.
- Metadata-only PC-wide inventory: Task 2.
- Safety filters: Task 2 and Task 6.
- Document extraction: Task 3.
- Draft wiki notes and wiki tree: Task 4.
- Standalone Copilot proxy normalizer: Task 5.
- Ingest workflow: Task 6.
- Current Everything HTTP loopback state and manual checkpoint: Task 7.
- Copilot proxy smoke and fallback behavior: Task 7.

Deferred by design:

- OCR for scanned PDFs.
- Everything SDK/IPC provider.
- `.doc` and `.xls` conversion.
- Local LLM summarization through Ollama or `local-rag`.
- `save_memory` pointer registration.
