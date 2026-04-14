# Ontology Sidecar README

> 대상 파일: `supabase/migrations/20260319_ontology_sidecar.sql`
>
> 목적: raw Excel 기반 HVDC/WH 데이터를 `ontology` sidecar schema로 정규화하고, 기존 Dashboard app 계약을 깨지 않으면서 `search / related search / drilldown / bridge view`를 추가한다.

---

## 1. 개요

이 migration은 기존 Supabase operational schema를 대체하지 않는다.
대신 `ontology` schema를 추가로 생성하고, 아래 3개 레이어를 한 번에 만든다.

1. **Master layer**
   - `ontology.shipment_master`
   - `ontology.case_master`

2. **Relation / Search layer**
   - `ontology.entity_edge`
   - `ontology.search_doc`
   - `ontology.embedding_index`

3. **Bridge view layer**
   - `public.v_overview_shipments_v2`
   - `public.v_cases_ontology_v1`

핵심 원칙은 다음과 같다.

- **Overview는 shipment grain 유지**
- **Pipeline / Sites / Cargo / Chain은 case grain 유지**
- 기존 app이 읽는 public view 계약은 바로 덮어쓰지 않고, **sidecar view**를 먼저 검증한다.
- exact search는 `FTS`, related search는 `entity_edge + embedding`으로 분리한다.

---

## 1.1 현재 repo와의 연결 기준

이 문서는 현재 `apps/logistics-dashboard` 단일 active app 기준으로 작성되었다.
운영 연결 포인트는 아래 2개다.

- Overview 계층: shipment-only source
- Pipeline / Sites / Cargo / Chain 계층: case/detail source

따라서 ontology sidecar도 이 split contract를 그대로 따른다.

---

## 2. 왜 필요한가

현재 app 계약은 이미 분리되어 있다.

- Overview 계층은 shipment/voyage 중심이다.
- detail 계층은 case/package 중심이다.

raw Excel만 그대로 적재하면 다음 문제가 생긴다.

- 같은 shipment와 연결된 문서/warehouse/site 관계를 재사용하기 어렵다.
- row 검색은 되지만 related search 품질이 낮다.
- app마다 계산 grain이 달라져 KPI와 detail 숫자가 흔들릴 수 있다.
- 나중에 vector search를 붙여도 entity 관계가 약하면 검색 정확도가 낮다.

이 sidecar는 raw ingest를 **운영용 ontology 형태**로 재구성해서,

- exact lookup
- semantic search
- relation traversal
- shipment ↔ case drilldown
- warehouse / MOSB / site 경로 해석

을 모두 Postgres 안에서 처리할 수 있게 한다.

---

## 3. 생성 객체

### 3.1 Schema / Extension

- `ontology`
- `extensions`
- `extensions.pgcrypto`
- `extensions.vector`

### 3.2 Core Tables

#### `ontology.shipment_master`
Shipment / voyage grain master.

주요 역할:
- `hvdc_status_raw`를 shipment 기준으로 정규화
- Overview용 KPI / stage / route / site 신호 제공
- planned site / actual site / customs / delivery / risk 정보를 한 row에 유지

#### `ontology.case_master`
Case / package grain master.

주요 역할:
- `wh_status_raw`를 case 기준으로 정규화
- Flow Code, warehouse 상태, final location, site handling, dwell day 계산 유지
- Pipeline / Sites / Cargo / Chain에서 쓰는 detail source 제공

#### `ontology.entity_edge`
Graph-like relation table.

예시 관계:
- shipment → planned site
- shipment → actual site
- shipment → document
- shipment → case
- case → current location
- case → final location
- case → vendor

#### `ontology.search_doc`
검색용 canonical document.

주요 역할:
- shipment당 1개 search document
- case당 1개 search document
- `title + body + keywords` 기반 exact / lexical search surface 제공
- `fts` generated column 저장

#### `ontology.embedding_index`
semantic search용 vector 저장소.

주요 역할:
- `search_doc`와 1:N 연결
- embedding model/version별 재생성 가능
- HNSW index 기반 related search 지원

