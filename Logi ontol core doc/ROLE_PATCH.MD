문서 전체를 직접 검토했습니다. 결론은 명확합니다. 지금 문서군은 **HVDC 전체 물류 체인**을 보려는 방향은 맞지만, 실제 설계에서는 **Flow Code가 항만·문서·비용·해상·현장까지 확장 사용**되고 있어, 사용자가 지정한 원칙인 **“Flow Code = Warehouse 전용 용어”**와 정면으로 충돌합니다. 따라서 상위 온톨로지는 **Journey Stage / Route Type / Milestone / Leg** 중심으로 재구성하고, **Flow Code는 Warehouse Handling 하위 모델로만 격리**해야 합니다. 이 수정이 들어가야 “UNIT 기준으로 ETA, HVDC CODE, Vendor 등 아무 키로 조회해도 전체가 이어지는 KG”가 논리적으로 완성됩니다.  

좋은 점도 분명합니다. 이미 문서들 안에는 **program-wide visibility**, **multi-key identity graph**, **RDF/OWL/SHACL/SPARQL**, **Excel→RDF mapping**, **document/cost/communication evidence layer**의 재료가 대부분 들어 있습니다. 즉, 새로 처음부터 만들 문제는 아니고, **상위 개념 계층을 다시 정렬하는 편집/거버넌스 작업**이 핵심입니다.    

## 핵심 판정

| 항목               | 현재 상태         |  판정 | 필요한 조치                  |
| ---------------- | ------------- | --: | ----------------------- |
| 전체 물류 관점         | 있음            |  적합 | 유지                      |
| Flow Code 범위     | 과도하게 확장됨      | 부적합 | Warehouse 전용으로 축소       |
| 단계 용어            | 문서별 제각각       | 부적합 | 표준 Stage 용어로 통일         |
| Multi-key KG     | 골격 존재         |  적합 | Master graph로 통합        |
| UNIT 단위 조회       | 부분 가능         | 미완성 | ShipmentUnit 중심 SSOT 필요 |
| MOSB 분류          | Warehouse와 혼재 | 부적합 | Offshore Staging로 분리    |
| 문서/OCR/Cost와의 연결 | 있음            |  적합 | “증거 레이어”로만 사용           |

## 지금 문서에서 가장 큰 충돌

가장 중요한 기준 문서는 `AGENTS.md`입니다. 여기서는 이 제품을 **warehouse dashboard가 아니라 program-wide HVDC logistics control tower**로 정의하고, 기본 체인을 **Origin → Port / Air Entry → Customs → Warehouse → MOSB / Offshore Leg → Site Delivery**로 유지하라고 요구합니다. 또한 public language는 `route_type`, `current stage`, `next stage`, `site arrival` 같은 **전체 물류 체인 용어**를 우선하라고 명시합니다. 동시에 Flow Code는 **WAREHOUSE 입고(WH In) 기준의 분류**로 다뤄야 한다고 규정합니다.   

그런데 현재 업로드된 문서들은 이 규칙을 여러 곳에서 깨고 있습니다. `CONSOLIDATED-07-port-operations.md`는 **항만이 Flow Code의 출발점이며 port clearance 시점에 Flow Code를 부여한다**고 서술하고, `CONSOLIDATED-03-document-ocr.md`는 BOL/Invoice/Packing List/Customs Declaration에서 **Flow Code를 추출·검증하는 문서 속성**으로 다룹니다. `CONSOLIDATED-05-invoice-cost.md`는 **Flow Code를 직접 비용 구조의 기준**으로 쓰고, `CONSOLIDATED-06-material-handling.md`와 `CONSOLIDATED-04-barge-bulk-cargo.md`는 **전체 물류 경로와 offshore routing 자체를 Flow Code로 기술**합니다. 이 다섯 문서의 현재 표현은 모두 warehouse-only rule과 충돌합니다.      

또 하나의 구조 충돌은 **MOSB의 정체성**입니다. 상위 체인에서는 Warehouse와 MOSB/Offshore Leg가 분리되어 있는데, mapping guide는 `MOSB`를 `Outdoor` warehouse classification 안에 넣고 있고, warehouse ontology는 MOSB를 “특수 창고성 노드”처럼 취급합니다. 프로그램 전체 관점에서는 MOSB를 **Warehouse가 아니라 Offshore Staging / Marine Interface Node**로 분리해야 용어가 깨끗해집니다. 물리적으로 야드 기능이 있어도, 상위 온톨로지 역할은 warehouse가 아니라 **offshore staging hub**입니다.   

