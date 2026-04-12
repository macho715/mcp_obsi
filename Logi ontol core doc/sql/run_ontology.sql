-- Run ontology sidecar: schema, ingest, views, cutover, smoke.
-- Usage: psql $DATABASE_URL -f run_ontology.sql
-- Or from sql/: psql $DATABASE_URL -f run_ontology.sql
-- Order: 00 (schema) -> 01, 02 (ingest) -> 03, 04 (parallel-capable) -> 05 -> 06, 07 -> 08 (smoke).

\ir 00_schema_ddl.sql
\ir 01_ingest_shipment_master.sql
\ir 02_ingest_case_master.sql
\ir 03_ingest_entity_edge.sql
\ir 04_ingest_search_doc.sql
\ir 05_ingest_embedding_index.sql
\ir 06_views_overview_cases.sql
\ir 07_cutover_aliases.sql
\ir 08_smoke_test.sql
