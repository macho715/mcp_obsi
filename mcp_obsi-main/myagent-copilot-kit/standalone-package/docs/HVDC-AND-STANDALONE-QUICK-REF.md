# HVDC & Standalone Quick Reference

`hvdc_get_domain_summary` 호출 결과와 standalone 패키지 문서(README / OPERATIONS / MIGRATION) 요약을 한 문서로 정리합니다.

---

# HVDC Project Domain Summary

## Project
- **Client**: Samsung C&T x ADNOC x DSV, UAE HVDC Project
- **Role**: SCM/Logistics (Invoice Audit, Customs, Marine Ops, WH Management)
- **Scale**: ~400 TEU / 100 BL per month, 6 sites

## Node Network (8 nodes)
| Node | Type | Key Info |
|------|------|----------|
| Zayed Port | Import Port | Bulk/Heavy cargo, customs 47150 |
| Khalifa Port | Import Port | Container cargo, customs 47150 |
| Jebel Ali | Import Port | Freezone / ADOPT, customs 1485718 |
| MOSB | Central Hub | Central hub, 20,000 sqm, SCT resident team |
| MIR | Onshore Site | SPMT operations, DOT > 90t |
| SHU | Onshore Site | SPMT operations, DOT > 90t |
| DAS | Offshore Site | 20h LCT, MOSB leg mandatory |
| AGI | Offshore Site | 10h LCT, MOSB leg mandatory |

## Flow Code v3.5
| Code | Description |
|------|-------------|
| 0 | Pre Arrival |
| 1 | Port → Site (direct, no WH) |
| 2 | Port → WH → Site |
| 3 | Port → MOSB → Site |
| 4 | Port → WH → MOSB → Site |
| 5 | Mixed / Waiting / Incomplete |

- **Algorithm**: FLOW = 0 if PreArrival else clip(wh_count + offshore + 1, 1, 4)
- **AGI/DAS Rule**: Flow Code 0/1/2 → auto-upgrade to 3 (MOSB leg mandatory)
- **DOT Rule**: MIR/SHU require DOT only when gross weight > 90 tons

## KPI Gates
| KPI | Target | Direction |
|-----|--------|-----------|
| invoice-ocr | 98.0% | ≥ |
| invoice-audit delta | 2.0% | ≤ |
| cost-guard warn rate | 5.0% | ≤ |
| hs-risk misclass | 0.5% | ≤ |
| cert-chk auto-pass | 90.0% | ≥ |
| wh-forecast util | 85.0% | ≤ |
| weather-tie ETA MAPE | 12.0% | ≤ |

## Key Regulations
- **FANR**: 방사선 수입허가 (60일)
- **MOIAT_ECAS**: 적합성 인증
- **MOIAT_EQM**: 규제 제품 품질 마크 / 관련 인증
- **DOT**: 중량물 운송 허가
- **CICPA**: 게이트패스
- **ADNOC_FRA**: 리프팅 위험성 평가

## Available Domain Docs (16 files)
CONSOLIDATED-01~09, CORE_DOCUMENTATION_MASTER, FLOW_CODE_V35_*, LOGI_ONTOL_CORE_MERGED, NAMESPACE_REGISTRY, agents_template 등

## Ontology Standards
UN/CEFACT, WCO-DM v4.2, DCSA eBL 3.0, ICC Incoterms 2020, HS-2022, BIMCO SUPPLYTIME 2017

---

# Standalone Package 문서 요약

## README.md — 설치·실행·API

