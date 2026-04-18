import json
from pathlib import Path

from scripts.local_research_service import (
    ResearchService,
    dedupe_candidates,
    generate_search_queries,
    rank_candidates,
)


class FakeProviderRouter:
    def __init__(self):
        self.calls = []

    def health(self):
        return {
            "active_provider": "minimax",
            "minimax": {"status": "ok", "model": "MiniMax-M2.7", "api_key_configured": True},
            "copilot": {"status": "ok"},
        }

    def analyze(self, packet, *, provider="auto", analysis_mode="ask", tool_use=False):
        self.calls.append(
            {
                "packet": packet,
                "provider": provider,
                "analysis_mode": analysis_mode,
                "tool_use": tool_use,
            }
        )
        if analysis_mode == "find-bundle":
            return {
                "provider": provider,
                "model": "MiniMax-M2.7",
                "bundle_title": "selected bundle",
                "core_files": [{"path": packet["sources"][0]["source_path"], "role": "core"}],
                "supporting_files": [],
                "duplicates_or_versions": [],
                "missing_or_gap_hints": [],
                "next_actions": [],
                "warnings": [],
            }
        return {
            "provider": provider,
            "model": "MiniMax-M2.7",
            "short_answer": "provider answer",
            "findings": [
                {"text": "selected evidence", "source_path": packet["sources"][0]["source_path"]}
            ],
            "structured_data": {"answer_quality": "ai-generated"},
            "gaps": [],
            "next_actions": [],
            "warnings": [],
        }


def test_generate_search_queries_keeps_meaningful_tokens():
    queries = generate_search_queries("Globalmaritime MWS 13차 기성 관련 파일")

    assert "Globalmaritime" in queries
    assert "MWS" in queries
    assert "Globalmaritime MWS" in queries
    assert "MWS 13차" in queries
    assert "13차" in queries
    assert "기성" in queries


def test_dedupe_candidates_uses_case_insensitive_path():
    candidates = dedupe_candidates(
        [
            {"path": "C:\\Docs\\Report.pdf", "name": "Report.pdf"},
            {"path": "c:\\docs\\report.pdf", "name": "Report.pdf"},
        ]
    )

    assert candidates == [{"path": "C:\\Docs\\Report.pdf", "name": "Report.pdf"}]


def test_rank_candidates_prefers_filename_match_and_clean_paths():
    candidates = [
        {"path": "C:\\Users\\SAMSUNG\\.cursor\\cache\\Globalmaritime.pdf", "extension": ".pdf"},
        {"path": "C:\\HVDC_WORK\\Globalmaritime MWS 13차.docx", "extension": ".docx"},
    ]

    ranked = rank_candidates(candidates, ["Globalmaritime", "MWS"])

    assert ranked[0]["path"].endswith("Globalmaritime MWS 13차.docx")
    assert ranked[0]["score"] > ranked[1]["score"]
    assert "filename match" in ranked[0]["rank_reason"]
    assert ranked[1]["selected_by_default"] is False


def test_rank_candidates_strongly_prefers_exact_filename_entity_match():
    candidates = [
        {
            "path": "C:\\Docs\\SCT-Import VAT-08~10-2024Box 6.md",
            "name": "SCT-Import VAT-08~10-2024Box 6.md",
            "extension": ".md",
            "modifiedAt": "2026-04-17",
            "size": 6887,
        },
        {
            "path": "C:\\Users\\SAMSUNG\\Downloads\\TAX_INVOICE_AE70066475.md",
            "name": "TAX_INVOICE_AE70066475.md",
            "extension": ".md",
            "modifiedAt": "2026-04-17",
            "size": 96959,
        },
    ]

    ranked = rank_candidates(candidates, ["TAX_INVOICE_AE70066475", "세금계산서"])

    assert ranked[0]["name"] == "TAX_INVOICE_AE70066475.md"
    assert ranked[0]["score"] >= ranked[1]["score"] + 50
    assert "exact filename/entity match" in ranked[0]["rank_reason"]


