---
title: "HVDC Material Handling — Consolidated (v2.0)"
type: "ontology-design"
domain: "material-handling"
sub-domains: ["customs","storage","offshore","receiving","transformer","bulk-cargo"]
version: "consolidated-2.0"
date: "2026-04-11"
spine_ref: "CONSOLIDATED-00-master-ontology.md"
extension_of: "hvdc-master-ontology-v1.0"
status: "active"
source_files: [
  "2_EXT-08A-hvdc-material-handling-overview.md",
  "2_EXT-08B-hvdc-material-handling-customs.md",
  "2_EXT-08C-hvdc-material-handling-storage.md",
  "2_EXT-08D-hvdc-material-handling-offshore.md",
  "2_EXT-08E-hvdc-material-handling-site-receiving.md",
  "2_EXT-08F-hvdc-material-handling-transformer.md",
  "2_EXT-08G-hvdc-material-handling-bulk-integrated.md"
]
---

> **MASTER GOVERNANCE RULE**
> 1. **Flow Code is a warehouse-handling classification only.** Restricted to `WarehouseHandlingProfile`. No other domain may own or assign Flow Code.
> 2. **Program-wide shipment visibility shall use Journey Stage, RoutingPattern, Milestone, and Leg.** (`routingPattern`, `currentStage`, `leg_sequence`, `JourneyLeg`)
> 3. **Port, Customs, Document, Cost, Marine, and Communication domains** may reference warehouse-flow *evidence*, but shall NOT own or assign Flow Code.
> 4. **MOSB is an Offshore Staging / Marine Interface Node**, not a Warehouse.

> **Extension Document** — 이 문서는 [`CONSOLIDATED-00-master-ontology.md`](CONSOLIDATED-00-master-ontology.md)의 도메인 확장입니다.
> RoutingPattern Dictionary, Milestone M10~M160, Identifier Policy 정의는 CONSOLIDATED-00을 참조하세요.

# hvdc-material-handling · CONSOLIDATED-06 (v2.0)

