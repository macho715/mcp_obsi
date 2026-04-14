**Verdict**

PARTIAL

**Done**

GUIDE 문서와 raw 그룹채팅 패턴을 확인했습니다.  
핵심은 WhatsApp이 단순 대화 로그가 아니라, 그룹마다 역할이 다른 **운영 채널 시스템**이라는 점입니다.

확인된 그룹 성격은 이렇게 나뉩니다.

- `Project Lightning`: 프로그램 전체 통합 상황실
- `Jopetwil 71 Group`: LCT 운항 통제방
- `DSV Delivery`: stuffing / gate / delivery 실행 통제방
- `Abu Dhabi / MIR / SHU`: site execution / receiving / gate / escort 방
- Master Policy: **email이 SSOT**, WhatsApp은 실행 알림, 예외 대응, 조정, escalation 레이어

**Partial**

이걸 ontology/TTL과 Obsidian wiki에 넣는 방식은 3안으로 정리됩니다.

| 옵션 | 설명 | 장점 | 단점 |
|---|---|---|---|
| A | WhatsApp은 wiki evidence로만 저장하고, ontology에는 파생된 issue/event만 넣음 | 단순함 | 그룹 역할과 액션 흐름이 ontology에 안 남음 |
| B | WhatsApp을 `운영 커뮤니케이션 레이어`로 설계해서, ontology에는 `Evidence + OperationalEvent + Action`을 넣고, wiki에는 그룹별 운영 handbook와 incident page를 둠 | ontology와 wiki를 같이 살릴 수 있어서 추천 | 설계 범위가 중간 이상 |
| C | 메시지 단위 conversation graph를 전부 ontology화 | 가장 자세함 | 너무 무겁고 운영용 TTL에는 과함 |

제 추천은 `B`입니다.

### 추천 아이디어

쉽게 말하면, WhatsApp은 새 TTL 안에서 “채팅 데이터”가 아니라 **운영 커뮤니케이션 레이어**로 들어가야 합니다.

#### 1. Ontology에 넣을 것
메시지 전체를 다 넣지 말고, 아래처럼 **파생된 운영 객체**만 넣습니다.

- `CommunicationEvidence`
  - 원문 채팅 로그 조각을 가리키는 증거
- `StatusUpdateEvent`
  - 선박 상태, unloading status, gate status, site readiness
- `ActionRequest`
  - “guide”, “arrange”, “share manifest”, “check gate pass” 같은 지시
- `EscalationEvent`
  - site room에서 control tower로 올라온 예외
- `ExceptionEvent`
  - `high tide`, `no gate pass`, `forklift late`, `manifest lag`, `damage`
- `CoordinationDecision`
  - 우선순위 결정, hold/release, route change, vessel/site priority
- `HandoverNotice`
  - captain 교체, focal 변경, group member 변경

즉, ontology에는 “무슨 말이 있었는가”보다  
**무슨 운영 사실과 액션이 생겼는가**를 남깁니다.

#### 2. Group 자체도 모델링
group을 그냥 텍스트로 두지 말고, 운영 타입으로 나눕니다.

- `ProgramControlGroup`
  - 예: `Project Lightning`
- `VesselOpsGroup`
  - 예: `Jopetwil 71 Group`
- `ExecutionControlGroup`
  - 예: `DSV Delivery`
- `SiteLogisticsGroup`
  - 예: `MIR`, `SHU`, `Abu Dhabi Logistics`

이렇게 두면 나중에 ontology 질의에서  
“이 이슈가 어느 그룹에서 처음 올라왔고, 어느 그룹에서 실행됐는가”를 볼 수 있습니다.

#### 3. Guide 문서도 TTL에 반영
GUIDE는 단순 첨부파일이 아니라 **운영 규칙 소스**로 다룹니다.

예:
- `email SSOT`
- `07:30 / 16:00 SITREP`
- `D-1 16:00 plan`
- `A-Frame = LB 우선`
- `high tide = risk escalation`
- `damage = photo or sketch + time + cause`

이 규칙은 ontology에서 아래처럼 들어갈 수 있습니다.