def test_rank_candidates_excludes_pytest_temp_artifacts():
    candidates = [
        {
            "path": (
                "C:\\Users\\SAMSUNG\\AppData\\Local\\Temp\\pytest-of-SAMSUNG\\pytest-224"
                "\\test_preview_candidates_return0\\Globalmaritime MWS 13차.docx"
            ),
            "name": "Globalmaritime MWS 13차.docx",
            "extension": ".docx",
            "source": "everything-http",
        },
        {
            "path": (
                "C:\\HVDC_WORK\\REPORTS\\기성\\GM202603"
                "\\260412_UAE HVDC_(Globalmaritime)_MWS 기성(13차) 집행의 건.docx"
            ),
            "name": "260412_UAE HVDC_(Globalmaritime)_MWS 기성(13차) 집행의 건.docx",
            "extension": ".docx",
        },
    ]

    ranked = rank_candidates(dedupe_candidates(candidates), ["Globalmaritime", "MWS", "13차"])

    assert len(ranked) == 1
    assert ranked[0]["path"].startswith("C:\\HVDC_WORK")


def test_rank_candidates_prefers_recent_file_when_matches_are_equal():
    candidates = [
        {
            "path": "C:\\Docs\\TR5 review old.txt",
            "name": "TR5 review.txt",
            "extension": ".txt",
            "modifiedAt": "2020-01-01",
        },
        {
            "path": "C:\\Docs\\TR5 review new.txt",
            "name": "TR5 review.txt",
            "extension": ".txt",
            "modifiedAt": "2026-04-17",
        },
    ]

    ranked = rank_candidates(candidates, ["TR5", "review"])

    assert ranked[0]["path"].endswith("TR5 review new.txt")
    assert ranked[0]["score"] > ranked[1]["score"]
    assert "recent modification" in ranked[0]["rank_reason"]


def test_rank_candidates_adds_duplicate_version_annotations_and_size_reason():
    candidates = [
        {
            "path": "C:\\Docs\\DSV Delivery v1.md",
            "name": "DSV Delivery v1.md",
            "extension": ".md",
            "size": 100,
            "modifiedAt": "2026-04-01",
        },
        {
            "path": "C:\\Docs\\DSV Delivery v2.md",
            "name": "DSV Delivery v2.md",
            "extension": ".md",
            "size": 120,
            "modifiedAt": "2026-04-02",
        },
    ]

    ranked = rank_candidates(candidates, ["DSV", "Delivery"])

    assert all(candidate["duplicate_group"] for candidate in ranked)
    assert any("duplicate/version group" in candidate["rank_reason"] for candidate in ranked)
    assert "has size" in ranked[0]["rank_reason"]


def test_health_reports_route_ready_when_minimax_ok_and_copilot_unavailable(tmp_path):
    class Router:
        def health(self):
            return {
                "active_provider": "minimax",
                "minimax": {"status": "ok"},
                "copilot": {"status": "unavailable"},
            }

    service = ResearchService(
        output_root=tmp_path / "runtime" / "research",
        provider_router=Router(),
        search=lambda query, limit=1: [],
    )

    health = service.health()

    assert health["status"] == "ready"
    assert health["route_ready"] is True
    assert health["route_status"] == "ready"
    assert health["active_provider"] == "minimax"


def test_preview_candidates_returns_stable_ids_without_extracting_or_saving(tmp_path):
    source = tmp_path / "Globalmaritime MWS 13차.docx"
    source.write_text("not extracted during preview", encoding="utf-8")
    extract_calls = []

    service = ResearchService(
        output_root=tmp_path / "runtime" / "research",
        search=lambda query, limit=50: [
            {
                "path": str(source),
                "name": source.name,
                "extension": ".docx",
                "size": 100,
                "modifiedAt": "2026-04-17",
            }
        ],
        extract=lambda path: extract_calls.append(path) or {"status": "ok", "text": "body"},
    )

    first = service.preview_candidates("Globalmaritime MWS 13차", mode="find-bundle")
    second = service.preview_candidates("Globalmaritime MWS 13차", mode="find-bundle")

    assert first["mode"] == "find-bundle"
    assert first["prompt"] == "Globalmaritime MWS 13차"
    assert first["candidates"][0]["candidate_id"] == second["candidates"][0]["candidate_id"]
    assert first["candidates"][0]["path"] == str(source)
    assert first["candidates"][0]["selected_by_default"] is True
    assert extract_calls == []
    assert not (tmp_path / "runtime").exists()


