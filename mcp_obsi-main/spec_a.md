# Spec: Production Recent Business Memory Filtering

Feature ID/Branch: recent-business-memory-filter
Created: 2026-04-08
Status: In Review
Owner: mcp_obsidian maintainers
Input: `plan_a.md`
Last Updated: 2026-04-08
Version: v0.1.0

## Summary

### Problem

Production recent memory results currently place verification-oriented `write-check` notes near or at the top of user-facing recent lists. This makes it harder for users to find actual business memories when they ask for "recent memos" or similar requests.

### Goals

- G1: Ensure recent user-facing output prioritizes business memories over verification memories.
- G2: Keep verification memories available for audit and operator review without deleting or mutating them.
- G3: Make the filtering or prioritization rule explicit, testable, and aligned across production-facing recent-list experiences.

### Non-Goals

- NG1: Replacing the existing memory store, MCP protocol, or search engine.
- NG2: Deleting historical verification records.
- NG3: Redesigning wiki search, storage routing, or unrelated UI flows.
- NG4: Reclassifying all historical memories by manual review.

## User Scenarios & Testing

### User Story 1 - Business memories appear first in recent list (Priority: P1)

A user asks for recent memories and expects business-relevant notes before internal verification artifacts.

Why this priority: This is the primary user-facing failure described in the approved Plan.

Independent Test: Seed or identify a mixed recent set containing both business and verification memories, run the recent-list logic, and verify that business memories are shown ahead of verification memories.

Acceptance Scenarios:
1. Given recent results contain both business memories and verification memories, When the user asks for recent memories, Then business memories are listed before verification memories.
2. Given a verification memory has a newer timestamp than a business memory, When the user asks for recent memories, Then the verification memory does not appear ahead of the business memory solely because it is newer.

### User Story 2 - Verification memories remain available when explicitly needed (Priority: P2)

An operator or advanced user still needs to see verification records for audit or debugging.

Why this priority: Hiding verification records completely could weaken traceability and operational review.

Independent Test: Run the explicit verification-oriented query path and verify that verification memories are still retrievable.

Acceptance Scenarios:
1. Given verification memories exist, When the user asks for verification or write-check memories explicitly, Then the system can still return them.
2. Given verification memories are deprioritized in default recent output, When an operator uses an explicit verification query, Then the same records remain searchable and fetchable.

### User Story 3 - Fallback is explicit when no business memories exist (Priority: P2)

A user should not be misled when the recent pool contains only verification memories.

Why this priority: The current failure mode can incorrectly imply that no recent content exists.

Independent Test: Use a recent pool containing only verification memories and verify that the output clearly states that no business memories were found.

Acceptance Scenarios:
1. Given the recent pool contains no business memories, When the user asks for recent memories, Then the response states that no business memories were found in the current window.
2. Given the recent pool contains only verification memories, When fallback results are shown, Then those results are clearly labeled as verification or test records.

### Edge Cases

- EC1: A business memory has sparse metadata and title-only evidence. The rule must not silently discard it without an explicit fallback or clarification path.
- EC2: A verification memory lacks the usual `write-check` title pattern but still carries verification tags. Classification must use more than one signal when available.
- EC3: Recent results include mixed language titles. Classification must not depend on English-only title matching.
- EC4: A memory is archived but still recent. Archived status handling must remain explicit and not be conflated with verification classification.

## Requirements

### Functional Requirements