| 항목 | 내용 |
|------|------|
| **역할** | myagent-copilot-standalone 패키지 설치·빌드·로그인·실행·배포·검증 절차 |
| **기능** | GitHub device login, token 교환, usage 조회, `GET /api/ai/health`, `POST /api/ai/chat`, DLP, 라우팅, CORS, 프록시 토큰 인증, `.bat` 실행, zip 배포 |
| **요구** | Node ≥22.12, pnpm, 포트 3010 |
| **빠른 시작** | `pnpm install` → `pnpm build` → `pnpm login` → `pnpm serve:local` |
| **상태 디렉터리** | `~/.myagent-copilot` (auth, token cache). fallback: `~/.openclaw/...` |
| **주요 env** | `MYAGENT_PROXY_HOST/PORT`, `MYAGENT_PROXY_CORS_ORIGINS`, `MYAGENT_PROXY_AUTH_TOKEN`, `MYAGENT_HOME` 등 |
| **API** | `GET /api/ai/health`, `POST /api/ai/chat` (model, sensitivity, messages) |
| **원칙** | Standalone 우선, OpenClaw는 호환 경로, 무차감 관측 / 정책상 무제한 확정 불가 |

---

## OPERATIONS.md — 일상 운영

| 항목 | 내용 |
|------|------|
| **역할** | 일상 점검, 재시작, 토큰 교체, 장애 대응, 업데이트 |
| **일상** | 프로세스·`GET /api/ai/health` 확인, 오류 로그, origin/토큰, DLP 비율 |
| **시작/재시작** | `node dist/cli.js serve --host 127.0.0.1 --port 3010`, Windows는 `serve-local.bat` / `serve-public.bat` |
| **정기** | 매일 health, 토큰 만료·auth 오류, `pnpm usage` 보관, zip 재생성 검토 |
| **토큰** | `pnpm login` 또는 `MYAGENT_PROXY_AUTH_TOKEN` 교체 후 재기동 |
| **업데이트** | 새 소스 → `pnpm install --frozen-lockfile` → `pnpm build` → health → 스모크 → 재기동 |
| **로그** | 스키마 `openclaw.copilot.proxy.log.v1`, requestId/route/dlpStatus/latency 중심, payload 전문 저장 금지 |
| **롤백 기준** | CORS 실패, sanitize/로컬 정책 충돌, 토큰 유출 의심, GitHub 재인증 반복 |

---

## MIGRATION.md — OpenClaw → Standalone 이관

| 항목 | 내용 |
|------|------|
| **역할** | OpenClaw 경유 구성에서 standalone 패키지 중심으로 옮기는 절차 |
| **목표** | 운영 문서를 standalone 기준으로 통일, 인증을 `~/.myagent-copilot`로 전환, OpenClaw는 호환/비교용 |
| **사전** | OpenClaw auth 위치, 대시보드 엔드포인트, payload 구조, CORS/origin 확인 |
| **절차** | standalone 설치 → `pnpm build` → `pnpm login` → `pnpm health` → 스모크 → 대시보드 엔드포인트를 standalone으로 전환 → OpenClaw fallback 없이 동작 확인 → 문서 갱신 |
| **인증** | 빠른 전환(standalone 비어 있으면 OpenClaw fallback) 또는 권장 전환(`pnpm login`으로 standalone만 사용 후 fallback 제거) |
| **프론트** | `http://127.0.0.1:3010/api/ai/chat` 또는 공개 HTTPS로 변경, request schema·payload 요약 JSON 유지 |
| **롤백** | standalone login 불가, CORS/토큰 설계 미정, payload 최소화 미완이면 OpenClaw 경유 임시 유지. 문서 기준은 계속 standalone |

---

## 문서 간 관계

- **README.md**: 처음 설치·실행·API·env·배포(zip) 참고
- **OPERATIONS.md**: 서비스 띄운 뒤 매일·재시작·토큰·업데이트·로그·롤백 참고
- **MIGRATION.md**: 기존 OpenClaw 사용 중일 때 standalone으로 옮길 때만 참고

이 세 파일만 있으면 standalone 패키지 설치부터 이관·일상 운영까지 흐름을 따라갈 수 있습니다.

---

# Standalone + Predict 연동

standalone에서 HVDC 지연 예측(predict)을 붙이는 두 가지 방식과 선택 기준을 정리했습니다.

