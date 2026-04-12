ExecSummary

The corpus is broad enough to cover full HVDC project logistics - core framework, customs, port/terminal, offshore/LCT, warehouse, site receiving, transformer handling, bulk cargo, cost, OCR, and communication - so the problem is not lack of scope. The problem is semantic control: the current documents are not yet fit to serve as the master HVDC Logistics ontology reference because FLOW CODE has been expanded into a cross-domain route/customs/document/cost status language, which conflicts with your required interpretation and breaks clean graph design.

The salvage path is clear: keep the end-to-end operational coverage, but rebuild the document around a canonical backbone of master data + execution transactions + documents + events/milestones + exceptions/claims + cost, and reserve FLOW CODE for warehouse internal operations only. For external benchmark, the right target stack is GS1 EPCIS for event-centric visibility, DCSA Track & Trace for shipping/container milestones, UN/CEFACT BSP-RDM + JSON-LD vocabulary for semantic reference data, WCO Data Model for customs, and ICC Incoterms 2020 + current MOIAT ECAS service logic for commercial/compliance controls.

I excluded archive/legacy history as the design baseline and relied on the current consolidated corpus and current hub index.

Section 1. Executive Assessment
Criterion	Assessment	Verdict
Suitable as master HVDC Logistics reference	Valuable source corpus, but not yet structurally master-ready	No
Reflects full project logistics perspective	Yes; customs, port, offshore, warehouse, site receiving, heavy lift, and cost are all present	Yes, but uneven
FLOW CODE correctly restricted to warehouse usage	Port, OCR, invoice-cost, material handling, bulk cargo, and operations docs all expand FLOW CODE outside warehouse scope	No - critical defect
Terminology standardized	Mixed standard terms, local shorthand, domain overlap, and duplicated semantics	No
Ontology / KG conversion feasible	Feasible after redesign; currently blocked by identity, milestone, and FLOW CODE collisions	Yes, after redesign
Full-chain query traceability from any key	Partially present via multi-key concepts, but not guaranteed across project-vendor-shipment-customs-warehouse-site-cost chain	Partial only

The current corpus already contains the raw ingredients of a usable master model: the core framework defines Parties, Assets, Documents, Processes, Events, Regulations, Locations, and KPIs; material-handling carries the operational chain from customs to site receiving; port ops contributes a multi-key identity and invoice/service pattern; site receiving contributes MRS/MIS/MRR/MRI/OSDR logic; and heavy-lift/offshore sections contribute specialized execution detail. What is missing is a single canonical semantic spine.

Section 2. Major Findings and Structural Issues
2.1 Major findings
Scope is broad, but the document is not organized as a master control model.
The corpus covers framework, ports, customs, offshore/LCT, warehouse, site receiving, transformer handling, invoice-cost, OCR, and communication. However, those domains are documented as adjacent ontology notes, not as one controlled operating model with a single identity hierarchy and milestone dictionary.
FLOW CODE is the primary structural blocker.
It is currently used as a lifecycle/routing language in port operations, as an OCR-extracted document field, as a pricing driver in invoice-cost, as the full end-to-end route model in material handling, as the marine pattern in bulk/LCT, and as a KPI axis in operations management. That violates your rule that FLOW CODE must be warehouse-only.
Warehouse concepts are being used to represent total logistics concepts.
The current route code uses patterns such as Port -> WH -> MOSB -> Site and treats MOSB/offshore routing as part of “Flow Code.” That is a shipment-routing construct, not a warehouse-internal movement construct.
Canonical entity boundaries are weak.
The corpus uses overlapping terms such as Material, Cargo, Case, Item, Shipment, LogisticsFlow, TransportEvent, PortCall, and Receiving, but it does not define one parent-child identity policy that shows exactly what contains what, and which identifiers belong to which object.
Master data, transaction data, document data, event data, exception data, and cost data are mixed together.
In many places, a section contains ontology classes, example JSON-LD, SHACL, KPIs, slash commands, and SOP content all at once. That is useful as working notes, but not as a master ontology reference.
Milestone logic is incomplete.
There is no single canonical milestone dictionary spanning vendor readiness -> packing -> pickup -> export -> terminal receipt -> loading/ATD -> ocean/transshipment -> ATA -> BOE -> DO -> gate-out -> warehouse receive -> put-away -> dispatch -> site receive -> inspection -> POD/GRN/handover -> claim/cost close. The closest thing is fragmented process text.
Identity resolution is strong only in pockets.
Port ops and invoice-cost already think in multi-key terms (OFCO/SAFEEN/ADP invoice no., Rotation no., Samsung Ref, HVDC Code, BL/Container/DO/Invoice/etc.), but this approach is not generalized into a project-wide identifier framework.
Site receiving is one of the strongest operational sections and should be preserved almost intact, but re-anchored.
The current corpus clearly defines delivery plan, unloading, PTW, MRR/MRI, inspection request, MRS/MIS, Construction Team approval, and OSDR/claim handling. This is good target-state downstream execution logic.
Heavy-lift / offshore execution detail is strong, but it belongs in a specialized extension layer, not the core master model.
The corpus contains strong transformer/LCT/offshore details: PTW, hot-work, working-over-water permit, tide table, lashing, stability, rigging, roll-on/off, and sail-away approval. These should remain, but as an OOG/marine extension ontology.
The external benchmark confirms the redesign direction.
Event/milestone modeling should be event-centric, not row-centric; GS1 EPCIS is explicitly built around visibility events, while DCSA T&T standardizes operational events along the end-to-end container journey. UNECE BSP-RDM / vocabulary is the right semantic reference layer, and WCO DM is the right customs package model.
2.2 FLOW CODE misuse map

