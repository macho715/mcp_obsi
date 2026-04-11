# Ontology 적재 — 개요

판정: 예 — 아래 SQL로 바로 붙일 수 있습니다. 다만 `ingest.hvdc_status_raw` / `ingest.wh_status_raw` 스테이징 테이블 이름과 snake_case 컬럼명은 그대로 맞춰야 합니다.

근거: 현재 앱은 Overview에서 `v_overview_shipments_v1`의 shipment-only 컬럼 세트를 읽고, `/api/cases`는 `v_cases`에서 case-grain 컬럼 세트를 읽습니다. Supabase는 generated `tsvector` + GIN, 그리고 vector + HNSW 조합을 공식 예시로 안내합니다. ([Supabase][1])

다음행동: 아래 순서로 실행하십시오. `shipment_master → case_master → entity_edge → search_doc → embedding_index → view → alias cutover`.

가정:

* raw staging 테이블: `ingest.hvdc_status_raw`, `ingest.wh_status_raw`
* raw 컬럼은 헤더를 snake_case로 정규화한 상태
* raw 테이블에 `source_batch_id`가 있음
* 임베딩은 별도 job이 `ingest.embedding_stage`에 적재함

---

## 마무리 요약

`v_overview_shipments_v2`는 현재 repo의 `overviewSource.ts`가 읽는 shipment-only select 컬럼에 맞췄고, `v_cases_ontology_v1`는 `/api/cases`와 summary helper가 읽는 case-grain 컬럼에 맞췄습니다. `flow_code → route_type` 매핑도 repo 설정과 동일하게 0~5를 6개 route type으로 연결했습니다.

`search_doc`와 `embedding_index`는 Supabase의 FTS + vector hybrid 패턴에 맞춰 구성했습니다. `fts`는 generated `tsvector` + GIN으로 가고, vector 쪽은 HNSW를 붙이는 방식이 공식 예시와 맞습니다. cosine 검색이면 `vector_cosine_ops`를 써야 하고, pgvector 0.7.0+ 기준 `vector` 인덱스는 2,000 dimensions까지입니다. ([Supabase][1])

원하면 다음 답변에서 이 SQL을 기준으로 `supabase/migrations/20260319_ontology_sidecar.sql` 한 파일 형태로 정리해서 바로 붙여드리겠습니다.

[1]: https://supabase.com/docs/guides/database/full-text-search "https://supabase.com/docs/guides/database/full-text-search"
