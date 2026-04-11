# Ontology — 핵심 변환 규칙·매핑·템플릿·적재 규칙

## 2) 핵심 변환 규칙

### 2-1. `route_class` → `route_type`

현재 앱은 user-facing 라벨을 `route_type`으로 사용하고, internal `flow_code`는 detail 쪽에 남기는 구조입니다.

```sql
case
  when route_class = 'DIRECT_SITE' then 'direct-to-site'
  when route_class in ('WH_SITE', 'WH_ONLY') then 'via-warehouse'
  when route_class in ('MOSB_SITE', 'MOSB_ONLY') then 'via-mosb'
  when route_class in ('WH_MOSB_SITE', 'WH_MOSB_PENDING') then 'via-warehouse-mosb'
  when route_class = 'NO_DELIVERY' then 'pre-arrival'
  else 'review-required'
end
```

### 2-2. shipment stage 계산

Overview는 Flow Code가 아니라 milestone 기반이어야 합니다. `hvdc all status`는 Overview only, `wh status + Flow Code`는 case drilldown only가 현재 계약입니다.

```sql
case
  when last_deliver_date is not null then 'delivered'
  when array_length(actual_sites, 1) > 0 then 'at_site'
  when current_location_code = 'MOSB' then 'mosb_staging'
  when current_location_code ilike 'DSV%' or current_location_code ilike '%WH%' then 'warehouse_staging'
  when customs_close_date is not null then 'customs_cleared'
  when customs_start_date is not null then 'customs_in_progress'
  when ata is not null then 'arrived_port'
  when eta is not null or atd is not null then 'in_transit'
  else 'pre_arrival'
end
```

### 2-3. shipment ↔ case 링크 우선순위

소스 품질상 `wh status`에 `SCT SHIP NO.`나 `Case No.`가 비는 행이 있으므로 아래 순서로 링크하십시오.

```text
1) case.shipment_no = shipment.shipment_no
2) 없으면 case.shipment_invoice_no = shipment.commercial_invoice_no
3) 둘 다 없으면 orphan_case로 남기고 review queue로 보냄
```

## 3) Excel 컬럼 매핑표

### 3-1. `hvdc status` → `ontology.shipment_master`

