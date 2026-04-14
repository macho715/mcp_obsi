-- ============================================================================
-- File: supabase/migrations/20260319_ontology_sidecar.sql
-- Purpose:
--   Ontology sidecar schema for HVDC logistics dashboard.
--   Creates ontology tables, search surfaces, refresh functions, and bridge views.
--
-- Assumptions:
--   1) ingest.hvdc_status_raw contains the current published HVDC shipment snapshot.
--   2) ingest.wh_status_raw contains the current published WH / case snapshot.
--   3) Raw column names are snake_case-normalized from the Excel headers.
--   4) Embedding dimension is 1536. Change to your model dimension if different.
--
-- Notes:
--   - This migration does NOT automatically replace public.v_overview_shipments_v1 or public.v_cases.
--   - It creates public.v_overview_shipments_v2 and public.v_cases_ontology_v1.
--   - Optional alias cutover block is provided at the bottom as comments.
-- ============================================================================

begin;

set search_path = public, extensions;

create schema if not exists ontology;
create schema if not exists extensions;

create extension if not exists pgcrypto with schema extensions;
create extension if not exists vector with schema extensions;

-- ============================================================================
-- 1) Core tables
-- ============================================================================

create table if not exists ontology.shipment_master (
  shipment_id uuid primary key default gen_random_uuid(),

  source_batch_id text not null,
  source_sheet text not null default 'hvdc status',
  source_row_no integer not null,

  shipment_key text not null unique,
  shipment_group_key text not null,
  shipment_no text not null,

  mr_no text,
  commercial_invoice_no text,
  invoice_date date,
  po_no text,

  vendor_name text,
  category text,
  main_description text,
  sub_description text,

  incoterm text,
  currency_code text,

  invoice_value numeric(18,2),
  freight_value numeric(18,2),
  insurance_value numeric(18,2),
  cif_value numeric(18,2),

  country_of_export text,
  port_of_loading text,
  port_of_discharge text,

  bl_awb_no text,
  vessel_or_flight_no text,
  vessel_imo_no text,
  shipping_line text,
  forwarder text,
  ship_mode text,

  pkg_count integer,
  qty_of_cntr integer,

  container_mix jsonb not null default '{}'::jsonb,
  bulk_mix jsonb not null default '{}'::jsonb,

  gross_weight_kg numeric(18,2),
  cbm numeric(18,3),
  chargeable_weight_kg numeric(18,2),

  etd date,
  atd date,
  eta date,
  ata date,

  attestation_date date,
  do_collection_date date,
  customs_start_date date,
  customs_close_date date,

  custom_code text,
  duty_amt_aed numeric(18,2),
  vat_amt_aed numeric(18,2),

  planned_sites text[] not null default '{}'::text[],
  actual_sites text[] not null default '{}'::text[],
  site_basis text not null default 'unknown'
    check (site_basis in ('planned','actual','mixed','unknown')),

  first_deliver_date date,
  last_deliver_date date,
  first_touch_location text,
  last_touch_location text,
  current_location_code text,

  transport_days integer,
  customs_days integer,
  dispatch_first_days integer,
  dispatch_last_days integer,
  delivery_span_days integer,

  route_class text,
  route_type text
    check (route_type in (
      'pre-arrival',
      'direct-to-site',
      'via-warehouse',
      'via-mosb',
      'via-warehouse-mosb',
      'review-required'
    )),

  milestone_status text,
  anomaly_count integer not null default 0,
  anomaly_flags text,
  risk_score numeric(10,2),
  risk_band text,

  raw_payload jsonb not null default '{}'::jsonb,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  unique (source_sheet, source_row_no)
);

create index if not exists ix_shipment_master_group_key
  on ontology.shipment_master (shipment_group_key);
create index if not exists ix_shipment_master_shipment_no
  on ontology.shipment_master (shipment_no);
create index if not exists ix_shipment_master_invoice_no
  on ontology.shipment_master (commercial_invoice_no);
create index if not exists ix_shipment_master_bl_awb
  on ontology.shipment_master (bl_awb_no);
