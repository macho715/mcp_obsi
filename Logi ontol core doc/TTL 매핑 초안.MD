**Verdict**

PARTIAL

**Done**

- 최종 클래스 묶음은 승인됐습니다.
- 이제 `속성 목록 + 식별자 규칙 + xlsx별 매핑` 초안을 제시합니다.

**Partial**

쉽게 말하면,  
이제부터는 `ID는 source key에서 고정`, `속성은 class별로 최소 핵심만`, `엑셀 파일마다 역할을 분리`하는 방식으로 갑니다.

## Section: 속성 목록 + 식별자 규칙 + xlsx 매핑

### 1. 식별자 규칙

**공통 원칙**

- 모든 URI는 deterministic해야 합니다.
- 같은 source row를 다시 읽어도 같은 ID가 나와야 합니다.
- 사람이 읽을 수 있는 key를 우선 사용합니다.
- event는 시간축이 들어가므로 entity보다 더 구체적인 key를 씁니다.

### 1.1 Core URI 패턴

- `Shipment`
  - `shipment/{sct_ship_no}`
- `Case`
  - `case/{sct_ship_no}/{case_no}`
- `CargoItem`
  - `cargo/{sct_ship_no}/{case_no}/{item_or_pkg}`
- `PortLocation`
  - `port/{normalized_name}`
- `HubLocation`
  - `hub/{normalized_name}`
- `WarehouseLocation`
  - `warehouse/{normalized_name}`
- `SiteLocation`
  - `site/{normalized_name}`
- `OperationalLocation`
  - `oploc/{parent}/{normalized_name}`
- `OperationCarrier`
  - `carrier/{normalized_name}`
- `LCTOperation`
  - `lct-op/{carrier}/{normalized_voyage_or_batch}/{date}`
- `PortCall`
  - `portcall/{carrier}/{location}/{datetime}`
- `TransportDocument`
  - `doc/{doc_type}/{normalized_ref}`
- `Invoice`
  - `invoice/{invoice_no}`
- `ChargeSummary`
  - `charge/{invoice_no}/{charge_type}`
- `SettlementRecord`
  - `settlement/{invoice_no}`
- `ReconciliationRecord`
  - `recon/{normalized_voyage_id}`
- `IncidentLesson`
  - `lesson/{group_slug}/{date}/{sequence}`
- `GroupGuide`
  - `guide/{group_slug}`
- `CommunicationEvidence`
  - `evidence/{group_slug}/{date}/{window_hash}`

### 1.2 Event ID 규칙

- `ArrivalEvent`
  - `arrival/{subject_id}/{location}/{date}`
- `DepartureEvent`
  - `departure/{subject_id}/{location}/{date}`
- `StorageEvent`
  - `storage/{case_or_shipment}/{warehouse}/{date}`
- `TransferEvent`
  - `transfer/{subject_id}/{from}_{to}/{date}`
- `CargoHandlingEvent`
  - `handling/{carrier_or_site}/{cargo_type}/{date}`
- `IssueEvent`
  - `issue/{group_or_context}/{date}/{slug}`
- `InspectionEvent`
  - `inspection/{subject_id}/{location}/{date}`
- `DetentionEvent`
  - `detention/{subject_id}/{location}/{date}`

가정:
- 날짜가 없으면 event를 임의 생성하지 않습니다.
- 날짜가 불완전하면 `date_unknown` 같은 속성으로 우회하지 말고 별도 정책을 둡니다.

---

### 2. 클래스별 핵심 속성

### 2.1 Shipment
- `shipmentNo`
- `commercialInvoiceNo`
- `invoiceDate`
- `vendorName`
- `category`
- `mainDescription`
- `subDescription`
- `incoterms`
- `currency`
- `invoiceValue`
- `freightValue`
- `insuranceValue`
- `cifValue`
- `pol`
- `pod`
- `blOrAwbNo`
- `currentStatus`

### 2.2 Case
- `caseNo`
- `shipmentNo`
- `site`
- `eqNo`
- `pkgCount`
- `storageCode`
- `description`
- `lengthCm`
- `widthCm`
- `heightCm`
- `cbm`
- `netWeightKg`
- `grossWeightKg`
- `stackable`
- `hsCode`
- `price`
- `vesselName`
- `etaAta`
- `etdAtd`

### 2.3 Location
공통 최소 속성:
- `locationCode`
- `locationName`
- `locationType`
- `parentLocation`
- `isOperationalLocation`

