```sql
-- =========================================================
-- 8) Optional cutover alias
-- 현재 앱은 v_overview_shipments_v1 / v_cases 를 직접 읽음
-- =========================================================

create or replace view public.v_overview_shipments_v1 as
select * from public.v_overview_shipments_v2;

create or replace view public.v_cases as
select * from public.v_cases_ontology_v1;

grant select on public.v_overview_shipments_v2 to anon, authenticated, service_role;
grant select on public.v_cases_ontology_v1 to anon, authenticated, service_role;
grant select on public.v_overview_shipments_v1 to anon, authenticated, service_role;
grant select on public.v_cases to anon, authenticated, service_role;
```
