from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class BuiltKnowledge:
    guides: list[dict[str, object]] = field(default_factory=list)
    rules: list[dict[str, object]] = field(default_factory=list)
    lessons: list[dict[str, object]] = field(default_factory=list)
    evidence: list[dict[str, object]] = field(default_factory=list)
    patterns: list[dict[str, object]] = field(default_factory=list)


def build_knowledge_objects(notes: list[dict[str, Any]]) -> BuiltKnowledge:
    guides: list[dict[str, object]] = []
    rules: list[dict[str, object]] = []
    lessons: list[dict[str, object]] = []
    evidence: list[dict[str, object]] = []
    patterns: list[dict[str, object]] = []

    for note in notes:
        frontmatter = note.get("frontmatter")
        slug = str(frontmatter.get("slug", "")) if isinstance(frontmatter, dict) else ""
        body = str(note.get("body", ""))
        body_lower = body.lower()

        if slug.startswith("guideline_"):
            guides.append({"class_name": "GroupGuide", "slug": slug})
            if "07:30 / 16:00 sitrep" in body_lower:
                rules.append(
                    {
                        "base_class": "OperatingRule",
                        "class_name": "ReportingRule",
                        "guide_slug": slug,
                        "rule_key": "sitrep_window",
                    }
                )
            if "email ssot" in body_lower:
                rules.append(
                    {
                        "base_class": "OperatingRule",
                        "class_name": "DocumentAuthorityRule",
                        "guide_slug": slug,
                        "rule_key": "email_ssot",
                    }
                )
            if "high tide" in body_lower:
                rules.append(
                    {
                        "base_class": "OperatingRule",
                        "class_name": "EscalationRule",
                        "guide_slug": slug,
                        "rule_key": "high_tide_escalation",
                    }
                )
            continue

        lessons.append({"class_name": "IncidentLesson", "slug": slug})
        evidence.append({"class_name": "CommunicationEvidence", "slug": slug})
        if "high tide" in body_lower:
            patterns.append({"class_name": "RecurringPattern", "pattern_key": "HighTideDelay"})

    return BuiltKnowledge(
        guides=guides,
        rules=rules,
        lessons=lessons,
        evidence=evidence,
        patterns=patterns,
    )
