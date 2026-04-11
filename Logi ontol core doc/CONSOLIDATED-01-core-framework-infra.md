---
title: "HVDC Framework & Infrastructure Ontology - Consolidated"
type: "ontology-design"
domain: "framework-infrastructure"
sub-domains: ["logistics-framework", "node-infrastructure", "construction-logistics", "transport-network"]
version: "consolidated-1.0"
date: "2025-10-26"
tags: ["ontology", "hvdc", "framework", "infrastructure", "logistics", "samsung-ct", "adnoc", "consolidated"]
standards: ["UN/CEFACT", "WCO-DM", "DCSA", "ICC-Incoterms-2020", "HS-2022", "MOIAT", "FANR", "UN/LOCODE", "BIMCO-SUPPLYTIME", "ISO-6346"]
status: "active"
spine_ref: "CONSOLIDATED-00-master-ontology.md"
extension_of: "hvdc-master-ontology-v1.0"
source_files: ["1_CORE-01-hvdc-core-framework.md", "1_CORE-02-hvdc-infra-nodes.md"]
---

> **MASTER GOVERNANCE RULE**
> 1. **Flow Code is a warehouse-handling classification only.** Restricted to WarehouseHandlingProfile. No other domain may own or assign Flow Code as primary language.
> 2. **Program-wide shipment visibility shall use Journey Stage, Route Type, Milestone, and Leg.** (
oute_type, shipment_stage, leg_sequence, JourneyLeg)
> 3. **Port, Customs, Document, Cost, Marine, and Communication domains** may reference warehouse-flow *evidence*, but shall NOT own or assign Flow Code.
> 4. **MOSB is an Offshore Staging / Marine Interface Node**, not a Warehouse in the top-level logistics ontology.

> **Extension Document** — 이 문서는 [`CONSOLIDATED-00-master-ontology.md`](CONSOLIDATED-00-master-ontology.md)의 도메인 확장입니다.
> RoutingPattern Dictionary, Milestone M10~M160, Identifier Policy 정의는 CONSOLIDATED-00을 참조하세요.

# hvdc-core-framework-infra · CONSOLIDATED-01

