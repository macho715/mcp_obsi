# mcp_obsidian — Project Upgrade Report
> Generated: 2026-03-28 | Skill: project-upgrade v2.0

---

## 1) Executive Summary

- **목표**: obsidian-memory MCP 서버의 검색 품질, 보안, 운영 안정성을 production-grade로 끌어올린다.
- **핵심 발견**: 현재 SQLite keyword search가 유일한 검색 엔진이며 FTS5/vector search 미적용, Bearer token 인증만 존재(OAuth 미지원), rate limiting/caching 미들웨어 없음, CI에 coverage/security scan 미포함.
- **권장 방향**: (1) FTS5+sqlite-vec hybrid search 도입 → 검색 정확도 대폭 향상, (2) FastMCP 미들웨어로 rate limiting 추가, (3) OAuth 2.1 준비를 위한 auth 계층 리팩터링.

---

## 2) Current State Snapshot

| Area | Status | Evidence | Risk |
|------|--------|----------|------|
| **Search** | SQLite LIKE 기반, 최대 5건 | `app/services/index_store.py` | 🔴 정확도/성능 낮음 |
| **Auth** | Bearer token (MCP_API_TOKEN), no OAuth | `app/main.py:77-83` | 🟡 production 장기 운영 시 불충분 |
| **Rate Limiting** | 없음 | `app/main.py` | 🔴 agent loop 시 무제한 호출 가능 |
| **Caching** | 없음 | — | 🟡 반복 검색 시 불필요한 I/O |
| **CI** | pytest + ruff (3.11/3.13) | `.github/workflows/ci.yml` | 🟡 coverage 미측정, security scan 없음 |
| **Monitoring** | `/healthz` only | `app/main.py` | 🟡 메트릭/로그 미구축 |
| **Docs** | 16+ markdown docs, SYSTEM_ARCHITECTURE | `docs/`, root `.md` | 🟢 양호 |
| **Tests** | 11 test files, ~2920 LOC | `tests/` | 🟢 양호 (coverage gate 85%) |
| **Deploy** | Railway Docker, volume `/data` | `Dockerfile`, `deploy/` | 🟢 안정 |
| **Schema** | JSON Schema 2종 (memory_item, raw_conversation) | `schemas/` | 🟢 계약 존재 |

**Stack**: Python 3.11+, FastAPI 0.115+, Pydantic 2.8+, SQLite, FastMCP 1.0+, Railway Docker

---

## 3) Upgrade Ideas Top 10

| Rank | Idea | Bucket | Impact | Effort | Risk | Conf | PriorityScore | Evidence | First PR |
|-----:|------|--------|-------:|-------:|-----:|-----:|-----:|----------|----------|
| 1 | **FTS5 + sqlite-vec Hybrid Search** | Performance | 5 | 3 | 2 | 5 | **4.17** | Memento, sqlite-vec blog | `index_store.py` FTS5 마이그레이션 |
| 2 | **FastMCP Rate Limiting Middleware** | Reliability | 5 | 2 | 1 | 5 | **12.50** | FastMCP 2.9, fast.io guide | 미들웨어 등록 1 PR |
| 3 | **OAuth 2.1 Auth Layer** | Security | 5 | 4 | 3 | 4 | **1.67** | MCP spec draft, Microsoft ISE | auth 모듈 분리 |
| 4 | **CI Coverage + Security Scan** | DX/Tooling | 4 | 2 | 1 | 5 | **10.00** | GitHub Actions best practice | `ci.yml` 확장 |
| 5 | **Response Caching Middleware** | Performance | 3 | 2 | 1 | 4 | **6.00** | FastMCP middleware docs | cache middleware PR |
| 6 | **Structured Logging + Metrics** | Reliability | 4 | 3 | 1 | 4 | **5.33** | FastAPI production guide | `structlog` 도입 |
| 7 | **Gunicorn + Multi-worker** | Performance | 3 | 2 | 2 | 3 | **2.25** | Railway FastAPI guide | `Dockerfile` CMD 변경 |
| 8 | **Knowledge Graph / Backlink Index** | Architecture | 4 | 4 | 3 | 3 | **1.00** | obsidian-mcp-plugin, KG tools | graph store 신규 |
| 9 | **Embedding Generation Pipeline** | Architecture | 4 | 4 | 3 | 3 | **1.00** | sqlite-vec guide | embedding worker |
| 10 | **MCP Tool Annotations Completion** | Docs/Process | 2 | 1 | 1 | 5 | **10.00** | MCP spec, FastMCP docs | annotation 추가 |