세부적으로는 `AGENTS.md` 안에도 미세한 문구 충돌이 있습니다. 한쪽에서는 “Flow Code는 WH In event 기준”이라고 하고, 동시에 `Flow 1 = Port → Site 직송`을 둡니다. 그래서 정의 문장을 더 정확하게 고쳐야 합니다. 즉, **Flow Code는 warehouse-handling classification**이며, `Flow 0 = pre-arrival`, `Flow 1 = warehouse bypass confirmed`, `Flow 2~5 = warehouse/movement evidence 기반 pattern`으로 재정의하면 문서 전체가 닫힙니다. 이 수정은 개념을 바꾸는 것이 아니라, 현재 문구의 논리 모순을 제거하는 정리입니다. 

## 문서 전반에 삽입해야 할 마스터 규칙

아래 4줄은 모든 consolidated 문서 상단에 공통으로 들어가야 합니다.

```text
MASTER GOVERNANCE RULE
1. Flow Code is a warehouse-handling classification only.
2. Program-wide shipment visibility shall use Journey Stage, Route Type, Milestone, and Leg.
3. Port, Customs, Document, Cost, Marine, and Communication domains may reference warehouse-flow evidence, but shall not own or assign Flow Code as their primary language.
4. MOSB is an Offshore Staging / Marine Interface Node, not a Warehouse in the top-level logistics ontology.
```

이 규칙은 현재 AGENTS의 full-chain 요구사항, public stage language 규칙, warehouse-only Flow Code rule을 하나로 묶은 상위 선언문입니다.   

## 문서별 수정 방향

| 문서                                     | 현재 문제                                 | 수정 방향                                                                   |
| -------------------------------------- | ------------------------------------- | ----------------------------------------------------------------------- |
| `CONSOLIDATED-07-port-operations.md`   | Port가 Flow Code를 assign한다고 서술         | `plannedRouteType`, `declaredDestination`, `offshoreRequired`로 교체       |
| `CONSOLIDATED-03-document-ocr.md`      | 문서에서 Flow Code를 직접 추출/검증              | `warehouse-flow evidence`, `route evidence`, `destination evidence`로 교체 |
| `CONSOLIDATED-05-invoice-cost.md`      | 비용 분석을 Flow Code 중심으로 설명              | `route_type + warehouse_handling + MOSB_leg + marine_leg`로 분리           |
| `CONSOLIDATED-06-material-handling.md` | 전체 물류 단계에 Flow Code 적용                | `Journey Stage`와 `Movement Pattern`으로 교체                                |
| `CONSOLIDATED-04-barge-bulk-cargo.md`  | offshore routing을 Flow Code로 서술       | `Offshore Delivery Pattern`, `MOSB Route Pattern`으로 교체                  |
| `HVDC_MAPPING_SYSTEM_GUIDE.md`         | ontology 명칭이 warehouse 편향, MOSB 분류 혼재 | 이름을 `HVDC Logistics Knowledge Graph Ontology`로 변경, MOSB 분리              |
| communication TTL / docs               | event/message 계층에 Flow 개념이 스며듦        | communication은 evidence/action layer로만 유지                               |

특히 mapping guide의 TTL header가 아직 **“HVDC Full Data Warehouse Ontology”**로 잡혀 있는데, 사용자가 요구한 최종 목적은 warehouse ontology가 아니라 **HVDC Logistics Knowledge Graph**입니다. 제목부터 바꿔야 문서 철학이 정리됩니다.  

## 단계 용어는 이렇게 통일하는 것이 맞습니다

업계 표준 벤치마크를 보면, 상위 물류 모델은 **event / phase / leg / visibility** 중심으로 설계하는 것이 일반적입니다. GS1 EPCIS/CBV는 공급망 가시성을 위해 `what / where / when / why / how`를 event로 표현하고, DCSA Track & Trace는 shipment phase를 표준화하며, IATA ONE Record는 end-to-end digital logistics chain을 지향합니다. UN/CEFACT의 reference data model 계열도 상위 모델을 domain-specific code가 아니라 reference data와 business event 중심으로 정리합니다. 이 기준을 따르면 귀 문서의 상위 용어는 Flow Code가 아니라 **Journey Stage와 Route Type**이 되어야 합니다. ([GS1 Reference][1])

