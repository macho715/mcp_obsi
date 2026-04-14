-- =========================================================
-- 9) Smoke test
-- =========================================================

select count(*) as shipment_cnt from ontology.shipment_master;
select count(*) as case_cnt from ontology.case_master;
select count(*) as edge_cnt from ontology.entity_edge;
select count(*) as search_doc_cnt from ontology.search_doc;

select * from public.v_overview_shipments_v2 limit 5;
select * from public.v_cases_ontology_v1 limit 5;

select flow_code, count(*)
from public.v_cases_ontology_v1
group by 1
order by 1;

select route_type, count(*)
from public.v_overview_shipments_v2
group by 1
order by 1;