create index if not exists ix_shipment_master_vendor
  on ontology.shipment_master (vendor_name);
create index if not exists ix_shipment_master_route_type
  on ontology.shipment_master (route_type);
create index if not exists ix_shipment_master_milestone
  on ontology.shipment_master (milestone_status);
create index if not exists ix_shipment_master_pol_pod
  on ontology.shipment_master (port_of_loading, port_of_discharge);
create index if not exists ix_shipment_master_eta
  on ontology.shipment_master (eta);


create table if not exists ontology.case_master (
  case_id uuid primary key default gen_random_uuid(),

  source_batch_id text not null,
  source_sheet text not null default 'wh status',
  source_row_no integer not null,

  case_key text not null unique,
  shipment_group_key text,
  shipment_invoice_no text,
  shipment_no text,

  site_code text,
  eq_no text,
  case_no text,

  pkg_count integer,
  storage_type text,
  description text,

  len_cm numeric(12,2),
  width_cm numeric(12,2),
  height_cm numeric(12,2),

  cbm numeric(18,3),
  net_weight_kg numeric(18,2),
  gross_weight_kg numeric(18,2),

  stack_rule text,
  hs_code text,
  currency_code text,
  price_amount numeric(18,2),

  vessel_name text,
  country_of_export text,
  port_of_loading text,
  port_of_discharge text,

  departed_or_etd_date date,
  arrived_or_eta_date date,

  location_dates jsonb not null default '{}'::jsonb,

  status_warehouse text,
  status_site text,
  status_current text,
  status_location text,
  status_location_date date,
  status_storage text,

  wh_handling integer,
  total_handling integer,
  minus_handling integer,
  final_handling integer,

  sqm numeric(18,2),
  stack_status text,
  total_sqm numeric(18,2),

  site_handling_original integer,
  total_handling_original integer,
  wh_handling_original integer,

  flow_code smallint not null check (flow_code between 0 and 5),
  flow_description text,

  final_location text,
  source_vendor text,

  first_touch_date date,
  last_touch_date date,
  first_touch_location text,
  last_touch_location text,

  linehaul_days integer,
  arrival_to_first_touch_days integer,
  arrival_to_last_touch_days integer,
  touch_span_days integer,
  wh_dwell_total_days integer,
  wh_dwell_last_days integer,
  wh_dwell_open_days integer,
  mosb_staging_days integer,

  raw_payload jsonb not null default '{}'::jsonb,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  unique (source_sheet, source_row_no)
);

create index if not exists ix_case_master_shipment_group_key
  on ontology.case_master (shipment_group_key);
create index if not exists ix_case_master_shipment_invoice_no
  on ontology.case_master (shipment_invoice_no);
create index if not exists ix_case_master_shipment_no
  on ontology.case_master (shipment_no);
create index if not exists ix_case_master_case_no
  on ontology.case_master (case_no);
create index if not exists ix_case_master_eq_no
  on ontology.case_master (eq_no);
create index if not exists ix_case_master_site
  on ontology.case_master (site_code);
create index if not exists ix_case_master_flow_code
  on ontology.case_master (flow_code);
create index if not exists ix_case_master_status_current
  on ontology.case_master (status_current);
create index if not exists ix_case_master_status_location
  on ontology.case_master (status_location);
create index if not exists ix_case_master_final_location
  on ontology.case_master (final_location);
create index if not exists ix_case_master_vendor
  on ontology.case_master (source_vendor);


create table if not exists ontology.entity_edge (
  edge_id uuid primary key default gen_random_uuid(),

  source_batch_id text not null,
  edge_key text not null unique,

  src_entity_type text not null
    check (src_entity_type in ('shipment','case','site','location','document','vendor','route')),
  src_ref text not null,

  rel_type text not null,

  dst_entity_type text not null
    check (dst_entity_type in ('shipment','case','site','location','document','vendor','route')),
  dst_ref text not null,
  dst_label text,

  evidence jsonb not null default '{}'::jsonb,

  valid_from date,
  valid_to date,
  is_current boolean not null default true,
  sort_order integer,

  created_at timestamptz not null default now()
);

