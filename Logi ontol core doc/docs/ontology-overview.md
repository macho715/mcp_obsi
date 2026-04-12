# Ontology sidecar — 개요

판정: 예 — 지금 구조라면 `ontology` 전용 sidecar schema를 먼저 만들고, 그 안에 `shipment_master / case_master / entity_edge / search_doc / embedding_index` 5개를 적재하는 방식이 맞습니다. 현재 앱도 Overview는 shipment/voyage grain, detail은 case/package grain으로 분리되어 있어 이 분리를 그대로 유지해야 합니다.

근거: Supabase 공식 문서도 keyword search는 `tsvector` generated column + GIN index, semantic search는 vector column + HNSW index, 둘을 합친 hybrid search를 권장합니다. 현재 대시보드 계약도 `v_overview_shipments_v1`은 shipment-only, `v_cases`는 case/package 쪽으로 분리되어 있습니다. ([Supabase][1])

다음행동: 아래 DDL로 `ontology` schema를 먼저 올리고, Excel 두 시트를 배치 적재한 뒤, 마지막에 `v_overview_shipments_v2`와 `v_cases_ontology_v1` 같은 bridge view를 만들어 기존 앱과 연결하십시오. Overview에는 `shipment_master`만, Cargo/Sites/Pipeline drilldown에는 `case_master`만 연결해야 합니다.

가정:

* embedding 모델은 1536-dim 기준입니다. 다른 모델이면 `vector(1536)`만 바꾸십시오.
* exact lookup 정확도를 극대화하려면 나중에 `entity_alias` 1개를 추가하는 편이 더 좋습니다. 아래는 요청한 5개 테이블 기준안입니다.

[1]: https://supabase.com/docs/guides/ai/hybrid-search "https://supabase.com/docs/guides/ai/hybrid-search"