권장 단계 용어는 아래처럼 정리하면 됩니다.

| 단계 | 표준 권장 용어                               | 비고                                  |
| -- | -------------------------------------- | ----------------------------------- |
| 1  | Planning / Pre-Arrival                 | 출발 전, 예약, 문서 준비                     |
| 2  | Origin Dispatch / Main Carriage        | 해외/국내 출발 운송                         |
| 3  | Port / Air Entry                       | UAE 진입                              |
| 4  | Terminal Handling                      | Port handling, berth, gate, release |
| 5  | Import Customs Clearance               | eDAS, BL endorse, declaration, duty |
| 6  | Inland Haulage                         | Port/terminal to next node          |
| 7  | Warehouse Receipt (WH In)              | 여기서 warehouse evidence 발생           |
| 8  | Storage / Preservation                 | 온습도, laydown, stock snapshot        |
| 9  | Warehouse Dispatch (WH Out)            | 출고                                  |
| 10 | MOSB / Offshore Staging                | MOSB staging, pre-load prep         |
| 11 | Offshore Marine Transport              | LCT / barge leg                     |
| 12 | Site Receiving & Inspection            | MRR/MRI/ITP/MAR/OSDR                |
| 13 | Site Storage / Laydown / Preservation  | 현장 보관                               |
| 14 | Material Issue / Installation Support  | MIS, issue to construction          |
| 15 | Return / Reverse Logistics / Close-out | 반출, 회수, close-out                   |

이 표는 AGENTS의 public language rule과 full-chain contract에도 맞습니다. `Origin`, `Port / Air Entry`, `Customs`, `Warehouse`, `MOSB / Offshore`, `Site Delivery`, `route_type`, `current stage`, `next stage`가 상위 표현으로 우선되어야 한다는 점이 이미 내부 기준에 들어 있습니다. 

## Flow Code는 이렇게 좁혀야 합니다

Flow Code는 상위 journey language가 아니라 아래 **warehouse submodel**로만 남겨야 합니다.

| Flow Code | 새 해석                                           | 소유 레이어                   |
| --------- | ---------------------------------------------- | ------------------------ |
| 0         | Pre-Arrival / No WH evidence yet               | WarehouseHandlingProfile |
| 1         | Warehouse bypass confirmed                     | WarehouseHandlingProfile |
| 2         | Single warehouse handling pattern              | WarehouseHandlingProfile |
| 3         | Warehouse-linked offshore pattern              | WarehouseHandlingProfile |
| 4         | Multi-warehouse + offshore pattern             | WarehouseHandlingProfile |
| 5         | Mixed / pending / unresolved warehouse pattern | WarehouseHandlingProfile |

즉, **Port**, **Customs**, **Document**, **Cost**, **Marine**, **Communication** 문서는 Flow Code를 primary noun으로 쓰면 안 됩니다. 그 대신 각 레이어는 다음처럼 표현하면 됩니다.

* Port: `plannedRouteType`, `declaredDestination`, `offshoreRequired`
* Document/OCR: `destinationEvidence`, `routeEvidence`, `warehouseFlowEvidence`
* Cost: `costByRouteType`, `costByWarehouseHandlingProfile`
* Marine/Bulk: `offshoreDeliveryPattern`, `MOSBStagingPattern`
* Communication: `shipmentTag`, `ETA`, `GATE`, `CRANE`, `ACTION`

## 최종 목표 KG는 이렇게 설계해야 합니다

현재 문서들이 이미 말하고 있는 핵심은 **multi-key identity graph**입니다. Port Ops는 `InvoiceNo / RotationNo / SamsungRef / HVDCCode / Vessel+ETA`로 클러스터링을 제안하고 있고, Invoice/Cost는 `BL / Container / DO / Invoice / Case / Booking / ShipmentID / hvdc_code`를 아무 키나 받아 cascade 하겠다고 하며, Communication은 message/thread/tag를 asset/site/cargo/approval에 연결합니다. 이 세 가지를 합치면 정답은 하나입니다. **중심 클래스는 ShipmentUnit**이어야 합니다.   

