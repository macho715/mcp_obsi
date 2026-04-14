create schema if not exists ontology;

create extension if not exists pgcrypto;
create extension if not exists vector;

-- =========================================================
-- 1. shipment_master
-- grain = shipment / voyage row from "hvdc status"
-- NOTE:
-- - shipment_no(SCT SHIP NO.)는 소스에서 중복 가능성이 있으므로 unique 금지
-- - shipment_key는 ETL에서 만든 deterministic unique key
-- - shipment_group_key는 같은 shipment_no 묶음용
-- =========================================================
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

  unique (source_batch_id, source_sheet, source_row_no)
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


-- =========================================================
-- 2. case_master
-- grain = case / package row from "wh status"
-- NOTE:
-- - case_no, shipment_no 모두 null 가능한 행이 있으므로 case_key를 ETL에서 생성
-- - 상세 routing, FLOW_CODE, warehouse stop은 여기만 둠
-- =========================================================
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

  unique (source_batch_id, source_sheet, source_row_no)
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


-- =========================================================
-- 3. entity_edge
-- graph-like relation table
-- src_ref/dst_ref examples:
--   shipment:<shipment_key>
--   case:<case_key>
--   site:AGI
--   location:DSV Indoor
--   document:CI:<commercial_invoice_no>
-- =========================================================
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


-- =========================================================
-- 4. search_doc
-- one search document per shipment and per case
-- FTS uses 'simple' dictionary to preserve codes like AGI, MOSB, BL, SCT, HVDC
-- =========================================================
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


-- =========================================================
-- 5. embedding_index
-- semantic index separated from search_doc as requested
-- ASSUMPTION: vector dimension = 1536
-- =========================================================
create table if not exists ontology.embedding_index (
  embedding_id uuid primary key default gen_random_uuid(),

  search_doc_id uuid not null
    references ontology.search_doc(search_doc_id)
    on delete cascade,