운영 장소 subtype 예:
- `Jetty`
- `AnchorageArea`
- `YardArea`
- `GateArea`

### 2.4 OperationCarrier
- `carrierName`
- `carrierType`
- `charterer`
- `opsArea`
- `callToPort`
- `crewPax`
- `vesselFlag`
- `operatingStatus`

### 2.5 LCTOperation
- `voyageNo`
- `loadingDate`
- `subContractor`
- `cargoDescription`
- `sizeSpec`
- `deliveryQtyTon`
- `operationStatus`
- `eta`
- `etd`
- `startDateTime`
- `endDateTime`

### 2.6 PortCall
- `callLocation`
- `callType`
- `arrivalTime`
- `departureTime`
- `berthStatus`
- `tideCondition`
- `weatherCondition`

### 2.7 TransportDocument
- `documentType`
- `documentRef`
- `documentDate`
- `issuedBy`
- `documentStatus`

### 2.8 Invoice / Settlement
- `invoiceNo`
- `invoiceDate`
- `amount`
- `vat`
- `grossTotal`
- `currency`
- `chargeType`
- `matchStatus`
- `mismatchFlag`
- `notes`

### 2.9 IncidentLesson
- `incidentTitle`
- `groupName`
- `incidentDate`
- `issueType`
- `rootCause`
- `actionTaken`
- `lessonLearned`
- `severity`
- `relatedPattern`

### 2.10 GroupGuide
- `groupName`
- `groupType`
- `scope`
- `ssotRule`
- `reportingWindow`
- `escalationRule`
- `documentAuthority`
- `version`

---

### 3. xlsx별 매핑 원칙

## 3.1 `HVDC STATUS.xlsx`
역할: **Shipment spine + 문서 메타데이터 + route event source**

주요 매핑:

- `SCT SHIP NO.` -> `Shipment.shipmentNo`
- `COMMERCIAL INVOICE No.` -> `Shipment.commercialInvoiceNo`
- `PO No.` -> `TransportDocument` 또는 `Shipment` 문서 속성
- `VENDOR` -> `Shipment.vendorName`
- `CATEGORY` -> `Shipment.category`
- `MAIN DESCRIPTION (PO)` -> `Shipment.mainDescription`
- `SUB DESCRIPTION` -> `Shipment.subDescription`
- `COE` / `POL` / `POD` -> `TransportDocument` + `Location`
- `B/L No./ AWB No.` -> `TransportDocument`
- `VESSEL NAME/ FLIGHT No.` -> `OperationCarrier` 또는 shipment-linked carrier ref
- `MOSB`, `SHU`, `MIR`, `DAS`, `AGI`, warehouse date columns -> `ArrivalEvent` / `StorageEvent` / `TransferEvent`

핵심 역할:
- shipment identity의 기준 파일
- route chronology의 1차 기준 파일

## 3.2 `HVDC WAREHOUSE STATUS.xlsx`
역할: **Case layer + warehouse/state tracking**

주요 매핑:

- `SCT SHIP NO.` -> `Shipment`
- `Case No.` -> `Case.caseNo`
- `Pkg` -> `Case.pkgCount`
- `Storage` -> `WarehouseLocation` 또는 storage code
- `Site` -> `SiteLocation`
- `Description` -> `Case.description`
- `L/W/H`, `CBM`, `N.W`, `G.W` -> `Case` physical attributes
- `HS Code` -> `Case.hsCode`
- `Vessel` -> linked `OperationCarrier`
- `COE`, `POL`, `POD` -> document/location ref
- `ETA/ATA`, `ETD/ATD` -> case-linked event timestamps

핵심 역할:
- shipment 밑의 실제 추적 단위는 case라는 점을 보장
- 창고/yard/site 상태를 case 기준으로 연결

## 3.3 `JPT-reconciled_v6.0.xlsx`
역할: **LCT operation carrier layer + reconciliation layer**

시트별 권장 매핑:

- `1_Decklog`
  - `OperationCarrier`
  - `PortCall`
  - `CargoHandlingEvent`
  - `BunkeringEvent`
  - `FreshWaterSupplyEvent`
  - `Weather/Tide` context
- `3_Voyage_Master`
  - `LCTOperation`
  - cargo manifest summary
- `4_Voyage_Rollup`
  - normalized `LCTOperation` summary
- `6_Reconciliation`
  - `ReconciliationRecord`
  - `SettlementRecord`