| No | Source Sheet | Source Column(s)                                                                                    | Target Column                                               | Rule                                             |
| -: | ------------ | --------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- | ------------------------------------------------ |
|  1 | hvdc status  | `NO`                                                                                                | `source_row_no`                                             | 그대로                                              |
|  2 | hvdc status  | 파일명/배치시각                                                                                            | `source_batch_id`                                           | 예: `leadtime_2026-03-17_v1`                      |
|  3 | hvdc status  | `SCT SHIP NO.`                                                                                      | `shipment_no`, `shipment_group_key`                         | trim/upper                                       |
|  4 | hvdc status  | `MR#`                                                                                               | `mr_no`                                                     | 그대로                                              |
|  5 | hvdc status  | `COMMERCIAL INVOICE No.`                                                                            | `commercial_invoice_no`                                     | 그대로                                              |
|  6 | hvdc status  | `INVOICE Date`                                                                                      | `invoice_date`                                              | date cast                                        |
|  7 | hvdc status  | `PO No.`                                                                                            | `po_no`                                                     | text cast                                        |
|  8 | hvdc status  | `VENDOR`                                                                                            | `vendor_name`                                               | vendor normalize                                 |
|  9 | hvdc status  | `CATEGORY`                                                                                          | `category`                                                  | 그대로                                              |
| 10 | hvdc status  | `MAIN DESCRIPTION (PO)`                                                                             | `main_description`                                          | 그대로                                              |
| 11 | hvdc status  | `SUB DESCRIPTION`                                                                                   | `sub_description`                                           | 그대로                                              |
| 12 | hvdc status  | `INCOTERMS`                                                                                         | `incoterm`                                                  | upper                                            |
| 13 | hvdc status  | `CURRENCY`                                                                                          | `currency_code`                                             | upper                                            |
| 14 | hvdc status  | `INVOICE VALUE (A)`                                                                                 | `invoice_value`                                             | numeric(18,2)                                    |
| 15 | hvdc status  | `FREIGHT (B)`                                                                                       | `freight_value`                                             | numeric(18,2)                                    |
| 16 | hvdc status  | `INSURANCE (C)`                                                                                     | `insurance_value`                                           | numeric(18,2)                                    |
| 17 | hvdc status  | `CIF VALUE (A+B+C)`                                                                                 | `cif_value`                                                 | numeric(18,2)                                    |
| 18 | hvdc status  | `COE`, `POL`, `POD`                                                                                 | `country_of_export`, `port_of_loading`, `port_of_discharge` | trim                                             |
| 19 | hvdc status  | `B/L No./ AWB No.`                                                                                  | `bl_awb_no`                                                 | text cast                                        |
| 20 | hvdc status  | `VESSEL NAME/ FLIGHT No.`                                                                           | `vessel_or_flight_no`                                       | 그대로                                              |
| 21 | hvdc status  | `VESSEL IMO NO.`                                                                                    | `vessel_imo_no`                                             | text cast                                        |
| 22 | hvdc status  | `SHIPPING LINE`, `FORWARDER`, `SHIP MODE`                                                           | `shipping_line`, `forwarder`, `ship_mode`                   | trim                                             |
| 23 | hvdc status  | `PKG`, `QTY OF CNTR`                                                                                | `pkg_count`, `qty_of_cntr`                                  | integer                                          |
| 24 | hvdc status  | `20DC`~`LCL`                                                                                        | `container_mix`                                             | JSONB 묶음                                         |
| 25 | hvdc status  | `G Bulk`, `O Bulk`, `H Bulk`                                                                        | `bulk_mix`                                                  | JSONB 묶음                                         |
| 26 | hvdc status  | `GWT (KG)`, `CBM`, `A_CWT(KG)`                                                                      | `gross_weight_kg`, `cbm`, `chargeable_weight_kg`            | numeric                                          |
| 27 | hvdc status  | `ETD`, `ATD`, `ETA`, `ATA`                                                                          | `etd`, `atd`, `eta`, `ata`                                  | date cast                                        |
| 28 | hvdc status  | `Attestation Date`, `DO Collection`, `Customs Start`, `Customs Close`                               | 대응 날짜 컬럼                                                    | date cast                                        |
| 29 | hvdc status  | `Custom Code`, `DUTY AMT (AED)`, `VAT AMT (AED)`                                                    | `custom_code`, `duty_amt_aed`, `vat_amt_aed`                | numeric/date                                     |
| 30 | hvdc status  | `DOC_SHU`, `DOC_MIR`, `DOC_DAS`, `DOC_AGI`                                                          | `planned_sites`                                             | O/값 존재 시 site array 생성                           |
| 31 | hvdc status  | `SHU`, `MIR`, `DAS`, `AGI`                                                                          | `actual_sites`                                              | date 존재 시 site array 생성                          |
| 32 | hvdc status  | `SHU`~`Vijay Tanks`                                                                                 | `raw_payload.site_dates`                                    | location-date JSONB 보존                           |
| 33 | hvdc status  | `first_deliver_date`, `last_deliver_date`                                                           | 대응 날짜 컬럼                                                    | date cast                                        |
| 34 | hvdc status  | `first_touch_location`, `last_touch_location`                                                       | 대응 텍스트 컬럼                                                   | trim                                             |
| 35 | hvdc status  | `transport_days`, `customs_days`, `dispatch_*`, `delivery_span_days` | 대응 정수 컬럼                                                    | integer                                          |
| 36 | hvdc status  | `route_class`                                                                                       | `route_class`                                               | 그대로                                              |
| 37 | hvdc status  | `route_class`                                                                                       | `route_type`                                                | CASE 변환                                          |
| 38 | hvdc status  | `milestone_status`                                                                                  | `milestone_status`                                          | 그대로                                              |
| 39 | hvdc status  | `anomaly_count`, `anomaly_flags`, `risk_score`, `risk_band`                                         | 대응 컬럼                                                       | 그대로                                              |
| 40 | hvdc status  | 전체 row                                                                                              | `raw_payload`                                               | 원본 보존                                            |
| 41 | hvdc status  | 복합                                                                                                  | `current_location_code`                                     | `last_touch_location` 우선, 없으면 actual site latest |
| 42 | hvdc status  | 복합                                                                                                  | `site_basis`                                                | actual / planned / mixed / unknown               |
| 43 | hvdc status  | 복합                                                                                                  | `shipment_key`                                              | sha256(shipment_no \| commercial_invoice_no \| bl_awb_no \| etd \| eta \| pod \| ship_mode) |

