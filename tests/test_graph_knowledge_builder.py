from app.services.graph_knowledge_builder import build_knowledge_objects


def test_build_knowledge_objects_creates_guide_rule_lesson_and_pattern():
    notes = [
        {
            "path": "guideline_jopetwil_71_group.md",
            "frontmatter": {"slug": "guideline_jopetwil_71_group", "title": "Guide"},
            "body": "07:30 / 16:00 SITREP\nemail SSOT\nhigh tide risk escalation",
        },
        {
            "path": "logistics_issue_jpt71_2024-12-23_3.md",
            "frontmatter": {"slug": "logistics_issue_jpt71_2024-12-23_3", "title": "Delay"},
            "body": "high tide delayed offloading at AGI",
        },
        {
            "path": "guideline_misc_note.md",
            "frontmatter": {"slug": "misc_note", "title": "Misc"},
            "body": "general note without guide keywords",
        },
    ]

    knowledge = build_knowledge_objects(notes)

    assert len(knowledge.guides) == 1
    assert len(knowledge.rules) == 3
    assert len(knowledge.lessons) == 2
    assert len(knowledge.evidence) == 2
    assert len(knowledge.patterns) == 1

    assert knowledge.guides[0]["class_name"] == "GroupGuide"
    assert knowledge.rules[0]["base_class"] == "OperatingRule"
    assert knowledge.rules[0]["class_name"] == "ReportingRule"
    assert knowledge.rules[1]["class_name"] == "DocumentAuthorityRule"
    assert knowledge.rules[2]["class_name"] == "EscalationRule"

    assert knowledge.lessons[0]["class_name"] == "IncidentLesson"
    assert knowledge.lessons[1]["class_name"] == "IncidentLesson"
    assert knowledge.evidence[0]["class_name"] == "CommunicationEvidence"
    assert knowledge.evidence[1]["class_name"] == "CommunicationEvidence"
    assert knowledge.patterns[0]["class_name"] == "RecurringPattern"

    assert knowledge.guides[0]["slug"] == "guideline_jopetwil_71_group"
    assert all(guide["slug"] != "misc_note" for guide in knowledge.guides)
    assert all(rule["guide_slug"] != "misc_note" for rule in knowledge.rules)
    assert any(
        lesson["slug"] == "logistics_issue_jpt71_2024-12-23_3" for lesson in knowledge.lessons
    )
    assert any(item["slug"] == "logistics_issue_jpt71_2024-12-23_3" for item in knowledge.evidence)
    assert knowledge.patterns[0]["pattern_key"] == "HighTideDelay"
    assert knowledge.rules[0]["guide_slug"] == "guideline_jopetwil_71_group"
    assert knowledge.rules[1]["guide_slug"] == "guideline_jopetwil_71_group"
    assert knowledge.rules[2]["guide_slug"] == "guideline_jopetwil_71_group"
