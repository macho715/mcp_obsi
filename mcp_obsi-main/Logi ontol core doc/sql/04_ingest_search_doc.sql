-- 4) search_doc 적재
-- =========================================================

delete from ontology.search_doc d
using (
  select distinct source_batch_id from ingest.hvdc_status_raw
  union
  select distinct source_batch_id from ingest.wh_status_raw
) b
where d.metadata ->> 'source_batch_id' = b.source_batch_id;

insert into ontology.search_doc (
  search_doc_key,
  entity_type,
  entity_ref,
  doc_scope,
  title,
  body,
  keywords,
  vendor_name,
  site_code,
  route_type,
  flow_code,
  status_current,
  risk_band,
  source_sheet,
  source_row_no,
  metadata
)
select
  'shipment:' || sm.shipment_key as search_doc_key,
  'shipment' as entity_type,
  'shipment:' || sm.shipment_key as entity_ref,
  'primary' as doc_scope,
  concat_ws(' ', sm.shipment_no, sm.vendor_name, concat_ws(' → ', sm.port_of_loading, sm.port_of_discharge)) as title,
  concat_ws(E'\n',
    'shipment_no=' || coalesce(sm.shipment_no, ''),
    'commercial_invoice_no=' || coalesce(sm.commercial_invoice_no, ''),
    'mr_no=' || coalesce(sm.mr_no, ''),
    'po_no=' || coalesce(sm.po_no, ''),
    'vendor=' || coalesce(sm.vendor_name, ''),
    'category=' || coalesce(sm.category, ''),
    'description=' || coalesce(sm.main_description, ''),
    'incoterm=' || coalesce(sm.incoterm, ''),
    'bl_awb_no=' || coalesce(sm.bl_awb_no, ''),
    'vessel=' || coalesce(sm.vessel_or_flight_no, ''),
    'ship_mode=' || coalesce(sm.ship_mode, ''),
    'coe=' || coalesce(sm.country_of_export, ''),
    'pol=' || coalesce(sm.port_of_loading, ''),
    'pod=' || coalesce(sm.port_of_discharge, ''),
    'etd=' || coalesce(sm.etd::text, ''),
    'eta=' || coalesce(sm.eta::text, ''),
    'ata=' || coalesce(sm.ata::text, ''),
    'customs_start=' || coalesce(sm.customs_start_date::text, ''),
    'customs_close=' || coalesce(sm.customs_close_date::text, ''),
    'planned_sites=' || array_to_string(coalesce(sm.planned_sites, '{}'::text[]), ','),
    'actual_sites=' || array_to_string(coalesce(sm.actual_sites, '{}'::text[]), ','),
    'current_location=' || coalesce(sm.current_location_code, ''),
    'route_type=' || coalesce(sm.route_type, ''),
    'milestone_status=' || coalesce(sm.milestone_status, ''),
    'risk_band=' || coalesce(sm.risk_band, '')
  ) as body,
  array_cat(
    array_cat(
      array_remove(array[
        sm.shipment_no,
        sm.commercial_invoice_no,
        sm.bl_awb_no,
        sm.vendor_name,
        sm.country_of_export,
        sm.port_of_loading,
        sm.port_of_discharge,
        sm.current_location_code,
        sm.route_type,
        sm.milestone_status
      ], null),
      coalesce(sm.planned_sites, '{}'::text[])
    ),
    coalesce(sm.actual_sites, '{}'::text[])
  ) as keywords,
  sm.vendor_name,
  null::text as site_code,
  sm.route_type,
  null::smallint as flow_code,
  sm.milestone_status as status_current,
  sm.risk_band,
  'hvdc status' as source_sheet,
  sm.source_row_no,
  jsonb_build_object('source_batch_id', sm.source_batch_id)
from ontology.shipment_master sm

union all

select
  'case:' || cm.case_key as search_doc_key,
  'case' as entity_type,
  'case:' || cm.case_key as entity_ref,
  'primary' as doc_scope,
  concat_ws(' ', coalesce(cm.shipment_invoice_no, cm.shipment_no), coalesce(cm.case_no, cm.eq_no), cm.description) as title,
  concat_ws(E'\n',
    'shipment_invoice_no=' || coalesce(cm.shipment_invoice_no, ''),
    'shipment_no=' || coalesce(cm.shipment_no, ''),
    'site=' || coalesce(cm.site_code, ''),
    'eq_no=' || coalesce(cm.eq_no, ''),
    'case_no=' || coalesce(cm.case_no, ''),
    'description=' || coalesce(cm.description, ''),
    'hs_code=' || coalesce(cm.hs_code, ''),
    'storage_type=' || coalesce(cm.storage_type, ''),
    'status_current=' || coalesce(cm.status_current, ''),
    'status_location=' || coalesce(cm.status_location, ''),
    'final_location=' || coalesce(cm.final_location, ''),
    'flow_code=' || coalesce(cm.flow_code::text, ''),
    'flow_description=' || coalesce(cm.flow_description, ''),
    'source_vendor=' || coalesce(cm.source_vendor, ''),
    'cbm=' || coalesce(cm.cbm::text, ''),
    'gross_weight_kg=' || coalesce(cm.gross_weight_kg::text, ''),
    'sqm=' || coalesce(cm.sqm::text, '')
  ) as body,
  array_remove(array[
    cm.shipment_invoice_no,
    cm.shipment_no,
    cm.site_code,
    cm.eq_no,
    cm.case_no,
    cm.description,
    cm.hs_code,
    cm.status_current,
    cm.status_location,
    cm.final_location,
    cm.source_vendor,
    case cm.flow_code
      when 0 then 'pre-arrival'
      when 1 then 'direct-to-site'
      when 2 then 'via-warehouse'
      when 3 then 'via-mosb'
      when 4 then 'via-warehouse-mosb'
      else 'review-required'
    end
  ], null) as keywords,
  cm.source_vendor as vendor_name,
  cm.site_code as site_code,
  case cm.flow_code
    when 0 then 'pre-arrival'
    when 1 then 'direct-to-site'
    when 2 then 'via-warehouse'
    when 3 then 'via-mosb'
    when 4 then 'via-warehouse-mosb'
    else 'review-required'
  end as route_type,
  cm.flow_code,
  cm.status_current,
  null::text as risk_band,
  'wh status' as source_sheet,
  cm.source_row_no,
  jsonb_build_object('source_batch_id', cm.source_batch_id)
from ontology.case_master cm;
