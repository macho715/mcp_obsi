-- 3) entity_edge 적재
-- =========================================================

delete from ontology.entity_edge e
using (
  select distinct source_batch_id from ingest.hvdc_status_raw
  union
  select distinct source_batch_id from ingest.wh_status_raw
) b
where e.source_batch_id = b.source_batch_id;

insert into ontology.entity_edge (
  source_batch_id,
  edge_key,
  src_entity_type,
  src_ref,
  rel_type,
  dst_entity_type,
  dst_ref,
  dst_label,
  evidence,
  valid_from,
  valid_to,
  is_current,
  sort_order
)
select *
from (
  -- shipment -> planned site
  select
    sm.source_batch_id,
    md5(concat_ws('|', sm.source_batch_id, 'shipment', sm.shipment_key, 'planned_for', s.site_code)) as edge_key,
    'shipment'::text as src_entity_type,
    'shipment:' || sm.shipment_key as src_ref,
    'planned_for'::text as rel_type,
    'site'::text as dst_entity_type,
    'site:' || s.site_code as dst_ref,
    s.site_code as dst_label,
    jsonb_build_object('source_sheet', 'hvdc status', 'source_row_no', sm.source_row_no) as evidence,
    null::date as valid_from,
    null::date as valid_to,
    true as is_current,
    10 as sort_order
  from ontology.shipment_master sm
  cross join lateral unnest(sm.planned_sites) as s(site_code)

  union all

  -- shipment -> actual site
  select
    sm.source_batch_id,
    md5(concat_ws('|', sm.source_batch_id, 'shipment', sm.shipment_key, 'actual_at', s.site_code)),
    'shipment',
    'shipment:' || sm.shipment_key,
    'actual_at',
    'site',
    'site:' || s.site_code,
    s.site_code,
    jsonb_build_object('source_sheet', 'hvdc status', 'source_row_no', sm.source_row_no),
    null,
    null,
    true,
    20
  from ontology.shipment_master sm
  cross join lateral unnest(sm.actual_sites) as s(site_code)

  union all

  -- shipment -> CI
  select
    sm.source_batch_id,
    md5(concat_ws('|', sm.source_batch_id, 'shipment', sm.shipment_key, 'has_document', sm.commercial_invoice_no)),
    'shipment',
    'shipment:' || sm.shipment_key,
    'has_document',
    'document',
    'document:CI:' || sm.commercial_invoice_no,
    sm.commercial_invoice_no,
    jsonb_build_object('doc_type', 'CI'),
    null,
    null,
    true,
    30
  from ontology.shipment_master sm
  where sm.commercial_invoice_no is not null

  union all

  -- shipment -> BL/AWB
  select
    sm.source_batch_id,
    md5(concat_ws('|', sm.source_batch_id, 'shipment', sm.shipment_key, 'has_document', sm.bl_awb_no)),
    'shipment',
    'shipment:' || sm.shipment_key,
    'has_document',
    'document',
    'document:BLAWB:' || sm.bl_awb_no,
    sm.bl_awb_no,
    jsonb_build_object('doc_type', 'BLAWB'),
    null,
    null,
    true,
    40
  from ontology.shipment_master sm
  where sm.bl_awb_no is not null

  union all

  -- shipment -> case
  select
    cm.source_batch_id,
    md5(concat_ws('|', cm.source_batch_id, 'shipment', sm.shipment_key, 'contains_case', cm.case_key)),
    'shipment',
    'shipment:' || sm.shipment_key,
    'contains_case',
    'case',
    'case:' || cm.case_key,
    coalesce(cm.case_no, cm.eq_no),
    jsonb_build_object('source_sheet', 'wh status', 'source_row_no', cm.source_row_no),
    null,
    null,
    true,
    50
  from ontology.case_master cm
  join ontology.shipment_master sm
    on sm.shipment_group_key = cm.shipment_group_key

  union all

  -- case -> current location
  select
    cm.source_batch_id,
    md5(concat_ws('|', cm.source_batch_id, 'case', cm.case_key, 'current_at', cm.status_location)),
    'case',
    'case:' || cm.case_key,
    'current_at',
    'location',
    'location:' || cm.status_location,
    cm.status_location,
    jsonb_build_object('status_current', cm.status_current),
    cm.status_location_date,
    null,
    true,
    60
  from ontology.case_master cm
  where cm.status_location is not null

  union all

  -- case -> final location
  select
    cm.source_batch_id,
    md5(concat_ws('|', cm.source_batch_id, 'case', cm.case_key, 'final_at', cm.final_location)),
    'case',
    'case:' || cm.case_key,
    'final_at',
    'location',
    'location:' || cm.final_location,
    cm.final_location,
    jsonb_build_object('flow_code', cm.flow_code),
    cm.last_touch_date,
    null,
    true,
    70
  from ontology.case_master cm
  where cm.final_location is not null

  union all

  -- case -> vendor
  select
    cm.source_batch_id,
    md5(concat_ws('|', cm.source_batch_id, 'case', cm.case_key, 'handled_by', cm.source_vendor)),
    'case',
    'case:' || cm.case_key,
    'handled_by',
    'vendor',
    'vendor:' || cm.source_vendor,
    cm.source_vendor,
    '{}'::jsonb,
    null,
    null,
    true,
    80
  from ontology.case_master cm
  where cm.source_vendor is not null
) x;
