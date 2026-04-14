좋습니다. 최신 기준은 이렇게 고정하겠습니다.

- 중심축: `Shipment`
- 세부 단위: `Case`
- 시간 표현: `이벤트형`
- `JPT-reconciled_v6.0.xlsx`: `Voyage 운영 레이어`
- 장소 체계: `핵심 + 운영 장소 확장`
- 범위: `운송 + 문서 + 정산`
- 입력 소스: `엑셀 3개`
- 추가 조건: `CONSOLIDATED-00~09 문서와 호환`

다음 질문입니다.  
여기서 **호환**의 의미를 하나로 고정해야 설계를 제대로 할 수 있습니다.

1. `URI/클래스/속성 이름까지 최대한 유지`  
   기존 문서의 용어와 predicate 이름을 거의 그대로 맞춤  
   가장 보수적이지만 재설계 자유도가 낮습니다.

2. `의미 호환 + 매핑 레이어 제공`  
   새 TTL은 새 구조로 설계하되, `CONSOLIDATED-00~09`에서 기대하는 클래스/관계로 매핑표를 제공  
   전면 재설계와 호환성을 같이 잡기 좋아서 추천합니다.

3. `문서도 새 TTL 기준으로 같이 다시 씀`  
   가장 깨끗하지만 범위가 크게 커집니다.

제 추천은 `2. 의미 호환 + 매핑 레이어 제공`입니다.  
어느 수준의 호환으로 갈지 답해 주십시오.

좋습니다. 이건 설계 축을 바꿀 만큼 중요합니다.

정리하면,  
`JPT-reconciled_v6.0.xlsx`는 일반 voyage 보조 자료가 아니라 **LCT 운영 데이터 원천**이고,  
새 TTL의 marine/LCT 의미는 [CONSOLIDATED-04-barge-bulk-cargo.md](C:/Users/jichu/Downloads/mcp_obsidian/Logi%20ontol%20core%20doc/CONSOLIDATED-04-barge-bulk-cargo.md) 와 호환되어야 합니다.

그래서 현재 기준은 이렇게 수정됩니다.

- 중심축: `Shipment`
- 세부 단위: `Case`
- 시간 표현: `이벤트형`
- `JPT-reconciled_v6.0.xlsx`: `LCT 운영 레이어`
- marine/LCT 의미 호환 기준: `CONSOLIDATED-04`
- 장소 체계: `핵심 + 운영 장소 확장`
- 범위: `운송 + 문서 + 정산`
- 입력 소스: 엑셀 3개
- 호환 방식: `의미 호환 + 매핑 레이어`

다음 질문입니다.  
**LCT를 새 TTL에서 무엇으로 모델링할지** 하나로 고정해야 합니다.

1. `Vessel subtype`  
   LCT를 `Vessel`의 하위 유형으로 둠  
   가장 단순하지만 운항 이벤트 표현이 얕아질 수 있습니다.

2. `Operation carrier`  
   LCT는 `MarineTransportUnit` 또는 `LCTCarrier`로 두고, `Vessel`과 분리된 운영 운반체로 모델링  
   `CONSOLIDATED-04`의 작업/운송 의미와 잘 맞아서 추천합니다.

3. `둘 다`  
   LCT를 `Vessel`이면서 `OperationUnit`이기도 하게 둠  
   유연하지만 설계가 쉽게 지저분해집니다.

제 추천은 `2. Operation carrier`입니다.  
어느 방식으로 갈지 답해 주십시오.
**Done**

- 새 TTL 재설계의 핵심 전제를 여기까지 고정했습니다.
  - 중심축: `Shipment`
  - 세부 단위: `Case`
  - 시간 표현: `이벤트형`
  - `JPT-reconciled_v6.0.xlsx`: `LCT 운영 레이어`
  - LCT 모델: `Operation carrier`
  - marine/LCT 의미 호환 기준: `CONSOLIDATED-04`
  - 장소 체계: `핵심 + 운영 장소 확장`
  - 범위: `운송 + 문서 + 정산`
  - 입력 소스: `엑셀 3개 + CONSOLIDATED-00~09와 의미 호환`
  - 호환 방식: `의미 호환 + 매핑 레이어`
  - 정산 깊이: `Invoice + Voyage 정산 연결`

**Partial**

- 이제 추천 구조는 하나로 좁혀집니다.

### 추천 구조

**`Shipment spine + Case layer + Event layer + LCT operation carrier layer + Document/Settlement layer + Compatibility mapping layer`**