### 3.3 Functions

#### `ontology._route_type_from_class(route_class text)`
`route_class`를 app 표준 `route_type`으로 변환한다.

매핑:
- `NO_DELIVERY` → `pre-arrival`
- `DIRECT_SITE` → `direct-to-site`
- `WH_SITE`, `WH_ONLY` → `via-warehouse`
- `MOSB_SITE`, `MOSB_ONLY` → `via-mosb`
- `WH_MOSB_SITE` → `via-warehouse-mosb`
- 나머지 → `review-required`

#### `ontology.refresh_sidecar_from_ingest()`
현재 ingest snapshot을 sidecar schema로 다시 적재한다.

동작:
1. ingest 테이블 존재 확인
2. sidecar 전체 truncate
3. shipment master 적재
4. case master 적재
5. entity edge 적재
6. search_doc 적재
7. 적재 건수 JSON 반환

주의:
- **incremental load가 아니라 snapshot refresh** 방식이다.
- 현재 published raw snapshot 1개를 기준으로 sidecar 전체를 재생성한다.

#### `ontology.refresh_embedding_from_stage()`
`ingest.embedding_stage`를 읽어 `ontology.embedding_index`를 다시 적재한다.

요구 staging shape:
- `search_doc_key`
- `embedding_model`
- `embedding_version`
- `content_sha256`
- `embedding`
- `is_active`

### 3.4 Bridge Views

#### `public.v_overview_shipments_v2`
shipment-only bridge view.

역할:
- 현재 Overview BFF가 기대하는 shipment 중심 컬럼 구조를 유지
- planned/actual site, warehouse hint, MOSB hint, customs/delivery signal 제공

#### `public.v_cases_ontology_v1`
case/detail bridge view.

역할:
- 기존 `v_cases`가 제공하던 case-grain 관점을 ontology sidecar에서 재구성
- `flow_code`, `route_type`, `site_arrival_date`, dwell metrics 제공

---

## 4. 입력 가정

이 migration은 아래 전제를 둔다.

### 4.1 Raw staging tables

반드시 아래 테이블이 있어야 한다.

- `ingest.hvdc_status_raw`
- `ingest.wh_status_raw`

선택:
- `ingest.embedding_stage`

### 4.2 컬럼 규칙

- Excel 헤더는 **snake_case**로 정규화되어 있어야 한다.
- 날짜는 text 또는 timestamp로 들어와도 function 내부에서 date cast 한다.
- 숫자 문자열은 `,` 제거 후 cast 한다.
- site/date/location 계열은 일부 누락이 있어도 JSONB로 보존한다.

### 4.3 Snapshot semantics

이 sidecar는 다중 batch 누적 저장소가 아니라 **현재 snapshot 운영용 서브모델**이다.
따라서 refresh 시 기존 ontology 데이터는 truncate 후 재생성된다.

---

## 5. 적재 흐름

```text
Excel raw
  -> ingest.hvdc_status_raw / ingest.wh_status_raw
  -> ontology.refresh_sidecar_from_ingest()
  -> ontology.shipment_master / ontology.case_master
  -> ontology.entity_edge / ontology.search_doc
  -> ingest.embedding_stage
  -> ontology.refresh_embedding_from_stage()
  -> ontology.embedding_index
  -> public.v_overview_shipments_v2 / public.v_cases_ontology_v1
  -> app / search / drilldown
```

---

## 6. Search 모델

### 6.1 Exact / lexical search

대상:
- `ontology.search_doc`

구성:
- `title`
- `body`
- `keywords`
- generated `fts`
- GIN index

적합한 질의:
- `SCT SHIP NO.`
- `COMMERCIAL INVOICE No.`
- `B/L No.`
- `Case No.`
- `EQ No`
- vendor / site / POD / POL

### 6.2 Related / semantic search

대상:
- `ontology.embedding_index`
- `ontology.entity_edge`

동작 예시:
- 같은 vendor + 비슷한 route_type + 유사 description case
- MOSB staging 패턴이 유사한 shipment 묶음
- 같은 shipment에 연결된 case / document / site 확장 탐색