## 📑 Table of Contents
1. [Core Logistics Framework](#section-1)
2. [Node Infrastructure](#section-2)

---

## Section 1: Core Logistics Framework

### Source
- **Original File**: `1_CORE-01-hvdc-core-framework.md`
- **Version**: unified-1.0
- **Date**: 2025-01-19

래는 __삼성 C&T 건설물류\(UA E 6현장, 400 TEU/100 BL·월\)__ 업무를 __온톨로지 관점__으로 재정의한 "작동 가능한 설계서"입니다\.
핵심은 \*\*표준\(UN/CEFACT·WCO DM·DCSA·ICC Incoterms·HS·MOIAT·FANR\)\*\*을 상위 스키마로 삼아 __문서·화물·설비·프로세스·이벤트·계약·규정__을 하나의 그래프\(KG\)로 엮고, 여기서 __Heat‑Stow·WHF/Cap·HSRisk·CostGuard·CertChk·Pre‑Arrival Guard__ 같은 기능을 \*\*제약\(Constraints\)\*\*으로 돌리는 것입니다\. \(Incoterms 2020, HS 2022 최신 적용\)\. [Wcoomd\+4UNECE\+4Wcoomd\+4](https://unece.org/trade/uncefact/rdm?utm_source=chatgpt.com)

__1\) Visual — Ontology Stack \(요약표\)__

__Layer__

__표준/근거__

__범위__

__당신 업무 매핑\(예\)__

__Upper__

__IOF/BFO Supply Chain Ontology__, __ISO 15926__

상위 개념\(행위자/행위/자산/이벤트\)·플랜트 라이프사이클

자산\(크레인, 스키드, 모듈\)·작업\(리깅, 해상 보급\)·상태\(검사/격납\) 정합성 프레임

__Reference Data \(Process/Data\)__

__UN/CEFACT Buy‑Ship‑Pay RDM & CCL__

주문–선적–결제 전과정 공통 데이터·용어

*Party, Shipment, Consignment, Transport Means, Invoice/LineItem* 공통 정의

__Border/Customs__

__WCO Data Model v4\.2\.0__, __HS 2022__

신고/승인/통관 데이터·코드셋

BOE\(수입신고\), 원산지·보증·증명, HS 분류·위험도

__Ocean/Carrier__

__DCSA Booking 2\.0 & eBL 3\.0__

예약/BL 데이터 모델·API

BL 데이터 정규화, eBL 규칙·검증

__Trade Terms__

__ICC Incoterms® 2020__

비용/리스크 이전 지점

EXW/FOB/CIF/DAP별 의무·리스크 노드 매핑

__UAE Reg\.__

__MOIAT ECAS/EQM__, __FANR 수입허가__, __CICPA/ADNOC 출입__

규제/인증/출입 통제

CertChk\(MOIAT·FANR\), 게이트패스 제약, 위험물 통제

__Offshore 계약__

__BIMCO SUPPLYTIME 2017__

OSV 타임차터 KfK 책임체계

보트/바지선 운영 KPI·책임 분기 조건

Hint: Abu Dhabi는 역사적으로 __CICPA/구 CNIA 보안패스__ 체계가 근간이며, 항만 __e‑pass__ 디지털화가 병행되었습니다\(현장 Gate 규정은 매년 공지 확인 필요\)\. [HLB Abudhabi\+1](https://hlbabudhabi.com/a-comprehensive-guide-on-cicpa-passes-in-abu-dhabi/?utm_source=chatgpt.com)

__2\) Domain Ontology — 클래스/관계\(업무 단위 재정의\)__

__핵심 클래스 \(Classes\)__

- __Party__\(Shipper/Consignee/Carrier/3PL/Authority\)
- __Asset__\(Container ISO 6346, OOG 모듈, 장비/스프레더, OSV/바지선\)
- __Document__\(CIPL, Invoice, BL/eBL, BOE, DO, INS, MS\(Method Statement\), Port Permit, Cert\[ECAS/EQM/FANR\], SUPPLYTIME17\)
- __Process__\(Booking, Pre‑alert, Export/Import Clearance, Berth/Port Call, Stowage, Gate Pass, Last‑mile, WH In/Out, Returns\)
- __Event__\(ETA/ATA, CY In/Out, Berth Start/End, DG Inspection, Weather Alert, FANR Permit Granted, MOIAT CoC Issued\)
- __Contract__\(IncotermTerm, SUPPLYTIME17\)
- __Regulation__\(HS Rule, MOIAT TR, FANR Reg\.\)
- __Location__\(UN/LOCODE, Berth, Laydown Yard, Site Gate\)
- __KPI__\(DEM/DET Clock, Port Dwell, WH Util, Delivery OTIF, Damage Rate, Cert SLA\)

__대표 관계 \(Object Properties\)__

- Shipment → hasIncoterm → IncotermTerm \(리스크/비용 이전 노드\) [ICC \- International Chamber of Commerce](https://iccwbo.org/business-solutions/incoterms-rules/?utm_source=chatgpt.com)
- InvoiceLineItem → classifiedBy → HSCode \(HS 2022\) [Wcoomd](https://www.wcoomd.org/en/topics/nomenclature/instrument-and-tools/hs-nomenclature-2022-edition/hs-nomenclature-2022-edition.aspx?utm_source=chatgpt.com)
- BL → conformsTo → DCSA\_eBL\_3\_0 \(데이터 검증 규칙\) [dcsa\.org](https://dcsa.org/newsroom/final-versions-of-booking-bill-of-lading-standards-released?utm_source=chatgpt.com)
- CustomsDeclaration\(BOE\) → usesDataModel → WCO\_DM\_4\_2\_0 \(전자신고 필드 정합\) [Wcoomd](https://www.wcoomd.org/en/media/newsroom/2025/july/world-customs-organization-releases-data-mode.aspx?utm_source=chatgpt.com)
- Equipment/OOG → requiresCertificate → MOIAT\_ECAS|EQM \(규제 제품\) [Ministry of Industry\+1](https://moiat.gov.ae/en/services/issue-conformity-certificates-for-regulated-products/?utm_source=chatgpt.com)
- Radioactive\_Source|Gauge → requiresPermit → FANR\_ImportPermit \(60일 유효\) [Fanr](https://www.fanr.gov.ae/en/services/import-and-export-permit/issue-import-permit-for-radiation-sources-and-nuclear-materials?utm_source=chatgpt.com)
- PortAccess → governedBy → CICPA\_Policy \(게이트패스\) [HLB Abudhabi](https://hlbabudhabi.com/a-comprehensive-guide-on-cicpa-passes-in-abu-dhabi/?utm_source=chatgpt.com)
- OSV\_Charter → governedBy → SUPPLYTIME2017 \(KfK 책임\) [BIMCO](https://www.bimco.org/contractual-affairs/bimco-contracts/contracts/supplytime-2017/?utm_source=chatgpt.com)

__데이터 속성 \(Data Properties\)__

- grossMass, dims\(L×W×H\), isOOG\(boolean\), dgClass, UNNumber, tempTolerance, stowHeatIndex, demClockStartAt, detClockStartAt, gatePassExpiryAt, permitId, costCenter, tariffRef\.

__3\) Use‑case별 제약\(Constraints\) = 운영 가드레일__

__3\.1 CIPL·BL Pre‑Arrival Guard \(eBL‑first\)__

- __Rule‑1__: BL 존재 → BL\.conformsTo = DCSA\_eBL\_3\_0 AND Party·Consignment·PlaceOfReceipt/Delivery 필수\. 미충족 시 *Berth Slot* 확정 금지\. [dcsa\.org](https://dcsa.org/newsroom/final-versions-of-booking-bill-of-lading-standards-released?utm_source=chatgpt.com)
- __Rule‑2__: 모든 InvoiceLineItem는 HSCode 필수 \+ OriginCountry·Qty/UM·FOB/CI 금액\. __WCO DM 필드__ 매핑 누락 시 __BOE 초안 생성 차단__\. [Wcoomd](https://www.wcoomd.org/en/media/newsroom/2025/july/world-customs-organization-releases-data-mode.aspx?utm_source=chatgpt.com)
- __Rule‑3__: IncotermTerm별 책임/비용 그래프 확인\(예: __DAP__면 현지 내륙운송·통관 리스크=Buyer\)\. [ICC \- International Chamber of Commerce](https://iccwbo.org/business-solutions/incoterms-rules/?utm_source=chatgpt.com)

__3\.2 Heat‑Stow \(고온 노출 최소화\)__

- stowHeatIndex = f\(DeckPos, ContainerTier, WeatherForecast\) → 임계치 초과 시 __Under‑deck/센터 베이__ 유도, __berth 시간대 조정__\. \(기상 이벤트는 Event로 연결\)
- dgClass ∈ \{1,2\.1,3,4\.1,5\.1,8\} → Heat‑Stow 규칙 엄격 적용\(위치·분리거리\)\.

__3\.3 WHF/Cap \(Warehouse Forecast/Capacity\)__

- InboundPlan\(TEU/주\)·Outplan → WHUtil\(%\) 예측, 임계치\(85\.00%\) 초과 시 *overflow yard* 예약, __DET 발생 예측__과 연결\.

__3\.4 HSRisk__

- RiskScore = g\(HS, Origin, DG, Cert 요구, 과거검사빈도\) → __검사·추징·지연 확률__ 추정\. \(HS·규제요건: HS 2022·MOIAT·FANR 근거\) [Wcoomd\+2Ministry of Industry\+2](https://www.wcoomd.org/en/topics/nomenclature/instrument-and-tools/hs-nomenclature-2022-edition/hs-nomenclature-2022-edition.aspx?utm_source=chatgpt.com)

__3\.5 CertChk \(MOIAT·FANR\)__

- 규제제품 → ECAS/EQM 승인서 필수 없으면 __DO·GatePass 발행 금지__, __선하증권 인도 보류__\. [Ministry of Industry\+1](https://moiat.gov.ae/en/services/issue-conformity-certificates-for-regulated-products/?utm_source=chatgpt.com)
- 방사선 관련 기자재 → FANR Import Permit\(유효 60일\) 없으면 __BOE 제출 중단__\. [Fanr](https://www.fanr.gov.ae/en/services/import-and-export-permit/issue-import-permit-for-radiation-sources-and-nuclear-materials?utm_source=chatgpt.com)

__4\) 최소 예시\(표현\) — JSON‑LD \(요지\)__

\{

  "@context": \{"incoterm":"https://iccwbo\.org/incoterms/2020\#","dcsa":"https://dcsa\.org/bl/3\.0\#","wco":"https://www\.wcoomd\.org/datamodel/4\.2\#"\},

  "@type":"Shipment",

  "id":"SHP\-ADNOC\-2025\-10\-001",

  "hasIncoterm":\{"@type":"incoterm:DAP","deliveryPlace":"Ruwais Site Gate"\},

  "hasDocument":\[

    \{"@type":"dcsa:BillOfLading","number":"DCSA123\.\.\.", "status":"original\-validated"\},

    \{"@type":"wco:CustomsDeclarationDraft","items":\[\{"hsCode":"850440", "qty":2, "value":120000\.00\}\]\}

  \],

  "consistsOf":\[\{"@type":"Container","isoCode":"45G1","isOOG":true,"dims":\{"l":12\.2,"w":2\.44,"h":2\.90\}\}\]

\}

__5\) 선택지\(3\) — 구축 옵션 \(pro/con/$·risk·time\)__

1. __Reference‑first \(표준 우선, 얇은 구현\)__

- __Pro__: 대외 연계 쉬움\(UN/CEFACT·WCO·DCSA\)\. __Con__: 현장 특성 반영 속도↓\.
- __$__: 초기 낮음\(₩·$$\)\. __Risk__: 커스터마이즈 지연\. __Time__: 6–8주 MVP\. [UNECE\+2Wcoomd\+2](https://unece.org/trade/uncefact/rdm?utm_source=chatgpt.com)

1. __Hybrid \(표준\+현장제약 동시\)__ ← *추천*

- __Pro__: 표준 적합 \+ GatePass/Heat‑Stow/WH 바로 적용\. __Con__: 설계 복잡\.
- __$__: 중간\. __Risk__: 스키마 복잡성\. __Time__: 10–12주 POC→Rollout\.

1. __Ops‑first \(현장 규칙 우선\)__

- __Pro__: 즉효\(DEM/DET·GatePass\)\. __Con__: 표준 정합 나중 기술부채\.
- __$__: 낮음→중간\. __Risk__: 대외 API 통합 시 재작업\. __Time__: 4–6주\.

__6\) Roadmap \(P→Pi→B→O→S \+ KPI\)__

- __P\(Plan\)__: 스코프 확정\(문서: CIPL/BL/BOE/DO/INS/Permit, 프로세스: Berth/Gate Pass/WH\)\. __KPI__: 데이터 필드 완전성 ≥ 98\.00%\.
- __Pi\(Pilot\)__: __eBL‑Pre‑Arrival Guard__ \+ __WHF/Cap__ 1현장 적용\. __KPI__: Port dwell ↓ 12\.50%, DET 비용 ↓ 18\.00% *\(가정\)*\.
- __B\(Build\)__: __HSRisk__·__CertChk__·__CostGuard__ 추가, __SUPPLYTIME17__ 운영지표 연계\. __KPI__: 검사로 인한 Leadtime 분산 ↓ 15\.00%\. [BIMCO](https://www.bimco.org/contractual-affairs/bimco-contracts/contracts/supplytime-2017/?utm_source=chatgpt.com)
- __O\(Operate\)__: 규칙/SHACL 자동검증, Slack/Telegram 알림\. __KPI__: 규칙 위반 건당 처리시간 ≤ 0\.50h\.
- __S\(Scale\)__: 6현장→글로벌 재사용, __UN/CEFACT Web Vocabulary__로 공개 스키마 매핑\. __KPI__: 시스템 간 매핑 공수 ↓ 30\.00%\. [Vocabulary UNCEFACT](https://vocabulary.uncefact.org/about?utm_source=chatgpt.com)

__7\) Data·Sim·BI \(운영 숫자 관점\)__

- __DEM/DET 시계__: ClockStart = \(CY In or FreeTime Start by Carrier\) → 컨테이너별 __DEM/DET Clock__ 노드 운영\.
- __WH Capacity Forecast__: Util\_t\+1 = Util\_t \+ Inbound \- Outbound \(ARIMA/Prophet 가능\)\.
- __Heat‑Stow 점수__: HI = α\*DeckExposure \+ β\*Tier \+ γ\*ForecastTemp\(°C\) → 임계 0\.70 이상 __스택 변경__\.
- __Risk@HS__: 로지스틱 회귀/GBT로 검사확률·추징금 기대값\.

__8\) Automation \(RPA·LLM·Sheets·TG\) — Slash Cmd 예시__

- __/logi\-master \-\-fast invoice\-audit__ → CIPL/Invoice 라인 __HS·Origin·Qty·Value 누락__ 탐지→BOE 초안 블록\. \(WCO DM/HS 2022\) [Wcoomd\+1](https://www.wcoomd.org/en/media/newsroom/2025/july/world-customs-organization-releases-data-mode.aspx?utm_source=chatgpt.com)
- __/logi\-master predict \-\-AEDonly weather\-tie__ → 기상경보 Event→Berth 스케줄 재배치\(Heat‑Stow 임계\)\.
- __/switch\_mode COST\-GUARD LATTICE__ → DET/DEM 예측비용 알림 \+ eBL 상태/도착지연 교차검증\(DCSA eBL 3\.0\)\. [dcsa\.org](https://dcsa.org/newsroom/final-versions-of-booking-bill-of-lading-standards-released?utm_source=chatgpt.com)
- __/visualize\_data \-\-type=heatmap <stow\.csv>__ → HI>0\.70 구간 강조\.

__9\) QA — Gap/Recheck 리스트__

- __eBL 상태 신뢰도__: Carrier별 DCSA 3\.0 호환 여부 점검\. [dcsa\.org](https://dcsa.org/newsroom/final-versions-of-booking-bill-of-lading-standards-released?utm_source=chatgpt.com)
- __HS·CCL 정합성__: UN/CEFACT CCL 릴리스\(예: __24A__\)와 로컬 속성 매핑 재검\. [UNECE](https://unece.org/trade/uncefact/unccl?utm_source=chatgpt.com)
- __UAE 인증__: MOIAT ECAS/EQM 최신 규제 범위/코드 확인, FANR 퍼밋 유효일\(60일\) 자동 만료 체크\. [Ministry of Industry\+2SGSCorp\+2](https://moiat.gov.ae/en/services/issue-conformity-certificates-for-regulated-products/?utm_source=chatgpt.com)
- __GatePass 체계__: 현장 보안 주체\(CICPA/ADNOC\) 최신 공지 확인\(사내 SOP 연결\)\. [HLB Abudhabi](https://hlbabudhabi.com/a-comprehensive-guide-on-cicpa-passes-in-abu-dhabi/?utm_source=chatgpt.com)

__10\) Fail‑safe "중단" 테이블 \(ZERO 전략\)__

__트리거\(중단\)__

__ZERO 액션__

__재개 조건__

eBL 비정합\(DCSA 3\.0 스키마 오류\)

Berth 확정 보류, 선적명세 수동검증

eBL 재검증 Pass

BOE 필수필드 미충족\(WCO DM\)

신고중단, Shipper 보완요청

필드 완전성 ≥ 98\.00%

규제제품 Cert 부재\(MOIAT/FANR\)

DO/게이트패스 발급 금지

유효 CoC/Permit 업로드

DET 임계 초과 예측\(>AED x/TEU\)

내륙 인도·반납 계획 재조정

비용 추정 < 임계값

__11\) 운영에 바로 쓰는 SHACL\(요지\)__

@prefix sh: <http://www\.w3\.org/ns/shacl\#> \.

:InvoiceLineItemShape a sh:NodeShape ;

  sh:targetClass :InvoiceLineItem ;

  sh:property \[

    sh:path :hsCode ; sh:minCount 1 ; sh:pattern "^\[0\-9\]\{6,10\}$"

  \] ;

  sh:property \[

    sh:path :originCountry ; sh:minCount 1

  \] ;

  sh:property \[

    sh:path :quantity ; sh:minInclusive 0\.01

  \] \.

__12\) GitHub·재사용__

- 리포지토리 __macho715/ontology\-insight__에 __/models \(TTL/JSON‑LD\)__, __/rules \(SHACL\)__, __/mappings \(CCL/HS/WCO/DCSA\)__ 디렉토리 구조 권장\.
- OFCO CostCenter 매핑은 __Invoice/LineItem → CostCenter__ 룰로 두고, __/mappings/ofco\.csv__로 관리\. *\(가정: OFCO는 내규 분류표\)*

__13\) Assumptions & Sources__

- __가정:__ OFCO/CostCenter·Heat‑Stow·HSRisk·CostGuard는 사내용 명칭/로직\. UAE 게이트패스\(e‑pass, CICPA/ADNOC\)는 현장별 차이 존재\(사는 공지 우선\)\.
- __표준/근거:__ UN/CEFACT BSP‑RDM & CCL, WCO DM v4\.2\.0, HS 2022, DCSA eBL 3\.0/Booking 2\.0, ICC Incoterms 2020, MOIAT ECAS/EQM, FANR Import Permit, SUPPLYTIME 2017\. [BIMCO\+10UNECE\+10UNECE\+10](https://unece.org/trade/uncefact/rdm?utm_source=chatgpt.com)

__14\) 다음 액션\(짧게\)__

- __/logi\-master \-\-fast invoice\-audit__ 로 현재 월간 100 BL 대상 __Pre‑Arrival Guard__ 돌리고,
- __/switch\_mode COST\-GUARD__ 로 __DEM/DET__ 시계 추정부터 막읍시다\(목표 ↓ 15\.00%\)\.
- __/wh\-capacity oracle \-\-horizon 12m__ 로 __WH Util__ 예측 배치\.

원하시면, 위 스택으로 __CIPL·BL Pre‑Arrival Guard__와 \*\*CertChk\(MOIAT·FANR\)\*\*부터 SHACL/룰팩을 묶어 드리겠습니다\.

---

# Part 2: HVDC Logistics AI Framework

## 개요

프로젝트 전체를 **온톨로지 관점**에서 정리하면, 'HVDC 물류 생명주기'를 하나의 **지식그래프(Ontology)**로 모델링할 수 있습니다.

핵심은 **"물류행위(Activity)"가 아닌 "관계(Relation)"** 중심으로 보는 것입니다 — 사람, 문서, 물품, 절차, 시스템 간의 연결망.

__🔶 1\. Ontology Root Class__

__hvdc\-adopt\-logiontology__

__Layer__

__Ontology Domain__

__대표 엔티티__

__관계 키\(Relation\)__

__L1__

Physical Stream

Material, Cargo, Port, Site, Vessel

movesFrom, movesTo, storedAt, handledBy

__L2__

Document Stream

BL, CI, PL, COO, eDAS, MRR, OSDR

certifies, refersTo, attachedTo

__L3__

Actor Stream

SCT, JDN, ALS, ADNOC, Subcon

responsibleFor, approves, reportsTo

__L4__

Regulatory Stream

MOIAT, FANR, Customs, DOT

requiresPermit, compliesWith, auditedBy

__L5__

System Stream

eDAS, SAP, NCM, LDG

feedsDataTo, validates, monitoredBy

__🔶 2\. Core Classes \(from Workshop\)__

__Class__

__Subclass of__

__Description__

__Onto\-ID__

__Material__

Asset

자재 및 기자재\(Transformer, Cable, CCU 등\)

hvdc\-asset\-mat

__TransportEvent__

Activity

Inland, Marine, Offloading, SiteReceiving

hvdc\-act\-trans

__Storage__

Location

Yard, Warehouse, Laydown

hvdc\-loc\-stor

__Inspection__

Process

MRR, MRI, OSDR

hvdc\-proc\-insp

__Permit__

Document

PTW, Hot Work, FRA

hvdc\-doc\-perm

__Actor__

Agent

SCT, ADNOC L&S, Vendor

hvdc\-agent\-role

__PortOperation__

Activity

RORO/LOLO, Sea Fastening

hvdc\-act\-port

__🔶 3\. Relation Model \(Partial\)__

Material \-\-hasDocument\-\-> MRR

Material \-\-transportedBy\-\-> TransportEvent

TransportEvent \-\-operatedAt\-\-> Port

TransportEvent \-\-requires\-\-> Permit

Permit \-\-approvedBy\-\-> ADNOC

Storage \-\-monitoredBy\-\-> SCT

Inspection \-\-reportedAs\-\-> OSDR

Actor\(SCT\) \-\-usesSystem\-\-> eDAS

이 관계망은 logiontology\.mapping 모듈에서 RDF triple로 구현 가능:

:TR001 rdf:type :Transformer ;

       :hasDocument :MRR\_20240611 ;

       :storedAt :Mussafah\_Yard ;

       :handledBy :SCT ;

       :requiresPermit :FRA\_202405 ;

       :transportedBy :LCT\_Operation\_202405 \.

__🔶 4\. Lifecycle Ontology \(Material Handling Flow\)__

__Stage 1 – Importation__
→ hasDocument\(BL, CI, COO\) → customsClearedBy\(ADOPT\) → storedAt\(PortYard\)

__Stage 2 – Inland/Marine Transport__
→ transportedBy\(LCT/SPMT\) → requiresPermit\(DOT/FRA\) → monitoredBy\(ALS\)

__Stage 3 – Site Receiving__
→ inspectedBy\(QAQC\) → resultsIn\(MRR/OSDR\) → issuedAs\(MIS\)

__Stage 4 – Preservation & Foundation__
→ preservedBy\(HitachiStd\) → foundationBy\(Mammoet\) → approvedBy\(OE\)

__🔶 5\. Alignment with AI\-Logi\-Guide__

__Ontology Node__

__대응 모듈__

__기능적 의미__

Activity

pipeline

단계별 절차 정의

Document

rdfio, validation

eDAS·MRR 등 문서형 triple

Agent

core

역할/권한 모델

Location

mapping

Port/Site 좌표·거점

RiskEvent

reasoning

Weather\-Tie·Delay inference

Report

report

KPI/Inspection 리포트

__🔶 6\. Semantic KPI Layer \(Onto\-KPI\)__

__KPI Class__

__Onto Property__

__계산식__

__Source__

__On\-Time Delivery__

meetsETA

ETA vs Actual ≤12%

ETA MAPE Rule

__Inspection Compliance__

hasMRR

MRR Count / Total Deliveries

QC Gate

__Storage Efficiency__

occupies

Used m² / Available m²

WH Forecast

__Safety Conformance__

requiresPermit

Valid PTW/FRA %

HSE Docs

__🔶 7\. Ontological Integration View__

\[Material\]

   ⟶ \[Document: CI/PL/COO/eDAS\]

   ⟶ \[TransportEvent: LCT/SPMT\]

   ⟶ \[Location: Port → Yard → Site\]

   ⟶ \[Inspection: MRR/OSDR\]

   ⟶ \[Report: KPI/Dashboard\]

   ⟶ \[Governance: AI\-Logi\-Guide Rules\]

이 전체를 hvdc\-adopt\-ontology\.ttl로 export하면,
GitHub macho715/ontology\-insight에서 RDF 시각화 및 reasoning 연결 가능\.

__🔶 8\. 요약 메타 구조__

\{

 "Ontology":"hvdc\-adopt\-logiontology",

 "CoreClasses":\["Material","TransportEvent","Storage","Inspection","Permit","Actor","PortOperation"\],
 "PrimaryRelations":\["hasDocument","transportedBy","storedAt","requiresPermit","inspectedBy","approvedBy"\],
 "AlignmentModule":"AI\-Logi\-Guide v2\.1\+",
 "ExportFormat":\["RDF/XML","TTL","JSON\-LD"\]

\}

이 프레임이면, HVDC 프로젝트 전체가 __"문서\-행위\-공간\-주체\-규정"의 지식망__으로 정규화됩니다\.
다음 단계는 logiontology\.reasoning 모듈에서 __Rule\-based inference__ 정의 — 예컨대 "운송허가가 누락된 자재는 SiteReceiving 단계로 진행 불가" 같은 정책을 OWL constraint로 명세하면 완성됩니다\.

---

## Section 2: Node Infrastructure

### Source
- **Original File**: `1_CORE-02-hvdc-infra-nodes.md`
- **Version**: unified-3.0
- **Date**: 2025-10-25

아래는 __HVDC 프로젝트 물류 노드 네트워크(UAE 8거점)__를 __온톨로지 관점__으로 정의한 "작동 가능한 설계서"입니다.
핵심은 __Port(입항)·Hub(집하)·Site(수령/설치)__ 를 하나의 그래프(KG)로 엮고, __컨테이너·벌크·중량화물 전반__을 포함한 __DOT 허가·LCT 운항·MOSB 중심 체계·보존조건__ 같은 제약을 **Constraints**로 운영하는 것입니다.

__1) Visual — Ontology Stack (요약표)__

| __Layer__                         | __표준/근거__                                    | __범위__                                       | __HVDC 업무 매핑(예)__                                        |
| --------------------------------- | ------------------------------------------------ | ---------------------------------------------- | ------------------------------------------------------------- |
| __Upper__                         | __IOF/BFO Supply Chain Ontology__, __ISO 15926__ | 상위 개념(행위자/행위/자산/이벤트)·플랜트 라이프사이클 | 노드(Port/Hub/Site)·행위(Transport/Storage)·상태(MRR/OSDR) 프레임 |
| __Reference Data (Location)__     | __UN/LOCODE__, __ISO 3166__                      | 항만·지역 코드 표준화                          | Zayed(AEZYD), Mugharaq, MOSB(Mussafah), Site 좌표             |
| __Transport/Marine__              | __BIMCO SUPPLYTIME 2017__, __ISO 6346__          | OSV/LCT 운항, Container 코드                   | LCT 운항(MOSB→DAS 20h, →AGI 10h), Roll-on/off                |
| __Heavy Transport__               | __DOT UAE Permit System__                        | 중량물(>90톤) 육상 운송 허가                   | MIR/SHU 트랜스포머 SPMT 이송, DOT 승인 필수                   |
| __Port Access Control__           | __CICPA/ADNOC Gate Pass__                        | 항만·현장 출입 통제                            | MOSB/Port 게이트패스, ALS 운영 규정                           |
| __Preservation Standards__        | __Hitachi Specification__, __IEC__               | 보존 환경 조건                                 | Dry air/N₂ 충전, +5~40°C, RH ≤85%, 습도 모니터링            |
| __Quality Control__               | __MRR/OSDR/MIS Standards__                       | 자재 검수·상태 리포팅                          | 수령 검수(MRR), 해상 상태(OSDR), 설치 전 검증(MIS)            |
| __Offshore Operations__           | __ADNOC L&S (ALS) Regulations__                  | 해상 작업·리프팅·안전                          | DAS/AGI 하역, Sea fastening, 기상 제약                        |

Hint: MOSB는 **ADNOC Logistics & Services (ALS)** 관할 Yard(20,000㎡)이며, **삼성물산(SCT) 물류본부**가 상주하는 실질적 중앙 노드입니다.

__2) Domain Ontology — 클래스/관계(노드 단위 재정의)__

__핵심 클래스 (Classes)__

- __Node__(Port/Hub/OnshoreSite/OffshoreSite)
- __Party__(SCT/JDN/ALS/ADNOC/Vendor/Subcon)
- __Asset__(Transformer/Cable/CCU/Module/Container/Bulk_Cargo/Heavy_Cargo/General_Materials)
- __TransportEvent__(노드 간 이동 및 상태 변경 이벤트)
- __Warehouse__(IndoorWarehouse/OutdoorWarehouse/DangerousCargoWarehouse)
- __Transport__(InlandTruck/SPMT/LCT/Vessel)
- __Document__(CI/PL/BL/COO/eDAS/MRR/OSDR/MIS/DOT_Permit/FRA/PTW)
- __Process__(Import_Clearance/Yard_Storage/Preservation/Inland_Transport/Marine_Transport/Site_Receiving/Installation)
- __Event__(ETA/ATA/Berth_Start/Berth_End/CY_In/CY_Out/LCT_Departure/LCT_Arrival/MRR_Issued/OSDR_Updated)
- __Permit__(DOT_Heavy_Transport/FANR_Import/MOIAT_CoC/CICPA_GatePass/FRA/PTW)
- __Location__(UN/LOCODE: AEZYD/AEMFA, Berth, Laydown_Yard, Site_Gate)
- __Regulation__(Customs_Code/DOT_Rule/ADNOC_Policy/Hitachi_Preservation_Spec)
- __ShipmentUnit__(hvdc:ShipmentUnit — 중심 KG 클래스. 어떤 식별키로도 resolve되는 단위)
- __Shipment__(hvdc:Shipment — ShipmentUnit 묶음. 선적 단위)
- __JourneyLeg__(hvdc:JourneyLeg — 노드 간 이동 구간)
- __JourneyEvent__(hvdc:JourneyEvent — 물류 이벤트 기록)
- __WarehouseHandlingProfile__(hvdc:WarehouseHandlingProfile — **Flow Code 유일 소유 클래스**. WH 처리 이력 전체 기록)

**참조**: route_type 시스템 상세 구현은 [`CONSOLIDATED-02-warehouse-routing.md`](CONSOLIDATED-02-warehouse-routing.md)를 참조하세요.
- __KPI__(Port_Dwell/Transit_Time/Storage_Duration/MRR_SLA/OSDR_Timeliness/Delivery_OTIF)

__대표 관계 (Object Properties)__

- Node → connectedTo → Node (물류 연결성)
- MOSB → centralHubFor → (SHU, MIR, DAS, AGI) (중앙 허브 역할)
- Port → importsFrom → Origin_Country (수입 출발지)
- Transformer → transportedBy → LCT/SPMT (운송 수단)
- Cargo → storedAt → Node (보관 위치)
- Transport → requiresPermit → DOT_Permit/FRA (허가 요구)
- Site → receivesFrom → MOSB (수령 관계)
- Asset → hasDocument → MRR/OSDR (검수 문서)
- LCT_Operation → operatedBy → ALS (운영 주체)
- Node → governedBy → ADNOC_Policy/CICPA_Rule (규정 적용)
- Asset → preservedBy → Hitachi_Spec (보존 기준)

__데이터 속성 (Data Properties)__

- grossMass, dims(L×W×H), laydownArea_sqm, transitTime_hours, storageCapacity_teu, gatePassExpiryAt, permitId, preservationTemp_min, preservationTemp_max, relativeHumidity_max, dryAirPressure_bar, n2ChargePressure_bar, lctVoyageDuration_hours, distanceFromMOSB_nm, dotPermitRequired(boolean), customsCode, operatingOrg, sctTeamLocation, hasRouteType (DIRECT|WH_ONLY|MOSB_DIRECT|WH_MOSB|MIXED), shipment_stage, leg_sequence[], wh_handling_cnt (integer 0-3).
ShipmentUnit: hasKey→IdentityKey, hasCurrentStage, hasNextStage, hasPlannedETA, hasActualATA.
WarehouseHandlingProfile: confirmedFlowCode (0~5), wh_handling_cnt, flowConfirmationStatus, flowEvidenceSource, warehouseDwellDays.

__3) Use-case별 제약(Constraints) = 운영 가드레일__

__3.1 Port Import & Clearance Guard__

- __Rule-1__: Port(Zayed/Mugharaq) → hasDocument(CI, PL, BL, COO) 필수. 미충족 시 *Customs Clearance 차단*.
- __Rule-2__: 통관 코드 검증: ADNOC(47150) for Abu Dhabi, ADOPT(1485718/89901) for Dubai/Free Zone. 미일치 시 *BOE 제출 거부*.
- __Rule-3__: 방사선 기자재 → FANR Import Permit(유효 60일) 필수. 없으면 *입항 승인 보류*.

__3.2 MOSB Central Hub Operations__

- __Rule-4__: 모든 자재는 MOSB를 경유. MOSB → consolidates → Cargo_from_Ports AND MOSB → dispatches → (SHU/MIR/DAS/AGI).
- __Rule-5__: Yard 용량 체크: MOSB.storageCapacity(20,000㎡) > CurrentUtilization. 초과 시 *overflow yard* 확보 또는 *출하 스케줄 조정*.
- __Rule-6__: 보존 조건: Indoor storage, Temp(+5~40°C), RH(≤85%). 미준수 시 *자재 손상 리스크 알림* + *재검수(MRR) 필수*.

__3.3 Heavy Inland Transport (DOT Permit)__

- __Rule-7__: Cargo.grossMass > 90_ton → DOT_Permit 필수. 없으면 *MIR/SHU 이송 금지*.
- __Rule-8__: SPMT 이송 시 routeApproval + escortVehicle 필수. 미확보 시 *이송 연기*.
- __Rule-9__: Laydown area capacity: SHU(10,556㎡), MIR(35,006㎡). 용량 초과 시 *site receiving schedule 재조정*.

__3.4 Marine Transport (LCT Operations)__

- __Rule-10__: LCT_Operation → operatedBy → ALS (ADNOC L&S 전담). 비승인 선박 *출항 금지*.
- __Rule-11__: 항로 및 소요시간: MOSB→DAS(≈20h), MOSB→AGI(≈10h). 기상 경보 시 *출항 연기* (Weather-Tie 규칙).
- __Rule-12__: Roll-on/off, Sea fastening 필수. 검증 미완료 시 *선적 중단*.
- __Rule-13__: 보존 조건 유지: Dry air/N₂ 충전 상태 체크. 압력 이탈 시 *즉시 재충전* + *OSDR 업데이트*.

__3.5 Site Receiving & Quality Control__

- __Rule-14__: 자재 수령 시 MRR(Material Receiving Report) 즉시 발행. 미발행 시 *납품 미완료 처리*.
- __Rule-15__: 해상 현장(DAS/AGI) → OSDR(Offshore Storage & Delivery Report) 주기적 업데이트. 지연 시 *상태 불명확 경고*.
- __Rule-16__: 설치 전 MIS(Material Installation Sheet) 최종 검증. 미통과 시 *설치 작업 보류*.

__3.6 Route Classification & Warehouse Stage System__

> **[핵심 원칙 — Dual System]**
> - **여정 분류**: `route_type` + `leg_sequence` + `shipment_stage` — Shipment 단위 전체 경로 표현
> - **창고 작업**: `wh_stage` (Flow Code) — WH In 이벤트 기준 창고 내부 단계 전용
> - 두 체계는 독립적이며 혼용 금지.

- __Route-Rule-1__: 모든 화물은 `route_type` 부여 필수. **확정 기준: `leg_sequence` 노드 배열 확정 시점.**
  - **DIRECT**: Port→Site — WH 미경유
  - **WH_ONLY**: Port→WH→Site — 창고 경유, 육상 현장
  - **MOSB_DIRECT**: Port→MOSB→Site — MOSB 경유, WH 없음
  - **WH_MOSB**: Port→WH→MOSB→Site — 창고 + MOSB 복합
  - **MIXED**: 다중 창고 / 미완료 / 예외
- __Route-Rule-2__: `wh_handling_cnt` = `leg_sequence`에서 "WH" 등장 횟수 자동 산출(0~3). 계획(예정) 경유 포함 금지.
- __WH-Rule-1__: WH In 이벤트가 기록되지 않은 화물의 `wh_stage`는 미설정(null). 잠정 상태에서 `wh_stage` 확정값 표시 금지.
- __WH-Rule-2__: `wh_stage` 허용값: `FC-RCV | FC-PUT | FC-STR | FC-PCK | FC-STG | FC-DSP`. 범위 외 값 감지 시 *데이터 검증 실패*.
- __WH-Rule-3__: `wh_stage`는 `hvdc:Shipment`에 직접 부여 금지 — `hvdc:WarehouseEvent`에만 설정.


__3.7 Journey Stage Vocabulary (15단계 표준)__

| Stage# | Journey Stage | 설명 | WH 이벤트 |
|--------|--------------|------|-----------|
| 1 | `PLANNING` | 도착 전, 예약, 문서 준비 | — |
| 2 | `ORIGIN_DISPATCH` | 해외/국내 출발 운송 | — |
| 3 | `PORT_ENTRY` | UAE 진입 (Port/Air) | — |
| 4 | `TERMINAL_HANDLING` | Port berth/gate/release | — |
| 5 | `CUSTOMS_CLEARANCE` | eDAS, BL, Declaration | — |
| 6 | `INLAND_HAULAGE` | Port → 다음 노드 | — |
| 7 | `WH_RECEIPT` | **WH In 이벤트 발생** → `WarehouseHandlingProfile` 시작 | ✅ |
| 8 | `WH_STORAGE` | 보관 · 보존 · 재고 관리 | ✅ |
| 9 | `WH_DISPATCH` | 창고 출고 | ✅ |
| 10 | `MOSB_STAGING` | **Offshore Staging** (MOSB) | — |
| 11 | `OFFSHORE_TRANSIT` | LCT / Barge 해상 운송 | — |
| 12 | `SITE_RECEIVING` | MRR / OSDR / ITP | — |
| 13 | `SITE_STORAGE` | 현장 보관 · Laydown | — |
| 14 | `MATERIAL_ISSUE` | MIS, 시공 지원 | — |
| 15 | `CLOSEOUT` | 반출 · 회수 · Close-out | — |

> `WarehouseHandlingProfile.confirmedFlowCode` 는 **Stage 7~9** 범위에서만 생성·확정된다.
__4) 최소 예시(표현) — JSON-LD (요지)__

```json
{
  "@context": {
    "hvdc": "https://hvdc-project.ae/ontology#",
    "geo": "http://www.w3.org/2003/01/geo/wgs84_pos#",
    "time": "http://www.w3.org/2006/time#"
  },
  "@type": "hvdc:LogisticsRoute",
  "id": "HVDC-FLOW-2025-10-001",
  "origin": {
    "@type": "hvdc:Port",
    "name": "Zayed Port",
    "locode": "AEZYD",
    "customsCode": "47150",
    "location": "Abu Dhabi"
  },
  "centralHub": {
    "@type": "hvdc:Hub",
    "name": "MOSB",
    "operatedBy": "ADNOC L&S",
    "sctTeamLocation": true,
    "storageCapacity_sqm": 20000,
    "role": "Central consolidation and dispatch hub"
  },
  "destinations": [
    {
      "@type": "hvdc:OnshoreSite",
      "name": "SHUWEIHAT (SHU)",
      "laydownArea_sqm": 10556,
      "receivesFrom": "Sweden",
      "transportMode": "Inland_SPMT",
      "requiresDOT": true
    },
    {
      "@type": "hvdc:OnshoreSite",
      "name": "MIRFA (MIR)",
      "laydownArea_sqm": 35006,
      "receivesFrom": "Brazil",
      "transportMode": "Inland_SPMT",
      "requiresDOT": true
    },
    {
      "@type": "hvdc:OffshoreSite",
      "name": "DAS Island",
      "cluster": "Zakum",
      "transportMode": "LCT",
      "voyageDuration_hours": 20,
      "preservationMethod": "Dry_air_N2"
    },
    {
      "@type": "hvdc:OffshoreSite",
      "name": "Al Ghallan Island (AGI)",
      "cluster": "Zakum",
      "transportMode": "LCT",
      "voyageDuration_hours": 10,
      "parallelTo": "DAS"
    }
  ],
  "hasDocument": [
    {"@type": "hvdc:CI", "status": "validated"},
    {"@type": "hvdc:PL", "status": "validated"},
    {"@type": "hvdc:BL", "status": "original"},
    {"@type": "hvdc:COO", "origin": "Brazil/Sweden"}
  ],
  "consistsOf": [
    {
      "@type": "hvdc:Transformer",
      "origin": "Brazil",
      "grossMass_ton": 120,
      "dims": {"l": 12.5, "w": 3.2, "h": 4.8},
      "requiresDOT": true,
      "preservationTemp": {"min": 5, "max": 40},
      "preservationRH_max": 85,
      "hasRouteType": "MOSB_DIRECT",
      "wh_handling_cnt": 1
    }
  ],
  "hasTransportEvent": [
    {
      "@type": "hvdc:TransportEvent",
      "hasCase": "HE-208221",
      "hasDate": "2025-05-13T08:00:00",
      "hasLocation": "DSV Indoor",
      "hasRouteType": "MOSB_DIRECT",
      "wh_handling_cnt": 1
    }
  ]
}
```

__5) 선택지(3) — 구축 옵션 (pro/con/$·risk·time)__

1. __Reference-first (표준 우선, 글로벌 호환)__

- __Pro__: UN/LOCODE·BIMCO·ISO 표준 즉시 적용, 대외 연계 용이.
- __Con__: HVDC 특화 제약(DOT/CICPA/ALS 규정) 반영 속도↓.
- __$__: 초기 낮음(₩·$$). __Risk__: 현장 커스터마이즈 지연. __Time__: 8–10주 MVP.

2. __Hybrid (표준+현장제약 동시)__ ← *추천*

- __Pro__: UN/LOCODE + MOSB 중심 체계 + DOT/LCT/보존 규칙 즉시 적용.
- __Con__: 스키마 복잡성↑.
- __$__: 중간. __Risk__: 초기 설계 공수. __Time__: 12–14주 POC→Rollout.

3. __Ops-first (현장 규칙 우선)__

- __Pro__: MOSB 운영·DOT 허가·LCT 스케줄 즉효.
- __Con__: 표준 정합 나중 기술부채.
- __$__: 낮음→중간. __Risk__: 글로벌 확장 시 재작업. __Time__: 6–8주.

__6) Roadmap (P→Pi→B→O→S + KPI)__

- __P(Plan)__: 스코프 확정(노드: 7개, 문서: CI/PL/BL/MRR/OSDR, 프로세스: Import/Storage/Transport/Receiving). __KPI__: 노드 정의 완전성 ≥ 100%.
- __Pi(Pilot)__: __MOSB Central Hub__ + __DOT Permit Guard__ 1현장 적용. __KPI__: Transit time ↓ 15%, DOT 지연 건수 ↓ 25%.
- __B(Build)__: __LCT Operations__ + __Preservation Monitoring__ + __MRR/OSDR 자동화__ 추가. __KPI__: 보존 이탈 건수 ↓ 30%, MRR SLA ≥ 95%.
- __O(Operate)__: 규칙/SHACL 자동검증, Slack/Telegram 알림, KPI 대시보드. __KPI__: 규칙 위반 건당 처리시간 ≤ 0.5h.
- __S(Scale)__: 7거점→글로벌 재사용, __UN/LOCODE Web Vocabulary__로 공개 스키마 매핑. __KPI__: 타 프로젝트 적용 공수 ↓ 40%.

__7) Data·Sim·BI (운영 숫자 관점)__

- __Transit Time Clock__: TransitStart = (Port CY Out or MOSB Dispatch) → 노드별 __Transit Clock__ 운영.
- __MOSB Capacity Forecast__: Util_t+1 = Util_t + Inbound - Outbound (ARIMA/Prophet 가능).
- __DOT Permit Lead Time__: 평균 승인 기간 추적, 지연 시 *대안 경로* 제시.
- __LCT Voyage Risk__: Weather score + Cargo weight + Voyage distance → 출항 적합성 판정.
- __Preservation Compliance__: Temp/RH 센서 데이터 실시간 수집 → 이탈 시 *자동 알림*.

__8) Automation (RPA·LLM·Sheets·TG) — Slash Cmd 예시__

- __/logi-master --fast node-audit__ → 7개 노드별 __CI/PL/BL/MRR 누락__ 탐지→import 차단.
- __/logi-master predict --AEDonly transit-time__ → MOSB→Site 경로별 예상 소요시간 + DOT 지연 반영.
- __/switch_mode LATTICE RHYTHM__ → MOSB 용량 알림 + LCT 스케줄 교차검증.
- __/visualize_data --type=network <nodes.csv>__ → 7-노드 관계망 시각화(방사형).
- __/weather-tie check --port=MOSB__ → 기상 경보→LCT 출항 연기 여부 판단.
- __/compliance-check DOT-permit__ → 중량물(>90톤) 대상 DOT 승인 상태 일괄 체크.

__9) QA — Gap/Recheck 리스트__

- __UN/LOCODE 정합성__: Zayed(AEZYD), Mugharaq 코드 재확인.
- __DOT 규정__: 90톤 임계값, 승인 절차, escortVehicle 요구사항 최신화.
- __ALS 운영 규정__: MOSB Yard 규칙, LCT 출항 승인 프로세스 변경 추적.
- __CICPA/GatePass__: 최신 출입 통제 정책, e-pass 디지털화 상태 확인.
- __Hitachi Preservation Spec__: 온습도 기준, Dry air/N₂ 충전 압력, 모니터링 주기 재검.
- __MRR/OSDR/MIS 양식__: 최신 템플릿 및 필수 필드 매핑 점검.

__10) Fail-safe "중단" 테이블 (ZERO 전략)__

| __트리거(중단)__                           | __ZERO 액션__                              | __재개 조건__                         |
| ------------------------------------------ | ------------------------------------------ | ------------------------------------- |
| CI/PL/BL/COO 미충족                        | Customs clearance 보류, Shipper 보완요청   | 필수 문서 완전성 ≥ 100%               |
| 통관코드 불일치(ADNOC/ADOPT)               | BOE 제출 중단, 코드 재확인                 | 올바른 코드 적용 확인                 |
| FANR Permit 부재(방사선 기자재)            | 입항 승인 보류, Vendor 퍼밋 요청           | 유효 FANR Permit 업로드(60일 이내)    |
| MOSB 용량 초과(>20,000㎡)                  | 추가 입고 중단, overflow yard 확보         | 용량 < 임계값 or 출하 완료            |
| 보존 조건 이탈(Temp/RH)                    | 자재 격리, 재검수(MRR) 필수                | 환경 조건 복구 + MRR Pass             |
| DOT Permit 부재(>90톤)                     | 내륙 이송 금지, DOT 승인 대기              | 유효 DOT Permit 발급                  |
| 기상 경보(LCT 출항 부적합)                 | LCT 출항 연기, 기상 재평가                 | Weather score < 임계값                |
| Sea fastening 검증 미완료                  | 선적 중단, 고박 재작업                     | Sea fastening 검증 Pass               |
| Dry air/N₂ 압력 이탈                       | 해상 운송 중단, 즉시 재충전 + OSDR 업데이트 | 보존 압력 정상 범위 복구              |
| MRR 미발행(자재 수령 후 24h 초과)          | 납품 미완료 처리, Site 검수팀 긴급 투입    | MRR 발행 + 승인                       |
| OSDR 업데이트 지연(해상 현장 >7일)         | 상태 불명확 경고, 현장 긴급 점검           | OSDR 최신화 + 보존 상태 확인          |
| MIS 최종 검증 미통과                       | 설치 작업 보류, QAQC 재검증                | MIS Pass + OE(Owner's Engineer) 승인 |

__11) 운영에 바로 쓰는 SHACL(요지)__

```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix hvdc: <https://hvdc-project.ae/ontology#> .

hvdc:PortNodeShape a sh:NodeShape ;
  sh:targetClass hvdc:Port ;
  sh:property [
    sh:path hvdc:hasDocument ;
    sh:minCount 4 ;  # CI, PL, BL, COO 필수
    sh:message "Port must have CI, PL, BL, COO documents"
  ] ;
  sh:property [
    sh:path hvdc:customsCode ;
    sh:minCount 1 ;
    sh:pattern "^(47150|1485718|89901)$" ;
    sh:message "Invalid customs code for UAE"
  ] .

hvdc:HeavyCargoShape a sh:NodeShape ;
  sh:targetClass hvdc:Transformer ;
  sh:property [
    sh:path hvdc:grossMass_ton ;
    sh:minInclusive 0.01
  ] ;
  sh:sparql [
    sh:message "Cargo >90 ton requires DOT Permit" ;
    sh:select """
      SELECT $this
      WHERE {
        $this hvdc:grossMass_ton ?mass .
        FILTER (?mass > 90)
        FILTER NOT EXISTS { $this hvdc:requiresPermit ?permit .
                           ?permit a hvdc:DOT_Permit }
      }
    """
  ] .

hvdc:MOSBCapacityShape a sh:NodeShape ;
  sh:targetClass hvdc:MOSB ;
  sh:property [
    sh:path hvdc:storageCapacity_sqm ;
    sh:hasValue 20000
  ] ;
  sh:sparql [
    sh:message "MOSB storage capacity exceeded" ;
    sh:select """
      SELECT $this
      WHERE {
        $this hvdc:currentUtilization_sqm ?util .
        $this hvdc:storageCapacity_sqm ?cap .
        FILTER (?util > ?cap)
      }
    """
  ] .

hvdc:PreservationShape a sh:NodeShape ;
  sh:targetClass hvdc:Asset ;
  sh:property [
    sh:path hvdc:preservationTemp_min ;
    sh:hasValue 5
  ] ;
  sh:property [
    sh:path hvdc:preservationTemp_max ;
    sh:hasValue 40
  ] ;
  sh:property [
    sh:path hvdc:preservationRH_max ;
    sh:maxInclusive 85
  ] .

# Route Classification 검증 규칙 (Dual System)
# route_type: Shipment 여정 전체 분류 (leg_sequence 기반)
# wh_stage: WH In 이벤트 기준 창고 내부 전용 코드
hvdc:ShipmentRouteShape a sh:NodeShape ;
  sh:targetClass hvdc:Shipment ;
  sh:property [
    sh:path hvdc:hasRouteType ;
    sh:in ("DIRECT" "WH_ONLY" "MOSB_DIRECT" "WH_MOSB" "MIXED") ;
    sh:minCount 1 ;
    sh:message "route_type 누락 — leg_sequence 확인 필요"
  ] ;
  sh:property [
    sh:path hvdc:wh_handling_cnt ;
    sh:datatype xsd:integer ;
    sh:minInclusive 0 ;
    sh:maxInclusive 3 ;
    sh:message "wh_handling_cnt 범위 오류 (0~3, 실제 WH In 이벤트만 산출)"
  ] .

# Warehouse Stage 검증 규칙 (WH 내부 전용)
hvdc:WarehouseStageShape a sh:NodeShape ;
  sh:targetClass hvdc:WarehouseEvent ;
  sh:property [
    sh:path hvdc:wh_stage ;
    sh:in ("FC-RCV" "FC-PUT" "FC-STR" "FC-PCK" "FC-STG" "FC-DSP") ;
    sh:minCount 1 ;
    sh:message "wh_stage는 WH 내부에서만 설정 가능 (FC-RCV~FC-DSP)"
  ] ;
  sh:sparql [
    sh:message "wh_stage는 shipment_stage=WH_INBOUND 이후에만 설정 가능" ;
    sh:select """
      SELECT $this
      WHERE {
        $this hvdc:wh_stage ?ws .
        FILTER NOT EXISTS {
          $this hvdc:hasWHInEvent ?whEvent .
          ?whEvent hvdc:eventType "WH_IN" ;
                   hvdc:confirmed true .
        }
      }
    """
  ] .
```

__12) GitHub·재사용__

- 리포지토리 __macho715/hvdc-node-ontology__에 __/models (TTL/JSON-LD)__, __/rules (SHACL)__, __/mappings (UN-LOCODE/CICPA/DOT)__ 디렉토리 구조 권장.
- MOSB 중심 흐름은 __Node → centralHubFor → Site__ 룰로 두고, __/mappings/mosb-dispatch.csv__로 관리.
- LCT 운항 스케줄은 __/data/lct-operations.json__으로 버전 관리.

__13) Assumptions & Sources__

- __가정:__ MOSB는 모든 자재의 필수 경유지. DOT 90톤 임계값은 UAE 법규 기준. ALS 운영 규정은 ADNOC L&S 내부 정책 따름. CICPA/e-pass는 현장별 차이 존재(현장 공지 우선).
- __표준/근거:__ UN/LOCODE, BIMCO SUPPLYTIME 2017, ISO 6346(Container), DOT UAE Heavy Transport Regulation, CICPA/ADNOC Gate Pass Policy, Hitachi Preservation Specification, IEC Standards, HVDC Material Handling Workshop 2024-11-13.

__14) 다음 액션(짧게)__

- __/logi-master --fast node-audit__ 로 7개 노드 대상 __필수 문서·허가__ 일괄 점검,
- __/switch_mode LATTICE__ 로 __MOSB 용량__ 및 __DOT 지연__ 모니터링 시작,
- __/visualize_data --type=network <hvdc-nodes.csv>__ 로 __노드 관계망__ 시각화.

원하시면, 위 스택으로 __Port Import Guard__와 __MOSB Central Hub Operations__부터 SHACL/룰팩을 묶어 드리겠습니다.

---

# Part 2: HVDC Node Lifecycle Framework

## 개요

HVDC 프로젝트의 7개 물류 노드를 **온톨로지 관점**에서 정리하면, '물류 생명주기'를 하나의 **지식그래프(Ontology)**로 모델링할 수 있습니다.

핵심은 **"노드 간 행위(Activity)"가 아닌 "관계(Relation)"** 중심으로 보는 것입니다 — Port, Hub, Site, Actor, Document, Permit 간의 연결망.

__🔶 1. Ontology Root Class__

**hvdc-node-ontology**

| __Layer__ | __Ontology Domain__ | __대표 엔티티__                        | __관계 키(Relation)__                                |
| --------- | ------------------- | -------------------------------------- | ---------------------------------------------------- |
| __L1__    | Physical Stream       | Cargo, Port, MOSB, Site, LCT, SPMT    | movesFrom, movesTo, storedAt, consolidatedAt         |
| __L2__    | Document Stream       | CI, PL, BL, COO, eDAS, MRR, OSDR, MIS | certifies, refersTo, attachedTo, validates           |
| __L3__    | Actor Stream          | SCT, JDN, ALS, ADNOC, Vendor, Subcon  | responsibleFor, operates, approves, reportsTo        |
| __L4__    | Regulatory Stream     | DOT, FANR, MOIAT, CICPA, Customs      | requiresPermit, compliesWith, auditedBy, governedBy  |
| __L5__    | System Stream         | eDAS, SAP, NCM, LDG, KPI Dashboard    | feedsDataTo, validates, monitoredBy, alertsOn        |

__🔶 2. Core Classes (from Workshop + Verified Facts)__

| __Class__               | __Subclass of__ | __Description__                                              | __Onto-ID__       |
| ----------------------- | --------------- | ------------------------------------------------------------ | ----------------- |
| __Node__                | Location        | 물류 거점(Port/Hub/OnshoreSite/OffshoreSite)                | hvdc-loc-node     |
| __Cargo__               | Asset           | 자재 및 기자재(Transformer, Cable, CCU, Module)              | hvdc-asset-cargo  |
| __TransportEvent__      | Activity        | Inland(SPMT), Marine(LCT), Offloading, Receiving             | hvdc-act-trans    |
| __Storage__             | Process         | Yard Storage, Preservation(Dry air/N₂), Laydown              | hvdc-proc-stor    |
| __Inspection__          | Process         | MRR(Material Receiving), OSDR(Offshore Status), MIS(Install) | hvdc-proc-insp    |
| __Permit__              | Document        | DOT Heavy Transport, FANR Import, CICPA GatePass, FRA, PTW   | hvdc-doc-perm     |
| __Actor__               | Agent           | SCT Logistics Team, ADNOC L&S, Vendor, Subcon                | hvdc-agent-role   |
| __PortOperation__       | Activity        | Import Clearance, CY In/Out, Customs BOE                     | hvdc-act-port     |
| __PreservationStandard__ | Specification   | Hitachi Spec(Temp/RH), Dry air/N₂ Charging                   | hvdc-spec-presrv  |

__🔶 3. Relation Model (Partial)__

```turtle
Cargo --hasDocument--> MRR
Cargo --transportedBy--> TransportEvent
TransportEvent --departsFrom--> MOSB
TransportEvent --arrivesAt--> Site
TransportEvent --requires--> DOT_Permit
DOT_Permit --approvedBy--> DOT_Authority
Storage --locatedAt--> MOSB
Storage --monitoredBy--> SCT_Team
Inspection --reportedAs--> MRR/OSDR/MIS
Actor(SCT) --usesSystem--> eDAS
LCT_Operation --operatedBy--> ALS
Site --receivesFrom--> MOSB
MOSB --consolidates--> Cargo_from_Ports
Port(Zayed) --importsFrom--> Brazil
Port(Mugharaq) --importsFrom--> Sweden
```

이 관계망은 `hvdc-node-ontology.ttl`로 구현 가능:

```turtle
:MOSB rdf:type :Hub ;
      :hosts :SCT_Logistics_Team ;
      :operatedBy :ALS ;
      :storageCapacity_sqm 20000 ;
      :consolidates :Cargo_from_Zayed, :Cargo_from_Mugharaq ;
      :dispatches :SHU, :MIR, :DAS, :AGI .

:TR_001 rdf:type :Transformer ;
        :origin "Brazil" ;
        :grossMass_ton 120 ;
        :hasDocument :MRR_20241113 ;
        :storedAt :MOSB ;
        :transportedBy :SPMT_Operation_20241120 ;
        :requiresPermit :DOT_Permit_20241115 ;
        :preservedBy :Hitachi_Spec .

:SPMT_Operation_20241120 rdf:type :InlandTransport ;
                          :departsFrom :MOSB ;
                          :arrivesAt :MIR ;
                          :requiresPermit :DOT_Permit_20241115 ;
                          :operatedBy :Mammoet .

:LCT_Operation_20241125 rdf:type :MarineTransport ;
                         :departsFrom :MOSB ;
                         :arrivesAt :DAS ;
                         :voyageDuration_hours 20 ;
                         :operatedBy :ALS ;
                         :cargo :TR_002 ;
                         :preservationMethod "Dry_air_N2" .
```

__🔶 4. Lifecycle Ontology (Node-based Material Flow)__

__Stage 1 – Import & Clearance__
→ arrivesAt(Port: Zayed/Mugharaq) → hasDocument(CI, PL, BL, COO) → customsClearedBy(ADNOC/ADOPT) → storedAt(Port Yard)

__Stage 2 – Consolidation at MOSB__
→ transportedBy(Inland Truck) → consolidatedAt(MOSB) → storedAt(MOSB Yard 20,000㎡) → preservedBy(Hitachi Spec: +5~40°C, RH≤85%)

__Stage 3 – Inland Transport (Onshore Sites)__
→ requiresPermit(DOT >90ton) → transportedBy(SPMT) → arrivesAt(SHU/MIR) → inspectedBy(QAQC) → resultsIn(MRR)

__Stage 4 – Marine Transport (Offshore Sites)__
→ requiresPermit(FRA) → transportedBy(LCT) → operatedBy(ALS) → arrivesAt(DAS/AGI ≈10~20h) → resultsIn(OSDR) → preservationMonitored(Dry air/N₂)

__Stage 5 – Installation Preparation__
→ finalInspection(MIS) → approvedBy(OE) → installedAt(Site) → commissionedBy(Hitachi/Vendor)

__🔶 5. Alignment with AI-Logi-Guide__

| __Ontology Node__      | __대응 모듈__     | __기능적 의미__                 |
| ---------------------- | ----------------- | ------------------------------- |
| Node                   | mapping           | 7-거점 좌표·연결성              |
| Activity               | pipeline          | Import→Storage→Transport→Install |
| Document               | rdfio, validation | CI/PL/BL/MRR/OSDR triple 구조   |
| Agent                  | core              | SCT/ALS/ADNOC 역할/권한 모델    |
| Permit                 | compliance        | DOT/FANR/CICPA 규제 검증        |
| RiskEvent              | reasoning         | Weather-Tie·Delay 추론          |
| Report                 | report            | KPI/MRR/OSDR 리포트 생성        |

__🔶 6. Semantic KPI Layer (Onto-KPI)__

| __KPI Class__              | __Onto Property__ | __계산식__                         | __Source__      |
| -------------------------- | ----------------- | ---------------------------------- | --------------- |
| __Port Dwell Time__        | portDwellDays     | (CY Out - CY In) days              | Port Event Log  |
| __MOSB Storage Duration__  | storageDays       | (Dispatch - Arrival) days          | MOSB Yard Data  |
| __Transit Time Accuracy__  | meetsETA          | ETA vs Actual ≤12%                 | Transport Event |
| __MRR SLA Compliance__     | mrrIssuedWithin   | MRR Issued ≤ 24h after Receiving   | QC Gate         |
| __OSDR Timeliness__        | osdrUpdatedWithin | OSDR Updated ≤ 7 days              | Offshore Report |
| __DOT Permit Lead Time__   | permitApprovalDays | (Issued - Requested) days          | DOT System      |
| __Preservation Compliance__ | tempRHWithinSpec  | Temp(5~40°C) AND RH(≤85%) %        | Sensor Data     |
| __Flow Code Distribution__ | flowCodeCoverage | Count per Flow Code (0~5, v3.5) — WH 입고 확정 기준 | Transport Events (WH In confirmed) |

__🔶 7. Ontological Integration View__

```
[Origin: Sweden/Brazil]
     │
     ▼
[Port: Zayed/Mugharaq]
  ⟶ [Document: CI/PL/BL/COO]
  ⟶ [Customs: BOE·Duty]
     │
     ▼
[Hub: MOSB (Central Node)]
  ⟶ [Storage: 20,000㎡ Yard]
  ⟶ [Preservation: Hitachi Spec]
  ⟶ [Actor: SCT Team + ALS]
     │
     ├──→ [Onshore: SHU/MIR]
     │     ⟶ [Transport: SPMT + DOT Permit]
     │     ⟶ [Inspection: MRR]
     │     ⟶ [Installation: MIS + OE Approval]
     │
     └──→ [Offshore: DAS/AGI]
           ⟶ [Transport: LCT + FRA + ALS]
           ⟶ [Inspection: OSDR]
           ⟶ [Preservation: Dry air/N₂]
           ⟶ [Installation: MIS + Hitachi]
```

이 전체를 `hvdc-node-ontology.ttl`로 export하면,
GitHub macho715/hvdc-node-ontology에서 RDF 시각화 및 reasoning 연결 가능.

__🔶 8. 요약 메타 구조__

```json
{
 "Ontology": "hvdc-node-ontology",
 "CoreNodes": [
   {"name": "Zayed Port", "type": "Port", "locode": "AEZYD"},
   {"name": "Mugharaq Port", "type": "Port", "locode": null},
   {"name": "MOSB", "type": "Hub", "role": "Central consolidation", "capacity_sqm": 20000},
   {"name": "SHUWEIHAT (SHU)", "type": "OnshoreSite", "laydown_sqm": 10556},
   {"name": "MIRFA (MIR)", "type": "OnshoreSite", "laydown_sqm": 35006},
   {"name": "DAS Island", "type": "OffshoreSite", "voyageTime_h": 20},
   {"name": "Al Ghallan (AGI)", "type": "OffshoreSite", "voyageTime_h": 10}
 ],
 "PrimaryRelations": [
   "Port → consolidatedAt → MOSB",
   "MOSB → dispatches → (SHU, MIR, DAS, AGI)",
   "Cargo → transportedBy → (SPMT, LCT)",
   "Transport → requiresPermit → (DOT, FANR, CICPA)",
   "Site → receivesFrom → MOSB",
   "Asset → hasDocument → (MRR, OSDR, MIS)",
   "Operation → operatedBy → (SCT, ALS, ADNOC)"
 ],
 "AlignmentModule": "AI-Logi-Guide v2.1+",
 "ExportFormat": ["RDF/XML", "TTL", "JSON-LD"],
 "VerifiedSource": "HVDC Material Handling Workshop 2024-11-13"
}
```

이 프레임이면, HVDC 프로젝트 전체가 __"Port-Hub-Site의 지식망"__으로 정규화됩니다.
다음 단계는 `hvdc-node-ontology.reasoning` 모듈에서 __Rule-based inference__ 정의 — 예컨대 "DOT Permit가 누락된 중량물(>90톤)은 Site 이송 불가" 같은 정책을 OWL constraint로 명세하면 완성됩니다.

---

## 🔶 9. 핵심 노드 상세 정보 (검증된 사실 기반 - v3.0)

### 9.1 Core Node Set (8개 노드)

| 구분                                       | 유형                | 위치                       | 주요 기능                                                                                          | 연계 관계                                  |
| ------------------------------------------ | ------------------- | -------------------------- | -------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| **자이드항 (Zayed Port)**                  | 해상입항노드         | 아부다비                   | **중량 및 일반 벌크 화물 처리항.** 변압기, 케이블드럼, 구조물 등 비컨테이너 자재 중심. SCT·JDN 확보 야드(1,100㎡) 존재. ADNOC 코드(47150)로 통관. | → MOSB / MIR                               |
| **칼리파항 (Khalifa Port)**                | 해상입항노드         | 아부다비                   | **컨테이너 전용항.** 해외(한국, 일본 등) 공급 자재 대부분 도착. ADNOC L&S 또는 DSV 관리하 적출. 자재는 트럭으로 MOSB 또는 현장 직송. | → MOSB / MIR / SHU                         |
| **제벨알리항 (Jebel Ali Port)**             | 해상입항노드 (특수케이스) | 두바이               | Free Zone 및 비ADNOC 공급사 사용. 일부 파이어파이팅, 전기부품 등 통관 후 ADOPT 코드로 재이송. SCT가 관세 납부 후 ADNOC에 비용 환급 요청. | → MOSB (재통관 경유)                       |
| **MOSB (Mussafah Offshore Supply Base)**  | **중앙 물류 허브**  | 아부다비 무사파            | ADNOC L&S 운영 Yard (20,000㎡). **SCT 물류본부 상주.** 해상화물(LCT/RoRo/Barge) 집하 및 적재. 컨테이너·CCU(약 80EA) 임시보관. 운송계획·FRA·Permit·Gate Pass 관리. | ← Zayed/Khalifa/Jebel Ali → MIR/SHU/DAS/AGI |
| **MIRFA SITE (MIR)**                       | 육상 현장           | 아부다비 서부              | 내륙 시공현장. 컨테이너·일반자재·중량화물 도착 후 설치. 35,000㎡ Laydown. 저장컨테이너(방화, 온도조절) 비치. 자재관리절차(SJT-19LT-QLT-PL-023) 적용. | ← MOSB / Zayed / Khalifa                  |
| **SHUWEIHAT SITE (SHU)**                   | 육상 현장           | 아부다비 서부              | 내륙 시공현장. Laydown 약 10,500㎡. 공간 제약으로 **운송순서·HSE 통제** 중요. 전기/기계류, 포설장비 등 일반자재 도착지. | ← MOSB / Khalifa                           |
| **DAS ISLAND (DAS)**                       | 해상 현장           | ADNOC 해역 (Zakum Cluster) | ADNOC 운영 해상기지. MOSB→LCT 약 20시간 항해. 컨테이너·벌크 혼재 화물 하역 및 적재장 운영. ADNOC HSE 표준, Lifting inspection, Gate control 준수. | ← MOSB                                     |
| **AL GHALLAN ISLAND (AGI)**                | 해상 현장           | ADNOC 해역 (DAS 병렬)     | MOSB→LCT 약 10시간 항해. 일반자재, 설치기구, 전기부품 운송. Laydown 47,000㎡ (3구역), 보안 강화. ADNOC L&S 동일 절차로 하역·보존 수행. | ← MOSB / ↔ DAS                             |

### 9.2 물류 흐름 구조 (v3.0 - All Cargo Types)

```
[해외 공급사 (Asia/EU 등)]
         ↓ (선적)
┌───────────────────────────┐
│   ZAYED PORT   KHALIFA PORT   JEBEL ALI PORT   │
└───────────────────────────┘
         ↓ (통관·운송)
             MOSB
    ┌────────┼────────┐
    ↓        ↓        ↓
  MIR      SHU     DAS / AGI
```

* **컨테이너 화물:** 주로 Khalifa Port → MOSB → 육상/해상 현장.
* **일반 벌크 화물:** Zayed Port → MOSB 또는 직접 MIR/SHU.
* **특수자재(Free Zone):** Jebel Ali → 재통관 → MOSB 경유.

### 9.3 기능 계층 구조 (v3.0)

| 계층                       | 설명                                     | 대표 노드                     |
| -------------------------- | ---------------------------------------- | ----------------------------- |
| **① 입항·통관 계층**       | 선적서류 검토(CI/PL/COO/eDAS), BL Endorsement, 통관코드 관리 | Zayed, Khalifa, Jebel Ali    |
| **② 집하·분류 계층**       | Port cargo 집하, 임시보관, Crane/Forklift 배차, Gate Pass, FRA 관리 | **MOSB**                      |
| **③ 육상 운송·시공 계층**  | 컨테이너·벌크 화물의 도로 운송 및 현장 인수, MRR/MRI 관리 | MIR, SHU                      |
| **④ 해상 운송·설치 계층**  | LCT/Barge 출항, ADNOC 해상안전기준(HSE), 하역·보존 | DAS, AGI                      |

### 9.4 운영·관리 사실 (v3.0)

* **SCT 물류본부:** MOSB 상주. 현장·항만·해상 노드 통합 관리.
* **운항 주체:** ADNOC Logistics & Services (ALS).
* **통관 관리:** ADOPT/ADNOC 코드 사용.
* **저장 관리:** MOSB + 인근 실내창고(6,000~8,000㎡) + 각 Site Laydown.
* **운송수단:** 트럭 / SPMT / CCU / LCT / Barge.
* **HSE 절차:** FRA, Method Statement, PTW, Lifting Certificate.
* **문서 체계:** MRR, MRI, OSDR, Gate Pass, Delivery Note.
* **중량물 운송 허가:** DOT 승인 필수(90톤 초과).
* **보존조건:** 실내 +5~40 °C, RH ≤ 85 % (Hitachi 권장).
* **항로거리:** MOSB→DAS 약 20 h, MOSB→AGI 약 10 h.

### 9.5 온톨로지 관계 (3중 구조 요약 - v3.0)

```
(MOSB, hosts, SCT_Logistics_Team)
(MOSB, consolidates, Container_and_Bulk_Cargo)
(MOSB, dispatches, MIR)
(MOSB, dispatches, SHU)
(MOSB, dispatches, DAS)
(MOSB, dispatches, AGI)
(Zayed_Port, handles, Heavy_and_Bulk_Cargo)
(Khalifa_Port, handles, Container_Cargo)
(Jebel_Ali_Port, handles, Freezone_Shipments)
(DAS, connected_to, AGI)
(MIR, and, SHU are Onshore_Receiving_Sites)
```

### 9.6 검증된 사실 요약 (v3.0)

1. **입항 및 통관:**
   * 중량·벌크 화물 → 자이드항,
   * 컨테이너 화물 → 칼리파항,
   * 일부 특수품 → 제벨알리항(Free Zone).

2. **중앙 허브(MOSB):**
   * 모든 화물의 **집하·검수·보존·해상출하** 기능 수행.
   * SCT 물류팀 본사 및 ADNOC L&S 현장운영팀 상주.

3. **육상 현장(MIR·SHU):**
   * 설치 및 시공 자재 수령지.
   * Laydown 내 임시보관, MRR/MRI·HSE 통제 중심.

4. **해상 현장(DAS·AGI):**
   * LCT 운항으로 자재 운송 및 하역.
   * ADNOC 해상안전 절차에 따라 작업.

5. **전체 구조:**
   > "**Zayed/Khalifa/Jebel Ali → MOSB → (MIR·SHU·DAS·AGI)**"
   > 형태의 다계층 물류 체계이며, **MOSB가 중앙 온톨로지 노드**로 작동한다.

---

**결론:**

HVDC 물류 시스템은 트랜스포머뿐 아니라 **컨테이너·벌크·일반자재 전반을 포함하는 복합 네트워크**이다.
모든 자재는 항만(자이드·칼리파·제벨알리)에서 통관 후 **MOSB를 중심으로 집하·분류·출하**되며,
최종 목적지는 육상(MIR·SHU) 또는 해상(DAS·AGI)으로 구분된다.
MOSB는 이 전체 체계의 **운영·정보·의사결정의 중심 노드**다.

---

🔧 **추천 명령어:**
`/logi-master node-audit` [8개 노드 필수 문서·허가 일괄 점검 - MOSB 중심 검증]
`/visualize_data --type=network hvdc-nodes` [노드 관계망 시각화 - 다계층 구조 확인]
`/compliance-check DOT-permit` [중량물(>90톤) DOT 승인 상태 검증 - MIR/SHU 대상]
`/cargo-route analyze --type=all` [컨테이너·벌크·중량화물 전체 흐름 분석]
`/flow-code validate --strict` [Flow Code + WH Handling 일치성 검증 - 데이터 품질 보장]