## 📑 Table of Contents
1. [Material Handling Overview & RoutingPattern Map](#section-1)
2. [Customs & Port Stage (M40~M100)](#section-2)
3. [Warehouse Operations (M110~M121)](#section-3)
4. [Offshore / Marine / Heavy-lift (M115~M117)](#section-4)
5. [Site Receiving & Inspection (M130~M140)](#section-5)

> **Version Note**: v2.0 restructured from v1.1 (3495 lines).
> Original content preserved in `CONSOLIDATED-06-material-handling.bak.md`.
> Flow Code 0~5 전체 체인 → RoutingPattern + MilestoneStatus로 전환.
> Flow Code는 Section 3의 WarehouseHandlingProfile 내부에서만 사용.

---

## Section 1: Material Handling Overview & RoutingPattern Map {#section-1}

> **참조**: RoutingPattern 전체 정의는 [`CONSOLIDATED-00`](CONSOLIDATED-00-master-ontology.md) Part 1 §1.2를 참조하세요.

### 1.1 자재 카테고리별 RoutingPattern

| Material Category | Primary RoutingPattern | 기본 경로 | 이유 |
|---|---|---|---|
| Container Cargo | `WH_ONLY`, `WH_MOSB` | Port→WH→(MOSB)→Site | 표준 컨테이너, 창고 경유 |
| Bulk Cargo | `MOSB_DIRECT`, `WH_MOSB` | Port→(WH→)MOSB→Site | 대형 자재, MOSB 집하 필요 |
| Transformer/OOG | `WH_MOSB`, `MOSB_DIRECT` | Port→WH→MOSB→Site | 특수 취급, Lashing/Stability 필요 |
| MIR/SHU Onshore | `WH_ONLY`, `DIRECT` | Port→WH→Site | MOSB 불필요 |
| AGI/DAS Offshore | `MOSB_DIRECT`, `WH_MOSB`, `MIXED` | MOSB 경유 필수 | **VIOLATION-2 적용** |

### 1.2 AGI/DAS 도메인 룰

> **AGI/DAS Domain Rule**: `declaredDestination IN (AGI, DAS)` 화물은
> `routingPattern IN (MOSB_DIRECT, WH_MOSB, MIXED)` 필수.
> M115 (MOSB Staged) 없이 M130 (Site Arrived) 기록 시 **VIOLATION-2** 발동.
> → SHACL 구현: `CONSOLIDATED-00` Part 6 `hvdc:AGIDASStagingShape`

### 1.3 Material Category Definitions

| Category | Description | UOM | Packaging Requirement | Storage Requirement |
|---|---|---|---|---|
| **Container Cargo** | 표준 컨테이너 화물 (FCL/LCL). 전기기기, 부품, 소형장비 포함 | PCS / PKG | ISO 20' / 40' container or carton | Dry indoor; max humidity 85% |
| **Bulk Cargo** | 비컨테이너 대형화물. Cable drum, pipe, steel structure | TON / M / M² | Skid, pallet, bundle lashing | Outdoor yard 허용; 방청 처리 필수 |
| **Transformer / OOG** | Over-size / Over-weight 대형 변압기 및 중량물 | UNIT | 제조사 승인 Lashing Plan 적용 | Indoor heated (+15~+25°C, 85% RH 이하); 질소 봉입 유지 |
| **Dangerous Goods** | IMDG/ADR 규정 위험물 (배터리, 가스, 가연성 액체) | KG / L | UN 승인 용기, DG label 부착 | 지정 DG 구역; FANR 허가 별도 |
| **MIR/SHU 온쇼어** | 육상 사이트 직납 자재. MOSB 경유 불필요 | PCS / SET | 표준 포장 | Site 창고 수령 또는 직납 |
| **AGI/DAS 오프쇼어** | 해상 도서 사이트 자재. MOSB 경유 **필수** | PCS / TON | 해상 운송 내구 포장, 방수·방청 처리 | MOSB Laydown; LCT 적재 전 Sea-fastening 검증 |

### 1.4 Journey Stage Vocabulary

총 15개 단계. 각 단계는 Entry Milestone 진입 시 활성화되고 Exit Milestone 도달 시 종료됩니다.

| Stage Code | Korean Name | Entry Milestone | Exit Milestone |
|---|---|---|---|
| `PLANNING` | 계획 | M10 (PO Issued) | M20 (Origin Ready) |
| `ORIGIN_DISPATCH` | 원산지 출발 | M20 (Origin Ready) | M30 (Vessel Departed) |
| `PORT_ENTRY` | 입항 | M30 (Vessel Departed) | M50 (Terminal Received) |
| `TERMINAL_HANDLING` | 터미널 작업 | M50 (Terminal Received) | M60 (Loaded/ATD) |
| `CUSTOMS_CLEARANCE` | 통관 | M80 (ATA) | M92 (DO Released) |
| `INLAND_HAULAGE` | 내륙 운송 | M92 (DO Released) | M100 (Gate-out) |
| `WH_RECEIPT` | 창고 입고 | M100 (Gate-out) | M110 (WH Received) |
| `WH_STORAGE` | 창고 보관 | M110 (WH Received) | M120 (Picked/Staged) |
| `WH_DISPATCH` | 창고 출고 | M120 (Picked/Staged) | M121 (WH Dispatched) |
| `MOSB_STAGING` | MOSB 스테이징 | M121 (WH Dispatched) | M115 (MOSB Staged) |
| `OFFSHORE_TRANSIT` | 해상 운송 | M116 (LCT Loaded) | M117 (Sail-away) |
| `SITE_RECEIVING` | 현장 수령 | M117 (Sail-away) | M130 (Site Arrived) |
| `MATERIAL_ISSUE` | 자재 불출 | M131/M132 (Inspected) | M140 (POD/GRN) |
| `CLOSEOUT` | 완료 | M140 (POD/GRN) | M160 (Closed) |
| `EXCEPTION` | 예외 처리 | 임의 Milestone | 원인 해결 후 복귀 |

> **참조**: Milestone 코드 전체 정의 → `CONSOLIDATED-00` Part 1 §1.5

### 1.5 WarehouseHandlingProfile (요약)

`WarehouseHandlingProfile`은 M110 (WH Received) 이벤트 발생 시 자동 생성되는 창고 운영 프로파일입니다.

```
WarehouseHandlingProfile {
  profileId:               string            // MH-{shipmentId}-{timestamp}
  location:                string            // DSV Indoor / AAA Storage / MOSB Yard
  operator:                string            // 담당 창고 운영자
  storageClass:            enum              // DRY / HUMID_CONTROL / TEMP_CONTROL / HAZMAT / OOG
  flowConfirmationStatus:  enum              // tentative | confirmed | override
  confirmedFlowCode:       integer (0~5)     // M110 이후 put-away 시 확정
  createdAt:               ISO-8601 datetime
}
```

- `confirmedFlowCode`는 **이 클래스 안에서만** 사용됩니다 (Section 3 참조).
- 전체 알고리즘 상세 → [`CONSOLIDATED-02`](CONSOLIDATED-02-warehouse-flow.md) Section 2.

---

## Section 2: Customs & Port Stage (M40~M100) {#section-2}

> **Milestones**: M40 (Export Cleared) → M50 (Terminal Received) → M60/M61 (Loaded/ATD)
> → M80 (ATA) → M90/M91 (BOE Submitted/Cleared) → M92 (DO Released) → M100 (Gate-out)
>
> **참조**: Milestone 정의 `CONSOLIDATED-00` Part 1 §1.5. CustomsEntry 클래스 `CONSOLIDATED-00` Part 4.

### 2.1 Document Requirements by Port Stage

> **참조**: 문서 OCR·검증 상세 → [`CONSOLIDATED-03`](CONSOLIDATED-03-document-ocr.md)

| Stage | Required Documents | Source System | Owner |
|---|---|---|---|
| **Export (Origin)** | CL (Cargo List), CI (Commercial Invoice), PL (Packing List) | ERP / Vendor | Shipper |
| **Export (Origin)** | AWB / BL (Bill of Lading) | Carrier | Freight Forwarder |
| **Export (Origin)** | E/L (Export License), FCO (Final Certificate of Origin) | Gov't portal | Shipper |
| **Export (Origin)** | COO (Certificate of Origin), Form E (FTA), Health/Phyto Cert | Certification body | Shipper |
| **Import (UAE)** | BOE (Bill of Entry) | eDAS / CUSTOMS | ADOPT / ADNOC |
| **Import (UAE)** | Release Order (RO), DO (Delivery Order) | Port Authority | Freight Agent |
| **Import (UAE)** | Customs Bond, CE-Marking Declaration | Customs | Importer |
| **Import (UAE)** | FANR Permit (방사성 자재), MOIAT Type Approval | Regulator | Importer |

**Consignee 코드표**:

| Location | Consignee | Customs Code |
|---|---|---|
| Abu Dhabi (CNTR) | ADOPT | 47150 / 1485718 |
| Dubai (Jebel Ali) | ADOPT Dubai | 89901 |

### 2.2 HS Code & Classification

- **HS Code 필수**: BOE 제출 시 모든 line item에 8-digit HS code 기재 필수.
- **FANR 대상**: 방사성 물질·방사선 기기 포함 품목은 FANR(Federal Authority for Nuclear Regulation) 사전 승인 후 BOE 제출.
- **MOIAT 대상**: 전기·기계류 중 Type Approval 대상 품목은 MOIAT(Ministry of Industry & Advanced Technology) 인증서 첨부.
- **금지·규제 품목**: Dual-use 품목(보안 규제), 마약류, CITES 품목은 별도 허가 필요 → ZERO 게이트 적용.
- **리스크 분류**: `LOW` (표준 전기 부품) / `MEDIUM` (화학류, 배터리) / `HIGH` (FANR, MOIAT 대상) → 분류별 처리 경로 상이.

### 2.3 BOE Process Flow

BOE (Bill of Entry) 제출부터 DO 발급까지의 7단계 흐름:

1. **Submit** (M90): 수입 신고서(BOE) + 첨부 서류 eDAS 시스템 업로드
2. **DG Risk Assessment**: 위험물 여부 자동 검사 (FANR/ADR/IMDG 대조)
3. **Classification**: HS code 검토 및 관세 분류 확정 (MOIAT 연동)
4. **Assessment**: 관세·부가세 산정 (Duty = CIF × 관세율; UAE 표준 5%)
5. **Payment**: 관세 납부 (ADOPT 선납 후 ADNOC 정산 또는 Customs Bond 사용)
6. **Clearance** (M91): 통관 승인 완료 — `CustomsEntry.status = CLEARED`
7. **DO Release** (M92): 포워더가 선사로부터 DO 수령 → 항만 게이트 반출 가능

> 평균 소요: 표준화물 2~4일, FANR/MOIAT 대상 7~14일

### 2.4 Free Time & DEM/DET Risk

컨테이너 미반환·초과 체류 시 DEM(Demurrage) 또는 DET(Detention) 비용 발생.

| Port | Free Time (DEM) | Free Time (DET) | DEM Rate (Est.) | DET Rate (Est.) |
|---|---|---|---|---|
| Khalifa Port (Abu Dhabi) | 5 일 | 7 일 | USD 40~80/box/day | USD 30~60/box/day |
| Mina Zayed (Abu Dhabi) | 5 일 | 7 일 | USD 40~80/box/day | USD 30~60/box/day |
| Jebel Ali (Dubai) | 5 일 | 7 일 | USD 50~100/box/day | USD 40~80/box/day |

> **모니터링 규칙**: M92 (DO Released) 이후 3일 이내 Gate-out(M100) 미완료 시 DEM/DET 경보 발송.
> 상세 비용 계산 → [`CONSOLIDATED-05`](CONSOLIDATED-05-invoice-cost.md)

---

## Section 3: Warehouse Operations (M110~M121) {#section-3}

> **Milestones**: M110 ★ (WH Received) → M111 (Put-away) → M120 (Picked/Staged) → M121 (Dispatched)
>
> **M110 = WarehouseHandlingProfile 생성 트리거.**
> `confirmedFlowCode`는 이 섹션의 WH In 이벤트(M110) 이후에만 설정됩니다.
>
> **참조**: WH 내부 운영 상세 → [`CONSOLIDATED-02`](CONSOLIDATED-02-warehouse-flow.md) Section 2: WarehouseHandlingProfile Algorithm

> **[Warehouse Domain Rule]** `confirmedFlowCode`는 `WarehouseHandlingProfile` 클래스 안에서만
> 설정됩니다. Material Handling 레이어에서는 `routingPattern`과 `MilestoneStatus`를 사용하세요.

### 3.1 WarehouseHandlingProfile Algorithm

> **전체 알고리즘**: [`CONSOLIDATED-02`](CONSOLIDATED-02-warehouse-flow.md) Section 2 참조.

**빠른 요약**:

1. M110 (WH Received) 이벤트 발생 → 시스템이 `WarehouseHandlingProfile` 자동 생성
2. 초기 `flowConfirmationStatus = "tentative"` (물리 검증 전)
3. Put-away 작업 완료 시 창고 담당자가 `confirmedFlowCode` 확정 입력
4. `flowConfirmationStatus = "confirmed"` 로 전환

**Flow Code 정의표** (창고 내부 분류 전용):

| confirmedFlowCode | 명칭 | 의미 |
|---|---|---|
| `0` | Standard Inside | 일반 표준 실내 보관 |
| `1` | Standard Outside | 일반 표준 실외 보관 |
| `2` | Special Inside | 특수 조건 실내 보관 (온습도 제어) |
| `3` | Special Outside | 특수 조건 실외 보관 (방청·커버링) |
| `4` | Hazmat | 위험물 지정 구역 |
| `5` | OOG / Abnormal | 초대형·중량물 특수 취급 구역 |

### 3.2 Storage Classification Matrix

| Flow Code | Storage Type | 구역 | 조건 | 주요 장비 |
|---|---|---|---|---|
| 0 | Standard Indoor | DSV Indoor / AAA Indoor | 온도 +5~+40°C, 습도 ≤ 85% | 표준 포크리프트, 선반 |
| 1 | Standard Outdoor | DSV Yard / AAA Yard | 방청 커버, UV 차단 | 지게차, 크레인 |
| 2 | Special Indoor (Heated) | DSV Heated Room | 온도 +15~+25°C, 습도 ≤ 85% | 환경 센서, 제습기 |
| 3 | Special Outdoor | Zayed Port Yard / MOSB Yard | 방청·방수 포장, 토크 체크 | 중장비 크레인 |
| 4 | Hazmat Area | DG 지정 구역 | IMDG 규정, 환기 필수 | DG 인증 장비만 |
| 5 | OOG / Heavy | OOG 전용 야드 | 지면 하중 검토 필수, SWL 확인 | 대형 크레인, 트레일러 |

> **Hitachi 권고**: Indoor Heated (+15~+25°C, 85% RH 이하), 질소 봉입(변압기), 진동 모니터 부착.

### 3.3 Preservation Monitoring

| 보관 유형 | 점검 주기 | 기록 양식 | 특이 사항 |
|---|---|---|---|
| Dry (Flow 0/1) | 월 1회 | Preservation Inspection Report | 방청 상태, 포장 손상 여부 |
| Humid/Controlled (Flow 2) | 주 1회 | Temperature & Humidity Log | 센서 알람 이력 포함 |
| Hazmat (Flow 4) | 입·출고 시마다 | DG Inspection Checklist | FANR 허가 조건 이행 확인 |
| OOG / Transformer (Flow 3/5) | 월 1회 + 이동 전 | OOG Preservation Record | 질소 압력, 부싱 보호 캡 상태 |

### 3.4 WH Dispatch Process

1. **M120 — Pick / Stage**: 출고 오더 수령 → 창고 내 위치에서 자재 피킹 → 출고 스테이징 구역 집결
2. **Load Check**: 수량·포장 상태·라벨 일치 확인 (MRR 사본 vs 피킹 리스트 대조)
3. **Transport Manifest**: 운반 트럭 배차, 운송 매니페스트 (출발지·목적지·화물 리스트) 작성
4. **M121 — WH Dispatched**: 게이트 반출 스캔 → `JourneyLeg.exitTimestamp` 기록 → 다음 단계(MOSB 또는 Site) 연계

---

## Section 4: Offshore / Marine / Heavy-lift (M115~M117) {#section-4}

> **Milestones**: M115 (MOSB Staged) → M116 (LCT/Barge Loaded) → M117 (Sail-away Approved)
>
> **MOSB = Offshore Staging / Marine Interface Node** (창고 아님).
>
> **참조**: MarineRoutingPattern 정의 → `CONSOLIDATED-00` Part 1 §1.2 Tier 2.
> Marine/Bulk 상세 → [`CONSOLIDATED-04`](CONSOLIDATED-04-barge-bulk-cargo.md)

> **[Marine Domain Rule]** Marine/Offshore 작업은 `MarineRoutingPattern`과
> `offshoreDeliveryPattern`을 사용합니다.
> Marine 도메인은 `confirmedFlowCode`를 할당하지 않습니다.

### 4.1 MOSB Staging Operations (M115)

**MOSB = Mussafah Offshore Supply Base** — Offshore Staging / Marine Interface Node (창고 아님).

**M115 선행 조건**:
- M121 (WH Dispatched) 완료 또는 Port 직납 자재의 경우 M100 (Gate-out) 완료
- MOSB 스테이징 요청서 (MOSB Staging Request) ALS 승인
- 화물 중량·치수 MOSB Laydown Plan과 대조 확인

**스테이징 구역**:
| 구역 | 용도 | 비고 |
|---|---|---|
| Laydown Area (실내) | 소형 컨테이너, 전기 부품 | 우천 시 우선 배치 |
| Open Deck Area (실외) | OOG, 중량물, Bulk | 방청 포장 유지 |
| DG Segregation Zone | 위험물 별도 격리 | IMDG 기준 이격거리 준수 |

**M115 완료 조건**: ALS 검수 서명 → `MilestoneStatus.M115 = COMPLETED`

### 4.2 LCT / Barge Operations (M116)

> **Safety Constant**: `MAX_CONTAINER_PRESSURE: 4.0 t/m²` — 모든 LCT/Barge 갑판 적재 시 초과 금지.

**M116 적재 확인 절차**:
1. **Weight & Stability Check**: 선박 안정성 계산서 (Stability Calculation) ALS 승인
2. **Cargo Manifest**: 자재 목록·중량·치수·위치 기재
3. **Sea-fastening Plan**: 각 화물 Lashing 방법 (체인, 스트랩, 용접 패드) 사전 제출 및 승인
4. **Deck Pressure Verification**: 전체 화물 중량 / 배치 면적 ≤ 4.0 t/m² 확인 → 초과 시 **ZERO 게이트** 발동
5. **Pre-sail Inspection**: 선장 + ALS 담당자 공동 최종 점검
6. **M116 완료**: Load Confirmation 서명 → `MilestoneStatus.M116 = COMPLETED`

### 4.3 Sail-away Protocol (M117)

M117 (Sail-away Approved) 승인 체인:

1. **ALS Marine Coordinator** → Sailing 준비 완료 확인 서명
2. **Marine Superintendent** → Stability 및 Safety 최종 검토
3. **Project Manager** → 최종 Sail-away 승인

승인 완료 후 출항 → `MilestoneStatus.M117 = COMPLETED`

### 4.4 Offshore Delivery Confirmation (M140)

| 단계 | 문서 | Milestone |
|---|---|---|
| LCT 접안·하역 | Offshore Unloading Report | M130 (Site Arrived) |
| 현장 수령 검수 | Offshore GRN (Goods Receipt Note) | M131 (Inspected Good) |
| POD 서명 | POD (Proof of Delivery) | M140 완료 조건 |
| GRN 등록 | GRN 시스템 등록 | M140 완료 조건 |

### 4.5 Heavy Lift / OOG Special Procedures (Transformer)

변압기 및 OOG(Out-of-Gauge) 중량물 취급 특수 절차:

| 항목 | 요건 |
|---|---|
| **Center of Gravity** | 제조사 제공 COG 도면 기준; Lift Plan에 명시 |
| **Lashing Pattern** | 승인된 Lashing Calculation (체인 SWL, 각도 계산 포함) |
| **Crane SWL** | 화물 중량의 최소 1.25배 이상 SWL 확보 |
| **Tailing Requirement** | 80t 초과 변압기: Tailing Crane 병행 사용 필수 |
| **Transport Route Survey** | 도로 하중·교량·진입로 치수 사전 조사 (Route Survey Report) |
| **AGI/DAS 해상 운송** | MOSB → LCT 적재 시 MAX_CONTAINER_PRESSURE ≤ 4.0 t/m² 재검증 필수 |

> **참조**: Marine/Bulk 상세 → [`CONSOLIDATED-04`](CONSOLIDATED-04-barge-bulk-cargo.md)

---

## Section 5: Site Receiving & Inspection (M130~M140) {#section-5}

> **Milestones**: M130 (Site Arrived) → M131/M132 (Inspected Good/OSD) → M140 (POD/GRN/Handover)
>
> **Documents**: MRR, MRI, ITP, MAR, MRS, MIS, POD, GRN, OSDR
>
> **참조**: SiteReceipt 클래스 → `CONSOLIDATED-00` Part 4.

### 5.1 Site Documents

| Document | Code | Trigger Milestone | Owner |
|---|---|---|---|
| Material Receipt Report | **MRR** | M130 (Site Arrived) | SCT / Site Logistics |
| Material Receipt Inspection | **MRI** | M131 / M132 | QA/QC + OE |
| Inspection Test Plan | **ITP** | Pre-M130 (사전 수립) | QA/QC |
| Material Acceptance Record | **MAR** | M131 (Inspected Good) | QA/QC |
| OverShortDamage Report | **OSDR** | M132 (Inspected OSD) | Site Logistics + QA |
| Material Requisition Slip | **MRS** | M140 (불출 요청) | Sub-Contractor |
| Material Issue Slip | **MIS** | M140 (불출 실행) | Site Logistics |
| Proof of Delivery | **POD** | M140 (수령 확인) | Sub-Contractor |
| Goods Receipt Note | **GRN** | M140 (시스템 등록) | Site Logistics / ERP |

### 5.2 Inspection Classification

**Good (M131)**: 수량·품질 모두 이상 없음 → MAR 발행 → M140 진행 가능.

**OSD (M132)** — 4가지 유형:

| OSD 유형 | 정의 | 허용 공차 | 조치 |
|---|---|---|---|
| **Shortage** | 실수량 < 서류 수량 | 0% (전량 일치 원칙) | OSDR 발행, 공급사 클레임 |
| **Damage** | 포장 손상 또는 물리적 파손 | 없음 (모두 보고) | OSDR + 사진 첨부, NCR 개시 |
| **Over-delivery** | 실수량 > 서류 수량 | 수량의 5% 이내 수용 | 초과분 격리, 공급사 확인 |
| **Wrong Item** | 품목 코드/규격 불일치 | 0% | OSDR, 반환 또는 대체 요청 |

### 5.3 NCR / Claim Lifecycle

OSDR 발생 시 NCR (Non-Conformance Report) 프로세스 개시:

1. **Report** (M150): NCR 번호 발행, OSDR 첨부, 사진·계측 기록 포함
2. **Root Cause**: 공급사·운송사·현장 각 영역에서 원인 분석
3. **Supplier Response**: 공급사 30일 이내 원인 분석 및 시정 계획 제출
4. **Resolution**: 대체 자재 공급 / 수량 보정 / 금액 공제 중 선택
5. **Close** (M160): 해결 확인 서명 → `ClaimStatus = CLOSED`

> NCR 추적 대시보드: 단계별 경과 일수 모니터링, 30일 초과 시 에스컬레이션.

### 5.4 Physical Count & Stock Reconciliation

| 유형 | 주기 | 대상 | 결과 처리 |
|---|---|---|---|
| **Cycle Count** | 월 1회 (A-class 자재 우선) | 고가·고위험 자재 순환 점검 | 오차 발견 시 즉시 조정 |
| **Full Count** | 분기 1회 또는 공정 마일스톤 시 | 전체 사이트 재고 | 재고 원장 vs 실물 전수 대조 |

**조정 절차**:
1. MRR 기준 입고 수량 합계 vs WH Dispatch 기록 합계 대조
2. 차이 발생 시 OSDR 이력, 반환 기록 확인
3. 조정 내역 Reconciliation Form 작성, Site Manager 서명
4. ERP 재고 원장 업데이트 → `GRN.reconciledStatus = CONFIRMED`

---