- `GroupOperatingRule`
- `ReportingWindowRule`
- `EscalationRule`
- `ExecutionConstraintRule`
- `DocumentAuthorityRule`

그러면 WhatsApp에서 나온 액션과 event를  
“어떤 그룹 규칙을 따랐는지 / 어겼는지”까지 연결할 수 있습니다.

#### 4. Obsidian wiki 구조 아이디어
wiki는 2층으로 나누는 게 좋습니다.

1. **그룹 handbook**
   - 그룹 목적
   - SSOT
   - 주요 참여자 역할
   - 반복 리스크
   - reporting / escalation / tagging rule
   - 대표 예외 패턴

2. **incident / lesson page**
   - raw chat evidence
   - issue summary
   - action timeline
   - decision
   - lesson learned
   - ontology node/event 링크

즉,
- ontology = 구조화된 사실
- wiki = 사람이 읽는 운영 지식과 근거

#### 5. 이 아이디어가 좋은 이유
- GUIDE 문서의 규칙이 죽지 않습니다.
- 그룹채팅의 산만한 텍스트를 event/action 단위로 올릴 수 있습니다.
- `Project Lightning ↔ Jopetwil 71 ↔ DSV Delivery ↔ site groups`의 흐름을 graph로 볼 수 있습니다.
- 나중에 `/scan`, `/main`, `/audit full` 같은 자동화도 ontology와 wiki 위에서 바로 얹을 수 있습니다.

### Section 1 초안

**WhatsApp Integration Layer**

- raw chat는 evidence로 저장
- group는 운영 채널 entity로 저장
- guide는 operating rule source로 저장
- ontology에는 `Evidence + Event + Action + Decision`만 올림
- wiki에는 `Group Handbook + Incident Page + Lesson Page`를 둠

**Not done**

- 클래스/속성 상세 설계
- 그룹별 taxonomy
- event/action extraction 규칙
- wiki 폴더 구조 상세안

**Evidence**

changed files:
- 없음

generated files:
- 없음

test names:
- 없음

execution path or command:
- 읽은 문서:
  - [00_WhatsApp_Group_Master_Policy.md](C:/Users/jichu/Downloads/mcp_obsidian/whatsapp%20groupchat/00_WhatsApp_Group_Master_Policy.md)
  - [Guideline_Jopetwil_71_Group.txt](C:/Users/jichu/Downloads/mcp_obsidian/whatsapp%20groupchat/Guideline_Jopetwil_71_Group.txt)
  - [Guideline_DSV_Delivery.txt](C:/Users/jichu/Downloads/mcp_obsidian/whatsapp%20groupchat/Guideline_DSV_Delivery.txt)
  - [Guideline_HVDC_Project_Lightning.txt](C:/Users/jichu/Downloads/mcp_obsidian/whatsapp%20groupchat/Guideline_HVDC_Project_Lightning.txt)
- 참조한 raw chat:
  - [대화 폴더](C:/Users/jichu/Downloads/mcp_obsidian/whatsapp%20groupchat/%EB%8C%80%ED%99%94)

one-line result summary:
- WhatsApp은 새 ontology에 “운영 커뮤니케이션 레이어”로 넣고, wiki에는 그룹 handbook와 incident knowledge로 분리하는 구성이 가장 적합합니다.

**Risks**

- 메시지 전체를 ontology에 넣으면 TTL이 너무 무거워집니다.
- GUIDE 규칙을 별도 레이어로 안 두면, group별 차이가 다시 텍스트 메모로만 남게 됩니다.

**Next action**

- 이 추천안이 맞는지 승인해 주십시오. 승인되면 바로 Section 2로 `WhatsApp 관련 클래스와 관계 목록`을 설계하겠습니다.

**Verdict**

PARTIAL

**Done**

- `Lesson Learned + Rule + Incident` 구조는 승인됐습니다.
- 이제 WhatsApp/analyses를 포함한 **최종 클래스 목록 초안**을 제시합니다.

**Partial**

쉽게 말하면, 새 TTL은 클래스를 7개 묶음으로 나누는 것이 가장 안정적입니다.

## Section: 최종 클래스 묶음

### 1. Shipment Spine
실제 물류 추적의 중심입니다.