create index if not exists ix_entity_edge_src
  on ontology.entity_edge (src_ref, rel_type);
create index if not exists ix_entity_edge_dst
  on ontology.entity_edge (dst_ref, rel_type);
create index if not exists ix_entity_edge_rel
  on ontology.entity_edge (rel_type);


create table if not exists ontology.search_doc (
  search_doc_id uuid primary key default gen_random_uuid(),

  search_doc_key text not null unique,
  entity_type text not null
    check (entity_type in ('shipment','case')),
  entity_ref text not null,
  doc_scope text not null default 'primary'
    check (doc_scope in ('primary','related')),

  title text not null,
  body text not null,
  keywords text[] not null default '{}'::text[],

  vendor_name text,
  site_code text,
  route_type text,
  flow_code smallint,
  status_current text,
  risk_band text,

  source_sheet text not null,
  source_row_no integer not null,
  metadata jsonb not null default '{}'::jsonb,

  fts tsvector generated always as (
    to_tsvector(
      'simple',
      coalesce(title,'') || ' ' ||
      coalesce(body,'') || ' ' ||
      array_to_string(coalesce(keywords, '{}'::text[]), ' ')
    )
  ) stored,

  created_at timestamptz not null default now(),

  unique (entity_ref, doc_scope)
);

create index if not exists ix_search_doc_fts
  on ontology.search_doc using gin (fts);
create index if not exists ix_search_doc_entity_ref
  on ontology.search_doc (entity_ref);
create index if not exists ix_search_doc_vendor
  on ontology.search_doc (vendor_name);
create index if not exists ix_search_doc_site
  on ontology.search_doc (site_code);
create index if not exists ix_search_doc_route_type
  on ontology.search_doc (route_type);
create index if not exists ix_search_doc_flow_code
  on ontology.search_doc (flow_code);


create table if not exists ontology.embedding_index (
  embedding_id uuid primary key default gen_random_uuid(),

  search_doc_id uuid not null
    references ontology.search_doc(search_doc_id)
    on delete cascade,

  embedding_model text not null,
  embedding_version text,
  content_sha256 text not null,

  embedding extensions.vector(1536) not null,

  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  unique (search_doc_id, embedding_model, embedding_version)
);

create index if not exists ix_embedding_index_doc
  on ontology.embedding_index (search_doc_id);
create index if not exists ix_embedding_index_hnsw
  on ontology.embedding_index using hnsw (embedding vector_cosine_ops);

-- ============================================================================
-- 2) Utility function
-- ============================================================================

create or replace function ontology._route_type_from_class(route_class text)
returns text
language sql
immutable
as $$
  select case route_class
    when 'NO_DELIVERY' then 'pre-arrival'
    when 'DIRECT_SITE' then 'direct-to-site'
    when 'WH_SITE' then 'via-warehouse'
    when 'WH_ONLY' then 'via-warehouse'
    when 'MOSB_SITE' then 'via-mosb'
    when 'MOSB_ONLY' then 'via-mosb'
    when 'WH_MOSB_SITE' then 'via-warehouse-mosb'
    when 'WH_MOSB_PENDING' then 'review-required'
    else 'review-required'
  end;
$$;

-- ============================================================================
-- 3) Refresh from current ingest snapshot
-- ============================================================================

create or replace function ontology.refresh_sidecar_from_ingest()
returns jsonb
language plpgsql
set search_path = public, extensions, ontology
as $$
declare
  v_has_hvdc boolean;
  v_has_wh boolean;
  v_shipments integer := 0;
  v_cases integer := 0;
  v_edges integer := 0;
  v_docs integer := 0;