def test_preview_candidates_marks_vanished_candidates_not_selected(tmp_path):
    missing = tmp_path / "Globalmaritime MWS deleted.docx"

    service = ResearchService(
        output_root=tmp_path / "runtime" / "research",
        search=lambda query, limit=50: [
            {"path": str(missing), "name": missing.name, "extension": ".docx"}
        ],
    )

    result = service.preview_candidates("Globalmaritime MWS", mode="ask")

    assert result["candidates"][0]["status"] == "missing"
    assert result["candidates"][0]["selected_by_default"] is False
    assert "missing file" in result["candidates"][0]["rank_reason"]


def test_preview_candidates_returns_warning_when_search_fails(tmp_path):
    service = ResearchService(
        output_root=tmp_path / "runtime" / "research",
        search=lambda query, limit=50: (_ for _ in ()).throw(RuntimeError("everything timeout")),
    )

    result = service.preview_candidates("TR5 PreOp", mode="ask")

    assert result["candidates"] == []
    assert "everything timeout" in result["warnings"][0]
    assert not (tmp_path / "runtime").exists()


def test_ask_research_saves_source_backed_answer(tmp_path):
    source = tmp_path / "TR5_PreOp_Gantt_20260415_162140.txt"
    source.write_text("TR5 schedule risk includes duplicate PDF versions.", encoding="utf-8")

    service = ResearchService(
        output_root=tmp_path / "runtime" / "research",
        search=lambda query, limit=50: [
            {
                "path": str(source),
                "name": source.name,
                "extension": ".txt",
                "size": 100,
                "modifiedAt": "2026-04-15 16:21",
            }
        ],
        extract=lambda path: {
            "status": "ok",
            "text": Path(path).read_text(encoding="utf-8"),
            "path": str(path),
            "extension": ".txt",
        },
        copilot=lambda packet: {
            "short_answer": "최신 TR5 일정 파일은 근거 파일에서 확인됩니다.",
            "findings": [
                {
                    "text": "중복 PDF 버전 리스크가 있습니다.",
                    "source_path": str(source),
                }
            ],
            "gaps": [],
            "next_actions": ["PDF 최신본을 비교하세요."],
        },
        timestamp=lambda: "20260416-120000",
    )

    result = service.ask_research("TR5 PreOp 최신 파일과 리스크")

    assert result["mode"] == "ask"
    assert result["sources"][0]["path"] == str(source)
    assert result["saved_markdown"].endswith(
        "runtime\\research\\answers\\20260416-120000-answer.md"
    )
    assert Path(result["saved_markdown"]).exists()
    assert Path(result["saved_json"]).exists()
    saved = json.loads(Path(result["saved_json"]).read_text(encoding="utf-8"))
    assert saved["short_answer"].startswith("최신 TR5")


def test_ask_research_returns_provider_neutral_partial_result_when_provider_fails(tmp_path):
    source = tmp_path / "note.txt"
    source.write_text("alpha beta", encoding="utf-8")

    service = ResearchService(
        output_root=tmp_path / "runtime" / "research",
        search=lambda query, limit=50: [{"path": str(source), "name": source.name}],
        extract=lambda path: {"status": "ok", "text": "alpha beta", "path": str(path)},
        provider_router=FakeProviderRouter(),
        timestamp=lambda: "20260416-120001",
    )
    service.provider_router.analyze = lambda *args, **kwargs: (_ for _ in ()).throw(
        RuntimeError("provider 422")
    )

    result = service.ask_research("alpha", provider="minimax-highspeed")

    assert result["short_answer"].startswith("AI provider unavailable")
    assert "Copilot" not in result["short_answer"]
    assert result["sources"][0]["path"] == str(source)
    assert "provider 422" in result["warnings"][0]