쉽게 말하면, 새 TTL은 아래 6층으로 갑니다.

1. **Shipment spine**
   - 모든 추적의 중심축
   - shipment가 route, case, document, settlement, operation을 묶습니다.

2. **Case layer**
   - `HVDC WAREHOUSE STATUS.xlsx`를 받아 case 단위 위치/보관/상태를 표현
   - warehouse 추적은 shipment가 아니라 case가 직접 받습니다.

3. **Event layer**
   - direct edge 대신 `LoadingEvent`, `StorageEvent`, `ArrivalEvent`, `DepartureEvent`, `TransferEvent`, `IssueEvent`를 둡니다.
   - 날짜와 순서 정보는 여기 보존합니다.

4. **LCT operation carrier layer**
   - `JPT-reconciled_v6.0.xlsx`에서 나온 LCT 운항, decklog, port call, cargo operation을 담당
   - LCT는 `Operation carrier`로 모델링하고 `CONSOLIDATED-04` 의미와 맞춥니다.

5. **Document and settlement layer**
   - B/L, invoice, normalized voyage id, reconciliation status, mismatch 상태를 담습니다.
   - line item은 제외하고 invoice-voyage-operation 연결까지만 갑니다.

6. **Compatibility mapping layer**
   - 새 클래스/속성과 `CONSOLIDATED-00~09` 용어를 연결하는 매핑 표를 둡니다.
   - 이름을 억지로 복제하지 않고 의미 호환을 유지합니다.

### Section 2. 핵심 클래스 초안

- `Shipment`
- `Case`
- `WarehouseLocation`
- `SiteLocation`
- `PortLocation`
- `HubLocation`
- `OperationalLocation`
- `OperationCarrier`
- `LCTOperation`
- `PortCall`
- `RouteEvent`
- `StorageEvent`
- `CargoHandlingEvent`
- `IssueEvent`
- `TransportDocument`
- `Invoice`
- `ReconciliationRecord`

### Section 3. 핵심 관계 초안

- `hasCase`
- `hasEvent`
- `occurredAt`
- `handledByCarrier`
- `participatesInOperation`
- `documentsShipment`
- `invoicedAs`
- `reconciledBy`
- `mappedToConsolidatedConcept`

이 구조는 `CONSOLIDATED-04`의 marine/LCT 의미를 살리면서도, 전체 TTL의 중심축은 여전히 `Shipment`로 유지합니다.

**Not done**

- 클래스별 속성 정의
- 이벤트 taxonomy 상세화
- `CONSOLIDATED-00~09` 매핑 표
- 설계 문서 작성

**Evidence**

changed files:
- 없음

generated files:
- 없음

test names:
- 없음

execution path or command:
- 참고 확인:
  - [CONSOLIDATED-04-barge-bulk-cargo.md](C:/Users/jichu/Downloads/mcp_obsidian/Logi%20ontol%20core%20doc/CONSOLIDATED-04-barge-bulk-cargo.md)
  - [JPT-reconciled_v6.0.xlsx](C:/Users/jichu/Downloads/mcp_obsidian/Logi%20ontol%20core%20doc/JPT-reconciled_v6.0.xlsx)
  - [HVDC WAREHOUSE STATUS.xlsx](C:/Users/jichu/Downloads/mcp_obsidian/Logi%20ontol%20core%20doc/HVDC%20WAREHOUSE%20STATUS.xlsx)
  - [HVDC STATUS.xlsx](C:/Users/jichu/Downloads/mcp_obsidian/Logi%20ontol%20core%20doc/HVDC%20STATUS.xlsx)

one-line result summary:
- 새 TTL은 `Shipment 중심`을 유지하되, `LCT 운영`과 `정산 연결`을 별도 레이어로 분리하는 구조가 가장 맞습니다.

**Risks**

- LCT를 carrier로 두면서도 shipment spine과 연결 규칙을 명확히 안 하면, operation 레이어가 다시 독립 섬처럼 될 수 있습니다.
- `OperationalLocation`을 너무 넓게 허용하면 장소 taxonomy가 다시 흐트러질 수 있습니다.

**Next action**

- 이 추천 구조와 Section 2/3 초안이 맞는지 승인해 주십시오. 승인되면 바로 Section 4로 `속성(property) 목록 + 식별자 규칙 + 매핑 원칙`을 설계하겠습니다.

PARTIAL

**Done**