The following usages must be corrected because they extend FLOW CODE beyond warehouse-internal operations.

Current domain	Current misuse	Why it is wrong	Correct replacement
Port Operations	assignedFlowCode at customs clearance; port KPIs by Flow Code	Port is deciding shipment routing, not warehouse internal movement	RoutingPattern, OffshoreTransitRequired, ImportRoutingDecision
Document OCR / LDG	extractedFlowCode from BL, invoice, packing list, customs declaration, DO	Documents evidence destination and route indicators, not warehouse codes	DestinationIndicator, RouteIndicator, MOSBLegIndicator
Invoice & Cost	Cost validation and rate logic by Flow Code	Cost is driven by service pattern / route composition, not warehouse flow	RouteBasedCostDriver, TariffApplicability
Material Handling	Flow Code 0-5 across import, customs, warehouse, offshore, site receipt	This is an end-to-end shipment route/status model	RoutingPattern + MilestoneStatus
Bulk Cargo / LCT	Flow Code 3/4/5 for MOSB/LCT paths	Marine transfer pattern is not warehouse flow	MarineRoutingPattern, OffshoreTransferPattern
Operations Management	Flow Code as full Port->WH->MOSB->Site KPI axis	This is lifecycle routing analytics, not warehouse-internal logic	RoutingPatternAnalytics
Warehouse Flow doc itself	Port->WH->MOSB->Site embedded in “warehouse flow”	Even here, current meaning is broader than warehouse task flow	Split into WarehouseFlowCode and RoutingPattern

Hard redesign rule:

Keep FLOW CODE only for warehouse receiving, put-away, storage, internal transfer, picking, staging, dispatch, stock status, and warehouse task logic.
Rename the current 0-5 route model to Routing Pattern (or ShipmentRoutingPattern).
Model AGI/DAS/MOSB requirements as routing constraints / offshore-leg requirements, not as warehouse flow.
Section 3. Terminology Normalization Table
Existing term	Recommended standard term	Reason	Scope	Risk if uncorrected
Flow Code (used for Port -> WH -> MOSB -> Site)	Routing Pattern	Route shape is not warehouse-internal flow	Shipment / transport	Semantic collision
Flow Code 0 “Pre Arrival”	Pre-arrival Status	Pre-arrival is a shipment milestone, not warehouse flow	Pre-arrival	Wrong state machine
Flow Code 1 “Port -> Site”	Direct Delivery Pattern	Route descriptor	Shipment	Broken warehouse semantics
Flow Code 2 “Port -> WH -> Site”	Warehouse Consolidation Pattern	Route descriptor	Shipment	Confuses route vs warehouse task
Flow Code 3 “Port -> MOSB -> Site”	Offshore MOSB Routing Pattern	Marine/offshore route	Shipment / marine	Misclassifies MOSB logic
Flow Code 4 “Port -> WH -> MOSB -> Site”	Warehouse + Offshore Routing Pattern	Composite transport path	Shipment	Mixed semantics
Flow Code 5 “Mixed/Incomplete”	Routing Exception / Incomplete Route	Exception state, not warehouse flow	Exception	Unclear closure logic
A Stage	Import & Main Carriage Stage	Removes local shorthand	End-to-end	Ambiguous process language
B Stage	Offshore Transfer Stage	Removes local shorthand	Offshore	Ambiguous process language
Material Storage Code	Storage Requirement Class	It describes storage condition, not process flow	Storage	Wrong data typing
Case List	Cargo Unit Register	Better physical/logistics meaning	Packing / receipt	Weak package identity
Site Offloading	Site Unloading	Standard logistics wording	Site execution	Terminology inconsistency
Request for Inspection	Site Receiving Inspection Request	Clarifies process context	Site receiving	Ambiguous document usage
Material Receiving inspection Report	Material Receiving Report (MRR)	Normalize one document name	Site receiving	Duplicate document semantics
Materials Receiving Inspection	Material Receiving Inspection (MRI)	Normalize separate inspection artifact	Site receiving	Duplicate document semantics
Overage, Shortage & Damage Report	OSDR (Overage-Shortage-Damage Report)	Use standard acronym + long form	Exception / claim	Claim trace breaks
Port Storage / MOSB Yard	Port Laydown Yard / Marine Staging Yard	Distinguish storage from offshore transfer base	Port / marine	Location ambiguity
Delivery Plan	Site Delivery Schedule	Clarifies downstream execution use	Delivery / site	Wrong document mapping
Shipping (generic)	Ocean Freight / Marine Transport	Standard transport term	Shipment leg	Vague mode semantics
Site delivery status represented by Flow Code	Delivery Status / Site Receipt Status	Delivery completion is milestone logic	Site execution	Query failure
Section 4. End-to-End Process Rebuild

