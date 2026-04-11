# Task.md: UAE HVDC Logistics Knowledge Wiki & Graph Integration

## Goal
Implement an automated pipeline that integrates 6 WhatsApp logistics channels into an Obsidian Knowledge Wiki using a local LLM, and constructs an ontology-based Knowledge Graph from `HVDC STATUS.xlsx` centering on `SCT SHIP NO.` for multi-dimensional logistics tracking.

## Scope
**In Scope:**
- Enhancement of `scripts/parse_whatsapp_logistics.py` for comprehensive event block extraction based on risk keywords and tags.
- Local LLM (Ollama - gemma4) integration for structured Markdown generation.
- Automated saving of generated Markdown to `vault/wiki/analyses/`.
- Development of a graph parsing script to read `HVDC STATUS.xlsx` and create a Knowledge Graph (RDF/NetworkX/etc. based on later decision) defining specific relations (`hasOrder`, `suppliedBy`, `storedAt`, `consolidatedAt`, `transportedBy`, `deliveredTo`).
- Testing the pipeline against historical data.

**Out of Scope:**
- Real-time webhook integration (unless specified later).
- Implementing physical operational blockers based on Flow Code v3.5 (Advisory only).
- Creating a custom front-end UI for graph visualization (beyond standard graph query tools or basic integration).

## Inputs & References
- `docs/Spec.md`: System requirements and scenarios.
- `docs/MASTER_LOGISTICS_PLAN.md`: Great Plan outlining the overarching logistics node architecture and SOPs.
- `docs/web-clipping-setup.md`: Guide for WhatsApp logistics group chat knowledge automation and channel-specific personas.
- `HVDC STATUS.xlsx`: Source data for Knowledge Graph.
- WhatsApp exported chat logs for all 6 channels (Abu Dhabi Logistics, DSV Delivery, Project Lightning, Jopetwil 71 Group, MIR Logistics, SHU Logistics).
- `scripts/parse_whatsapp_logistics.py`: Initial PoC script for WhatsApp extraction.

## Deliverables
1. Completed and robust `scripts/parse_whatsapp_logistics.py`.
2. A new script for Knowledge Graph creation (e.g., `scripts/build_knowledge_graph.py`).
3. Output Wiki notes populated in `vault/wiki/analyses/` from test runs.
4. Output Knowledge Graph artifact (e.g., RDF/Turtle file, or GraphDB load script).
5. Verification test report documenting AC compliance.

## Acceptance Criteria
- **AC-1 (Parsing & Filtering):** Pipeline successfully filters WhatsApp logs using all standard tags (`[URGENT]`, `[ACTION]`, `[FYI]`, `[ETA]`, `[RISK]`, `[COST]`, `[GATE]`, `[CRANE]`, `[MANIFEST]`), pre-constraints (e.g., "D-1 16:00 Planning", "Hold at DSV"), and fallback keywords (delay, hold, cancel).
- **AC-2 (LLM Generation):** Pipeline generates Obsidian-ready Markdown notes matching the structured template (Issue, Response, Root Cause, Evidence) using local `gemma4`.
- **AC-3 (Wiki Storage):** Generated Markdown files are successfully persisted in `vault/wiki/analyses/`.
- **AC-4 (Graph Construction):** The graph builder script successfully parses `HVDC STATUS.xlsx` and constructs a graph where `SCT SHIP NO.` is the hub node, connected correctly to Order, Vendor, Warehouse, Hub, Vessel, and Site nodes.
- **AC-5 (Graph Validation):** Graph successfully answers a 3-hop SPARQL/Graph query matching Excel truth 100%.

## Definition of Done
- Code implemented and passes static analysis (`ruff check`, `ruff format`).
- All Acceptance Criteria (`AC-1` to `AC-5`) are verified and met.
- No sensitive keys or unredacted secrets are committed.
- Documentation and scripts are peer-reviewed (or self-reviewed in this context).
- Deliverables are saved to their correct target directories.

## Task List
- [ ] 1. Define standard ontology and choose Graph DB/Library (e.g., `rdflib` to generate `.ttl`).
- [ ] 2. Create `scripts/build_knowledge_graph.py` to parse `HVDC STATUS.xlsx` and map rows to Graph nodes/edges based on `SCT SHIP NO.`.
- [ ] 3. Refine `scripts/parse_whatsapp_logistics.py` to ensure robust tag parsing, fallback keyword matching, and adjust personas/keywords per channel using `docs/web-clipping-setup.md`.
- [ ] 4. Remove `MAX_TO_PROCESS` limit and run full batch processing for all 6 WhatsApp channels, verifying Markdown outputs in `vault/wiki/analyses/`.
- [ ] 5. Run SPARQL/Graph queries against the generated graph to validate structure and accuracy.
- [ ] 6. Update the 6 WhatsApp group chat descriptions with the standard SOP (tags and D-1 16:00 rules).
- [ ] 7. Document usage and execute end-to-end integration test.

## Dependencies & Risks
- **Dependencies:** Ollama running locally with `gemma4` model. `pandas` and graph library (e.g., `rdflib`) installed. Access to `HVDC STATUS.xlsx`.
- **Risks:** 
  - Graph database choice is unconfirmed. (Mitigation: Use `rdflib` to export a standard `.ttl` file as an intermediate format).
  - Variations in Excel column names might break parsing. (Mitigation: Hardcode column mapping or use fuzzy matching/config).

## Security & Privacy
- **Local LLM:** Execution strictly via local Ollama. No data should be sent to OpenAI/Anthropic APIs to protect logistics IP.
- **Data Protection:** Ignore or mask personal identifiable information (PII) if found in WhatsApp logs outside of logistics context.
- **No Secrets:** Do not commit `API_KEY`s if external services are used as a fallback.

## Evidence
- Verification will be proven by the existence of Markdown files in `vault/wiki/analyses/` and the output Knowledge Graph file.
- SPARQL/Query script output log demonstrating successful path traversal.

## Change Log
- 2026-04-09: Initial Task.md created from Spec.md.

## Clarifications Log
- `[NEEDS CLARIFICATION: Graph Database Technology]`: Assuming `rdflib` generating a `.ttl` (Turtle) file for file-based interoperability until a dedicated GraphDB is provisioned.
- `[NEEDS CLARIFICATION: Sync Frequency]`: Assuming manual batch runs for this implementation phase.