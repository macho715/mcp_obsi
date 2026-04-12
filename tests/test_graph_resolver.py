from app.services.graph_resolver import (
    resolve_analysis_note,
    resolve_carrier,
    resolve_location,
)


def test_resolve_location_maps_west_harbor_jetty_3_to_jetty():
    decision = resolve_location("West Harbor Jetty #3")

    assert decision.status == "resolved"
    assert decision.target_type == "Jetty"


def test_resolve_location_covers_anchorage_yard_and_gate():
    anchorage = resolve_location("AGI Anchorage")
    yard = resolve_location("VP24 yard")
    gate = resolve_location("CICPA gate")

    assert anchorage.target_type == "AnchorageArea"
    assert yard.target_type == "YardArea"
    assert gate.target_type == "GateArea"


def test_resolve_carrier_maps_jopetwil_71_to_operation_carrier():
    decision = resolve_carrier("JOPETWIL 71")

    assert decision.status == "resolved"
    assert decision.target_type == "OperationCarrier"
    assert decision.target_id.endswith("/carrier/jopetwil_71")


def test_resolve_analysis_note_maps_guidelines_and_incidents():
    guide = resolve_analysis_note(
        {
            "path": "guideline_jopetwil_71_group.md",
            "frontmatter": {"slug": "guideline_jopetwil_71_group"},
            "body": "guide body",
        }
    )
    incident = resolve_analysis_note(
        {
            "path": "logistics_issue_jpt71_2024-12-23_3.md",
            "frontmatter": {"slug": "logistics_issue_jpt71_2024-12-23_3"},
            "body": "incident body",
        }
    )

    assert guide["class_name"] == "GroupGuide"
    assert incident["class_name"] == "IncidentLesson"


def test_resolve_location_returns_unresolved_for_unknown_alias():
    decision = resolve_location("Unknown Harbor Point")

    assert decision.status == "unresolved"
    assert decision.target_id is None
    assert decision.target_type is None


def test_resolve_carrier_returns_unresolved_for_unknown_alias():
    decision = resolve_carrier("Unknown Carrier 12")

    assert decision.status == "unresolved"
    assert decision.target_id is None
    assert decision.target_type is None


def test_resolve_analysis_note_returns_explicit_unresolved_for_unknown_path():
    decision = resolve_analysis_note(
        {
            "path": "random_note.md",
            "frontmatter": {"slug": "random_note"},
            "body": "misc body",
        }
    )

    assert decision["class_name"] == "UnresolvedAnalysisNote"