def test_ask_selected_uses_only_selected_candidates_and_save_false_writes_nothing(tmp_path):
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    first.write_text("first evidence", encoding="utf-8")
    second.write_text("second evidence", encoding="utf-8")
    seen = []

    service = ResearchService(
        output_root=tmp_path / "runtime" / "research",
        extract=lambda path: {
            "status": "ok",
            "text": Path(path).read_text(encoding="utf-8"),
            "path": str(path),
        },
        copilot=lambda packet: (
            seen.append(packet)
            or {
                "short_answer": "selected answer",
                "findings": [{"text": "first only", "source_path": str(first)}],
                "gaps": [],
                "next_actions": [],
            }
        ),
    )

    selected = [{"candidate_id": "a", "path": str(first), "name": first.name, "extension": ".txt"}]
    excluded = {"candidate_id": "b", "path": str(second), "name": second.name, "extension": ".txt"}

    result = service.ask_selected(
        "use selected only",
        selected_candidates=selected,
        save=False,
    )

    assert result["mode"] == "ask"
    assert [source["path"] for source in result["sources"]] == [str(first)]
    assert str(second) not in json.dumps(seen[0], ensure_ascii=False)
    assert excluded["path"] not in [source["path"] for source in result["sources"]]
    assert result["saved_markdown"] == ""
    assert not (tmp_path / "runtime").exists()


def test_md_extraction_strips_leading_powershell_uvx_markitdown_noise(tmp_path):
    source = tmp_path / "TAX_INVOICE_AE70066475.md"
    source.write_text("placeholder", encoding="utf-8")
    noisy_text = (
        "uvx : Installed 33 packages in 3.71s\r\n"
        "위치 C:\\Users\\SAMSUNG\\AppData\\Local\\Temp\\ps-script.ps1:88 문자:54\r\n"
        '+ ... uvx --from markitdown[pdf] markitdown "C:\\invoice.pdf"\r\n'
        "+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\r\n"
        "    + CategoryInfo          : NotSpecified: "
        "(Installed 33 packages:String) [], RemoteException\r\n"
        "    + FullyQualifiedErrorId : NativeCommandError\r\n"
        "\r\n"
        "Abu Dhabi Marine Operations And Services Company LLC\r\n"
        "Invoice Number | : 98256434\r\n"
    )
    seen = []
    service = ResearchService(
        output_root=tmp_path / "runtime" / "research",
        extract=lambda path: {"status": "ok", "text": noisy_text},
        copilot=lambda packet: (
            seen.append(packet)
            or {
                "short_answer": "invoice extracted",
                "findings": [],
                "gaps": [],
                "next_actions": [],
            }
        ),
    )

    result = service.ask_selected(
        "extract invoice",
        selected_candidates=[{"path": str(source), "name": source.name, "extension": ".md"}],
        save=False,
    )

    assert result["sources"][0]["snippet"].startswith(
        "Abu Dhabi Marine Operations And Services Company LLC"
    )
    assert seen[0]["sources"][0]["excerpt"].startswith(
        "Abu Dhabi Marine Operations And Services Company LLC"
    )
    assert "uvx :" not in seen[0]["sources"][0]["excerpt"]
    assert "NativeCommandError" not in seen[0]["sources"][0]["excerpt"]


def test_ask_selected_routes_requested_provider_and_mode(tmp_path):
    source = tmp_path / "invoice.md"
    source.write_text("invoice evidence", encoding="utf-8")
    router = FakeProviderRouter()
    service = ResearchService(
        output_root=tmp_path / "runtime" / "research",
        extract=lambda path: {"status": "ok", "text": Path(path).read_text(encoding="utf-8")},
        provider_router=router,
    )

    result = service.ask_selected(
        "extract invoice",
        selected_candidates=[{"path": str(source), "name": source.name, "extension": ".md"}],
        provider="minimax",
        analysis_mode="invoice-audit",
        tool_use=True,
        save=False,
    )

    assert router.calls[0]["provider"] == "minimax"
    assert router.calls[0]["analysis_mode"] == "invoice-audit"
    assert router.calls[0]["tool_use"] is True
    assert result["provider"] == "minimax"
    assert result["model"] == "MiniMax-M2.7"
    assert result["short_answer"] == "provider answer"
    assert result["ai_applied"] is True
    assert result["provider_status"] == "ai"
    assert result["structured_data"] == {"answer_quality": "ai-generated"}


