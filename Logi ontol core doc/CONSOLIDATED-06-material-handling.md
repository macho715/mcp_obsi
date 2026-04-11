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

---

## Section 2: Customs & Port Stage (M40~M100) {#section-2}

> **Milestones**: M40 (Export Cleared) → M50 (Terminal Received) → M60/M61 (Loaded/ATD)
> → M80 (ATA) → M90/M91 (BOE Submitted/Cleared) → M92 (DO Released) → M100 (Gate-out)
>
> **참조**: Milestone 정의 `CONSOLIDATED-00` Part 1 §1.5. CustomsEntry 클래스 `CONSOLIDATED-00` Part 4.

_[이 섹션은 기존 CONSOLIDATED-06 v1.1의 Customs Clearance 및 Port Operations 내용을 RoutingPattern 기반으로 재작성 예정. 원본: `CONSOLIDATED-06-material-handling.bak.md` Section "Customs Clearance"]_

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

_[이 섹션은 기존 v1.1의 Storage & Inland Transportation 및 Warehouse Operations 내용을 RoutingPattern + Milestone 기반으로 재작성 예정. 원본: `CONSOLIDATED-06-material-handling.bak.md`]_

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

_[이 섹션은 기존 v1.1의 Offshore Marine Transportation, Transformer Handling, Bulk Cargo 내용을 재작성 예정. 원본: `CONSOLIDATED-06-material-handling.bak.md`]_

---

## Section 5: Site Receiving & Inspection (M130~M140) {#section-5}

> **Milestones**: M130 (Site Arrived) → M131/M132 (Inspected Good/OSD) → M140 (POD/GRN/Handover)
>
> **Documents**: MRR, MRI, ITP, MAR, MRS, MIS, POD, GRN, OSDR
>
> **참조**: SiteReceipt 클래스 → `CONSOLIDATED-00` Part 4.

_[이 섹션은 기존 v1.1의 Site Receiving 내용 보존 예정. 원본: `CONSOLIDATED-06-material-handling.bak.md`]_

---