Design note: The current corpus is strongest from customs/port/offshore onward and at site receiving/heavy-lift execution. Steps 1-3 and 18-19 below are necessary target-state additions because they are not consistently formalized in the current corpus. Customs through site receiving is evidenced more strongly.

Step Name	Purpose	Input Document	Event	Status	Owner	Key Data Fields	Exception / Risk
1. Project / Package / PO Release	Establish logistics demand baseline	Project plan, Package list, PO, material master	Demand released	Planned	Project Logistics + Procurement	Project, Package No., PO No., Material Code, HVDC CODE, Site, Required Date, Incoterm	Gap: Package/PO chain not yet canonical
2. Vendor Readiness / Cargo Readiness	Confirm material available to ship	Vendor readiness notice, inspection release, case/package register	Cargo ready	Ready / Not ready	Vendor + Expeditor	Vendor code, Material code, Serial/Package IDs, Ready date	Readiness delay, QA hold
3. Packing / Marking / Labelling	Create cargo-unit identity	Packing List, Marking Sheet, CI draft	Packed	Packed	Vendor	Package No., Marks & Numbers, Qty, GW/NW, Volume, Dimensions, HS Code, Origin	Packing discrepancy
4. Pickup / Origin Haulage	Move cargo to export terminal	Pickup note, transport order	Picked up	In transit to export port	Forwarder / trucker	Shipment ref, Cargo Unit ID, Pickup DT, Origin	Damage, no-show truck
5. Export Customs Clearance	Clear origin formalities	CI, PL, COO, export declaration, permit if needed	Export cleared	Export cleared	Export broker / forwarder	Declaration no., HS code, consignee, exporter	Export hold
6. Terminal Receiving / Port Handling	Register cargo at terminal	Booking, gate-in record, terminal receipt	Terminal received	At terminal	Terminal / port agent	Port, Terminal, Gate-in time, Cargo/Container, Rotation/Booking	Terminal delay
7. Vessel Loading / Departure	Create main carriage leg	Stowage plan, BL/eBL, load list	Loaded / ATD	On board / Departed	Carrier + Port Agent	BL No., Rotation No., Vessel, Container No., ATD	Rollover, lashing issue
8. Ocean Freight / Transshipment	Track long-haul movement	Carrier milestones, transshipment notice	In transit / transshipped	In transit	Carrier	Leg ID, ETD, ETA, ATD, ATA, Transshipment Port	Delay, missed connection
9. Arrival Notice / Pre-arrival Review	Prepare import and downstream resources	Arrival notice, document pack, permit pack	Pre-arrival reviewed	Awaiting arrival	Broker + Project Logistics	ETA, BL No., consignee, permit status, site	Missing docs
10. Import Customs / BOE	Clear import into UAE	BL endorsement, attestation/eDAS, CI, PL, COO, BOE, permits	BOE submitted / cleared	Under clearance / Cleared	Import Broker + Consignee	BOE No., Code No., Duty, HS Code, MOIAT/FANR/DOT/CICPA refs	Customs hold, permit expiry
11. DO Release / Gate-out	Obtain cargo release	Delivery Order, release note, gate pass	DO released / gate-out	Released	Carrier/Agent + Broker	DO No., free time, gate-out DT, terminal	DEM/DET exposure
12. Inland Transport to WH / MOSB / Site	Execute domestic move	Transport order, route permit, heavy-haul permit if needed	Inland departed / arrived	En route	Forwarder / Heavy-haul / ALS	Truck/SPMT/LCT, origin, destination, ETA, permit no.	Access restriction, transport delay
13. Warehouse Receiving	Formal receipt into warehouse	Delivery note, PL, unloading checklist	Warehouse received	Received	Warehouse operator	Warehouse ID, Receipt DT, Cargo Unit ID, Qty, condition	Receipt mismatch
14. Put-away / Storage / Preservation	Store and preserve material	Put-away note, storage instruction, preservation log	Put-away completed	Available / blocked / quarantine	Warehouse + Preservation owner	Warehouse Location, Stock Status, Temp/Humidity class, preservation due date	Wrong bin, preservation failure
15. Picking / Staging / Dispatch	Prepare outbound issue	Pick list, dispatch note, load checklist	Picked / staged / dispatched	Staged / Dispatched	Warehouse + Site logistics	Dispatch ID, destination site, truck/LCT assignment	Short pick, wrong material
16. Offshore / Heavy-lift / OOG Execution	Execute MOSB/LCT/SPMT/crane/lashing/stability tasks	PTW, FRA, Method Statement, Tide Table, Lifting Plan, Lashing Plan, Stability Report	Marine staged / loaded / sail-away approved	Executed	ALS / Marine contractor / Heavy-lift contractor	Equip ID, Vessel, Lift ID, Weather window, Approval refs	HSE stop, lift failure
17. Site Delivery / Receiving / Inspection	Receive and inspect on site	Packing List, Delivery Note, PTW, MRR/MRI, ITP, MAR, MRS, MIS	Site arrived / inspected	Good / OSD	Site Logistics + Construction + QA/QC + OE	Site code, Arrival DT, Inspection result, MRR/OSDR No., MRS/MIS	Shortage, damage, rejection
18. POD / GRN / Handover	Confirm accepted handover	POD, GRN, acceptance record	Handover accepted	Closed-accepted	Site Stores + Construction	POD No., GRN No., acceptance date	Missing acknowledgement
19. Exception / Claim / NCR / Cost Closure	Close operational and financial exposure	OSDR, claim file, NCR, carrier invoice, cost report	Exception opened / closed	Open / Closed	QA/QC + Claims + Cost Control	Exception ID, Claim Ref, NCR Ref, Cost Code, Invoice Ref	Lingering claim/cost exposure
Section 5. Ontology Design Proposal
5.1 Canonical model layers