권장 마스터 구조는 아래입니다.

```text
IdentityKey
  └─ resolvesTo → Shipment / ShipmentUnit / Package / Container / Document

Shipment
  └─ hasUnit → ShipmentUnit

ShipmentUnit
  ├─ hasKey → IdentityKey
  ├─ hasVendor → Organization
  ├─ hasOrigin / hasDestinationSite / hasCurrentLocation
  ├─ hasCurrentStage / hasNextStage / hasRouteType
  ├─ hasPlannedETA / hasActualATA / hasMilestone
  ├─ hasJourneyLeg → JourneyLeg
  ├─ hasJourneyEvent → JourneyEvent
  ├─ hasWarehouseHandlingProfile → WarehouseHandlingProfile   # Flow Code only here
  ├─ hasDocument → Document
  ├─ hasCostItem → CostItem
  ├─ hasCommunicationEvent → CommunicationEvent
  └─ hasComplianceCase → ComplianceCase
```

여기서 `WarehouseHandlingProfile`만 Flow Code를 가집니다.

```text
WarehouseHandlingProfile
  ├─ confirmedFlowCode
  ├─ whInboundCount
  ├─ whOutboundCount
  ├─ flowConfirmationStatus
  ├─ flowEvidenceSource
  └─ warehouseDwellDays
```

이렇게 나누면 사용자가 원하는 조회가 자연스럽게 됩니다.

| 입력 키                 | 해석 방식                              | 반환 결과                                            |
| -------------------- | ---------------------------------- | ------------------------------------------------ |
| UNIT No              | ShipmentUnit 직접 조회                 | ETA, current stage, vendor, docs, cost, messages |
| HVDC CODE            | IdentityKey → ShipmentUnit resolve | 전체 이력 연결                                         |
| SCT SHIP NO          | Shipment → Units                   | shipment-level/ unit-level 동시 조회                 |
| Packing No / Case No | Package / Case → ShipmentUnit      | package traceability                             |
| BL / AWB             | Document → related units           | port/customs/doc linkage                         |
| Rotation No          | PortCall → related shipment units  | vessel-port chain                                |
| Vendor + ETA window  | Organization + time filter         | 도착예정 unit 목록                                     |

사용자의 “UNIT별로 ETA, HVDC CODE, Vendor 등을 호출하면 전체가 이어져야 한다”는 요구는 바로 이 구조를 말합니다. 그리고 이 구조는 AGENTS가 요구하는 **timeline-first history lookup**과도 정확히 맞습니다. 현재 위치, 다음 단계, milestone history, dwell, site arrival을 모두 fact-first로 보여줘야 합니다. 점수화나 평가카드는 금지하는 것이 맞습니다.  

## 외부 벤치마크 기준의 추천 조합

식별자와 기준코드는 아래 조합이 가장 안정적입니다.

* **UN/LOCODE**: Port, airport, terminal, city-level international locations
* **GLN**: warehouse/site/office/facility/party location 식별
* **SSCC** 또는 내부 `UnitID`/`PackageID`: logistic unit 식별
* **PROV-O**: source, evidence, derived-from, validation provenance
* **OWL-Time**: ETA/ETD/ATA/ATD/milestone time model
* **SHACL**: KG validation
* **ORG**: vendor, carrier, consignee, operator, site team role
* **SKOS**: stage vocabulary / route_type / cargo category controlled terms
* **DQV**: source confidence, completeness, timeliness, granularity metadata

이는 W3C와 GS1, UN/CEFACT 계열이 각각 권장하는 역할 분담과 잘 맞습니다. GS1은 GLN/SSCC를 location/logistic unit 식별에 사용하고, W3C는 provenance/time/org/validation/vocabulary/quality 온톨로지를 각각 제공합니다. ([GS1 GO Customer Service Portal][2])

## 추천 아키텍처 3안

### 1안. 문서 패치형

현재 문서에서 Flow Code 관련 표현만 고쳐서 빠르게 맞추는 방식입니다.

* 장점: 가장 빠릅니다.
* 단점: 구조적 중복이 남습니다.
* 적합: 단기 자료 업데이트

### 2안. 이원화 표준형 — 권장

상위 `Journey Ontology`와 하위 `Warehouse Flow Ontology`를 분리합니다.