### 3-2. `wh status` → `ontology.case_master`

| No | Source Sheet | Source Column(s)                                                                                                 | Target Column                                 | Rule                         |
| -: | ------------ | ---------------------------------------------------------------------------------------------------------------- | --------------------------------------------- | ---------------------------- |
|  1 | wh status    | `no.`                                                                                                            | `source_row_no`                               | 그대로                          |
|  2 | wh status    | 파일명/배치시각                                                                                                         | `source_batch_id`                             | 예: `warehouse_2026-03-17_v1` |
|  3 | wh status    | `Shipment Invoice No.`                                                                                           | `shipment_invoice_no`                         | trim                         |
|  4 | wh status    | `SCT SHIP NO.`                                                                                                   | `shipment_no`, `shipment_group_key`           | trim/upper                   |
|  5 | wh status    | `Site`                                                                                                           | `site_code`                                   | upper                        |
|  6 | wh status    | `EQ No`                                                                                                          | `eq_no`                                       | 그대로                          |
|  7 | wh status    | `Case No.`                                                                                                       | `case_no`                                     | text cast                    |
|  8 | wh status    | `Pkg`                                                                                                            | `pkg_count`                                   | integer                      |
|  9 | wh status    | `Storage`                                                                                                        | `storage_type`                                | 그대로                          |
| 10 | wh status    | `Description`                                                                                                    | `description`                                 | 그대로                          |
| 11 | wh status    | `L(CM)`, `W(CM)`, `H(CM)`                                                                                        | `len_cm`, `width_cm`, `height_cm`             | numeric                      |
| 12 | wh status    | `CBM`, `N.W(kgs)`, `G.W(kgs)`                                                                                    | `cbm`, `net_weight_kg`, `gross_weight_kg`     | numeric                      |
| 13 | wh status    | `Stack`                                                                                                          | `stack_rule`                                  | 그대로                          |
| 14 | wh status    | `HS Code`                                                                                                        | `hs_code`                                     | text cast                    |
| 15 | wh status    | `Currency`, `Price`                                                                                              | `currency_code`, `price_amount`               | upper/numeric                |
| 16 | wh status    | `Vessel`, `COE`, `POL`, `POD`                                                                                    | 대응 컬럼                                         | trim                         |
| 17 | wh status    | `ETD/ATD`, `ETA/ATA`                                                                                             | `departed_or_etd_date`, `arrived_or_eta_date` | date cast                    |
| 18 | wh status    | `DHL WH`~`AGI`                                                                                                   | `location_dates`                              | JSONB location-date map      |
| 19 | wh status    | `Status_WAREHOUSE`, `Status_SITE`, `Status_Current`, …                                                           | 대응 status 컬럼                                  | 그대로                          |
| 20 | wh status    | `wh handling`, `total handling`, `minus`, `final handling`                                                       | 대응 handling 컬럼                                | integer                      |
| 21 | wh status    | `SQM`, `Stack_Status`, `Total sqm`                                                                               | `sqm`, `stack_status`, `total_sqm`            | numeric/text                 |
| 22 | wh status    | `site_handling_original`, `total_handling_original`, `wh_handling_original`                                      | 대응 original 컬럼                                | integer                      |
| 23 | wh status    | `FLOW_CODE`, `FLOW_DESCRIPTION`                                                                                  | `flow_code`, `flow_description`               | smallint/text                |
| 24 | wh status    | `Final_Location`                                                                                                 | `final_location`                              | trim                         |
| 25 | wh status    | `Source_Vendor`                                                                                                  | `source_vendor`                               | vendor normalize             |
| 26 | wh status    | `first_touch_date`, `last_touch_date`                                                                            | 대응 컬럼                                         | date cast                    |
| 27 | wh status    | `first_touch_location`, `last_touch_location`                                                                    | 대응 컬럼                                         | trim                         |
| 28 | wh status    | `linehaul_days`~`mosb_staging_days`                                                                              | 대응 metric 컬럼                                  | integer                      |
| 29 | wh status    | 전체 row                                                                                                           | `raw_payload`                                 | 원본 보존                        |
| 30 | wh status    | 복합                                                                                                               | `case_key`                                    | sha256(shipment_invoice_no \| shipment_no \| case_no \| eq_no \| source_row_no) |