def test_ask_selected_marks_fallback_when_provider_returns_fallback(tmp_path):
    source = tmp_path / "note.md"
    source.write_text("evidence", encoding="utf-8")

    class Router:
        def health(self):
            return {"active_provider": "fallback", "fallback": {"status": "ok"}}

        def analyze(self, packet, *, provider="auto", analysis_mode="ask", tool_use=False):
            return {
                "provider": "fallback",
                "model": "deterministic",
                "short_answer": "manual evidence only",
                "findings": [],
                "gaps": [],
                "next_actions": [],
            }

    service = ResearchService(
        output_root=tmp_path / "runtime" / "research",
        extract=lambda path: {"status": "ok", "text": Path(path).read_text(encoding="utf-8")},
        provider_router=Router(),
    )

    result = service.ask_selected(
        "question",
        selected_candidates=[{"path": str(source), "name": source.name, "extension": ".md"}],
        provider="auto",
        save=False,
    )

    assert result["provider"] == "fallback"
    assert result["ai_applied"] is False
    assert result["provider_status"] == "fallback"


def test_selected_analysis_save_true_writes_only_runtime_research(tmp_path):
    source = tmp_path / "evidence.txt"
    source.write_text("local evidence", encoding="utf-8")
    protected_dirs = [
        tmp_path / "vault" / "wiki",
        tmp_path / "vault" / "memory",
        tmp_path / "vault" / "mcp_raw",
    ]
    for protected_dir in protected_dirs:
        protected_dir.mkdir(parents=True)
        (protected_dir / "sentinel.txt").write_text("unchanged", encoding="utf-8")

    service = ResearchService(
        output_root=tmp_path / "runtime" / "research",
        extract=lambda path: {"status": "ok", "text": Path(path).read_text(encoding="utf-8")},
        copilot=lambda packet: {
            "short_answer": "answer",
            "findings": [],
            "gaps": [],
            "next_actions": [],
        },
        timestamp=lambda: "20260417-120000",
    )

    result = service.ask_selected(
        "local evidence",
        selected_candidates=[{"path": str(source), "name": source.name, "extension": ".txt"}],
        save=True,
    )

    assert Path(result["saved_markdown"]).is_relative_to(tmp_path / "runtime" / "research")
    assert Path(result["saved_json"]).is_relative_to(tmp_path / "runtime" / "research")
    for protected_dir in protected_dirs:
        assert sorted(path.name for path in protected_dir.iterdir()) == ["sentinel.txt"]
        assert (protected_dir / "sentinel.txt").read_text(encoding="utf-8") == "unchanged"


def test_ask_selected_rejects_empty_selection(tmp_path):
    service = ResearchService(output_root=tmp_path / "runtime" / "research")

    try:
        service.ask_selected("nothing", selected_candidates=[])
    except ValueError as exc:
        assert "selected_candidates" in str(exc)
    else:
        raise AssertionError("empty selection should fail")


def test_find_bundle_groups_core_and_supporting_files(tmp_path):
    doc = tmp_path / "Globalmaritime_MWS_13차.docx"
    pdf = tmp_path / "Globalmaritime_MWS_13차_v2.pdf"
    doc.write_text("execution approval", encoding="utf-8")
    pdf.write_text("exported report", encoding="utf-8")

    service = ResearchService(
        output_root=tmp_path / "runtime" / "research",
        search=lambda query, limit=50: [
            {"path": str(pdf), "name": pdf.name, "extension": ".pdf", "modifiedAt": "2026-04-15"},
            {"path": str(doc), "name": doc.name, "extension": ".docx", "modifiedAt": "2026-04-16"},
        ],
        extract=lambda path: {"status": "ok", "text": Path(path).read_text(encoding="utf-8")},
        copilot=lambda packet: {
            "bundle_title": "Globalmaritime MWS 13차",
            "core_files": [{"path": str(doc), "role": "execution approval"}],
            "supporting_files": [{"path": str(pdf), "role": "exported report"}],
            "duplicates_or_versions": [{"path": str(pdf), "reason": "version suffix"}],
            "missing_or_gap_hints": [],
            "next_actions": ["DOCX와 PDF 내용을 비교하세요."],
        },
        timestamp=lambda: "20260416-120002",
    )

    result = service.find_bundle("Globalmaritime MWS 13차")

    assert result["mode"] == "find-bundle"
    assert result["core_files"][0]["path"] == str(doc)
    assert result["supporting_files"][0]["path"] == str(pdf)
    assert Path(result["saved_markdown"]).exists()
    assert Path(result["saved_json"]).exists()