The redesigned ontology should be layered as follows:

Layer	Purpose	Main classes
Core Master Data	Stable reference data	Project, Package, PurchaseOrder, Vendor, MaterialMaster, Port, Terminal, Warehouse, WarehouseLocation, Site, Carrier, Forwarder, EquipmentResource
Execution Transactions	What moved / what happened	Shipment, ShipmentLeg, CargoUnit, Container, PortCall, CustomsEntry, ReleaseOrder, Delivery, WarehouseTask, SiteReceipt
Documents	Documentary evidence	CommercialInvoice, PackingList, BillOfLading, CertificateOfOrigin, BOE, DeliveryOrder, Permit, MRR, MRI, ITP, MAR, MRS, MIS, POD, GRN, OSDR
Events / Milestones	Planned / estimated / actual timepoints	MilestoneEvent, ArrivalEvent, ClearanceEvent, ReceiptEvent, PutAwayEvent, DispatchEvent, SiteInspectionEvent
Exceptions / Claims	Disruptions and resolution	Exception, Delay, Damage, Shortage, Overage, NCR, Claim
Cost / Finance	Monetary traceability	Invoice, InvoiceLine, CostTransaction, TariffRef, CostCode, DEMDETClock
Evidence / Communication	Provenance and action trail	CommunicationEvent, Alert, ApprovalAction, AuditRecord

This layered approach matches current best practice better than the present mixed-note structure. EPCIS is built around visibility events, DCSA T&T around standardized operational events, UNECE BSP-RDM around semantic supply-chain data, and WCO DM around cross-border customs exchange.