begin
  v_has_hvdc := to_regclass('ingest.hvdc_status_raw') is not null;
  v_has_wh := to_regclass('ingest.wh_status_raw') is not null;

  if not v_has_hvdc and not v_has_wh then
    return jsonb_build_object(
      'ok', false,
      'reason', 'missing_ingest_tables',
      'required', jsonb_build_array('ingest.hvdc_status_raw', 'ingest.wh_status_raw')
    );
  end if;

  truncate table ontology.embedding_index, ontology.search_doc, ontology.entity_edge, ontology.case_master, ontology.shipment_master restart identity cascade;

  if v_has_hvdc then
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
      ontology._route_type_from_class(src.route_class) as route_type,
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
    from src;

    get diagnostics v_shipments = row_count;
  end if;

  if v_has_wh then
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
        order by case when sm.shipment_group_key = raw.shipment_no then 0 else 1 end, sm.updated_at desc
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
      jsonb_build_object('source_row', to_jsonb(l)) as raw_payload
    from linked l;

    get diagnostics v_cases = row_count;
  end if;

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

  get diagnostics v_edges = row_count;

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
    concat_ws(' ', sm.shipment_no, sm.vendor_name, concat_ws(' -> ', sm.port_of_loading, sm.port_of_discharge)) as title,
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

  get diagnostics v_docs = row_count;

  return jsonb_build_object(
    'ok', true,
    'shipments', v_shipments,
    'cases', v_cases,
    'edges', v_edges,
    'search_docs', v_docs
  );
end;
$$;

-- ============================================================================
-- 4) Refresh embedding index from staging
-- ============================================================================

create or replace function ontology.refresh_embedding_from_stage()
returns jsonb
language plpgsql
set search_path = public, extensions, ontology
as $$
declare
  v_has_stage boolean;
  v_rows integer := 0;
begin
  v_has_stage := to_regclass('ingest.embedding_stage') is not null;

  if not v_has_stage then
    return jsonb_build_object(
      'ok', false,
      'reason', 'missing_ingest_embedding_stage',
      'required', 'ingest.embedding_stage(search_doc_key, embedding_model, embedding_version, content_sha256, embedding, is_active)'
    );
  end if;

  truncate table ontology.embedding_index restart identity;

  insert into ontology.embedding_index (
    search_doc_id,
    embedding_model,
    embedding_version,
    content_sha256,
    embedding,
    is_active
  )
  select
    sd.search_doc_id,
    st.embedding_model,
    st.embedding_version,
    st.content_sha256,
    st.embedding,
    coalesce(st.is_active, true)
  from ingest.embedding_stage st
  join ontology.search_doc sd
    on sd.search_doc_key = st.search_doc_key;

  get diagnostics v_rows = row_count;

  return jsonb_build_object(
    'ok', true,
    'embedding_rows', v_rows
  );
end;
$$;

-- ============================================================================
-- 5) Bridge views
-- ============================================================================

create or replace view public.v_overview_shipments_v2 as
select
  sm.shipment_key as id,
  sm.shipment_key,
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
  sm.route_type,
  sm.milestone_status,
  sm.current_location_code,
  sm.risk_band,

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


create or replace view public.v_cases_ontology_v1 as
select
  cm.case_key as id,
  cm.case_key,
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
  order by case when sm.shipment_group_key = cm.shipment_group_key then 0 else 1 end, sm.updated_at desc
  limit 1
) sm on true;

-- ============================================================================
-- 6) Grants
-- ============================================================================

grant usage on schema ontology to service_role;
grant select on public.v_overview_shipments_v2 to anon, authenticated, service_role;
grant select on public.v_cases_ontology_v1 to anon, authenticated, service_role;
grant execute on function ontology.refresh_sidecar_from_ingest() to service_role;
grant execute on function ontology.refresh_embedding_from_stage() to service_role;

commit;

-- ============================================================================
-- Manual run after raw load
-- ============================================================================
-- select ontology.refresh_sidecar_from_ingest();
-- select ontology.refresh_embedding_from_stage();

-- ============================================================================
-- Optional alias cutover
-- Use only after validating v2 / ontology view output against current app.
-- ============================================================================
-- create or replace view public.v_overview_shipments_v1 as
-- select * from public.v_overview_shipments_v2;
--
-- create or replace view public.v_cases as
-- select * from public.v_cases_ontology_v1;
