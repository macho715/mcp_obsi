# Task: Production Recent Business Memory Filtering

Task ID: TASK-2026-04-08-001
Created: 2026-04-08
Status: In Review
Owner: mcp_obsidian maintainers
Source Spec: [spec_a.md](c:/Users/jichu/Downloads/mcp_obsidian/spec_a.md)
Last Updated: 2026-04-08
Version: v0.1.0

## Goal

Define, validate, and document a recent-memory filtering behavior so that business memories appear before verification memories in production-facing recent-list experiences without deleting existing records or breaking the MCP recent-memory surface.

## Scope

### In Scope

- Define a classification rule for `business` vs `verification` recent memories using existing record evidence.
- Validate the rule against local and production recent-memory result sets.
- Decide and document the default handling of verification memories in recent output.
- Update runtime evidence and related documentation after validation.

### Out of Scope

- Replacing the existing search engine or MCP protocol.
- Deleting historical verification records.
- Changing wiki storage routing.
- Unrelated UI redesign or broad UX refactor.
- Manual reclassification of all historical memory records.

## Inputs & References

- Primary spec:
  - [spec_a.md](c:/Users/jichu/Downloads/mcp_obsidian/spec_a.md)
- Source plan:
  - [plan_a.md](c:/Users/jichu/Downloads/mcp_obsidian/plan_a.md)
- Runtime evidence:
  - [MCP_RUNTIME_EVIDENCE.md](c:/Users/jichu/Downloads/mcp_obsidian/docs/MCP_RUNTIME_EVIDENCE.md)
- Specialist route docs:
  - [CHATGPT_MCP.md](c:/Users/jichu/Downloads/mcp_obsidian/docs/CHATGPT_MCP.md)
  - [CLAUDE_MCP.md](c:/Users/jichu/Downloads/mcp_obsidian/docs/CLAUDE_MCP.md)
- Root contracts:
  - [README.md](c:/Users/jichu/Downloads/mcp_obsidian/README.md)
  - [SYSTEM_ARCHITECTURE.md](c:/Users/jichu/Downloads/mcp_obsidian/SYSTEM_ARCHITECTURE.md)
- Relevant code areas:
  - [app/chatgpt_mcp_server.py](c:/Users/jichu/Downloads/mcp_obsidian/app/chatgpt_mcp_server.py)
  - [app/claude_mcp_server.py](c:/Users/jichu/Downloads/mcp_obsidian/app/claude_mcp_server.py)
  - [app/services/memory_store.py](c:/Users/jichu/Downloads/mcp_obsidian/app/services/memory_store.py)
  - [app/services/index_store.py](c:/Users/jichu/Downloads/mcp_obsidian/app/services/index_store.py)
  - [app/utils/specialist_readonly.py](c:/Users/jichu/Downloads/mcp_obsidian/app/utils/specialist_readonly.py)

## Deliverables

- Filtering rule draft for `business` vs `verification`
- Validation notes for local and production recent-memory results
- Decision on default verification handling in recent output
- Documentation patch list and final evidence update
- Reviewer summary stating whether the task is approval-ready

## Acceptance Criteria

- AC-1: A documented rule exists that classifies recent-memory results into `business` and `verification` using only existing fields such as title, tags, project, and status.
- AC-2: The rule is validated against a mixed recent set where at least one business memory and one verification memory are present.
- AC-3: Default recent output behavior for verification memories is explicitly decided and documented as `deprioritize behind business`, not exclusion.
- AC-4: Validation evidence exists for both local and production recent-memory behavior.
- AC-5: Verification memories remain retrievable through an explicit verification-oriented query path after the filtering change.
- AC-6: Updated documentation distinguishes "no recent content" from "no recent business content."
- AC-7: No stored memories are deleted, rewritten, or archived as part of the filtering change.

## Definition of Done

- The task has a documented filtering rule and a documented decision for default verification handling.
- Validation evidence exists for both local and production behavior.
- Relevant documentation is updated to reflect the final behavior and known limitations.
- No critical ambiguity remains unresolved except items explicitly accepted by the reviewer.
- The final reviewer can trace each acceptance criterion to at least one concrete evidence item.

## Task List

- [ ] Review [spec_a.md](c:/Users/jichu/Downloads/mcp_obsidian/spec_a.md) and confirm the `deprioritize behind business` decision is reflected consistently.
- [ ] Collect a recent-memory sample set from production and local environments.
- [ ] Mark each sampled memory as provisional `business` or `verification` using title, tags, project, and status evidence.
- [ ] Verify the default recent response keeps verification memories visible only after business memories.
- [ ] Validate that explicit verification-oriented queries still return verification memories.
- [ ] Validate fallback behavior when no business memories exist in the inspected recent window.
- [ ] Prepare documentation patch notes for runtime evidence and route docs.
- [ ] Update evidence paths and reviewer summary after validation.

## Dependencies & Risks

### Dependencies

- Production and local recent-memory result sets must remain accessible for comparison.
- Specialist recent-memory routes must remain callable during validation.
- The approved default policy is `deprioritize verification behind business`; downstream validation must follow that rule consistently.

### Risks

- A title-only rule may hide legitimate business memories.
- A tag-only rule may miss older records with weak metadata hygiene.
- If verification memories are hidden completely, operator traceability may weaken.
- If verification memories are merely deprioritized, users may still see them when the recent pool is mostly operational probes.

## Security & Privacy

- Do not delete or mutate stored memories during validation unless a separate approved write path explicitly requires a reversible test.
- Do not expose secret tokens, bearer values, or private production data in the task output.
- Do not copy full memory bodies into public review notes when a title, id, and metadata summary are sufficient.
- Forbidden data types in task output:
  - bearer tokens
  - private URLs not already documented for operators
  - raw secret-bearing transcripts
  - personally identifying information not already approved for documentation

## Evidence

- Required evidence items:
  - Recent-memory sample set with ids, titles, and classification rationale
  - Local validation command or probe result
  - Production validation command or probe result
  - Documentation patch references
- Expected evidence paths:
  - [MCP_RUNTIME_EVIDENCE.md](c:/Users/jichu/Downloads/mcp_obsidian/docs/MCP_RUNTIME_EVIDENCE.md)
  - [README.md](c:/Users/jichu/Downloads/mcp_obsidian/README.md)
  - [SYSTEM_ARCHITECTURE.md](c:/Users/jichu/Downloads/mcp_obsidian/SYSTEM_ARCHITECTURE.md)

## Open Questions

- Q-1: How large should the inspected recent window be before fallback logic concludes that no business memories exist?
- Q-2: Should archived verification records be treated differently from active verification records?

## Change Log

- v0.1.0 (2026-04-08): Initial Task draft from [spec_a.md](c:/Users/jichu/Downloads/mcp_obsidian/spec_a.md)
- v0.1.1 (2026-04-08): Resolved AC-3 default behavior to `deprioritize verification behind business`