5.2 Minimum entity set: validation and redesign
Entity	Current state in corpus	Redesign rule / core attributes
Project	Present	projectId, projectName, country, status
Package	Gap / not clearly canonical	packageNo, packageType, scope, siteCode
Purchase Order	Gap / not clearly canonical	poNo, vendorCode, incoterm, currency, issueDate
Vendor	Partial	vendorCode, vendorName, country, role
MaterialMaster	Partial	materialCode, description, uom, hsCode, origin
HVDCCodeTag	Partial	hvdcCode, engineeringArea, siteRelevance, packageRelevance
Shipment	Partial	shipmentId, mode, status, plannedRoute
CargoUnit	Partial	cargoUnitId, packageNo, grossWeight, volume, dimensions
Container	Partial	containerNo, sealNo, isoType, freeTime
BillOfLading	Present	blNo, issueDate, carrier, portOfLoading, portOfDischarge
BOE / CustomsEntry	Partial	boeNo, customsStatus, duty, broker, clearanceDate
DeliveryOrder / ReleaseOrder	Partial	doNo, releaseDate, terminal, freeTime
Permit	Partial	permitNo, permitType, authority, expiryDate
Port	Present	portCode, UNLOCODE, portName, country
Terminal	Partial	terminalId, terminalName, berth, portId
Carrier	Partial	carrierCode, carrierName, mode
Forwarder / 3PL	Partial	forwarderCode, name, serviceRole
Warehouse	Present	warehouseId, name, type, operator
WarehouseLocation	Present	locationCode, zone, rack/bin/yard, capacityClass
Site	Present	siteCode, siteName, onshoreOffshore, receivingRule
Delivery	Partial	deliveryId, dispatchDate, arrivalDate, destinationSite
Milestone	Gap - no canonical dictionary	milestoneType, plannedDt, estimatedDt, actualDt, status
Exception	Partial	exceptionId, type, severity, openedDt, status
Claim	Partial	claimRef, claimType, cause, amount, status
Cost	Partial	costEventId, costCode, currency, amount, linkedObject
Invoice	Present	invoiceNo, supplier, issueDate, currency, total
Equipment / Heavy-lift Resource	Present	equipId, equipType, SWL, operator, certificateRef
5.3 Attribute governance by entity
Project / Package / PO / Vendor / Material
These must carry the procurement-side keys that are currently not cleanly linked to execution. The parent-child chain must be explicit: Project -> Package -> PurchaseOrder -> MaterialRequirement -> CargoUnit.
Shipment / ShipmentLeg / CargoUnit / Container
These must carry operational identifiers and actual transport attributes: ETD, ETA, ATD, ATA, mode, grossWeight, volume, dimensions, origin, destination, status.
Documents
Every document must have: documentType, documentNo, documentDate, issuingParty, sourceSystem, linkedObject, fileHash or evidenceRef.
Warehouse
Warehouse data must carry: warehouseId, warehouseLocation, stockStatus, storageRequirementClass, preservationStatus, availableQty.
Customs / Compliance
Customs entry must carry BOE No., duty, customsStatus, consigneeCode, HS Code, and permit references.
Site Receipt
Site receipt must carry siteCode, receiptType (Good/OSD), inspectionResult, MRR/OSDR ref, MRS/MIS ref.
5.4 Relationship list

The minimum canonical relationship set should be:

Project hasPackage Package
Package coveredBy PurchaseOrder
PurchaseOrder issuedTo Vendor
Vendor supplies MaterialMaster
MaterialMaster requiredBy Package
HVDCCodeTag tags MaterialMaster
Shipment contains CargoUnit
CargoUnit packedIn Container
Shipment hasShipmentLeg ShipmentLeg
Shipment evidencedBy BillOfLading
Shipment hasPortCall PortCall
Shipment hasCustomsEntry CustomsEntry
CustomsEntry evidencedBy BOE
Shipment hasReleaseOrder ReleaseOrder
ReleaseOrder evidencedBy DeliveryOrder
Delivery moves CargoUnit
Delivery arrivesAt Warehouse or Site
Warehouse stores CargoUnit
WarehouseTask moves CargoUnit to WarehouseLocation
SiteReceipt receives CargoUnit
SiteReceipt requires Inspection
Inspection evidencedBy MRR / MRI / ITP / MAR / OSDR
Exception impacts Shipment / CargoUnit / Delivery / CostTransaction
Claim arisesFrom Exception
InvoiceLine chargesFor PortCall / Delivery / WarehouseTask / MarineTask
EquipmentResource executes HeavyLiftTask
Permit authorizes TransportLeg / PortAccess / MarineTask
5.5 Event / milestone structure

Do not use FLOW CODE as milestone logic.
Create a first-class MilestoneEvent model with at least the following fields:

milestoneId, milestoneType, objectType, objectId, plannedDt, estimatedDt, actualDt, location, responsibleParty, sourceDocument, sourceSystem, statusAfterEvent, exceptionFlag