* 장점: 사용자의 요구와 내부 문서 충돌을 가장 깔끔하게 해소합니다.
* 단점: property rename과 SHACL refactor가 필요합니다.
* 적합: 자료 업데이트 + 시스템 확장 동시 추진

### 3안. 국제표준 정렬형

UNECE/GS1/DCSA/IATA 용어에 최대한 맞춰 canonical KG를 재구축합니다.

* 장점: 장기 확장성과 외부 연계성이 가장 좋습니다.
* 단점: 초기 정리 비용이 큽니다.
* 적합: SSOT, API, 외부 파트너 연계를 전제로 할 때

제 판단으로는 **2안이 최적**입니다. 내부 실무 표현을 살리면서도, 상위 레이어를 국제표준형 event/stage 모델로 끌어올릴 수 있기 때문입니다. EPCIS/DCSA/IATA ONE Record를 참고하면 상위는 phase/event, 하위는 domain-specific code로 두는 구성이 자연스럽습니다. ([GS1 Reference][1])

## 단계별 실행 가이드

### Prepare

Owner: PMT + Ontology owner + Data owner

* 모든 문서 상단에 Master Governance Rule 삽입
* `Flow Code`라는 말을 전수 검색하여 domain owner 재분류
* `HVDC Full Data Warehouse Ontology` 명칭 변경
* MOSB 분류를 Warehouse에서 Offshore Staging으로 분리
* stage vocabulary, route_type vocabulary, location master, organization master 확정

KPI:

* 문서 용어 충돌 0건
* Flow Code 비-warehouse 사용 0건
* controlled vocabulary coverage 100%

### Pilot

Owner: Logistics + Warehouse + Port + Document + Cost

파일럿 대상:

* Onshore 1건: MIR/SHU direct or via warehouse
* Offshore 1건: AGI/DAS via MOSB
* Invoice 1건
* PortCall 1건
* Communication thread 1건

검증:

* 키 1개로 찾은 unit이 다른 키로도 동일 cluster에 resolve 되는지
* current stage / current location / next stage / ETA / docs / costs / latest message까지 한 화면 또는 한 query로 이어지는지
* Flow Code가 `WarehouseHandlingProfile` 밖에 존재하지 않는지

KPI:

* key resolution precision ≥95%
* mandatory milestone completeness ≥90%
* current stage / next stage missing 0건

### Operate

Owner: Systems + PMT

* RDF ingest + SHACL validation + SPARQL/GraphQL query layer 운영
* Document/OCR, Port Ops, Cost, Communication을 evidence layer로 연결
* history lookup를 timeline-first로 고정
* vendor별 granularity metadata 추가

KPI:

* traceability query response SLA
* source confidence coverage 100%
* tentative vs confirmed state 구분율 100%

### Scale

Owner: Integration + Governance

* DCSA ocean milestone alignment
* IATA ONE Record alignment for air shipments
* UN/LOCODE, GLN, SSCC 확장
* KPI dashboard / SITREP / cost guard 자동 발행

KPI:

* full-chain visibility coverage ≥95%
* missing milestone note auto-detection 100%
* hardcoded business truth 0건

## 품질 안전장치

현재 운영지침의 ZERO 조건은 유지해야 합니다. OCR precision <90%, 정합불일치 >2%, 요율 초과 >5%, 필수 승인 미확보 시 즉시 중단하는 현재 규칙은 ontology 운영에도 그대로 들어가야 합니다. 그리고 여기에 아래 두 가지를 추가해야 합니다.

1. `Flow Code found outside WarehouseHandlingProfile` → **Violation**
2. `Destination = AGI/DAS and MOSB milestone missing` → **Violation**

기존 운영지침은 이미 KPI gate, ontology mapper, RDF 산출, SITREP, cost guard, change management를 갖고 있으므로, 이 둘만 더하면 KG governance가 훨씬 단단해집니다.  

## 최종 결론

귀하의 요구사항은 타당하고, 문서 전체 방향도 크게는 맞습니다. 다만 지금 상태는 **HVDC 전체 물류 요약 문서**이면서 동시에 **warehouse flow document**의 논리를 여러 도메인에 퍼뜨린 상태입니다. 그래서 핵심 수정은 “내용 추가”가 아니라 **개념 분리**입니다.