- `7_Exceptions`
  - reconciliation exception / mismatch incident
- `8_Decklog_Context`
  - monthly carrier context snapshot

핵심 역할:
- JPT는 일반 voyage 보조가 아니라 LCT 운영 사실의 원천
- `CONSOLIDATED-04` marine 의미와 맞춰야 함

## 3.4 `HVDC Logistics cost(inland,domestic).xlsx`
역할: **inland/domestic 정산 레이어**

주요 매핑:

- `Invoice No` -> `Invoice.invoiceNo`
- `Invoice Date` -> `Invoice.invoiceDate`
- `Shipment No` -> `Shipment`
- `Job Description` -> `CostAttribution` 보조 근거
- `Inland`, `THC`, `Inspection`, `Detention`, `Storage`, `Others` -> `ChargeSummary`
- `TOTAL`, `VAT`, `G. TOTAL` -> `Invoice`
- 가능한 경우:
  - `Inland` -> `TransferEvent`
  - `Storage` -> `StorageEvent`
  - `Detention` -> `DetentionEvent`
  - `Inspection` -> `InspectionEvent`

핵심 역할:
- 비용을 shipment에만 묶지 않고 event/location에도 연결

---

### 4. WhatsApp / analyses 매핑 원칙

- `guideline_*.md` -> `GroupGuide`
- `logistics_issue_*.md` -> `IncidentLesson`
- raw chat excerpt -> `CommunicationEvidence`
- GUIDE 규칙 항목 -> `OperatingRule`, `ReportingRule`, `EscalationRule`
- 반복 문제 묶음 -> `RecurringPattern`

즉,
- wiki는 사람이 읽는 handbook/lesson
- ontology는 구조화된 rule/incident/evidence 링크

---

### 5. 추가 아이디어

1. `StatusSnapshot`를 따로 두기
- 최신 상태를 빠르게 읽는 데 유용
- event를 다 읽지 않아도 현재 상태를 보여줄 수 있음

2. `Attribution confidence`
- 비용이나 incident를 shipment/event/location에 연결할 때 confidence score를 둠
- 나중에 자동 추론과 수동 검토를 구분 가능

3. `Source precedence`
- 같은 사실이 여러 source에 나오면 우선순위를 명시
- 예:
  - route fact: `HVDC STATUS.xlsx`
  - case fact: `HVDC WAREHOUSE STATUS.xlsx`
  - LCT operation fact: `JPT-reconciled_v6.0.xlsx`
  - lesson/rule: `wiki/analyses`

**Not done**

- TTL property 명세를 RDF predicate 수준으로 확정
- namespace 설계
- compatibility mapping 표 상세화
- TTL 설계 문서 작성

**Evidence**

changed files:
- 없음

generated files:
- 없음

test names:
- 없음

execution path or command:
- 사용한 source 기준:
  - [HVDC STATUS.xlsx](C:/Users/jichu/Downloads/mcp_obsidian/Logi%20ontol%20core%20doc/HVDC%20STATUS.xlsx)
  - [HVDC WAREHOUSE STATUS.xlsx](C:/Users/jichu/Downloads/mcp_obsidian/Logi%20ontol%20core%20doc/HVDC%20WAREHOUSE%20STATUS.xlsx)
  - [JPT-reconciled_v6.0.xlsx](C:/Users/jichu/Downloads/mcp_obsidian/Logi%20ontol%20core%20doc/JPT-reconciled_v6.0.xlsx)
  - [HVDC Logistics cost(inland,domestic).xlsx](C:/Users/jichu/Downloads/mcp_obsidian/Logi%20ontol%20core%20doc/HVDC%20Logistics%20cost(inland,domestic).xlsx)
  - [analyses](C:/Users/jichu/Downloads/valut/wiki/analyses)

one-line result summary:
- 새 TTL은 source별 역할을 분리해서 `Shipment / Case / Event / LCT Ops / Cost / Lesson`을 각기 다른 입력 규칙으로 받아들이는 구조가 가장 적합합니다.

**Risks**

- event ID 규칙이 너무 느슨하면 중복 event가 생깁니다.
- 비용 attribution을 자동으로만 처리하면 오분류가 누적될 수 있습니다.

**Next action**

- 이 Section이 맞는지 승인해 주십시오. 승인되면 다음으로 `RDF predicate 이름 + namespace + 호환 매핑 원칙`을 설계하겠습니다.