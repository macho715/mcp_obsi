-- 1) shipment_master 적재
-- =========================================================

delete from ontology.shipment_master t
using (
  select distinct source_batch_id from ingest.hvdc_status_raw
) b
where t.source_batch_id = b.source_batch_id;

with src as (
  select
    r.source_batch_id,
    r.no::integer as source_row_no,

    upper(nullif(trim(r.sct_ship_no::text), '')) as shipment_no,
    nullif(trim(r.mr_no::text), '') as mr_no,
    nullif(trim(r.commercial_invoice_no::text), '') as commercial_invoice_no,
    case when nullif(trim(r.invoice_date::text), '') is null then null else (r.invoice_date::timestamp)::date end as invoice_date,
    nullif(trim(r.po_no::text), '') as po_no,

    nullif(trim(r.vendor::text), '') as vendor_name,
    nullif(trim(r.category::text), '') as category,
    nullif(trim(r.main_description_po::text), '') as main_description,
    nullif(trim(r.sub_description::text), '') as sub_description,

    nullif(trim(r.incoterms::text), '') as incoterm,
    upper(nullif(trim(r.currency::text), '')) as currency_code,

    nullif(replace(trim(r.invoice_value_a::text), ',', ''), '')::numeric(18,2) as invoice_value,
    nullif(replace(trim(r.freight_b::text), ',', ''), '')::numeric(18,2) as freight_value,
    nullif(replace(trim(r.insurance_c::text), ',', ''), '')::numeric(18,2) as insurance_value,
    nullif(replace(trim(r.cif_value_a_b_c::text), ',', ''), '')::numeric(18,2) as cif_value,

    nullif(trim(r.coe::text), '') as country_of_export,
    nullif(trim(r.pol::text), '') as port_of_loading,
    nullif(trim(r.pod::text), '') as port_of_discharge,

    nullif(trim(r.bl_awb_no::text), '') as bl_awb_no,
    nullif(trim(r.vessel_name_flight_no::text), '') as vessel_or_flight_no,
    nullif(trim(r.vessel_imo_no::text), '') as vessel_imo_no,
    nullif(trim(r.shipping_line::text), '') as shipping_line,
    nullif(trim(r.forwarder::text), '') as forwarder,
    nullif(trim(r.ship_mode::text), '') as ship_mode,

    nullif(trim(r.pkg::text), '')::integer as pkg_count,
    nullif(trim(r.qty_of_cntr::text), '')::integer as qty_of_cntr,

    jsonb_strip_nulls(jsonb_build_object(
      '20DC', nullif(trim(r.c20dc::text), '')::integer,
      '40DC', nullif(trim(r.c40dc::text), '')::integer,
      '40HQ', nullif(trim(r.c40hq::text), '')::integer,
      '45HQ', nullif(trim(r.c45hq::text), '')::integer,
      '20OT(IN)', nullif(trim(r.c20ot_in::text), '')::integer,
      '20OT(OH)', nullif(trim(r.c20ot_oh::text), '')::integer,
      '40OT(IN)', nullif(trim(r.c40ot_in::text), '')::integer,
      '40OT(OH)', nullif(trim(r.c40ot_oh::text), '')::integer,
      '20FR(IN)', nullif(trim(r.c20fr_in::text), '')::integer,
      '40FR(IN)', nullif(trim(r.c40fr_in::text), '')::integer,
      '20FR(FV)', nullif(trim(r.c20fr_fv::text), '')::integer,
      '40FR(OW)', nullif(trim(r.c40fr_ow::text), '')::integer,
      '20FR(OW,OH)', nullif(trim(r.c20fr_ow_oh::text), '')::integer,
      '40FR(OW,OH)', nullif(trim(r.c40fr_ow_oh::text), '')::integer,
      '40FR(OW,OL)', nullif(trim(r.c40fr_ow_ol::text), '')::integer,
      'LCL', nullif(trim(r.lcl::text), '')::integer
    )) as container_mix,

    jsonb_strip_nulls(jsonb_build_object(
      'G Bulk', nullif(trim(r.g_bulk::text), '')::numeric(18,2),
      'O Bulk', nullif(trim(r.o_bulk::text), '')::numeric(18,2),
      'H Bulk', nullif(trim(r.h_bulk::text), '')::numeric(18,2)
    )) as bulk_mix,

    nullif(replace(trim(r.gwt_kg::text), ',', ''), '')::numeric(18,2) as gross_weight_kg,
    nullif(replace(trim(r.cbm::text), ',', ''), '')::numeric(18,3) as cbm,
    nullif(replace(trim(r.a_cwt_kg::text), ',', ''), '')::numeric(18,2) as chargeable_weight_kg,

    case when nullif(trim(r.etd::text), '') is null then null else (r.etd::timestamp)::date end as etd,
    case when nullif(trim(r.atd::text), '') is null then null else (r.atd::timestamp)::date end as atd,
    case when nullif(trim(r.eta::text), '') is null then null else (r.eta::timestamp)::date end as eta,
    case when nullif(trim(r.ata::text), '') is null then null else (r.ata::timestamp)::date end as ata,

    case when nullif(trim(r.attestation_date::text), '') is null then null else (r.attestation_date::timestamp)::date end as attestation_date,
    case when nullif(trim(r.do_collection::text), '') is null then null else (r.do_collection::timestamp)::date end as do_collection_date,
    case when nullif(trim(r.customs_start::text), '') is null then null else (r.customs_start::timestamp)::date end as customs_start_date,
    case when nullif(trim(r.customs_close::text), '') is null then null else (r.customs_close::timestamp)::date end as customs_close_date,

    nullif(trim(r.custom_code::text), '') as custom_code,
    nullif(replace(trim(r.duty_amt_aed::text), ',', ''), '')::numeric(18,2) as duty_amt_aed,
    nullif(replace(trim(r.vat_amt_aed::text), ',', ''), '')::numeric(18,2) as vat_amt_aed,

    array_remove(array[
      case when upper(coalesce(trim(r.doc_shu::text), '')) = 'O' then 'SHU' end,
      case when upper(coalesce(trim(r.doc_mir::text), '')) = 'O' then 'MIR' end,
      case when upper(coalesce(trim(r.doc_das::text), '')) = 'O' then 'DAS' end,
      case when upper(coalesce(trim(r.doc_agi::text), '')) = 'O' then 'AGI' end
    ], null)::text[] as planned_sites,

    array_remove(array[
      case when nullif(trim(r.shu::text), '') is not null then 'SHU' end,
      case when nullif(trim(r.mir::text), '') is not null then 'MIR' end,
      case when nullif(trim(r.das::text), '') is not null then 'DAS' end,
      case when nullif(trim(r.agi::text), '') is not null then 'AGI' end
    ], null)::text[] as actual_sites,

    jsonb_strip_nulls(jsonb_build_object(
      'SHU', case when nullif(trim(r.shu::text), '') is null then null else to_char((r.shu::timestamp)::date, 'YYYY-MM-DD') end,
      'MIR', case when nullif(trim(r.mir::text), '') is null then null else to_char((r.mir::timestamp)::date, 'YYYY-MM-DD') end,
      'DAS', case when nullif(trim(r.das::text), '') is null then null else to_char((r.das::timestamp)::date, 'YYYY-MM-DD') end,
      'AGI', case when nullif(trim(r.agi::text), '') is null then null else to_char((r.agi::timestamp)::date, 'YYYY-MM-DD') end
    )) as site_dates,

    jsonb_strip_nulls(jsonb_build_object(
      'DSV Indoor', case when nullif(trim(r.dsv_indoor::text), '') is null then null else to_char((r.dsv_indoor::timestamp)::date, 'YYYY-MM-DD') end,
      'DSV Outdoor', case when nullif(trim(r.dsv_outdoor::text), '') is null then null else to_char((r.dsv_outdoor::timestamp)::date, 'YYYY-MM-DD') end,
      'DSV MZD', case when nullif(trim(r.dsv_mzd::text), '') is null then null else to_char((r.dsv_mzd::timestamp)::date, 'YYYY-MM-DD') end,
      'DSV Kizad', case when nullif(trim(r.dsv_kizad::text), '') is null then null else to_char((r.dsv_kizad::timestamp)::date, 'YYYY-MM-DD') end,
      'JDN MZD', case when nullif(trim(r.jdn_mzd::text), '') is null then null else to_char((r.jdn_mzd::timestamp)::date, 'YYYY-MM-DD') end,
      'JDN Waterfront', case when nullif(trim(r.jdn_waterfront::text), '') is null then null else to_char((r.jdn_waterfront::timestamp)::date, 'YYYY-MM-DD') end,
      'AAA Storage', case when nullif(trim(r.aaa_storage::text), '') is null then null else to_char((r.aaa_storage::timestamp)::date, 'YYYY-MM-DD') end,
      'ZENER (WH)', case when nullif(trim(r.zener_wh::text), '') is null then null else to_char((r.zener_wh::timestamp)::date, 'YYYY-MM-DD') end,
      'Hauler DG Storage', case when nullif(trim(r.hauler_dg_storage::text), '') is null then null else to_char((r.hauler_dg_storage::timestamp)::date, 'YYYY-MM-DD') end,
      'Vijay Tanks', case when nullif(trim(r.vijay_tanks::text), '') is null then null else to_char((r.vijay_tanks::timestamp)::date, 'YYYY-MM-DD') end
    )) as warehouse_dates,

    case when nullif(trim(r.mosb::text), '') is null then null else (r.mosb::timestamp)::date end as mosb_date,

    case when nullif(trim(r.first_deliver_date::text), '') is null then null else (r.first_deliver_date::timestamp)::date end as first_deliver_date,
    case when nullif(trim(r.last_deliver_date::text), '') is null then null else (r.last_deliver_date::timestamp)::date end as last_deliver_date,
    nullif(trim(r.first_touch_location::text), '') as first_touch_location,
    nullif(trim(r.last_touch_location::text), '') as last_touch_location,

    nullif(trim(r.transport_days::text), '')::integer as transport_days,
    nullif(trim(r.customs_days::text), '')::integer as customs_days,
    nullif(trim(r.dispatch_first_days::text), '')::integer as dispatch_first_days,
    nullif(trim(r.dispatch_last_days::text), '')::integer as dispatch_last_days,
    nullif(trim(r.delivery_span_days::text), '')::integer as delivery_span_days,

    nullif(trim(r.route_class::text), '') as route_class,
    nullif(trim(r.milestone_status::text), '') as milestone_status,
    coalesce(nullif(trim(r.anomaly_count::text), '')::integer, 0) as anomaly_count,
    nullif(trim(r.anomaly_flags::text), '') as anomaly_flags,
    nullif(trim(r.risk_score::text), '')::numeric(10,2) as risk_score,
    nullif(trim(r.risk_band::text), '') as risk_band
  from ingest.hvdc_status_raw r
  where nullif(trim(r.sct_ship_no::text), '') is not null
)
insert into ontology.shipment_master (
  source_batch_id,
  source_sheet,
  source_row_no,
  shipment_key,
  shipment_group_key,
  shipment_no,
  mr_no,
  commercial_invoice_no,
  invoice_date,
  po_no,
  vendor_name,
  category,
  main_description,
  sub_description,
  incoterm,
  currency_code,
  invoice_value,
  freight_value,
  insurance_value,
  cif_value,
  country_of_export,
  port_of_loading,
  port_of_discharge,
  bl_awb_no,
  vessel_or_flight_no,
  vessel_imo_no,
  shipping_line,
  forwarder,
  ship_mode,
  pkg_count,
  qty_of_cntr,
  container_mix,
  bulk_mix,
  gross_weight_kg,
  cbm,
  chargeable_weight_kg,
  etd,
  atd,
  eta,
  ata,
  attestation_date,
  do_collection_date,
  customs_start_date,
  customs_close_date,
  custom_code,
  duty_amt_aed,
  vat_amt_aed,
  planned_sites,
  actual_sites,
  site_basis,
  first_deliver_date,
  last_deliver_date,
  first_touch_location,
  last_touch_location,
  current_location_code,
  transport_days,
  customs_days,
  dispatch_first_days,
  dispatch_last_days,
  delivery_span_days,
  route_class,
  route_type,
  milestone_status,
  anomaly_count,
  anomaly_flags,
  risk_score,
  risk_band,
  raw_payload
)
select
  src.source_batch_id,
  'hvdc status',
  src.source_row_no,
  md5(concat_ws('|',
    src.shipment_no,
    coalesce(src.commercial_invoice_no, ''),
    coalesce(src.bl_awb_no, ''),
    coalesce(src.etd::text, ''),
    coalesce(src.eta::text, ''),
    coalesce(src.port_of_discharge, ''),
    coalesce(src.ship_mode, '')
  )) as shipment_key,
  src.shipment_no as shipment_group_key,
  src.shipment_no,
  src.mr_no,
  src.commercial_invoice_no,
  src.invoice_date,
  src.po_no,
  src.vendor_name,
  src.category,
  src.main_description,
  src.sub_description,
  src.incoterm,
  src.currency_code,
  src.invoice_value,
  src.freight_value,
  src.insurance_value,
  src.cif_value,
  src.country_of_export,
  src.port_of_loading,
  src.port_of_discharge,
  src.bl_awb_no,
  src.vessel_or_flight_no,
  src.vessel_imo_no,
  src.shipping_line,
  src.forwarder,
  src.ship_mode,
  src.pkg_count,
  src.qty_of_cntr,
  src.container_mix,
  src.bulk_mix,
  src.gross_weight_kg,
  src.cbm,
  src.chargeable_weight_kg,
  src.etd,
  src.atd,
  src.eta,
  src.ata,
  src.attestation_date,
  src.do_collection_date,
  src.customs_start_date,
  src.customs_close_date,
  src.custom_code,
  src.duty_amt_aed,
  src.vat_amt_aed,
  src.planned_sites,
  src.actual_sites,
  case
    when cardinality(src.actual_sites) > 0 and cardinality(src.planned_sites) > 0 then 'mixed'
    when cardinality(src.actual_sites) > 0 then 'actual'
    when cardinality(src.planned_sites) > 0 then 'planned'
    else 'unknown'
  end as site_basis,
  src.first_deliver_date,
  src.last_deliver_date,
  src.first_touch_location,
  src.last_touch_location,
  coalesce(
    src.last_touch_location,
    case when src.mosb_date is not null then 'MOSB' end
  ) as current_location_code,
  src.transport_days,
  src.customs_days,
  src.dispatch_first_days,
  src.dispatch_last_days,
  src.delivery_span_days,
  src.route_class,
  case src.route_class
    when 'NO_DELIVERY' then 'pre-arrival'
    when 'DIRECT_SITE' then 'direct-to-site'
    when 'WH_SITE' then 'via-warehouse'
    when 'WH_ONLY' then 'via-warehouse'
    when 'MOSB_SITE' then 'via-mosb'
    when 'MOSB_ONLY' then 'via-mosb'
    when 'WH_MOSB_SITE' then 'via-warehouse-mosb'
    when 'WH_MOSB_PENDING' then 'review-required'
    else 'review-required'
  end as route_type,
  src.milestone_status,
  src.anomaly_count,
  src.anomaly_flags,
  src.risk_score,
  src.risk_band,
  jsonb_build_object(
    'site_dates', src.site_dates,
    'warehouse_dates', src.warehouse_dates,
    'mosb_date', case when src.mosb_date is null then null else to_char(src.mosb_date, 'YYYY-MM-DD') end,
    'source_row', to_jsonb(src)
  ) as raw_payload
