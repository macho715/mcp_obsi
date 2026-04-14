# Spec.md: UAE HVDC Logistics Knowledge Wiki & Graph Integration

## Summary
The goal is to build an automated pipeline that integrates 6 major WhatsApp logistics channels into a permanent, searchable Obsidian Knowledge Wiki, and to construct an ontology-based Knowledge Graph from Excel tracking data (`HVDC STATUS.xlsx`). The system will parse chat logs for logistics issues, use a local LLM (gemma4) to structure the extraction, and map shipments through a directed graph centered on the `SCT SHIP NO.` to connect orders, vendors, warehouses, hubs, vessels, and sites.

## User Scenarios & Testing

### Scenario 1: WhatsApp Log Parsing and Wiki Generation
**Given** an exported WhatsApp chat log containing logistics operations and issue tags (e.g., [RISK], [COST]) and risk keywords (e.g., delay, hold),
**When** the automated extraction pipeline (`scripts/parse_whatsapp_logistics.py`) runs,
**Then** the system should filter risk-related conversations, group them into event blocks, and generate structured Markdown files (Wiki notes) containing Issue Summary, Response, Root Cause & Lessons Learned, and the Evidence Log.
**Testability**: Run the script against a sample log and verify the output Markdown structure and content accuracy against the sample.

### Scenario 2: Knowledge Graph Query for Shipment Traceability
**Given** the Knowledge Graph populated with `HVDC STATUS.xlsx` data,
**When** a user queries for shipments supplied by "Vendor A" that were consolidated at "MOSB" and delivered to "AGI" using a specific "LCT 선박",
**Then** the system should return a list of matching `SCT SHIP NO.` entities and their associated data.
**Testability**: Execute a SPARQL/Graph query representing this scenario and validate the returned results against the source Excel data.

### Scenario 3: Missing Standardized Tag Handling
**Given** a WhatsApp message describing a delay but missing the standardized `[RISK]` or `[URGENT]` tag,
**When** the pipeline processes the log,
**Then** the system should optionally fall back to keyword matching (e.g., "delay", "hold", "cancel") to identify the event block, but prioritize tagged messages.
**Testability**: Provide logs with and without tags, and ensure issue blocks are still extracted correctly based on the configured keyword heuristics.

## Requirements

### Functional Requirements
*   **FR-001 (Log Ingestion):** The system MUST ingest exported text logs from 6 specified WhatsApp channels.
*   **FR-002 (Event Filtering):** The system MUST filter chat messages based on predefined risk keywords and standardized tags (e.g., `[URGENT]`, `[RISK]`, `[GATE]`).
*   **FR-003 (LLM Extraction):** The system MUST utilize a local LLM (Ollama - gemma4) to analyze filtered event blocks and generate structured summaries (Issue, Response, Root Cause, Evidence).
*   **FR-004 (Wiki Storage):** The system MUST save the LLM-generated summaries as Markdown files within the Obsidian `vault/wiki/analyses/` directory.
*   **FR-005 (Graph Data Modeling):** The system MUST model logistics data into a Knowledge Graph using `SCT SHIP NO.` (Shipment) as the central node. The graph MUST include the following 7 entity classes: Shipment, Order, Vendor, Vessel, Hub, Warehouse, and Site.
*   **FR-006 (Graph Relationships):** The system MUST create directed edges representing `hasOrder`, `suppliedBy`, `storedAt`, `consolidatedAt`, `transportedBy`, and `deliveredTo` relationships.
*   **FR-007 (Graph Export Format):** The system MUST provide a pipeline to convert and export the `HVDC STATUS.xlsx` core columns into JSON/RDF format matching the ontology schema.
*   **FR-008 (Historical Full Run):** The system MUST support a full historical run mode by removing the `MAX_TO_PROCESS` limit to process large backlogs like Abu Dhabi and Project Lightning channels.

### Non-Functional Requirements
*   **NFR-001 (Local Processing):** All LLM inference MUST occur locally (via Ollama) to prevent sensitive logistics data from being transmitted to external APIs.
*   **NFR-002 (Data Consistency):** The Knowledge Graph MUST maintain chronological integrity, specifically differentiating "창고 처리일"와 "현장 하역일" (2-Track Dates).
*   **NFR-003 (Advisory Flow Codes):** The system SHOULD calculate or record Flow Code v3.5 metrics, but these MUST NOT act as hard constraints that block physical operations in the system logic.

## Assumptions & Dependencies

### Assumptions
*   Field operators will adhere to the standardized tagging SOP and D-1 16:00 Planning rule in the WhatsApp groups, including explicit pre-constraints for Weather/Tide and "Hold at DSV" spatial limits.
*   The `HVDC STATUS.xlsx` file will maintain a consistent column structure for mapping onto the Ontology classes.

### Dependencies
*   **Ollama Environment:** Requires a running local instance of Ollama with the `gemma4` model pulled and available.
*   **Obsidian Vault:** Requires the target Obsidian vault directory structure (`vault/wiki/analyses/`) to exist or be created by the pipeline.
*   **Python Ecosystem:** Requires Python 3.11+ and necessary libraries (e.g., `pandas` for Excel parsing, `rdflib` for graph creation).
*   **Documentation:** Pipeline creation and persona tuning rely on `docs/web-clipping-setup.md` as the reference guide.

## Success Criteria
*   **SC-001 (Extraction Accuracy):** The LLM pipeline successfully extracts and formats at least 80% of manually identified risk events from a historical WhatsApp log sample.
*   **SC-002 (Graph Traversal):** The constructed Knowledge Graph successfully returns accurate results for multi-hop queries (e.g., Vendor -> Shipment -> Hub -> Site) matching the raw Excel data 100% of the time.
*   **SC-003 (Automation Run):** The end-to-end pipeline (Log -> Parse -> LLM -> Markdown save) executes without manual intervention for a given chat log file.

## Open Questions & Clarifications Log
*   **[NEEDS CLARIFICATION: Graph Database Technology]**: Which specific graph database or triple store (e.g., Neo4j, GraphDB, local RDFLib file) will be used to host the Knowledge Graph derived from the Excel file?
*   **[NEEDS CLARIFICATION: Sync Frequency]**: How often should the WhatsApp logs and `HVDC STATUS.xlsx` be synced to the Wiki and Knowledge Graph (e.g., daily batch, real-time webhooks)?