- `Shipment`
- `Case`
- `CargoItem`  
  가정: `Case` 아래의 세부 품목을 일부 표현할 필요가 있을 때만 사용
- `DocumentRef`
- `StatusSnapshot`

핵심 관계:
- `Shipment hasCase Case`
- `Case containsCargoItem CargoItem`
- `Shipment hasDocumentRef DocumentRef`
- `Shipment hasStatusSnapshot StatusSnapshot`

### 2. Location Layer
핵심 장소와 운영 장소를 함께 담습니다.

- `PortLocation`
- `HubLocation`
- `WarehouseLocation`
- `SiteLocation`
- `OperationalLocation`
- `Jetty`
- `AnchorageArea`
- `YardArea`
- `GateArea`

핵심 관계:
- `OperationalLocation partOf SiteLocation|PortLocation|HubLocation`
- `Jetty partOf PortLocation|SiteLocation`
- `AnchorageArea associatedWith PortLocation|SiteLocation`

### 3. Event Layer
시간이 붙는 사실은 전부 event로 처리합니다.

- `RouteEvent`
- `ArrivalEvent`
- `DepartureEvent`
- `StorageEvent`
- `TransferEvent`
- `CargoHandlingEvent`
- `DeliveryEvent`
- `InspectionEvent`
- `DetentionEvent`
- `IssueEvent`

핵심 관계:
- `Shipment hasEvent Event`
- `Case hasEvent Event`
- `Event occurredAt Location`
- `Event hasStartTime xsd:dateTime`
- `Event hasEndTime xsd:dateTime`
- `Event relatesToShipment Shipment`
- `Event relatesToCase Case`

### 4. Marine / LCT Operations Layer
`JPT-reconciled_v6.0.xlsx`와 `CONSOLIDATED-04`를 받는 부분입니다.

- `OperationCarrier`
- `LCTOperation`
- `PortCall`
- `MarineLeg`
- `CargoManifest`
- `CarrierReadiness`
- `BunkeringEvent`
- `FreshWaterSupplyEvent`

핵심 관계:
- `OperationCarrier executes LCTOperation`
- `LCTOperation hasPortCall PortCall`
- `LCTOperation hasMarineLeg MarineLeg`
- `LCTOperation carriesShipment Shipment`
- `LCTOperation hasCargoManifest CargoManifest`
- `LCTOperation hasReadiness CarrierReadiness`

가정:
- `Jopetwil 71`, `JPT62`, `Thuraya` 같은 운항 단위는 `OperationCarrier`
- 특정 날짜/항차 실행은 `LCTOperation`

### 5. Document / Settlement Layer
운송 + 문서 + 정산 범위를 담습니다.

- `TransportDocument`
- `Invoice`
- `ChargeCategory`
- `ChargeSummary`
- `SettlementRecord`
- `ReconciliationRecord`
- `CostAttribution`

핵심 관계:
- `Shipment documentedBy TransportDocument`
- `Shipment invoicedAs Invoice`
- `Invoice hasChargeSummary ChargeSummary`
- `ChargeSummary hasChargeCategory ChargeCategory`
- `SettlementRecord settledInvoice Invoice`
- `ReconciliationRecord reconciles LCTOperation|Invoice`
- `CostAttribution attributedToShipment Shipment`
- `CostAttribution attributedToEvent Event`
- `CostAttribution attributedToLocation Location`

### 6. WhatsApp / Analyses Knowledge Layer
과거 대화는 raw chat 자체가 아니라 교훈/규칙/사건으로 남깁니다.

- `GroupGuide`
- `OperatingRule`
- `ReportingRule`
- `EscalationRule`
- `DocumentAuthorityRule`
- `IncidentLesson`
- `RecurringPattern`
- `CommunicationEvidence`

핵심 관계:
- `GroupGuide definesRule OperatingRule`
- `IncidentLesson supportedBy CommunicationEvidence`
- `IncidentLesson followsOrViolates OperatingRule`
- `IncidentLesson relatedToShipment Shipment`
- `IncidentLesson relatedToLocation Location`
- `IncidentLesson relatedToCarrier OperationCarrier`
- `IncidentLesson exemplifiesPattern RecurringPattern`

