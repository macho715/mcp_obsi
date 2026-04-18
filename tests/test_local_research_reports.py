from scripts.local_research_reports import build_research_report


def _section(report, title):
    for section in report["sections"]:
        if section["title"] == title:
            return section
    raise AssertionError(f"missing section: {title}")


def test_build_report_for_ask_result_orders_human_sections_before_debug():
    result = {
        "mode": "ask",
        "question": "invoice question",
        "provider": "minimax",
        "model": "MiniMax-M2.7",
        "ai_applied": True,
        "short_answer": "answer from sources",
        "findings": [{"text": "invoice exists", "source_path": "C:\\Docs\\invoice.md"}],
        "gaps": ["buyer missing"],
        "next_actions": ["open original"],
        "sources": [{"path": "C:\\Docs\\invoice.md", "name": "invoice.md"}],
    }

    report = build_research_report(result)

    assert report["title"] == "invoice question"
    assert report["ai_status"] == "AI applied via minimax / MiniMax-M2.7"
    assert [section["title"] for section in report["sections"]][:6] == [
        "Answer",
        "Key Findings",
        "Evidence",
        "Gaps",
        "Next Actions",
        "Sources",
    ]
    assert _section(report, "Answer")["items"] == ["answer from sources"]
    assert report["debug_json"]["short_answer"] == "answer from sources"


def test_build_report_for_find_bundle_result_includes_file_groups():
    result = {
        "mode": "find-bundle",
        "topic": "Globalmaritime MWS",
        "provider": "fallback",
        "model": "deterministic",
        "ai_applied": False,
        "bundle_title": "Globalmaritime bundle",
        "core_files": [{"path": "C:\\Docs\\core.docx", "role": "core"}],
        "supporting_files": [{"path": "C:\\Docs\\support.pdf", "role": "support"}],
        "duplicates_or_versions": [{"path": "C:\\Docs\\old.pdf", "reason": "older"}],
        "missing_or_gap_hints": [{"hint": "missing invoice"}],
        "next_actions": ["verify attachments"],
        "sources": [{"path": "C:\\Docs\\core.docx"}],
    }

    report = build_research_report(result)

    assert report["title"] == "Globalmaritime bundle"
    assert report["ai_status"] == "AI not applied; showing deterministic evidence only"
    assert _section(report, "Core Files")["items"][0]["path"] == "C:\\Docs\\core.docx"
    assert _section(report, "Duplicates / Versions")["items"][0]["reason"] == "older"
    assert _section(report, "Missing / Gap Hints")["items"][0]["hint"] == "missing invoice"


def test_build_report_for_invoice_audit_includes_invoice_fields_and_missing_fields():
    result = {
        "mode": "ask",
        "question": "audit invoice",
        "analysis_mode": "invoice-audit",
        "provider": "minimax",
        "model": "MiniMax-M2.7",
        "ai_applied": True,
        "short_answer": "invoice checked",
        "findings": [],
        "gaps": [],
        "next_actions": [],
        "sources": [],
        "structured_data": {
            "invoice_number": "AE70066475",
            "issue_date": "",
            "supplier": "Supplier LLC",
            "buyer": "",
            "amount": "",
            "vat": "",
            "total": "120.00",
            "currency": "USD",
        },
    }

    report = build_research_report(result)

    invoice_fields = _section(report, "Invoice Fields")["items"][0]
    missing_fields = _section(report, "Missing Fields")["items"]
    assert invoice_fields["invoice_number"] == "AE70066475"
    assert "issue_date" in missing_fields
    assert "buyer" in missing_fields