### 6.3 왜 `search_doc`를 분리했는가

master table에 바로 embedding을 두면

- 검색 모델 변경 시 영향 범위가 커지고
- entity 속성 변경과 search surface 변경이 섞이고
- 재임베딩 단위가 불명확해진다.

따라서 **entity source**와 **search surface**를 분리했다.

---

## 7. 기존 app과의 연결 방식

### 7.1 현재 권장 방식

즉시 alias cutover 하지 말고 아래 순서로 검증한다.

1. `public.v_overview_shipments_v2` 생성
2. `public.v_cases_ontology_v1` 생성
3. API 또는 SQL smoke test 수행
4. 결과 비교 완료 후 optional alias cutover 수행

### 7.2 Optional alias cutover

migration 파일 하단에는 아래 block이 주석으로 들어 있다.

```sql
create or replace view public.v_overview_shipments_v1 as
select * from public.v_overview_shipments_v2;

create or replace view public.v_cases as
select * from public.v_cases_ontology_v1;
```

이 block은 아래 조건에서만 실행한다.

- Overview KPI 숫자 일치
- detail 페이지 row count 일치
- `route_type`, `flow_code`, `site_arrival_date` 검증 완료
- 기존 app filter contract와 충돌 없음 확인

---

## 8. 실행 방법

### 8.1 파일 배치

아래 위치에 migration 파일을 둔다.

```text
supabase/migrations/20260319_ontology_sidecar.sql
```

### 8.2 로컬 반영

```bash
supabase db reset
```

권장 상황:
- 로컬 개발 DB 전체 재구성
- migration 전체 재실행
- seed와 함께 재검증

### 8.3 원격 반영

```bash
supabase db push
```

권장 상황:
- linked project 또는 remote DB에 local migration 반영
- 배포 전 dry-run 또는 변경 검토 후 적용

### 8.4 raw 적재 후 refresh

```sql
select ontology.refresh_sidecar_from_ingest();
select ontology.refresh_embedding_from_stage();
```

운영 순서:
1. raw Excel → ingest table load
2. sidecar refresh
3. embedding staging load
4. embedding refresh
5. view smoke test

---

## 9. 최소 Smoke Test

### 9.1 Count 검증

```sql
select count(*) as shipment_cnt from ontology.shipment_master;
select count(*) as case_cnt from ontology.case_master;
select count(*) as edge_cnt from ontology.entity_edge;
select count(*) as search_doc_cnt from ontology.search_doc;
select count(*) as embedding_cnt from ontology.embedding_index;
```

### 9.2 View 샘플 검증

```sql
select * from public.v_overview_shipments_v2 limit 20;
select * from public.v_cases_ontology_v1 limit 20;
```

### 9.3 Grain 검증

```sql
-- Overview는 shipment grain이어야 함
select sct_ship_no, count(*)
from public.v_overview_shipments_v2
group by 1
order by 2 desc
limit 20;

-- Cases는 case grain이어야 함
select case_no, count(*)
from public.v_cases_ontology_v1
group by 1
order by 2 desc
limit 20;
```

### 9.4 Route / Flow 검증

```sql
select route_type, count(*)
from public.v_overview_shipments_v2
group by 1
order by 1;

select flow_code, route_type, count(*)
from public.v_cases_ontology_v1
group by 1,2
order by 1,2;
```

---

## 10. 운영 Runbook

### 10.1 일일 배치

권장 순서:

1. 최신 Excel 수집
2. raw staging overwrite
3. `refresh_sidecar_from_ingest()` 실행
4. embedding 생성 job 실행
5. `refresh_embedding_from_stage()` 실행
6. count / KPI smoke 검증
7. app BFF 샘플 응답 확인

### 10.2 장애 시 체크 포인트

#### Case A — `missing_ingest_tables`
원인:
- raw staging table 미생성
- schema 명 불일치

조치:
- `ingest.hvdc_status_raw`, `ingest.wh_status_raw` 존재 확인
- schema / table naming 확인

#### Case B — embedding 미적재
원인:
- `ingest.embedding_stage` 미생성
- `search_doc_key` mismatch

