# OUTLOOK Email Ontology Workbook Redesign Plan

## Overview

이 계획의 목적은 `OUTLOOK_HVDC_ALL_20250920260.xlsx`를 Lessons Learned 분석까지 이어질 수 있는 ontology workbook으로 재구성하는 것이다.

옵션 C를 기준으로 간다.
즉, 이미 만든 `raw/xref/signal` 층은 유지하고, 그 위에 `mail_identifier_extract -> mail_message_classification -> review_gates -> lesson_fact_table` 4단계를 추가한다.

현재 구현은 evidence 추출용 workbook까지는 도달했지만, Lessons Learned 분석에 필요한 분류, 검토 게이트, 집계 테이블은 아직 없다.

## Goals

- 기존 `raw_email_message`, `raw_thread_index`, `xref_*`, `signal_*` 층을 유지한다.
- `mail_identifier_extract`를 추가해 message-level identifier cluster를 만든다.
- `mail_message_classification`을 추가해 각 메일에 `message_type`과 관련 ontology target을 부여한다.
- `review_gates`를 추가해 AGI/DAS MOSB continuity, mixed identifier, customs gap, milestone validity를 점검한다.
- `lesson_fact_table`을 추가해 `lesson_bucket`, `root_cause_bucket`, `impact_level`, `recommended_action`까지 집계한다.
- `canonical_ontology_export`는 유지하되, 중심 산출물이 아니라 downstream-only 시트로 내린다.

## Scope

### In Scope

- source workbook `전체_데이터`를 기반으로 한 메시지 정규화 재사용
- message-level identifier cluster 추출
- evidence 기반 message classification
- review gate 계산
- lesson fact aggregation
- output workbook sheet order 재정의
- 기존 `canonical_ontology_export`를 review 이후 산출물로 조정
- 선택적 `lessons_learned_report` 시트 추가
- 관련 테스트 추가 및 기존 통합 테스트 갱신

### Out of Scope

- source workbook 직접 수정
- Flow Code 계산 또는 Flow Code 파생 필드 생성
- 메일 본문을 운영 truth로 직접 확정하는 로직
- OCR, port, cost, marine 원본 ontology 자체의 전면 재설계
- dashboard UI 변경
- production 배포

## Constraints

- source workbook은 immutable로 유지해야 한다.
- 메일 본문은 evidence-first로 처리해야 한다.
- 식별자 추출이 분류보다 먼저 와야 한다.
- `candidate_milestone`은 explicit evidence가 있을 때만 만들어야 한다.
- `confirmedFlowCode`, `assignedFlowCode`, `extractedFlowCode`는 생성하면 안 된다.
- AGI/DAS 메일은 MOSB continuity가 없으면 review gate를 태워야 한다.
- 현재 구현된 `raw/xref/signal` 층은 버리지 않는다.

Assumption:
- 현재 worktree에 있는 outlook workbook 생성 코드는 계속 재사용 가능하며, 이번 작업은 그 위에 레이어를 추가하는 방식으로 진행한다.

## Phases

### Phase 0. Existing Foundation Freeze

목적:
- 현재 구현된 `raw_email_message`, `raw_thread_index`, `xref_*`, `signal_*` 층을 기준선으로 고정한다.

산출물:
- 유지 대상 시트 목록
- 변경 금지 규칙
- `canonical_ontology_export`를 downstream-only로 내리는 합의

### Phase 1. `mail_identifier_extract`

목적:
- 메일 1건당 1행 기준으로 identifier cluster를 만든다.

핵심 필드:
- `message_id`
- `thread_id`
- `source_row_no`
- `primary_identifier_type`
- `primary_identifier_value`
- `primary_identifier_confidence`
- `mixed_identifier_flag`
- `identifier_count`
- `id_case_list`
- `id_lpo_list`
- `id_po_list`
- `id_bl_awb_list`
- `id_customs_doc_list`
- `id_invoice_list`
- `id_vessel_list`
- `id_vehicle_list`
- `id_driver_list`
- `id_site_list`
- `evidence_summary`
- `parse_status`

원칙:
- xref 시트는 유지한다.
- `mail_identifier_extract`는 xref와 본문에서 나온 identifier를 한 행으로 묶는 상위 시트다.
- 리스트 값은 workbook에 안정적으로 저장 가능한 형식으로 serialize한다.

### Phase 2. `mail_message_classification`

목적:
- 각 메일에 `message_type`를 부여하고 ontology target과 lesson bucket 초안을 만든다.

핵심 필드:
- `message_id`
- `thread_id`
- `message_type`
- `ontology_target_class`
- `lesson_bucket`
- `root_cause_bucket`
- `classification_confidence`
- `classification_rule_id`