### 7. Compatibility Mapping Layer
`CONSOLIDATED-00~09`와의 의미 호환용입니다.

- `ConceptMapping`
- `PropertyMapping`
- `LegacyConcept`
- `LegacyRelation`

핵심 관계:
- `ConceptMapping mapsNewClassTo LegacyConcept`
- `PropertyMapping mapsNewPropertyTo LegacyRelation`
- `mappedToConsolidatedConcept`
- `mappedToConsolidatedRelation`

## 핵심 설계 원칙

1. `Shipment`는 spine이다.
2. 시간 있는 사실은 edge가 아니라 `Event`다.
3. `LCTOperation`은 shipment의 하위가 아니라 shipment와 연결된 운영 실행체다.
4. 비용은 invoice에만 묶지 않고 shipment/event/location에도 귀속 가능해야 한다.
5. WhatsApp은 raw message graph가 아니라 `IncidentLesson + Rule + Evidence`로 간다.
6. `analyses` 폴더 문서는 ontology의 `Guide` 또는 `IncidentLesson`과 1:1 대응시키는 것이 좋다.

## 추가 아이디어

다른 아이디어로는 아래 3개를 추천합니다.

1. `Node drilldown bundle`
- 노드 하나를 열면
  - 최신 이벤트
  - 주요 incident lesson
  - 관련 guide rule
  - 관련 invoice/reconciliation
  를 한 번에 보여주는 묶음 객체를 둡니다.
- UI에서 매우 유용합니다.

2. `Pattern-first navigation`
- 개별 사건보다 먼저 `RecurringPattern`으로 모읍니다.
- 예:
  - `High Tide Delay`
  - `Manifest Lag`
  - `Gate Pass Missing`
  - `Forklift Shortage`
- 그다음 해당 pattern 아래에 incident lesson이 붙게 합니다.

3. `Rule compliance scoring`
- incident가 어떤 rule을 위반했는지 기록해서
  - group별 반복 위반
  - site별 반복 문제
  - carrier별 반복 문제
  를 볼 수 있게 합니다.

이 3개는 ontology 자체보다, 나중에 dashboard와 wiki 연결에서 큰 힘을 줍니다.

**Not done**

- 속성(property) 상세 목록
- 식별자 규칙
- xlsx 시트별 클래스 매핑
- TTL 설계 문서 작성

**Evidence**

changed files:
- 없음

generated files:
- 없음

test names:
- 없음

execution path or command:
- 참조 기준:
  - [analyses](C:/Users/jichu/Downloads/valut/wiki/analyses)
  - [00_WhatsApp_Group_Master_Policy.md](C:/Users/jichu/Downloads/mcp_obsidian/whatsapp%20groupchat/00_WhatsApp_Group_Master_Policy.md)
  - [Guideline_Jopetwil_71_Group.txt](C:/Users/jichu/Downloads/mcp_obsidian/whatsapp%20groupchat/Guideline_Jopetwil_71_Group.txt)
  - [Guideline_DSV_Delivery.txt](C:/Users/jichu/Downloads/mcp_obsidian/whatsapp%20groupchat/Guideline_DSV_Delivery.txt)
  - [Guideline_HVDC_Project_Lightning.txt](C:/Users/jichu/Downloads/mcp_obsidian/whatsapp%20groupchat/Guideline_HVDC_Project_Lightning.txt)

one-line result summary:
- 새 TTL은 `Shipment spine + Event + LCT ops + Cost/Settlement + Lesson Learned/Rule + Compatibility mapping`의 7개 클래스 묶음으로 가는 것이 가장 안정적입니다.

**Risks**

- `OperationalLocation`을 너무 넓게 허용하면 taxonomy가 다시 흐트러질 수 있습니다.
- `IncidentLesson`과 `IssueEvent`의 경계를 안 나누면 wiki 문서와 실행 이벤트가 다시 섞입니다.

**Next action**

- 이 최종 클래스 묶음이 맞는지 승인해 주십시오. 승인되면 다음으로 `속성 목록 + 식별자 규칙 + xlsx별 매핑 설계`를 제시하겠습니다.