## 1. Subprocess 방식 (Express에서 `python predict2.py` 직접 실행)

**구성**
- Express에 `POST /api/hvdc/predict` 추가
- 요청 시 `child_process.spawn('python', ['predict2.py'], { cwd: predictDir })` 실행
- 입력 파일: 요청에서 업로드한 Excel을 `predict/input/`에 저장 후 실행, 또는 이미 있는 `hvdc status2.xlsx` 사용
- 완료 후 `predict/output/hvdc_status_with_ai_prediction_v2.xlsx` 경로 반환 또는 파일 스트리밍

**장점**
- 구현 단순, 기존 predict2.py 수정 없음
- Python 서버를 따로 띄울 필요 없음
- 한 번에 한 건만 돌리면 되는 배치성 작업에 적합

**단점**
- 서버에 Python + venv + predict 의존성 설치 필요
- 실행 시간 30초~1분대면 요청 타임아웃/블로킹 이슈 → **비동기(큐 + job id)** 권장
- 동시 다중 요청 시 input/output 파일 충돌 가능 → run 디렉터리 per request 또는 lock 필요
- 에러는 stderr/exit code로만 파악 가능

**아이디어**
- 동기: 타임아웃 90초 정도 두고 "실행 → 완료 시 파일 링크 반환".
- 비동기(권장): `POST /api/hvdc/predict` → `jobId` 반환, `GET /api/hvdc/predict/:jobId` 로 상태·결과 조회. 백그라운드에서 subprocess 실행.

---

## 2. Flask/FastAPI로 predict 감싼 뒤 HTTP 호출

**구성**
- `predict_server.py` (Flask 또는 FastAPI):
  - `POST /predict` — body에 Excel 업로드 또는 JSON으로 행 목록 전달
  - 내부에서 predict2와 동일한 전처리+모델 호출 (공통 코드를 모듈로 분리)
  - 응답: 예측 결과 JSON 또는 생성된 Excel 파일
- standalone(Express)는 `fetch('http://localhost:5000/predict', { body: formData })` 로 호출

**장점**
- REST로 역할 분리: "예측 서비스"가 포트 하나로 독립
- 여러 클라이언트(Express, 다른 앱, 스크립트)에서 재사용 가능
- 동시 요청은 각각 다른 메모리에서 처리 가능 (파일 경로 충돌 없음)
- 나중에 스케일 아웃(예측 서버만 여러 대) 하기 쉬움

**단점**
- predict 로직을 "스크립트"에서 "라이브러리+API"로 한 번 분리해야 함 (import 가능한 함수로 정리)
- Python 서버 프로세스 별도 관리 (실행/재시작/헬스체크)
- 배포 시 Python 런타임 + 의존성 필요

**아이디어**
- 1단계: predict2.py를 "엔트포인트 하나"로만 감싼다.
  - `POST /run` — `input/hvdc status2.xlsx` 사용, 실행 후 `output/...xlsx` 경로 또는 파일 반환.
  - 기존 스크립트를 `subprocess.run(['python', 'predict2.py'])` 로 부르는 형태로도 가능(가장 빠름).
- 2단계: 전처리·모델을 함수로 분리한 뒤, API는 "업로드 Excel → 메모리에서 DataFrame 처리 → 결과 JSON/Excel 반환"으로 바꿔서, 파일 시스템에 의존하지 않게 만든다.

---

## 3. 비교와 추천

| 기준 | Subprocess (Express만) | FastAPI/Flask (별도 서비스) |
|------|------------------------|-----------------------------|
| 구현 난이도 | 낮음 | 중간 (모듈 분리 필요할 수 있음) |
| 운영 | Node만 신경 쓰면 됨 | Node + Python 프로세스 관리 |
| 동시 요청 | 파일 lock/디렉터리 분리 필요 | 상대적으로 유리 |
| 재사용성 | standalone 전용에 가깝다 | 다른 앱에서도 호출 가능 |
| 장기 확장 | 예측 로직 추가 시 스크립트만 수정 | API 스펙만 유지하면 백엔드만 교체 가능 |