- FR-001: The system MUST classify recent memory results into at least two buckets: `business` and `verification`.
- FR-002: The classification rule MUST use only currently available evidence fields from stored records, including title patterns, tags, project, and status.
- FR-003: The default user-facing recent-memory response MUST prioritize `business` memories ahead of `verification` memories.
- FR-004: The system MUST preserve access to verification memories through explicit verification-oriented queries or operator review paths.
- FR-005: The system MUST NOT delete, archive, rewrite, or otherwise mutate stored memories as part of the filtering behavior.
- FR-006: When no business memories are found in the inspected recent window, the response MUST state that explicitly before showing any fallback verification results.
- FR-007: The same filtering or prioritization rule MUST be applied consistently anywhere the production recent-memory experience is defined for read-only specialist flows.
- FR-008: The filtering rule MUST be documented in the runtime evidence or equivalent operator-facing documentation after validation.
- FR-009: The output MUST make verification fallback items visibly distinguishable from business items.
- FR-010: The implementation MUST remain compatible with the existing recent-memory MCP surface and must not require deleting existing records.
- FR-011: The rule MUST support independent validation against both local and production recent-memory result sets.
- FR-012: The default recent-memory experience MUST continue to function even if the inspected recent window contains only verification memories.
- FR-013: The system MUST keep the underlying recent pool auditable so reviewers can inspect why an item was classified as `business` or `verification`.
- FR-014: The default recent-memory response MUST keep verification records visible but place them behind business records.

### Non-Functional Requirements

- NFR-001 (Traceability): The classification basis for each returned item SHOULD be reviewable from existing metadata without manual guesswork.
- NFR-002 (Compatibility): The design MUST avoid breaking the current MCP tool contract or requiring a storage-schema reset.
- NFR-003 (Auditability): Verification records MUST remain available for operational review after the filtering change.
- NFR-004 (Clarity): User-facing wording MUST distinguish "no recent content" from "no recent business content."
- NFR-005 (Reproducibility): Validation MUST be repeatable on both local and production recent-memory result sets with documented commands or evidence paths.

## Assumptions & Dependencies

### Assumptions

- A-001: Recent-memory classification can be derived from currently stored title, tags, project, and status evidence without requiring new schema fields.
- A-002: Verification-oriented records already have enough distinguishing patterns such as `write-check`, `verification`, or `rollback-archived` to support an initial rule.
- A-003: Business memories may require multiple weak signals rather than a single strict title pattern.
- A-004: The current MCP recent-memory surface remains available and stable during this work.

### Dependencies

- D-001: The recent-memory MCP surface must continue to expose recent-list retrieval on production specialist routes.
- D-002: Runtime evidence documents must be updated after validation so the operator-facing contract stays aligned with behavior.
- D-003: Local and production result sets must be available for side-by-side validation.
- D-004: Validation wording must distinguish the prioritized business-first view from explicit verification retrieval.

## Success Criteria

### Measurable Outcomes

- SC-001: In a validation set containing at least one business memory and at least one verification memory, the first returned item in default recent output is classified as `business`.
- SC-002: In a validation set containing only verification memories, the default response explicitly states that no business memories were found in the inspected window.
- SC-003: Verification memories remain retrievable through an explicit verification-oriented query path after the filtering change.
- SC-004: Local and production validation runs show the same classification behavior for the same input patterns.
- SC-005: Operator-facing documentation records the final rule, validation scope, and known limitations without unresolved critical ambiguity.

## Open Questions

- Q-001: What is the minimum recent window size used for fallback before the system concludes that no business memories exist?
- Q-002: Should archived verification memories be treated differently from active verification memories in fallback output?

## Clarifications Log

- 2026-04-08:
  - Source brief came from `plan_a.md`.
  - The current draft assumes a classification layer over existing recent results rather than a storage rewrite.
  - FR-014 resolved: verification memories remain visible in default recent output, but only after business memories.

## Reviewer Checklist

- [ ] Every user scenario is independently testable.
- [ ] FR-014 is reflected consistently as `deprioritize verification behind business`.
- [ ] Success criteria are measurable and mapped to validation evidence.
- [ ] Non-goals clearly prevent storage deletion or schema drift.
- [ ] The spec does not silently assume new metadata fields.

## Approval-Readiness Note

This draft is approval-ready provided reviewers accept the remaining non-blocking operational questions about recent-window size and archived verification handling.

## Changelog

- v0.1.0 (2026-04-08): Initial draft from `plan_a.md`
- v0.1.1 (2026-04-08): Resolved FR-014 to `deprioritize verification behind business`