### 3-3. 파생 매핑: `entity_edge / search_doc / embedding_index`

| No | Source                        | Target              | Rule |
| -: | ----------------------------- | ------------------- | ---- |
|  1 | shipment_master + case_master | entity_edge         | `shipment:<key> --contains_case--> case:<key>` 생성 |
|  2 | shipment_master               | entity_edge         | planned_sites 각 원소마다 `--planned_for--> site:<code>` |
|  3 | shipment_master               | entity_edge         | actual_sites 각 원소마다 `--actual_at--> site:<code>` |
|  4 | shipment_master               | entity_edge         | commercial_invoice_no 있으면 `--has_document--> document:CI:<no>` |
|  5 | shipment_master               | entity_edge         | bl_awb_no 있으면 `--has_document--> document:BLAWB:<no>` |
|  6 | shipment_master               | entity_edge         | route_type 있으면 `--uses_route--> route:<route_type>` |
|  7 | case_master                   | entity_edge         | status_location 있으면 `--current_at--> location:<status_location>` |
|  8 | case_master                   | entity_edge         | final_location 있으면 `--final_at--> location:<final_location>` |
|  9 | case_master                   | entity_edge         | source_vendor 있으면 `--handled_by--> vendor:<vendor>` |
| 10 | shipment_master               | search_doc          | shipment당 1행. title/body/keywords 생성 |
| 11 | case_master                   | search_doc          | case당 1행. title/body/keywords 생성 |
| 12 | search_doc                    | embedding_index     | title+body+keywords 임베딩 후 1행 생성 |
| 13 | search_doc                    | embedding_index     | content_sha256 = sha256(title \| body \| sorted_keywords) |
| 14 | search_doc                    | search_doc.fts      | generated column 자동 생성 |
| 15 | search_doc                    | search_doc.keywords | exact lookup: shipment_no, invoice_no, bl_awb_no, case_no, eq_no, vendor, POL, POD, site, route_type, flow_code |

## 4) `search_doc` title/body 템플릿

### shipment용

```text
title =
  [shipment_no] [vendor_name] [port_of_loading] -> [port_of_discharge]

body =
  shipment_no, commercial_invoice_no, mr_no, po_no, vendor_name, category,
  main_description, sub_description, incoterm, currency_code,
  bl_awb_no, vessel_or_flight_no, vessel_imo_no, shipping_line, forwarder,
  country_of_export, port_of_loading, port_of_discharge,
  etd, atd, eta, ata,
  customs_start_date, customs_close_date,
  planned_sites, actual_sites, current_location_code,
  route_type, milestone_status, risk_band, anomaly_flags
```

### case용

```text
title =
  [shipment_invoice_no] [case_no] [description]

body =
  shipment_invoice_no, shipment_no, site_code, eq_no, case_no, description,
  hs_code, storage_type, vessel_name,
  status_current, status_location, final_location,
  flow_code, flow_description, source_vendor,
  len_cm, width_cm, height_cm, cbm, gross_weight_kg, sqm,
  first_touch_location, last_touch_location
```

## 5) 바로 필요한 적재 규칙

1. Overview bridge view는 `shipment_master`만 보십시오. 현재 아키텍처도 `/api/overview`는 shipment-only source를 전제로 합니다.

2. Pipeline / Sites / Cargo / Chain bridge view는 `case_master`를 기준으로 보십시오. 현재 `v_cases`가 그 역할입니다.

3. exact search는 `search_doc.keywords + fts`, related search는 `embedding_index + entity_edge`로 나누십시오. Supabase 공식 예시도 FTS와 vector를 결합한 hybrid search 구조를 권장합니다. ([Supabase][1])

4. `flow_code`는 detail 전용입니다. Overview stage나 main path에는 쓰지 마십시오.

5. 기존 앱과 충돌하지 않게 1차는 `ontology` schema sidecar로 운영하고, 검증 후 bridge view로 cutover 하십시오. 현재 앱은 `shipments / shipments_status / v_cases / v_overview_shipments_v1` 계약 위에 있습니다.

[1]: https://supabase.com/docs/guides/ai/hybrid-search "https://supabase.com/docs/guides/ai/hybrid-search"