**추천**
- **당장 연동만 필요** → **Subprocess 방식**으로 Express에 `/api/hvdc/predict` 추가 (비동기 job + 단일 run 디렉터리 또는 job별 디렉터리).
- **여러 곳에서 쓰거나, 동시 실행·재사용을 염두에 두면** → **FastAPI 래퍼**를 두고, Express는 그 API를 HTTP로 호출.

---

## 4. Subprocess 쪽 구체 아이디어 (Express)

- **경로**: `predict` 디렉터리는 프로젝트 루트 기준 상대 경로로 해결 (예: `path.join(__dirname, '../../predict')`).
- **입력**:
  - 옵션 A: 요청 시 Excel 업로드 → `predict/input/hvdc status2.xlsx`에 저장 후 실행.
  - 옵션 B: 이미 서버에 있는 파일만 사용 → "예측 돌려줘" 요청이 오면 그 path로 실행.
- **실행**:
  - `python`은 `python3` 또는 venv의 `python`(절대 경로) 고정.
  - `spawn` 시 `cwd`를 `predict`로 두고, 필요하면 `env: { ...process.env }` 로 venv 활성화된 환경 유지.
- **응답**:
  - 비동기: `202 Accepted` + `{ jobId }` → 폴링 `GET /api/hvdc/predict/:jobId` → 완료 시 `outputFileUrl` 또는 파일 스트리밍.
  - 동기(실험용): 타임아웃 길게 두고 완료 시 `{ outputPath, downloadUrl }` 반환.
- **에러**: subprocess의 `stderr`와 exit code를 로그하고, 500 응답에 `message` 정도만 담아서 반환.

---

# Standalone + Predict 병합 → 시스템 업그레이드 아이디어

Quick Ref(HVDC 도메인 + Standalone 문서 + Predict 연동)와 predict 모듈을 한 덩어리로 보고, “시스템 업그레이드” 관점에서 정리한 아이디어입니다.

## 1. 업그레이드 목표

| 목표 | 설명 |
|------|------|
| **단일 진입점** | Copilot 채팅(standalone) + HVDC 지연 예측을 하나의 서비스(포트 3010)에서 제공 |
| **도메인 정합** | predict 출력(AI_RISK_BAND, 지연률)을 HVDC KPI·노드/Flow와 같은 관측 체계에 포함 |
| **문서 일원화** | 설치·운영·이관·predict 연동을 한 문서 트리(README / OPERATIONS / Quick Ref)로 유지 |
| **운영 관측** | health·로그·정기 점검에 predict 실행·결과 요약까지 포함 |

## 2. 단계별 업그레이드 아이디어

### 2.1 Phase 1 — 연동 (현재 Quick Ref § Standalone + Predict 연동 반영)

- Express에 `POST /api/hvdc/predict` 추가 (Subprocess 권장).
- 비동기 job: `jobId` 발급 → `GET /api/hvdc/predict/:jobId` 로 상태·결과 조회.
- predict 디렉터리: 프로젝트 루트 기준 상대 경로, `cwd`·venv 고정.
- **문서**: README에 “HVDC 지연 예측 API(선택)” 한 줄, OPERATIONS에 “predict job 성공/실패·로그” 점검 항목 추가.

### 2.2 Phase 2 — 관측·KPI 정합

- **건별 지연 리스크**: predict가 이미 제공 (AI_RISK_BAND, AI_ACTION_FLAG).  
  → OPERATIONS 정기 점검에 “지연 예측 실행 → HIGH 건 수·EXPEDITE 건 수” 요약 추가.