Recommended milestone dictionary

Milestone Code	Milestone Name
M10	Cargo Ready
M20	Packed / Marked
M30	Pickup Completed
M40	Export Cleared
M50	Terminal Received
M60	Loaded On Board
M61	Actual Time of Departure
M70	Transshipment Occurred
M80	Actual Time of Arrival
M90	BOE Submitted
M91	BOE Cleared
M92	DO Released
M100	Gate-out Completed
M110	Warehouse Received
M111	Put-away Completed
M120	Picked / Staged
M121	Dispatched
M130	Site Arrived
M131	Site Inspected - Good
M132	Site Inspected - OSD
M140	POD / GRN / Handover
M150	Claim Opened
M160	Cost Closed
5.6 Master vs transaction vs document vs exception classification
Data Class	Examples
Master Data	Project, Package, PO, Vendor, MaterialMaster, Port, Terminal, Warehouse, Site, EquipmentResource, TariffRef, CostCode
Transaction Data	Shipment, ShipmentLeg, PortCall, CustomsEntry, ReleaseOrder, Delivery, WarehouseTask, SiteReceipt
Document Data	CI, PL, BL, BOE, DO, Permit, MRR, MRI, ITP, MAR, MRS, MIS, POD, GRN, OSDR
Event Data	Arrival, Departure, Clearance, Receipt, Put-away, Dispatch, Inspection, Handover
Exception Data	Delay, Damage, Overage, Shortage, PermitGap, Hold, NCR, Claim
Cost Data	Invoice, InvoiceLine, Duty, Demurrage, Detention, PortCharge, WarehouseCharge, MarineCharge, InlandCharge

Critical redesign note:
The current port doc’s multi-key invoice logic, the invoice-cost doc’s any-key cascade, and the site-receiving doc’s MRS/MIS/MRR/OSDR pattern are all worth preserving - but as extensions hanging off a single core ontology, not as separate semantic centers.

Section 6. Knowledge Graph Design Proposal
6.1 Node design
Node family	Example nodes	Primary internal key	Common alternate keys
Master nodes	Project, Package, PO, Vendor, MaterialMaster, Site, Port, Warehouse	internal URI	Project code, Package No., PO No., Vendor Code, Material Code, Site Code
Transport nodes	Shipment, ShipmentLeg, PortCall, Delivery, CustomsEntry	internal URI	Shipment ID, Booking No., BL No., Rotation No., BOE No., DO No.
Physical nodes	CargoUnit, Container, EquipmentResource	internal URI	Package No., Case No., Container No., Seal No., Equipment ID
Document nodes	BL, BOE, DO, Permit, Invoice, PL, MRR, OSDR	internal URI	Document No., file hash, page refs
Event nodes	MilestoneEvent, InspectionEvent, WarehouseEvent, MarineEvent	internal URI	Event ID, source record ID
Exception nodes	Delay, Damage, Shortage, Claim, NCR	internal URI	Exception ID, Claim Ref, NCR Ref
Cost nodes	InvoiceLine, CostTransaction, TariffRef, CostCode	internal URI	Invoice No., Line No., Cost Code
Evidence nodes	AuditRecord, CommunicationEvent	internal URI	Email/thread/message IDs, alert IDs
6.2 Edge design

Use a consistent edge grammar:

Containment / hierarchy: hasPackage, coveredBy, containsCargoUnit, packedIn
Movement: hasLeg, departsFrom, arrivesAt, deliveredTo
Evidence: evidencedBy, references, attachedTo
Status / event: hasMilestone, hasInspection, hasException
Responsibility: issuedTo, operatedBy, approvedBy, handledBy
Compliance: requiresPermit, classifiedByHS, conformsTo
Finance: chargesFor, mappedToCostCode, linkedToInvoice
6.3 Identifier logic

The correct pattern is one internal object, many external identifiers.

Identifier object design

Identifier
identifierScheme
identifierValue
normalizedValue
sourceSystem
isPrimary
validFrom
validTo

Recommended identifier families

Project keys: project code
Procurement keys: package no., PO no., vendor code
Material keys: material code, manufacturer part no., serial no., HVDC CODE
Shipment keys: shipment ID, booking no., BL no., voyage/rotation no.
Container keys: container no., seal no.
Customs keys: BOE no., declaration line ref
Release keys: DO no., gate pass ref
Warehouse keys: warehouse receipt no., location code
Delivery keys: dispatch no., POD no., GRN no.
Exception keys: exception ID, claim ref, NCR ref
Cost keys: invoice no., line no., cost code

