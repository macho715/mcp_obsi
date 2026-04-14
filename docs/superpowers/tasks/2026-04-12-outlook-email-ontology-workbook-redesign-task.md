# Task.md: OUTLOOK Email Ontology Workbook Redesign

## Goal

기존 Outlook 메일 기반 ontology workbook 파이프라인 위에
`mail_identifier_extract -> mail_message_classification -> review_gates -> lesson_fact_table`
4단계를 추가해, Lessons Learned 분석까지 가능한 workbook을 만든다.

## Scope

### In Scope

- 기존 `raw_email_message`, `raw_thread_index`, `xref_*`, `signal_*` 층 유지
- `mail_identifier_extract` 시트와 모듈 추가
- `mail_message_classification` 시트와 모듈 추가
- `review_gates` 시트와 모듈 추가
- `lesson_fact_table` 시트와 모듈 추가
- `canonical_ontology_export`를 downstream-only 시트로 재배치
- 선택적 `lessons_learned_report` 시트 추가
- build script orchestration 순서 갱신
- 관련 테스트 추가 및 통합 테스트 갱신

### Out of Scope

- source workbook 직접 수정
- Flow Code 계산 또는 Flow Code 파생 필드 생성
- 메일 본문을 운영 truth로 직접 확정하는 로직
- dashboard UI 수정
- production 배포

## Inputs & References

- Spec: [2026-04-12-outlook-email-ontology-workbook-redesign-spec.md](C:/Users/jichu/Downloads/mcp_obsidian/docs/superpowers/specs/2026-04-12-outlook-email-ontology-workbook-redesign-spec.md)
- Plan: [2026-04-12-outlook-email-ontology-workbook-redesign-implementation.md](C:/Users/jichu/Downloads/mcp_obsidian/docs/superpowers/plans/2026-04-12-outlook-email-ontology-workbook-redesign-implementation.md)
- Design: [2026-04-12-outlook-email-ontology-workbook-redesign-design.md](C:/Users/jichu/Downloads/mcp_obsidian/docs/superpowers/specs/2026-04-12-outlook-email-ontology-workbook-redesign-design.md)
- Lesson references:
  - [Lessons Learned용 Excel 정보.md](C:/Users/jichu/.config/superpowers/worktrees/mcp_obsidian/outlook-email-ontology-workbook/Lessons%20Learned%EC%9A%A9%20Excel%20%EC%A0%95%EB%B3%B4.md)
  - [Lessons Learned용 Excel 정보1.md](C:/Users/jichu/.config/superpowers/worktrees/mcp_obsidian/outlook-email-ontology-workbook/Lessons%20Learned%EC%9A%A9%20Excel%20%EC%A0%95%EB%B3%B41.md)
  - [Lessons Learned용 Excel 정보2.md](C:/Users/jichu/.config/superpowers/worktrees/mcp_obsidian/outlook-email-ontology-workbook/Lessons%20Learned%EC%9A%A9%20Excel%20%EC%A0%95%EB%B3%B42.md)
- Source workbook:
  - `Logi ontol core doc/OUTLOOK_HVDC_ALL_20250920260.xlsx`
- Existing implementation files:
  - `app/services/outlook_email_workbook_contract.py`
  - `app/services/outlook_email_raw_normalizer.py`
  - `app/services/outlook_email_signal_extractor.py`
  - `app/services/outlook_email_ontology_mapper.py`
  - `app/services/outlook_email_wiki_pointer_builder.py`
  - `scripts/build_outlook_email_ontology_workbook.py`

## Deliverables

1. Updated workbook contract including the new lesson-oriented sheets
2. New identifier extraction module
3. New message classification module
4. New review gate module
5. New lesson fact aggregation module
6. Updated workbook build script
7. Updated automated tests for the new stages
8. Generated workbook proving the new sheets are written
9. Optional `lessons_learned_report` sheet only if the first slice leaves time

## Acceptance Criteria

