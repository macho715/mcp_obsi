# 그래프 TTL 자료 생성 관련 파일

최종 업데이트: 2026-04-14

---

## 실행 흐름

```
Excel (4개) ──► build_dashboard_graph_data.py ──► app/services/graph_*.py ──► nodes.json + edges.json ──► kg-dashboard
TTL 온톨로지 ──►
```

---

## 1. 입력 Excel 파일

기본 경로: `Logi ontol core doc/`

| 파일명 | 역할 | 크기 | 상태 |
|---|---|---|---|
| HVDC STATUS.xlsx | 선적 상태 메인 데이터 | 374 KB | ✅ 존재 |
| HVDC WAREHOUSE STATUS.xlsx | 창고 재고 현황 | 2.6 MB | ✅ 존재 |
| JPT-reconciled_v6.0.xlsx | JPT 다중 시트 파일 | 987 KB | ✅ 존재 |
| HVDC Logistics cost(inland,domestic).xlsx | 내륙 물류 비용 | 176 KB | ✅ 존재 |

### JPT 필수 시트 6개

| 시트명 |
|---|
| 1_Decklog |
| 3_Voyage_Master |
| 4_Voyage_Rollup |
| 6_Reconciliation |
| 7_Exceptions |
| 8_Decklog_Context |

하나라도 없으면 ValueError: Missing required JPT sheets 로 빌드 중단

### 추가 참고 Excel

| 파일명 | 크기 |
|---|---|
| OUTLOOK_HVDC_ALL_20250920260.xlsx | 14.4 MB |
| OUTLOOK_HVDC_ALL_20250920260.re-prefix-fixed.xlsx | 11.7 MB |

---

## 2. 온톨로지 소스 (Logi ontol core doc/)

### TTL 파일

| 파일 | 역할 |
|---|---|
| CONSOLIDATED-08-communication-enhanced.ttl | 온톨로지 정의 TTL — 유일한 실제 TTL 파일 |

### 설계 문서

| 파일 | 역할 |
|---|---|
| 온톨리지 TTL 설계.MD | 전체 온톨로지 설계 |
| TTL CLASS.MD | 클래스 설계 |
| TTL 매핑 초안.MD | TTL 매핑 초안 |
| 호환 매핑 원칙.MD | 호환 매핑 원칙 |
| CORE_DOCUMENTATION_MASTER.md | 마스터 문서 |
| ontology.md / ontology_2.md | 온톨로지 상세 |
| Role.md / ROLE_PATCH.MD / ROLE_PATCH2.MD | 역할 정의 및 패치 |
| plan.md | 작업 계획 |

### CONSOLIDATED 시리즈

| 파일 | 내용 |
|---|---|
| CONSOLIDATED-00-master-ontology.md | 마스터 온톨로지 |
| CONSOLIDATED-01-core-framework-infra.md | 핵심 프레임워크/인프라 |
| CONSOLIDATED-02-warehouse-flow.md | 창고 흐름 |
| CONSOLIDATED-03-document-ocr.md | 문서/OCR |
| CONSOLIDATED-04-barge-bulk-cargo.md | 바지선/벌크 화물 |
| CONSOLIDATED-05-invoice-cost.md | 인보이스/비용 |
| CONSOLIDATED-06-material-handling.md | 자재 처리 |
| CONSOLIDATED-07-port-operations.md | 항만 운영 |
| CONSOLIDATED-08-communication.md | 커뮤니케이션 |
| CONSOLIDATED-09-operations.md | 운영 전반 |

### P 시리즈 : P1.MD P2.MD P3.MD P4.MD p5.md p6.md

### docs/ 서브폴더

| 파일 | 역할 |
|---|---|
| docs/ontology-overview.md | 온톨로지 개요 |
| docs/ontology-rules.md | 온톨로지 규칙 |
| docs/ontology-ingest-overview.md | 인제스트 개요 |
| docs/README_ontology_sidecar.md | 사이드카 README |

### sql/ 서브폴더

| 파일 | 역할 |
|---|---|
| sql/00_schema_ddl.sql | 스키마 DDL |
| sql/01_ingest_shipment_master.sql | 선적 마스터 인제스트 |
| sql/02_ingest_case_master.sql | 케이스 마스터 인제스트 |
| sql/03_ingest_entity_edge.sql | 엔티티/엣지 인제스트 |
| sql/04_ingest_search_doc.sql | 검색 문서 인제스트 |
| sql/05_ingest_embedding_index.sql | 임베딩 인덱스 |
| sql/06_views_overview_cases.sql | 케이스 뷰 |
| sql/07_cutover_aliases.sql | 컷오버 별칭 |
| sql/08_smoke_test.sql | 스모크 테스트 |
| sql/run_ontology.sql | 온톨로지 실행 |

---

## 3. 빌드 스크립트

| 파일 | 역할 |
|---|---|
| scripts/build_dashboard_graph_data.py | 메인 엔트리포인트 — Excel to TTL to JSON |
| scripts/ttl_to_json.py | Deprecated — 구버전 사용 금지 |
| scripts/test_kg_queries.py | KG 쿼리 테스트 |

---

## 4. app/services 서비스 레이어

| 파일 | 역할 |
|---|---|
| app/services/graph_source_loader.py | Excel 파일 로드 + JPT 시트 파싱 |
| app/services/graph_normalizer.py | 소스 데이터 정규화 |
| app/services/graph_canonical_builder.py | 정규 그래프 구조 생성 |
| app/services/graph_mapping_builder.py | 호환성 매핑 생성 |
| app/services/graph_knowledge_builder.py | 지식 객체 빌드 |
| app/services/graph_resolver.py | 위치/분석 노트 해석 |
| app/services/graph_projection_builder.py | 대시보드용 프로젝션 생성 |
| app/services/graph_validation.py | 그래프 유효성 검사 |
| app/services/graph_types.py | 타입 정의 |
| app/services/external_schema_import.py | 외부 스키마 임포트 + UI 필터 생성 |

---

## 5. 출력 결과물

| 파일 | 역할 |
|---|---|
| kg-dashboard/public/data/nodes.json | 대시보드 노드 데이터 |
| kg-dashboard/public/data/edges.json | 대시보드 엣지 데이터 |
| kg-dashboard/public/data/external_schema_filters.json | 온톨로지 필터 UI용 |

---

## 6. 테스트

| 파일 | 역할 |
|---|---|
| tests/test_ttl_to_json.py | TTL to JSON 변환 테스트 |

---

## 현재 상태

- Excel 파일 4개 모두 존재 ✅
- 빌드 실행 가능 상태 ✅