- **weather-tie ETA MAPE(12%)**: 전역 ETA 품질 KPI.  
  → predict의 **실제 지연(actual_delay_days)** 과 “예측 vs 실제” 비교 지표를 나중에 한 줄 추가하면 같은 KPI 패밀리로 묶임.
- **로그**: `openclaw.copilot.proxy.log.v1`에 predict job 시 `requestId`, `jobId`, `route: "hvdc-predict"`, `exitCode`, `durationMs` 정도만 남기고, payload 전문은 저장하지 않음.

### 2.3 Phase 3 — 도메인·노드/Flow 활용

- predict 입력 컬럼(POL, POD, LANE 등)은 이미 HVDC 노드·Flow와 대응 가능.
- **아이디어**: 예측 결과를 “노드별·Flow별” 집계해 `/api/hvdc/predict/summary?by=node` 또는 `?by=lane` 같은 읽기 전용 API를 두면, 대시보드·리포트에서 Quick Ref의 Node 8개·Flow Code v3.5와 동일한 용어로 표시 가능.
- 규제(FANR, DOT 등)는 현재 predict에서 직접 쓰지 않지만, “DOT > 90t” 구간(MIR/SHU) 등은 나중에 필터/라벨로 넣을 수 있음.

### 2.4 Phase 4 — 배포·환경 통일

- **zip/배포**: standalone zip에 “predict는 별도 디렉터리(또는 서버)” 로 명시하고, 동일 서버에 둘 때는 “Node + Python(venv) + predict” 설치 가이드 한 페이지(예: `docs/DEPLOY-WITH-PREDICT.md`)로 정리.
- **환경변수**: `PREDICT_DIR`, `PREDICT_PYTHON`(선택) 등을 두어 경로·인터프리터를 고정하면 OPERATIONS 재시작·업데이트 절차와 맞출 수 있음.

### 2.5 Phase 5 — FastAPI 분리(선택)

- 동시 실행·다중 클라이언트·재사용이 필요해지면 predict를 FastAPI로 분리하고, Express는 해당 API를 HTTP로 호출.
- 이때 OPERATIONS에 “Python 예측 서비스 시작/재시작/health” 절차를 추가하고, 정기 점검에 “예측 서비스 health” 항목 포함.

## 3. 문서 구조 제안(업그레이드 후)

```
standalone-package/
├── README.md              # 설치·실행·API (+ HVDC predict API 요약)
├── OPERATIONS.md          # 일상·재시작·토큰·predict job·로그·롤백
├── MIGRATION.md           # OpenClaw → Standalone (기존 유지)
└── docs/
    ├── HVDC-AND-STANDALONE-QUICK-REF.md   # 도메인 + 문서 요약 + 연동 + 업그레이드 아이디어
    └── DEPLOY-WITH-PREDICT.md              # (Phase 4) Node + Python + predict 동일 서버 배포
```

- **Quick Ref**: HVDC 도메인 + Standalone 요약 + Predict 연동 + **본 업그레이드 아이디어**를 한 문서에서 참조.
- **DEPLOY-WITH-PREDICT**: zip만 쓰는 경우와 “standalone + predict 한 서버” 경우를 구분해 설치·경로·env·실행 순서만 기술.

## 4. 요약

| Phase | 내용 |
|-------|------|
| 1 | Express에 /api/hvdc/predict (Subprocess), 비동기 job, README/OPERATIONS 반영 |
| 2 | predict 결과를 관측·KPI에 포함, 로그 스키마 확장 |
| 3 | 노드/Flow 기준 집계 API, 도메인 용어 통일 |
| 4 | 배포 가이드·env 통일 (PREDICT_DIR 등) |
| 5 | (선택) FastAPI 분리, Python 서비스 운영 절차 추가 |

이 순서로 가면 “standalone + predict 병합”을 한 번에 하지 않고, 단계적으로 시스템 업그레이드하면서 Quick Ref와 운영 문서를 같이 갱신할 수 있습니다.
