-- =========================================================
-- 2) case_master 적재
-- =========================================================

delete from ontology.case_master t
using (
  select distinct source_batch_id from ingest.wh_status_raw
) b
where t.source_batch_id = b.source_batch_id;

with raw as (
  select
    r.source_batch_id,
    r.no::integer as source_row_no,

    upper(nullif(trim(r.sct_ship_no::text), '')) as shipment_no,
    nullif(trim(r.shipment_invoice_no::text), '') as shipment_invoice_no,

    upper(nullif(trim(r.site::text), '')) as site_code,
    nullif(trim(r.eq_no::text), '') as eq_no,
    nullif(trim(r.case_no::text), '') as case_no,

    nullif(trim(r.pkg::text), '')::integer as pkg_count,
    nullif(trim(r.storage::text), '') as storage_type,
    nullif(trim(r.description::text), '') as description,

    nullif(replace(trim(r.l_cm::text), ',', ''), '')::numeric(12,2) as len_cm,
    nullif(replace(trim(r.w_cm::text), ',', ''), '')::numeric(12,2) as width_cm,
    nullif(replace(trim(r.h_cm::text), ',', ''), '')::numeric(12,2) as height_cm,
    nullif(replace(trim(r.cbm::text), ',', ''), '')::numeric(18,3) as cbm,
    nullif(replace(trim(r.n_w_kgs::text), ',', ''), '')::numeric(18,2) as net_weight_kg,
    nullif(replace(trim(r.g_w_kgs::text), ',', ''), '')::numeric(18,2) as gross_weight_kg,

    nullif(trim(r.stack::text), '') as stack_rule,
    nullif(trim(r.hs_code::text), '') as hs_code,
    upper(nullif(trim(r.currency::text), '')) as currency_code,
    nullif(replace(trim(r.price::text), ',', ''), '')::numeric(18,2) as price_amount,

    nullif(trim(r.vessel::text), '') as vessel_name,
    nullif(trim(r.coe::text), '') as country_of_export,
    nullif(trim(r.pol::text), '') as port_of_loading,
    nullif(trim(r.pod::text), '') as port_of_discharge,

    case when nullif(trim(r.etd_atd::text), '') is null then null else (r.etd_atd::timestamp)::date end as departed_or_etd_date,
    case when nullif(trim(r.eta_ata::text), '') is null then null else (r.eta_ata::timestamp)::date end as arrived_or_eta_date,

    jsonb_strip_nulls(jsonb_build_object(
      'DHL WH', case when nullif(trim(r.dhl_wh::text), '') is null then null else to_char((r.dhl_wh::timestamp)::date, 'YYYY-MM-DD') end,
      'DSV Indoor', case when nullif(trim(r.dsv_indoor::text), '') is null then null else to_char((r.dsv_indoor::timestamp)::date, 'YYYY-MM-DD') end,
      'DSV Al Markaz', case when nullif(trim(r.dsv_al_markaz::text), '') is null then null else to_char((r.dsv_al_markaz::timestamp)::date, 'YYYY-MM-DD') end,
      'AAA Storage', case when nullif(trim(r.aaa_storage::text), '') is null then null else to_char((r.aaa_storage::timestamp)::date, 'YYYY-MM-DD') end,
      'DSV Outdoor', case when nullif(trim(r.dsv_outdoor::text), '') is null then null else to_char((r.dsv_outdoor::timestamp)::date, 'YYYY-MM-DD') end,
      'DSV MZP', case when nullif(trim(r.dsv_mzp::text), '') is null then null else to_char((r.dsv_mzp::timestamp)::date, 'YYYY-MM-DD') end,
      'MOSB', case when nullif(trim(r.mosb::text), '') is null then null else to_char((r.mosb::timestamp)::date, 'YYYY-MM-DD') end,
      'Hauler Indoor', case when nullif(trim(r.hauler_indoor::text), '') is null then null else to_char((r.hauler_indoor::timestamp)::date, 'YYYY-MM-DD') end,
      'JDN MZD', case when nullif(trim(r.jdn_mzd::text), '') is null then null else to_char((r.jdn_mzd::timestamp)::date, 'YYYY-MM-DD') end,
      'Shifting', case when nullif(trim(r.shifting::text), '') is null then null else to_char((r.shifting::timestamp)::date, 'YYYY-MM-DD') end,
      'MIR', case when nullif(trim(r.mir::text), '') is null then null else to_char((r.mir::timestamp)::date, 'YYYY-MM-DD') end,
      'SHU', case when nullif(trim(r.shu::text), '') is null then null else to_char((r.shu::timestamp)::date, 'YYYY-MM-DD') end,
      'DAS', case when nullif(trim(r.das::text), '') is null then null else to_char((r.das::timestamp)::date, 'YYYY-MM-DD') end,
      'AGI', case when nullif(trim(r.agi::text), '') is null then null else to_char((r.agi::timestamp)::date, 'YYYY-MM-DD') end
    )) as location_dates,

    nullif(trim(r.status_warehouse::text), '') as status_warehouse,
    nullif(trim(r.status_site::text), '') as status_site,
    nullif(trim(r.status_current::text), '') as status_current,
    nullif(trim(r.status_location::text), '') as status_location,
    case when nullif(trim(r.status_location_date::text), '') is null then null else (r.status_location_date::timestamp)::date end as status_location_date,
    nullif(trim(r.status_storage::text), '') as status_storage,

    nullif(trim(r.wh_handling::text), '')::integer as wh_handling,
    nullif(trim(r.total_handling::text), '')::integer as total_handling,
    nullif(trim(r.minus::text), '')::integer as minus_handling,
    nullif(trim(r.final_handling::text), '')::integer as final_handling,

    nullif(replace(trim(r.sqm::text), ',', ''), '')::numeric(18,2) as sqm,
    nullif(trim(r.stack_status::text), '') as stack_status,
    nullif(replace(trim(r.total_sqm::text), ',', ''), '')::numeric(18,2) as total_sqm,

    nullif(trim(r.site_handling_original::text), '')::integer as site_handling_original,
    nullif(trim(r.total_handling_original::text), '')::integer as total_handling_original,
    nullif(trim(r.wh_handling_original::text), '')::integer as wh_handling_original,

    nullif(trim(r.flow_code::text), '')::smallint as flow_code,
    nullif(trim(r.flow_description::text), '') as flow_description,

    upper(nullif(trim(r.final_location::text), '')) as final_location,
    nullif(trim(r.source_vendor::text), '') as source_vendor,

    case when nullif(trim(r.first_touch_date::text), '') is null then null else (r.first_touch_date::timestamp)::date end as first_touch_date,
    case when nullif(trim(r.last_touch_date::text), '') is null then null else (r.last_touch_date::timestamp)::date end as last_touch_date,
    nullif(trim(r.first_touch_location::text), '') as first_touch_location,
    nullif(trim(r.last_touch_location::text), '') as last_touch_location,

    nullif(trim(r.linehaul_days::text), '')::integer as linehaul_days,
    nullif(trim(r.arrival_to_first_touch_days::text), '')::integer as arrival_to_first_touch_days,
    nullif(trim(r.arrival_to_last_touch_days::text), '')::integer as arrival_to_last_touch_days,
    nullif(trim(r.touch_span_days::text), '')::integer as touch_span_days,
    nullif(trim(r.wh_dwell_total_days::text), '')::integer as wh_dwell_total_days,
    nullif(trim(r.wh_dwell_last_days::text), '')::integer as wh_dwell_last_days,
    nullif(trim(r.wh_dwell_open_days::text), '')::integer as wh_dwell_open_days,
    nullif(trim(r.mosb_staging_days::text), '')::integer as mosb_staging_days
  from ingest.wh_status_raw r
),
linked as (
  select
    raw.*,
    coalesce(lk.shipment_group_key, raw.shipment_no, upper(raw.shipment_invoice_no)) as shipment_group_key_resolved
  from raw
  left join lateral (
    select sm.shipment_group_key
    from ontology.shipment_master sm
    where (raw.shipment_no is not null and sm.shipment_group_key = raw.shipment_no)
       or (raw.shipment_invoice_no is not null and sm.commercial_invoice_no = raw.shipment_invoice_no)
    order by
      case when sm.shipment_group_key = raw.shipment_no then 0 else 1 end,
      sm.updated_at desc
    limit 1
  ) lk on true
)
insert into ontology.case_master (
  source_batch_id,
  source_sheet,
  source_row_no,
  case_key,
  shipment_group_key,
  shipment_invoice_no,
  shipment_no,
  site_code,
  eq_no,
  case_no,
  pkg_count,
  storage_type,
  description,
  len_cm,
  width_cm,
  height_cm,
  cbm,
  net_weight_kg,
  gross_weight_kg,
  stack_rule,
  hs_code,
  currency_code,
  price_amount,
  vessel_name,
  country_of_export,
  port_of_loading,
  port_of_discharge,
  departed_or_etd_date,
  arrived_or_eta_date,
  location_dates,
  status_warehouse,
  status_site,
  status_current,
  status_location,
  status_location_date,
  status_storage,
  wh_handling,
  total_handling,
  minus_handling,
  final_handling,
  sqm,
  stack_status,
  total_sqm,
  site_handling_original,
  total_handling_original,
  wh_handling_original,
  flow_code,
  flow_description,
  final_location,
  source_vendor,
  first_touch_date,
  last_touch_date,
  first_touch_location,
  last_touch_location,
  linehaul_days,
  arrival_to_first_touch_days,
  arrival_to_last_touch_days,
  touch_span_days,
  wh_dwell_total_days,
  wh_dwell_last_days,
  wh_dwell_open_days,
  mosb_staging_days,
  raw_payload
)
select
  l.source_batch_id,
  'wh status',
  l.source_row_no,
  md5(concat_ws('|',
    coalesce(l.shipment_invoice_no, ''),
    coalesce(l.shipment_no, ''),
    coalesce(l.case_no, ''),
    coalesce(l.eq_no, ''),
    l.source_row_no::text
  )) as case_key,
  l.shipment_group_key_resolved,
  l.shipment_invoice_no,
  l.shipment_no,
  l.site_code,
  l.eq_no,
  l.case_no,
  l.pkg_count,
  l.storage_type,
  l.description,
  l.len_cm,
  l.width_cm,
  l.height_cm,
  l.cbm,
  l.net_weight_kg,
  l.gross_weight_kg,
  l.stack_rule,
  l.hs_code,
  l.currency_code,
  l.price_amount,
  l.vessel_name,
  l.country_of_export,
  l.port_of_loading,
  l.port_of_discharge,
  l.departed_or_etd_date,
  l.arrived_or_eta_date,
  l.location_dates,
  l.status_warehouse,
  l.status_site,
  l.status_current,
  l.status_location,
  l.status_location_date,
  l.status_storage,
  l.wh_handling,
  l.total_handling,
  l.minus_handling,
  l.final_handling,
  l.sqm,
  l.stack_status,
  l.total_sqm,
  l.site_handling_original,
  l.total_handling_original,
  l.wh_handling_original,
  l.flow_code,
  l.flow_description,
  l.final_location,
  l.source_vendor,
  l.first_touch_date,
  l.last_touch_date,
  l.first_touch_location,
  l.last_touch_location,
  l.linehaul_days,
  l.arrival_to_first_touch_days,
  l.arrival_to_last_touch_days,
  l.touch_span_days,
  l.wh_dwell_total_days,
  l.wh_dwell_last_days,
  l.wh_dwell_open_days,
  l.mosb_staging_days,
  jsonb_build_object(
    'source_row', to_jsonb(l)
  ) as raw_payload
from linked l;