- `AC-1` The output workbook contains `mail_identifier_extract`.
- `AC-2` `mail_identifier_extract` has one row per source message and includes a primary identifier, identifier count, mixed identifier flag, and serialized identifier lists.
- `AC-3` The output workbook contains `mail_message_classification`.
- `AC-4` Every source message has exactly one `message_type`.
- `AC-5` The output workbook contains `review_gates`.
- `AC-6` `review_gates` includes `candidate_stage`, `candidate_milestone`, `requires_human_review`, `review_severity`, and stable `review_reason` codes.
- `AC-7` AGI/DAS offshore rows without MOSB continuity evidence trigger a review gate.
- `AC-8` The output workbook contains `lesson_fact_table`.
- `AC-9` `lesson_fact_table` includes `lesson_bucket`, `root_cause_bucket`, `impact_level`, `evidence_count`, `lesson_statement`, and `recommended_action`.
- `AC-10` `canonical_ontology_export` is produced only from approved upstream rows and is not populated directly from raw signals alone.
- `AC-11` The source workbook remains byte-identical before and after a run.
- `AC-12` No Flow Code fields are generated anywhere in the output workbook.
- `AC-13` If `lessons_learned_report` is implemented, it is written as the final optional summary sheet and does not replace `lesson_fact_table`.
- `AC-14` The first delivery may keep classification and review rules in Python modules rather than external YAML files.
- `AC-15` The first delivery does not need a persisted `ontology_mapping_queue` sheet as long as `canonical_ontology_export` is derived only after identifier extraction, classification, and review.

## Definition of Done

- The source workbook is still immutable.
- The four new stages are present and wired into the build flow.
- Acceptance Criteria are verified with automated tests or explicit workbook readback checks.
- The build script can generate the redesigned workbook end to end.
- Security and privacy constraints are respected.
- Evidence paths for tests and output workbook are recorded.
- No unresolved critical ambiguity remains for the first delivery.

## Task List

- [ ] 1. Update workbook contract to add `mail_identifier_extract`, `mail_message_classification`, `review_gates`, `lesson_fact_table`, and keep `lessons_learned_report` optional.
- [ ] 2. Implement message-level identifier clustering from subject, body, and hint columns.
- [ ] 3. Add stable serialization for list-valued identifier outputs suitable for Excel storage.
- [ ] 4. Implement `message_type` classification with one result per message.
- [ ] 5. Map classification output to `ontology_target_class`, `lesson_bucket`, and `root_cause_bucket`.
- [ ] 6. Implement `candidate_stage` and `candidate_milestone` inference from explicit evidence only.
- [ ] 7. Implement `review_gates` with stable gate IDs and reason codes.
- [ ] 8. Implement AGI/DAS MOSB continuity review logic.
- [ ] 9. Rewire `canonical_ontology_export` to consume approved upstream rows after classification and review.
- [ ] 10. Implement `lesson_fact_table` aggregation.
- [ ] 11. Add `lessons_learned_report` only if the first delivery scope and verification budget allow it.
- [ ] 12. Update end-to-end workbook generation tests and workbook sheet-order tests.
- [ ] 13. Run verification and preserve evidence output paths.

## Dependencies & Risks

### Dependencies

- The source workbook still contains `전체_데이터` with the expected columns.
- Existing raw/xref/signal modules remain reusable.
- The lesson-rule documents remain the current source of truth for classification and review behavior.

### Risks

- Regex-only classification may over-trigger without alias dictionaries and stronger footer stripping.
- AGI/DAS MOSB continuity cannot be fully proven from email alone, so some rows will still require human review.
- If `canonical_ontology_export` stays too central, the lesson flow will remain under-specified.
- If list serialization is unstable, downstream Excel reading and tests will drift.

## Security & Privacy

- Source workbook must not be modified in place.
- Mail body content must be treated as evidence, not direct operational truth.
- No Flow Code fields may be generated by this pipeline.
- Full email body text must not be duplicated into lesson aggregation outputs unless explicitly approved later.
- Any output workbook path must remain local and should not introduce external upload behavior.

## Evidence

- Automated tests for:
  - identifier extraction
  - message classification
  - review gates
  - lesson fact aggregation
  - workbook build integration
- Workbook readback evidence showing the new sheets and required columns exist
- Source workbook hash comparison before and after build
- Output workbook path:
  - `output/spreadsheet/outlook_hvdc_email_ontology_workbook.xlsx`

## Change Log

- `2026-04-12` Initial task draft created from the workbook redesign spec.

## Open Questions

None at this stage.

## Clarifications Log

- `2026-04-12` Option C was selected: preserve the current `raw/xref/signal` base and add four new stages.
- `2026-04-12` `canonical_ontology_export` remains in scope but becomes downstream-only.
- `2026-04-12` Flow Code remains out of scope for this mail-based pipeline.
- `2026-04-12` The first delivery keeps classification and review rules in Python.
  External YAML rule files are deferred.
- `2026-04-12` `ontology_mapping_queue` is not required as a persisted workbook sheet in the first delivery.
- `2026-04-12` `lesson_fact_table` is required for first delivery approval.
  `lessons_learned_report` remains optional.