* 상위: `Shipment Journey / Stage / Route Type / Milestone / Leg`
* 하위: `Warehouse Handling Profile / Flow Code`
* 증거: `Document / Cost / Port / Communication / Compliance`
* 중심 키: `ShipmentUnit + Multi-Key Identity Graph`

이렇게 정리하면, 사용자가 `UNIT`, `HVDC CODE`, `Vendor`, `ETA`, `BL`, `Invoice`, `Rotation No` 어느 것으로 들어와도 결국 동일한 `ShipmentUnit` cluster로 resolve 되고, 거기서 **현재 위치, 다음 단계, 과거 이력, 문서, 비용, 승인, 통신 로그, warehouse flow**가 한 그래프로 이어집니다. 그때 비로소 이 문서는 “warehouse 설명서”가 아니라 **HVDC Logistics Knowledge Graph master specification**이 됩니다.

## TL;DR

전체 문서를 직접 확인한 결과, 현재 문서군은 HVDC를 창고 단위가 아니라 **전체 물류 체인**으로 보려는 큰 방향은 맞습니다. 내부 기준문서인 `AGENTS.md`도 이 시스템을 program-wide logistics control tower로 정의하고, `Origin → Port / Air Entry → Customs → Warehouse → MOSB / Offshore Leg → Site Delivery` 체인을 유지하라고 말합니다. 문제는 실제 consolidated 문서들에서 `Flow Code`가 warehouse submodel을 넘어 port, document OCR, invoice cost, material handling, barge/bulk까지 확장 사용되고 있다는 점입니다. 이 상태로는 사용자가 요구한 “Flow Code는 문서 전반에서 warehouse 전용 용어로만 사용” 원칙과 충돌합니다. 따라서 상위 온톨로지는 반드시 `Journey Stage`, `Route Type`, `Milestone`, `Leg` 중심으로 통일하고, `Flow Code`는 `WarehouseHandlingProfile` 안으로만 가둬야 합니다. Port는 `plannedRouteType`와 `declaredDestination`을 말해야지 Flow Code를 assign하면 안 되고, Document/OCR은 `warehouse-flow evidence`만 다뤄야 하며, Cost는 `route_type + warehouse_handling + MOSB_leg + marine_leg` 기준으로 풀어야 합니다. MOSB도 warehouse가 아니라 상위 모델에서는 `Offshore Staging / Marine Interface Node`로 분리해야 합니다. 좋은 점은 이미 문서 안에 multi-key identity graph, RDF/OWL/SHACL/SPARQL, Excel→RDF mapping, communication evidence, port/invoice linkage 등 KG의 핵심 재료가 거의 다 있다는 것입니다. 따라서 처음부터 새로 만드는 문제가 아니라, 상위 개념과 용어를 다시 정렬하는 것이 핵심입니다. 외부 벤치마크로도 GS1 EPCIS/CBV, DCSA Track & Trace, IATA ONE Record, UN/CEFACT RDM은 상위 공급망 모델을 event/phase/leg 중심으로 설계하고, W3C의 PROV-O/SHACL/OWL-Time/ORG/SKOS/DQV는 provenance·validation·time·organization·controlled vocabulary·data quality를 보강하는 방식이라, 귀하가 요구한 방향과 완전히 맞습니다. 최종적으로는 `ShipmentUnit`을 중심 클래스로 두고, `HVDC Code`, `Unit No`, `SCT SHIP NO`, `Packing No`, `BL`, `Invoice`, `Rotation No`, `Vendor`, `ETA` 등을 모두 `IdentityKey`로 연결한 뒤, 그 아래에 `JourneyEvent`, `JourneyLeg`, `Documen

t`, `CostItem`, `CommunicationEvent`, `ComplianceCase`, `WarehouseHandlingProfile`을 붙이면 됩니다. 그러면 어떤 키로 조회해도 전체 이력과 현재 상태, 다음 액션이 한 번에 이어지는 진짜 ontology knowledge graph가 완성됩니다.

[1]: https://ref.gs1.org/epcis/ "https://ref.gs1.org/epcis/"
[2]: https://support.gs1.org/support/solutions/articles/43000734241-how-do-i-use-a-global-location-number-to-identify-a-physical-location- "https://support.gs1.org/support/solutions/articles/43000734241-how-do-i-use-a-global-location-number-to-identify-a-physical-location-"