Important rule:
HVDC CODE should not be the only identity anchor. It should be modeled as a cross-cutting engineering/logistics relevance tag that can connect MaterialMaster, CargoUnit, Delivery, and Site demand, but not replace BL/Container/BOE/DO/PO identity domains.

6.4 Search entry points

The redesigned KG must support search from:

ETA, ETD, ATA, Vendor, Vendor Code, Package No., PO No., Material Code, HVDC CODE, Shipment ID, Cargo Unit ID, Container No., Seal No., BL No., BOE No., DO No., Port, Terminal, Warehouse, Warehouse Location, Site Code, Exception ID, Claim Ref, Cost Code

6.5 Query traversal examples

ETA query

ETA
-> Shipment
-> Current ShipmentLeg
-> Carrier / Vessel / PortCall
-> Container / CargoUnit
-> BOE / DO / permit status
-> Next inland transport leg
-> Warehouse receiving appointment or direct site plan
-> Risk / delay / cost exposure

HVDC CODE query

HVDC CODE
-> MaterialMaster
-> Package
-> PurchaseOrder
-> Vendor
-> CargoUnit(s)
-> Shipment / BL / Container
-> Warehouse stock or site receipt
-> Exception / inspection / claim history
-> Cost transactions

Vendor query

Vendor
-> PurchaseOrders
-> Material readiness
-> Packed cargo units
-> Shipment performance
-> Documentation defects
-> Customs holds
-> OSD / quality / claim history
-> Cost and delay trend

Container No. query

Container No.
-> Container
-> Shipment
-> BL
-> PortCall / ETA / ATA
-> BOE / DO
-> Gate-out
-> Warehouse receipt / put-away / dispatch
-> Site receipt / POD / OSD

BOE No. query

BOE No.
-> CustomsEntry
-> Shipment / BL / CI / PL / COO
-> Cleared cargo units / containers
-> DO release
-> Gate-out
-> Warehouse receipt or direct site delivery
-> Duty / invoice / reimbursement trace

Why this redesign matches external best practice
EPCIS treats visibility as event records across objects, locations, and organizations; DCSA T&T standardizes end-to-end container operational events and data exchange; UNECE BSP-RDM and vocabulary provide a semantic reference layer; WCO DM provides the universal cross-border data language. That is exactly the structure needed for your “traceable logistics query chain.”

Section 7. Revised Document Structure

The current document should be reissued as a master reference, not as a stack of adjacent ontology notes.

Proposed rewritten table of contents
Purpose, Scope, Governance
What the master reference controls
What is core vs extension
Excluded archive/legacy status
Canonical Dictionaries
Logistics term dictionary
Document type dictionary
Party role dictionary
Compliance authority dictionary
Status / milestone dictionary
Warehouse-only FLOW CODE dictionary
Identity & Key Policy
Internal object IDs
External identifier sets
Parent-child hierarchy
Matching / resolution rules
Core Master Data Model
Project, Package, PO, Vendor, MaterialMaster
Port, Terminal, Warehouse, WarehouseLocation, Site
Carrier, Forwarder, EquipmentResource
Execution Transaction Model
Shipment, ShipmentLeg, PortCall, CustomsEntry, ReleaseOrder, Delivery
WarehouseTask, SiteReceipt
Heavy-lift / marine task model
Document Model
CI, PL, BL/eBL, COO, BOE, DO, Permit
MRR, MRI, ITP, MAR, MRS, MIS, POD, GRN, OSDR
Document provenance / OCR / evidence rules
End-to-End Process Model
Procurement interface
Vendor readiness
Packing
Inland export
Export customs
Port/terminal
Ocean/transshipment
Import customs
DO/gate-out
Warehouse
Site delivery
Handover
Warehouse Extension
Receiving
Put-away
Storage
Internal transfer
Picking
Staging
Dispatch
FLOW CODE only here
Offshore / OOG / Heavy-Lift Extension
MOSB staging
LCT/barge
Rigging/lashing/stability
PTW/FRA/tide/HSE
Sail-away approval
Exception / Claim / Risk / Cost Model
Delay
OSD / damage / shortage
NCR
Claim
DEM / DET
Invoice / CostTransaction / CostCode
Validation Rules
SHACL package
Required identifiers
Milestone completeness
Customs/document consistency
Warehouse validation
Site receipt validation
Query Templates & Dashboard Logic
ETA
HVDC CODE
Vendor
Container No.
BOE No.
Warehouse location
Exception / claim / cost
Integration Architecture
ERP / Procurement
WMS
TMS / Forwarder feeds
Port / Carrier / OFCO / SAFEEN / ADP
LDG / OCR
eDAS / customs / compliance checkpoints
Appendix - Legacy Mapping
Old term -> new term
Old Flow Code usage -> new Routing Pattern or WarehouseFlowCode
Namespace reconciliation