조치:
- `search_doc_key` 생성 규칙과 staging key 비교
- embedding dimension 확인

#### Case C — Overview 숫자 불일치
원인 후보:
- shipment grain 중복
- route_type 변환 누락
- planned/actual site 신호 해석 불일치

조치:
- `shipment_key`, `shipment_group_key`, `route_class`, `route_type` 비교
- 기존 `v_overview_shipments_v1`와 병행 비교

#### Case D — detail 페이지 숫자 불일치
원인 후보:
- case ↔ shipment link 우선순위 오차
- `shipment_group_key` 해석 불일치
- `site_arrival_date` 파생 규칙 차이

조치:
- `shipment_no`, `shipment_invoice_no`, `case_key` 매핑 재검증

---

## 11. 설계 규칙

### 11.1 Grain split는 절대 유지

- Overview = shipment grain
- detail = case grain

이 원칙이 깨지면 KPI와 drilldown이 어긋난다.

### 11.2 Raw는 버리지 말고 보존

- normalized column은 app/read 성능용
- `raw_payload`는 audit/reprocess 용

### 11.3 Search는 2단 분리

- exact / filter / code lookup = `search_doc`
- similarity / related item = `embedding_index`

### 11.4 Graph는 lightweight로 시작

별도 Graph DB를 바로 붙이지 않고,
우선 `entity_edge`로 relation traversal을 Postgres 안에서 운영한다.
필요 시 추후 RDF/OWL/SHACL sidecar로 확장한다.

---

## 12. 보안 / 권한

migration은 아래 grant만 기본 포함한다.

- `usage on schema ontology to service_role`
- `select on public.v_overview_shipments_v2 to anon, authenticated, service_role`
- `select on public.v_cases_ontology_v1 to anon, authenticated, service_role`
- `execute on ontology.refresh_sidecar_from_ingest() to service_role`
- `execute on ontology.refresh_embedding_from_stage() to service_role`

주의:
- raw ingest table 접근 권한은 별도 운영 정책으로 관리한다.
- browser에는 service role key를 노출하지 않는다.

---

## 13. Rollback 전략

### 13.1 가장 안전한 rollback

alias cutover를 하지 않은 상태라면,
app는 기존 `v_overview_shipments_v1` / `v_cases`를 계속 사용하므로 영향이 없다.

### 13.2 cutover 이후 rollback

기존 view로 되돌리는 migration 또는 즉시 SQL을 준비한다.

예시:

```sql
-- 기존 source로 복원하는 SQL을 별도 rollback migration으로 관리
create or replace view public.v_overview_shipments_v1 as
select * from public.v_overview_shipments_v1_backup;

create or replace view public.v_cases as
select * from public.v_cases_backup;
```

실운영에서는 기존 view definition 백업본을 migration 전에 반드시 저장한다.

---

## 14. 권장 후속 작업

1. `entity_alias` 추가
   - invoice / BL / case / EQ / vendor alias exact lookup 강화

2. hybrid search RPC 추가
   - FTS 점수 + vector 점수 혼합

3. validation_flag / SHACL-like gate 추가
   - anomaly / missing key / route conflict 표시

4. batch audit log 추가
   - batch_id 단위 refresh 결과 기록

5. app API 점진 교체
   - `v_overview_shipments_v2`
   - `v_cases_ontology_v1`
   - search API

---

## 15. 바로 쓸 명령

### SQL

```sql
select ontology.refresh_sidecar_from_ingest();
select ontology.refresh_embedding_from_stage();
select * from public.v_overview_shipments_v2 limit 10;
select * from public.v_cases_ontology_v1 limit 10;
```

### CLI

```bash
supabase db reset
supabase db push
```

---

## 16. 한 줄 결론

이 migration은 **raw Excel 업로드**를 **ontology-aware operational model**로 바꾸는 첫 단계다.
즉, RDF 파일을 저장하는 것이 아니라 **Supabase 안에 shipment / case / relation / search / vector 레이어를 분리해서 운영 검색과 drilldown을 안정화하는 설계**다.