기본 분류 우선순위:
- `permit_access`
- `customs_compliance`
- `marine_offshore`
- `site_receiving`
- `movement_notice`
- `cost_invoice`
- `procurement_vendor`
- `exception_risk`
- `general_noise`

원칙:
- 분류는 body keyword만으로 결정하지 않는다.
- identifier cluster, evidence hit, site context를 함께 사용한다.

### Phase 3. `review_gates`

목적:
- 사람이 검토해야 하는 케이스를 명시적으로 분리한다.

핵심 필드:
- `message_id`
- `thread_id`
- `candidate_stage`
- `candidate_milestone`
- `requires_human_review`
- `review_severity`
- `review_reason`
- `review_gate_id`

필수 gate:
- mixed identifier gate
- customs without document reference gate
- site receiving without site anchor gate
- cost invoice without invoice/PO/LPO reference gate
- exception risk gate
- AGI/DAS MOSB continuity gate
- milestone without identifier gate

원칙:
- `review_reason`는 자유 문장보다 stable code 중심으로 간다.
- AGI/DAS 관련 offshore continuity는 classification이 아니라 review gate에서 강제한다.

### Phase 4. `lesson_fact_table`

목적:
- message-level facts를 집계해 Lessons Learned 분석용 표를 만든다.

핵심 필드:
- `lesson_date`
- `message_type`
- `lesson_bucket`
- `root_cause_bucket`
- `primary_site`
- `primary_case`
- `impact_level`
- `evidence_count`
- `top_identifiers`
- `lesson_statement`
- `recommended_action`
- `ontology_anchor`

원칙:
- full mail body는 여기 저장하지 않는다.
- 집계와 보고에 필요한 최소 사실만 넣는다.
- `canonical_ontology_export`는 이 단계와 병렬이 아니라, review 통과 결과에서 내려오는 하위 산출물이다.

### Phase 5. Optional `lessons_learned_report`

목적:
- 사람이 바로 읽을 수 있는 최종 요약 시트를 선택적으로 만든다.

핵심 섹션:
- Executive Summary
- Domain Lessons
- Root Causes
- Ontology Mapping View
- Priority Action Matrix

원칙:
- workbook 안에서 요약 시트를 두되, 원본 evidence와 분리한다.

## Tasks

1. 현재 workbook contract를 option C 기준으로 다시 정의한다.
2. `mail_identifier_extract` 시트와 모듈을 추가한다.
3. `mail_message_classification` 시트와 모듈을 추가한다.
4. `review_gates` 시트와 모듈을 추가한다.
5. `lesson_fact_table` 시트와 모듈을 추가한다.
6. `canonical_ontology_export`를 review 이후 단계로 재배치한다.
7. `scripts/build_outlook_email_ontology_workbook.py` orchestration 순서를 다시 맞춘다.
8. 테스트를 새 단계 기준으로 갱신한다.
9. 필요하면 `lessons_learned_report` 시트를 마지막에 추가한다.

## Risks

- `canonical_ontology_export`를 계속 중심 결과로 두면 lesson 분석 흐름이 약해질 수 있다.
- regex 기반 classification은 alias dictionary와 footer 정리가 약하면 오탐이 많아질 수 있다.
- AGI/DAS MOSB continuity는 메일만으로 완전히 판정하기 어려워 review gate 의존성이 남는다.
- identifier cluster를 안정적으로 serialize하지 않으면 Excel 출력 품질이 흔들릴 수 있다.
- 현재 구현과 새 단계가 동시에 살아 있으면 workbook 구조가 다시 두 갈래로 갈릴 수 있다.

## Review Criteria

- `mail_identifier_extract`가 message-level 1행 구조로 생성된다.
- `mail_message_classification`에서 모든 메일이 정확히 1개의 `message_type`를 가진다.
- `review_gates`에서 AGI/DAS MOSB continuity와 milestone validity가 점검된다.
- `lesson_fact_table`에서 `lesson_bucket`, `root_cause_bucket`, `impact_level`이 집계된다.
- `canonical_ontology_export`는 raw signal 직결이 아니라 review 이후 결과에서 내려온다.
- source workbook은 변경되지 않는다.
- Flow Code 관련 필드는 생성되지 않는다.

## Deliverables

- 수정된 구현 계획 문서
- revised workbook contract
- `mail_identifier_extract` 시트
- `mail_message_classification` 시트
- `review_gates` 시트
- `lesson_fact_table` 시트
- 갱신된 build script
- 갱신된 테스트 세트
- 선택적 `lessons_learned_report` 시트