def test_find_bundle_keeps_running_when_candidate_disappears(tmp_path):
    missing = tmp_path / "deleted.docx"
    existing = tmp_path / "Globalmaritime.txt"
    existing.write_text("Globalmaritime evidence", encoding="utf-8")

    service = ResearchService(
        output_root=tmp_path / "runtime" / "research",
        search=lambda query, limit=50: [
            {"path": str(missing), "name": missing.name, "extension": ".docx"},
            {"path": str(existing), "name": existing.name, "extension": ".txt"},
        ],
        extract=lambda path: (
            (_ for _ in ()).throw(FileNotFoundError(str(path)))
            if Path(path) == missing
            else {"status": "ok", "text": "Globalmaritime evidence"}
        ),
        copilot=lambda packet: {
            "bundle_title": "Globalmaritime",
            "core_files": [{"path": str(existing), "role": "candidate"}],
            "supporting_files": [],
            "duplicates_or_versions": [],
            "missing_or_gap_hints": [],
            "next_actions": [],
        },
        timestamp=lambda: "20260416-120003",
    )

    result = service.find_bundle("Globalmaritime", max_candidates=2, save=False)

    assert result["mode"] == "find-bundle"
    missing_source = next(source for source in result["sources"] if source["path"] == str(missing))
    assert missing_source["extraction_status"] == "limited"
    assert "FileNotFoundError" in missing_source["reason"]


def test_find_bundle_selected_uses_only_selected_candidates(tmp_path):
    doc = tmp_path / "Globalmaritime.docx"
    pdf = tmp_path / "Globalmaritime.pdf"
    doc.write_text("doc evidence", encoding="utf-8")
    pdf.write_text("pdf evidence", encoding="utf-8")

    service = ResearchService(
        output_root=tmp_path / "runtime" / "research",
        extract=lambda path: {"status": "ok", "text": Path(path).read_text(encoding="utf-8")},
        copilot=lambda packet: {
            "bundle_title": "selected bundle",
            "core_files": [{"path": str(doc), "role": "core"}],
            "supporting_files": [],
            "duplicates_or_versions": [],
            "missing_or_gap_hints": [],
            "next_actions": [],
        },
    )

    result = service.find_bundle_selected(
        "Globalmaritime",
        selected_candidates=[
            {"candidate_id": "doc", "path": str(doc), "name": doc.name, "extension": ".docx"}
        ],
        save=False,
    )

    assert result["mode"] == "find-bundle"
    assert [source["path"] for source in result["sources"]] == [str(doc)]
    assert str(pdf) not in json.dumps(result, ensure_ascii=False)


def test_find_bundle_selected_routes_provider_and_tool_use(tmp_path):
    doc = tmp_path / "bundle.md"
    doc.write_text("bundle evidence", encoding="utf-8")
    router = FakeProviderRouter()
    service = ResearchService(
        output_root=tmp_path / "runtime" / "research",
        extract=lambda path: {"status": "ok", "text": Path(path).read_text(encoding="utf-8")},
        provider_router=router,
    )

    result = service.find_bundle_selected(
        "bundle",
        selected_candidates=[{"path": str(doc), "name": doc.name, "extension": ".md"}],
        provider="minimax-highspeed",
        tool_use=True,
        save=False,
    )

    assert router.calls[0]["provider"] == "minimax-highspeed"
    assert router.calls[0]["analysis_mode"] == "find-bundle"
    assert router.calls[0]["tool_use"] is True
    assert result["provider"] == "minimax-highspeed"
    assert result["model"] == "MiniMax-M2.7"
    assert result["core_files"][0]["path"] == str(doc)