- 정산 소스 범위가 확장됐습니다.
  - 해상/LCT 정산: [JPT-reconciled_v6.0.xlsx](C:/Users/jichu/Downloads/mcp_obsidian/Logi%20ontol%20core%20doc/JPT-reconciled_v6.0.xlsx)
  - inland/domestic 정산: [HVDC Logistics cost(inland,domestic).xlsx](C:/Users/jichu/Downloads/mcp_obsidian/Logi%20ontol%20core%20doc/HVDC%20Logistics%20cost(inland,domestic).xlsx)
- inland/domestic 비용 연결 방식도 고정됐습니다.
  - `Shipment + Location/Event에 연결`

**Partial**

- 그래서 추천 구조를 한 단계 업데이트하면 아래와 같습니다.

### 업데이트된 추천 구조

**`Shipment spine + Case layer + Event layer + LCT operation carrier layer + Cost/Settlement layer + Compatibility mapping layer`**

쉽게 말하면, 새 TTL은 이제 운송 그래프 위에 정산 그래프를 얹는 구조가 됩니다.

1. **Shipment spine**
   - 전체의 중심입니다.
   - 모든 비용과 정산은 기본적으로 shipment를 anchor로 잡습니다.

2. **Case layer**
   - 창고와 보관은 case 단위로 표현합니다.
   - `HVDC WAREHOUSE STATUS.xlsx`가 여기로 들어옵니다.

3. **Event layer**
   - `LoadingEvent`
   - `StorageEvent`
   - `ArrivalEvent`
   - `DepartureEvent`
   - `TransferEvent`
   - `IssueEvent`
   - 날짜와 장소는 여기 보존합니다.

4. **LCT operation carrier layer**
   - `JPT-reconciled_v6.0.xlsx`를 통해 LCT decklog, operation, port call, voyage rollup을 표현합니다.
   - `CONSOLIDATED-04`와 의미 호환됩니다.

5. **Cost/Settlement layer**
   - `Invoice`
   - `ChargeCategory`
   - `SettlementRecord`
   - `CostAttribution`
   - inland/domestic 비용은 shipment에 기본 연결하고, 가능한 경우 `StorageEvent`, `DetentionEvent`, `InspectionEvent`, `InlandTransferEvent`에도 연결합니다.

6. **Compatibility mapping layer**
   - 새 클래스와 관계를 `CONSOLIDATED-00~09` 기대 의미에 연결합니다.

### 새로 필요한 핵심 클래스 초안

- `Invoice`
- `ChargeLineSummary`
- `ChargeCategory`
- `SettlementRecord`
- `CostAttribution`
- `InlandTransferEvent`
- `DetentionEvent`
- `InspectionEvent`

### 새로 필요한 핵심 관계 초안

- `invoicedAs`
- `hasChargeSummary`
- `attributedToShipment`
- `attributedToEvent`
- `attributedToLocation`
- `settledBy`
- `hasChargeCategory`

이렇게 두면  
`Inland`, `Storage`, `Detention`, `Inspection` 같은 비용이 단순 금액 표가 아니라  
“어느 shipment의 어떤 운영 이벤트에서 발생했는가”까지 같이 읽을 수 있습니다.

**Not done**

- 속성(property) 목록 상세화
- 식별자 규칙
- 이벤트-비용 연결 규칙
- 설계 문서 작성

**Evidence**

changed files:
- 없음

generated files:
- 없음

test names:
- 없음

execution path or command:
- 구조 확인:
  - [HVDC Logistics cost(inland,domestic).xlsx](C:/Users/jichu/Downloads/mcp_obsidian/Logi%20ontol%20core%20doc/HVDC%20Logistics%20cost(inland,domestic).xlsx)
- 확인된 주요 컬럼:
  - `Invoice No`, `Invoice Date`, `Shipment No`, `Job Description`, `Inland`, `THC`, `Inspection`, `Detention`, `Storage`, `Others`, `TOTAL`, `VAT`, `G. TOTAL`

one-line result summary:
- 새 TTL은 이제 운송 실행뿐 아니라 inland/domestic 비용까지 shipment와 event 기준으로 연결하는 구조로 가야 합니다.

**Risks**

- `Shipment No` 값 품질이 낮으면 비용 attribution이 흔들릴 수 있습니다.
- `Job Description` 기반 event 연결은 규칙이 약하면 오분류가 생길 수 있습니다.

**Next action**

- 이 업데이트된 구조가 맞는지 승인해 주십시오. 승인되면 바로 Section 4로 `속성 목록 + 식별자 규칙 + 비용 attribution 원칙`을 설계하겠습니다.