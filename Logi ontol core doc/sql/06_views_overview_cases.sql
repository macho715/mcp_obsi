-- =========================================================
-- 6) Overview bridge view
-- repo contract: v_overview_shipments_v1 shipment-only select
-- =========================================================

create or replace view public.v_overview_shipments_v2 as
select
  sm.shipment_id::text as id,
  sm.shipment_no as sct_ship_no,
  sm.mr_no as status_no,
  sm.commercial_invoice_no,
  sm.invoice_date,
  sm.vendor_name as vendor,
  sm.category,
  sm.main_description,
  sm.port_of_loading,
  sm.port_of_discharge,
  sm.vessel_or_flight_no as vessel_name,
  sm.bl_awb_no,
  sm.ship_mode,
  sm.country_of_export as coe,
  sm.etd,
  sm.atd,
  sm.eta,
  sm.ata,
  sm.do_collection_date,
  sm.customs_start_date,
  sm.customs_close_date,
  sm.last_deliver_date as final_delivery_date,
  sm.duty_amt_aed as duty_amount_aed,
  sm.vat_amt_aed as vat_amount_aed,
  sm.incoterm as incoterms,

  ('SHU' = any(coalesce(sm.planned_sites, '{}'::text[]))) as doc_shu,
  ('DAS' = any(coalesce(sm.planned_sites, '{}'::text[]))) as doc_das,
  ('MIR' = any(coalesce(sm.planned_sites, '{}'::text[]))) as doc_mir,
  ('AGI' = any(coalesce(sm.planned_sites, '{}'::text[]))) as doc_agi,

  nullif(sm.raw_payload #>> '{site_dates,SHU}', '')::date as shu_actual_date,
  nullif(sm.raw_payload #>> '{site_dates,MIR}', '')::date as mir_actual_date,
  nullif(sm.raw_payload #>> '{site_dates,DAS}', '')::date as das_actual_date,
  nullif(sm.raw_payload #>> '{site_dates,AGI}', '')::date as agi_actual_date,

  cardinality(coalesce(sm.actual_sites, '{}'::text[])) as actual_site_count,

  (wh.warehouse_hint_date is not null) as has_warehouse_hint,
  wh.warehouse_hint_location,
  wh.warehouse_hint_date,

  (nullif(sm.raw_payload ->> 'mosb_date', '') is not null) as has_mosb_hint,
  nullif(sm.raw_payload ->> 'mosb_date', '')::date as mosb_hint_date

from ontology.shipment_master sm
left join lateral (
  select
    x.key as warehouse_hint_location,
    nullif(x.value, '')::date as warehouse_hint_date
  from jsonb_each_text(coalesce(sm.raw_payload -> 'warehouse_dates', '{}'::jsonb)) x
  where nullif(x.value, '') is not null
  order by x.value desc, x.key
  limit 1
) wh on true;


```sql
-- =========================================================
-- 7) Cases bridge view
-- repo contract: /api/cases + summary helper compatible
-- =========================================================

create or replace view public.v_cases_ontology_v1 as
select
  cm.case_id::text as id,
  coalesce(cm.shipment_no, sm.shipment_no) as hvdc_code,
  coalesce(cm.shipment_no, sm.shipment_no) as sct_ship_no,
  cm.shipment_invoice_no,
  cm.case_no,
  cm.eq_no,
  cm.site_code as site,

  cm.flow_code,
  cm.flow_description,
  case cm.flow_code
    when 0 then 'pre-arrival'
    when 1 then 'direct-to-site'
    when 2 then 'via-warehouse'
    when 3 then 'via-mosb'
    when 4 then 'via-warehouse-mosb'
    else 'review-required'
  end as route_type,

  cm.status_warehouse,
  cm.status_site,
  cm.status_current,
  cm.status_location,
  cm.status_location_date,
  cm.status_storage,

  cm.final_location,
  cm.source_vendor,
  cm.storage_type,
  cm.stack_status,

  cm.sqm,
  cm.total_sqm,

  cm.description,
  cm.gross_weight_kg,
  cm.cbm,
  cm.hs_code,
  cm.currency_code as currency,
  cm.price_amount as price,

  cm.vessel_name as vessel,
  cm.country_of_export as coe,
  cm.port_of_loading as pol,
  cm.port_of_discharge as pod,
  cm.departed_or_etd_date as etd_atd,
  cm.arrived_or_eta_date as eta_ata,

  coalesce(
    nullif(cm.location_dates ->> cm.site_code, '')::date,
    case when cm.status_location = cm.site_code then cm.status_location_date end,
    case when cm.final_location = cm.site_code then cm.last_touch_date end
  ) as site_arrival_date,

  sm.category,

  cm.first_touch_date,
  cm.last_touch_date,
  cm.first_touch_location,
  cm.last_touch_location,
  cm.linehaul_days,
  cm.arrival_to_first_touch_days,
  cm.arrival_to_last_touch_days,
  cm.touch_span_days,
  cm.wh_dwell_total_days,
  cm.wh_dwell_last_days,
  cm.wh_dwell_open_days,
  cm.mosb_staging_days

from ontology.case_master cm
left join lateral (
  select
    sm.shipment_no,
    sm.category
  from ontology.shipment_master sm
  where sm.shipment_group_key = cm.shipment_group_key
     or (cm.shipment_invoice_no is not null and sm.commercial_invoice_no = cm.shipment_invoice_no)
  order by
    case when sm.shipment_group_key = cm.shipment_group_key then 0 else 1 end,
    sm.updated_at desc
  limit 1
) sm on true;