> PriorityScore = (Impact × Confidence) / (Effort × Risk)

---

## 4) Best 3 Deep Report

### BEST #1: FTS5 + sqlite-vec Hybrid Search

**Goal**
- SQLite FTS5로 full-text keyword search 전환 (현재 LIKE 기반 → trigram/BM25 순위)
- sqlite-vec로 semantic vector search 추가 (임베딩 기반 유사도)
- Hybrid scoring: `alpha * FTS5_rank + (1-alpha) * cosine_similarity`
- 검색 정확도 MAPE ≤ 15% 달성

**Non-goals**
- 외부 vector DB (Pinecone, Qdrant) 도입하지 않음 — SQLite embedded 유지
- 실시간 embedding generation 서버 구축하지 않음 — batch/on-write로 처리

**Proposed Design**
- `index_store.py` → FTS5 virtual table 마이그레이션 (title + content + tags)
- 신규 `vector_store.py` → sqlite-vec 테이블 생성, embedding 저장/검색
- `memory_store.py.search()` → hybrid scorer 호출
- Embedding source: `sentence-transformers/all-MiniLM-L6-v2` (384d, 로컬 or API)
- Migration: 기존 SQLite → FTS5 rebuild + 기존 노트 일괄 embedding 생성 스크립트

**PR Plan (4 PRs)**
1. **PR1**: `index_store.py` FTS5 마이그레이션 + 기존 테스트 호환 (scope: `app/services/index_store.py`, `tests/test_memory_store.py` | rollback: FTS5 테이블 drop → 기존 테이블 restore)
2. **PR2**: `vector_store.py` 신규 + sqlite-vec integration (scope: `app/services/vector_store.py`, `pyproject.toml` | rollback: 모듈 삭제)
3. **PR3**: Hybrid search scorer + `search_memory` tool 반환값 확장 (scope: `app/mcp_server.py`, `app/services/memory_store.py` | rollback: scorer 비활성화 → FTS5-only fallback)
4. **PR4**: Batch embedding 생성 스크립트 + CI integration test (scope: `scripts/`, `tests/` | rollback: 스크립트 삭제)

**Tests**
- Unit: FTS5 인덱싱/검색 정확도, vector 유사도 top-k 정확성
- Integration: hybrid search end-to-end (keyword + semantic 혼합 쿼리)
- Perf: 1000노트 기준 검색 latency < 100ms
- Security: embedding 입력 sanitization

**Rollout & Rollback**
- Feature flag: `SEARCH_MODE=fts5|hybrid|legacy` 환경변수
- Canary: preview env에서 7일 운영 후 production 전환
- Revert: `SEARCH_MODE=legacy`로 즉시 롤백

**Risks & Mitigations**
1. sqlite-vec 빌드 실패 (플랫폼 호환) → Docker 이미지에 pre-built wheel 포함
2. Embedding 모델 사이즈 → MiniLM-L6 (80MB) 경량 모델 선택
3. FTS5 마이그레이션 데이터 손실 → migration 전 SQLite backup 필수
4. Railway volume 크기 증가 → embedding 벡터 약 1.5MB/1000노트, 무시 가능
5. 검색 결과 품질 저하 → alpha 파라미터 튜닝 + A/B 비교 스크립트

**KPI Targets**
- Search relevance (nDCG@5): ≥ 0.75
- Search latency (p95): < 200ms
- Index rebuild time: < 30s for 5000 notes
- Zero regression on existing `pytest -q`

**Dependencies / Migration traps**
- `sqlite-vec` requires platform-specific binary → Docker multi-stage build 필요
- FTS5는 Python 3.11+ 기본 포함이지만 Railway slim 이미지에서 확인 필요
- 기존 `IndexStore` API 호환 유지 필수 (breaking change 금지)