Structural rule:

CONSOLIDATED-08-communication.md should move to supporting evidence / communication layer, not sit inside the core logistics master ontology.
CONSOLIDATED-04-barge-bulk-cargo.md and transformer/offshore details should remain as specialized extension chapters, not define the enterprise master vocabulary.
Section 8. Gap-to-Action Matrix
Issue	Impact	Required Fix	Priority	Dependency	Suggested Owner
FLOW CODE used outside warehouse	Breaks ontology boundaries and query logic	Rename current 0-5 route logic to RoutingPattern; define warehouse-only FLOW CODE	P0	None	Ontology Lead + Logistics Process Owner
No canonical Project -> Package -> PO -> Material chain	Upstream/downstream traversal fails	Publish procurement master model and parent-child rules	P0	FLOW CODE policy	MDM Lead + Procurement Systems Lead
No unified milestone dictionary	ETA-to-site query chain is unstable	Create canonical milestone event model with planned/estimated/actual fields	P0	Core entity model	Process Architect + Integration Lead
Identifier policy is fragmented	Any-key traceability is partial	Introduce Identifier objects and resolution rules across PO/BL/Container/BOE/DO/HVDC CODE	P0	Core entity model	KG Architect
Port ops, invoice-cost, material-handling each define their own semantic center	Multiple competing ontologies	Rebuild all as extensions hanging from one core ontology	P1	Core master model	Ontology Lead
Customs model is document-heavy, not transaction-heavy	BOE / DO / permit traversal weak	Split CustomsEntry transaction from BOE document; split ReleaseOrder from DO document	P1	Milestone model	Customs Lead
Site receiving is not fully linked upstream	Site acceptance cannot always trace back to shipment and PO	Model SiteReceipt, Inspection, RequestSlip, OSDR, POD/GRN explicitly and link to CargoUnit	P1	Identifier policy	Site Logistics Lead + QA/QC Lead
Claim / NCR lifecycle not canonical	Delay/damage/cost closure trace incomplete	Create Exception, Claim, NCR classes with causality and closure states	P1	SiteReceipt + Cost model	Claims Lead + QA/QC
Cost graph not uniformly linked to execution graph	Financial traceability breaks	Link InvoiceLine to PortCall / Delivery / WarehouseTask / MarineTask / Exception	P1	Identifier policy	Cost Control Lead
MOSB represented partly as warehouse, partly as offshore base	Location semantics ambiguous	Model MOSB as MarineStagingBase with optional storage capability, not as default warehouse synonym	P1	Core location model	Port & Marine Lead
Communication ontology sits too close to core model	Core ontology gets noisy	Move email/chat into evidence/action layer	P2	Core model stabilization	Integration Lead
Current docs mix ontology, SOP, SHACL, KPIs, slash commands	Master reference becomes hard to govern	Split conceptual model from implementation guide and automation appendix	P2	Revised TOC	Documentation Owner
Archive/legacy can contaminate target model	Version confusion	Mark current consolidated docs as baseline; archive kept read-only	P2	Governance	Repository Owner
Final judgement

Current-state verdict:
The corpus is not yet acceptable as the master reference for HVDC Logistics Ontology and Knowledge Graph.

Target-state verdict:
It can become that master reference without throwing away the corpus, because the core framework, material-handling chain, site-receiving logic, port multi-key model, and heavy-lift extension are all useful. The redesign must do three things first:

Re-scope FLOW CODE to warehouse-only internal logic
Create one canonical identity + milestone backbone
Separate route pattern, document evidence, transaction state, exception state, and cost state

Once those are done, the model will support the success condition you defined: a future user can start from ETA, HVDC CODE, Vendor, Material Code, Package, Shipment, Container No., BL No., BOE No., DO No., Warehouse Location, Site, Exception ID, or Cost Code and traverse the complete connected logistics context.

Assumptions / explicit gaps
Package / PO / upstream procurement entities are not clearly formalized enough in the current consolidated material to act as the canonical upstream backbone.
BOE / DO / Permit are referenced, but their transaction-document separation is still weak.
NCR / formal claim closure is not yet canonical in the retrieved corpus.
Terminal / Carrier / Forwarder roles are present in narrative form, but role typing is not yet consistent across all docs.
The strongest current evidence is from customs onward, and from site receiving / offshore heavy-lift execution downward.