**Evidence**
1. [iAchilles/memento - MCP memory server using SQLite + FTS5 + sqlite-vec](https://github.com/iachilles/memento) | github | 2025-12 | accessed: 2026-03-28
2. [Hybrid full-text search and vector search with SQLite](https://alexgarcia.xyz/blog/2024/sqlite-vec-hybrid-search/index.html) | blog | 2024-10 | accessed: 2026-03-28
3. [sqlite-vec official docs](https://github.com/sqliteai/sqlite-vector) | github | 2025+ | accessed: 2026-03-28

---

### BEST #2: FastMCP Rate Limiting Middleware

**Goal**
- Read tool (search, fetch): 120 req/min per client
- Write tool (save_memory, update_memory): 30 req/min per client
- Agent retry loop 방어 (1000+ calls/min 시나리오)
- 429 Too Many Requests 응답 + Retry-After 헤더

**Non-goals**
- 글로벌 distributed rate limiter (Redis 기반) 도입하지 않음
- IP-based blocking 하지 않음 (Bearer token 기반 클라이언트 식별)

**Proposed Design**
- FastMCP 2.9+ `RateLimitingMiddleware` 사용 (token bucket)
- Read/Write tool 분류 → 차등 limit 적용
- `app/main.py` 또는 `app/mcp_server.py`에서 middleware 등록
- 로그: rate limit hit 시 warning 로그 + client identifier

**PR Plan (3 PRs)**
1. **PR1**: FastMCP middleware 등록 + read/write 분류 (scope: `app/mcp_server.py`, `app/claude_mcp_server.py`, `app/chatgpt_mcp_server.py` | rollback: middleware 제거)
2. **PR2**: Rate limit 설정 환경변수화 (`RATE_LIMIT_READ`, `RATE_LIMIT_WRITE`) (scope: `app/config.py` | rollback: 환경변수 삭제 → 기본값)
3. **PR3**: Rate limit 테스트 + CI (scope: `tests/test_rate_limiting.py` | rollback: 테스트 파일 삭제)

**Tests**
- Unit: token bucket 알고리즘 정확성
- Integration: 연속 호출 시 429 반환 확인
- Perf: rate limiter 오버헤드 < 1ms/request

**Rollout & Rollback**
- Feature flag: `RATE_LIMIT_ENABLED=true|false` 환경변수
- 초기값: read=120/min, write=30/min (보수적)
- Revert: `RATE_LIMIT_ENABLED=false`

**Risks & Mitigations**
1. FastMCP 버전 호환 → `mcp[cli]>=1.0.0` + FastMCP 2.9+ 확인
2. 정상 사용자 차단 → 초기 limit 넉넉하게 + 모니터링 후 조정
3. Multi-profile 분리 미적용 → profile별 middleware 인스턴스 분리
4. Burst 허용 미흡 → token bucket capacity 2x refill rate
5. 429 응답 형식 → MCP 프로토콜 호환 error response 확인

**KPI Targets**
- Rate limit trigger rate: < 2% of total requests (정상 운영 시)
- 429 response latency: < 5ms
- Zero false positives in first 7 days

**Dependencies / Migration traps**
- FastMCP 2.9+ 필요 → `pyproject.toml` 의존성 업데이트
- 현재 `mcp[cli]>=1.0.0`만 명시 → FastMCP 버전 pin 필요

**Evidence**
1. [FastMCP 2.9 Middleware - rate_limiting.py](https://github.com/PrefectHQ/fastmcp/blob/main/src/fastmcp/server/middleware/rate_limiting.py) | github | 2026-02 | accessed: 2026-03-28
2. [MCP Server Rate Limiting: Implementation Guide](https://fast.io/resources/mcp-server-rate-limiting/) | fast.io | 2026-01 | accessed: 2026-03-28
3. [FastMCP Middleware docs](https://gofastmcp.com/servers/middleware) | official | 2026 | accessed: 2026-03-28

---

### BEST #3: CI Coverage + Security Scan 강화

**Goal**
- `coverage` 리포트를 CI에 추가하고 fail_under=85 게이트 활성화
- `bandit` 또는 `safety` 로 보안 취약점 스캔
- Dependabot/Renovate로 의존성 자동 업데이트
- PR 코멘트에 coverage diff 표시

**Non-goals**
- SAST/DAST 풀 파이프라인 구축하지 않음
- Container image 스캔 (Trivy 등) 은 Phase 2로 미룸

**Proposed Design**
- `ci.yml` 확장: `coverage run -m pytest` + `coverage report` + `coverage xml`
- `bandit -r app/ -ll` 스텝 추가
- GitHub Dependabot 설정 (`dependabot.yml`)
- codecov 또는 coverage-comment GitHub Action

**PR Plan (3 PRs)**
1. **PR1**: CI에 coverage + bandit 추가 (scope: `.github/workflows/ci.yml`, `pyproject.toml` | rollback: CI 스텝 삭제)
2. **PR2**: Dependabot 설정 (scope: `.github/dependabot.yml` | rollback: 파일 삭제)
3. **PR3**: PR coverage comment action (scope: `.github/workflows/ci.yml` | rollback: action 스텝 삭제)

**Tests**
- CI 파이프라인 자체가 테스트 → PR에서 green check 확인
- bandit false positive 검토 → `# nosec` 주석 최소화

**Rollout & Rollback**
- CI 변경은 PR 단위로 즉시 활성화
- 실패 시 CI 스텝 삭제로 롤백
- Dependabot은 auto-merge 비활성화 상태로 시작

**Risks & Mitigations**
1. Coverage 85% 미달 → 기존 테스트로 이미 달성 가능 (2920 LOC 테스트)
2. Bandit false positive → severity level `-ll` (medium+) 로 필터
3. Dependabot PR 폭주 → weekly frequency + grouping
4. CI 시간 증가 → coverage + bandit 총 < 30초 추가
5. codecov 토큰 관리 → GitHub Secrets 사용

**KPI Targets**
- Coverage: ≥ 85% (이미 `pyproject.toml`에 설정됨)
- Security findings (bandit medium+): 0
- Dependency freshness: 30일 이내

**Dependencies / Migration traps**
- `bandit`를 dev 의존성에 추가 필요
- codecov 무료 플랜 제한 확인
- Dependabot은 GitHub repo 설정 필요

**Evidence**
1. [15 Best Practices for Building MCP Servers in Production](https://thenewstack.io/15-best-practices-for-building-mcp-servers-in-production/) | thenewstack | 2025-11 | accessed: 2026-03-28
2. [MCP Server Security: Auth Best Practices 2026](https://medium.com/data-science-collective/why-your-mcp-server-is-a-security-disaster-waiting-to-happen-660577d8077c) | medium | 2026-01 | accessed: 2026-03-28

---

## 5) Options A/B/C

| Option | 범위 | 리스크 | 일정 | 비용(AED) |
|--------|------|--------|------|----------|
| **A (보수)** | CI 강화 (#3) + Rate Limiting (#2) + Tool Annotations (#10) | Low | 2주 | 0 |
| **B (중간)** | A + FTS5 Hybrid Search (#1) + Structured Logging (#6) | Medium | 6주 | 0 |
| **C (공격)** | B + OAuth 2.1 (#3 Top10) + Knowledge Graph (#8) + Embedding Pipeline (#9) | High | 12주+ | TBD |

---

## 6) 30/60/90-day Roadmap

**30d (Option A)**
- CI coverage + bandit 추가 (PR1-3)
- FastMCP rate limiting middleware 등록 (PR1-3)
- MCP tool annotations 완성
- Dependabot 활성화

**60d (Option B 추가)**
- FTS5 마이그레이션 + 테스트 (PR1-2)
- sqlite-vec integration + hybrid scorer (PR3-4)
- structlog 도입 + Railway 로그 구조화
- 검색 품질 A/B 비교

**90d (Option C 일부)**
- OAuth 2.1 auth 모듈 분리 + PKCE flow
- Embedding generation pipeline (on-write)
- Gunicorn multi-worker 전환
- Production monitoring dashboard

---

## 7) Evidence Table

| Idea | Platform | Title | Published | Accessed | Popularity | URL |
|------|----------|-------|-----------|----------|------------|-----|
| #1 FTS5+vec | github | Memento: SQLite+FTS5+sqlite-vec | 2025-12 | 2026-03-28 | stars TBD | [link](https://github.com/iachilles/memento) |
| #1 FTS5+vec | blog | Hybrid search with SQLite | 2024-10 | 2026-03-28 | HN 200+ | [link](https://alexgarcia.xyz/blog/2024/sqlite-vec-hybrid-search/index.html) |
| #1 FTS5+vec | github | sqlite-vector official | 2025+ | 2026-03-28 | stars 500+ | [link](https://github.com/sqliteai/sqlite-vector) |
| #2 Rate Limit | github | FastMCP rate_limiting.py | 2026-02 | 2026-03-28 | — | [link](https://github.com/PrefectHQ/fastmcp/blob/main/src/fastmcp/server/middleware/rate_limiting.py) |
| #2 Rate Limit | fast.io | MCP Server Rate Limiting Guide | 2026-01 | 2026-03-28 | — | [link](https://fast.io/resources/mcp-server-rate-limiting/) |
| #2 Rate Limit | official | FastMCP Middleware docs | 2026 | 2026-03-28 | — | [link](https://gofastmcp.com/servers/middleware) |
| #3 CI Security | thenewstack | 15 Best Practices MCP Production | 2025-11 | 2026-03-28 | — | [link](https://thenewstack.io/15-best-practices-for-building-mcp-servers-in-production/) |
| #3 CI Security | medium | MCP Server Security 2026 | 2026-01 | 2026-03-28 | — | [link](https://medium.com/data-science-collective/why-your-mcp-server-is-a-security-disaster-waiting-to-happen-660577d8077c) |
| #4 OAuth | official | MCP Authorization Spec | 2025-03 | 2026-03-28 | — | [link](https://modelcontextprotocol.io/specification/draft/basic/authorization) |
| #4 OAuth | microsoft | Secure MCP with OAuth 2.1 + Azure AD | 2026-02 | 2026-03-28 | — | [link](https://devblogs.microsoft.com/ise/aca-secure-mcp-server-oauth21-azure-ad/) |
| #8 KG | github | obsidian-mcp-plugin (graph traversal) | 2026-03 | 2026-03-28 | — | [link](https://github.com/aaronsb/obsidian-mcp-plugin) |

---

## 8) AMBER_BUCKET

| Item | Reason | Potential |
|------|--------|-----------|
| Gunicorn multi-worker (#7) | Railway 단일 컨테이너에서 multi-worker 효과 미확인 | Medium — 부하 테스트 필요 |
| Knowledge Graph (#8) | 구현 복잡도 높고 현재 노트 수 적음 | High — 노트 1000+ 시 재평가 |
| Embedding Pipeline (#9) | 모델 호스팅 비용/복잡도 불확실 | High — FTS5 먼저 후 평가 |

---

## 9) Verification Gate

### PASS/FAIL Table

| Idea | Tier | Verdict | Why | Required checks | Minimal tests |
|------|------|---------|-----|-----------------|---------------|
| #1 FTS5+vec | Best | **PASS** | evidence 3개, 스택 호환, 롤백 가능 | FTS5 빌드, sqlite-vec 호환 | search 정확도, latency |
| #2 Rate Limit | Best | **PASS** | FastMCP native, 1PR 핵심, 즉시 적용 | FastMCP 2.9 호환 | 429 반환 테스트 |
| #3 CI Security | Best | **PASS** | 코드 변경 없음, CI만 확장 | bandit 설치 | green CI |
| #4 OAuth | Top10 | **AMBER** | 스펙 안정적이나 effort 높고 현재 필요성 낮음 | auth 모듈 분리 | token flow e2e |
| #10 Annotations | Top10 | **PASS** | 1PR, risk 0 | MCP spec 준수 | tool list 검증 |

### Apply Gates

- **Gate 0 (Dry-run)**: 코드 변경 없음. 문서만 산출.
- **Gate 1 (Change list)**: Best #1 → 4 files, Best #2 → 4 files, Best #3 → 2 files
- **Gate 2 (Explicit approval)**: ⏳ 사용자 승인 대기
- **Gate 3 (Feature flag)**: Best #1 `SEARCH_MODE`, Best #2 `RATE_LIMIT_ENABLED`
- **Gate 4 (Rollback)**: 모든 Best에 환경변수 기반 즉시 롤백 경로 존재

### Final: **Go** (Option A 즉시 실행 가능, Option B는 FTS5 PoC 후 결정)

---

## 10) Open Questions (≤3)

1. **Embedding 모델 선택**: MiniLM-L6 로컬 vs. OpenAI/Anthropic embedding API — 비용/latency 트레이드오프?
2. **sqlite-vec Railway 호환**: Railway Docker slim 이미지에서 sqlite-vec C extension 빌드 가능한지 PoC 필요
3. **OAuth 필요 시점**: 현재 단일 사용자(Cha) 기준으로는 Bearer로 충분하나, 멀티유저/팀 확장 시 OAuth 전환 시점은?
