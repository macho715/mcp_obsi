from pathlib import Path

from fastapi.testclient import TestClient

from scripts.local_research_web import create_app


class FakeService:
    def health(self):
        return {
            "status": "ok",
            "everything": {"status": "ok", "base_url": "http://127.0.0.1:8080"},
            "copilot": {"status": "ok", "base_url": "http://127.0.0.1:3010"},
            "minimax": {
                "status": "ok",
                "model": "MiniMax-M2.7",
                "api_key_configured": True,
            },
            "active_provider": "minimax",
            "output_root": "runtime/research",
        }

    def preview_candidates(self, prompt, *, mode="ask", scope="all", max_candidates=10):
        return {
            "mode": mode,
            "prompt": prompt,
            "candidates": [
                {
                    "candidate_id": "abc",
                    "path": "C:\\Docs\\a.txt",
                    "name": "a.txt",
                    "extension": ".txt",
                    "score": 10,
                    "rank_reason": "filename match",
                    "selected_by_default": True,
                    "status": "available",
                },
                {
                    "candidate_id": "def",
                    "path": "C:\\Docs\\b.md",
                    "name": "b.md",
                    "extension": ".md",
                    "score": 5,
                    "rank_reason": "path match",
                    "selected_by_default": False,
                    "status": "available",
                },
            ][:max_candidates],
            "warnings": [],
        }

    def ask_research(
        self,
        question,
        *,
        scope="all",
        max_candidates=10,
        save=True,
        provider="auto",
        analysis_mode="ask",
        tool_use=False,
    ):
        return {
            "mode": "ask",
            "question": question,
            "provider": provider,
            "ai_applied": provider != "fallback",
            "provider_status": "fallback" if provider == "fallback" else "ai",
            "analysis_mode": analysis_mode,
            "tool_use": tool_use,
            "short_answer": "answer",
            "findings": [],
            "sources": [],
            "gaps": [],
            "next_actions": [],
            "saved_markdown": "runtime/research/answers/a.md" if save else "",
            "saved_json": "runtime/research/answers/a.json" if save else "",
            "warnings": [],
        }

    def ask_selected(
        self,
        question,
        selected_candidates,
        *,
        scope="all",
        save=True,
        provider="auto",
        analysis_mode="ask",
        tool_use=False,
    ):
        return {
            "mode": "ask",
            "question": question,
            "selected_candidates": selected_candidates,
            "provider": provider,
            "ai_applied": provider != "fallback",
            "provider_status": "fallback" if provider == "fallback" else "ai",
            "analysis_mode": analysis_mode,
            "tool_use": tool_use,
            "short_answer": "selected answer",
            "sources": selected_candidates,
            "saved_markdown": "runtime/research/answers/a.md" if save else "",
            "saved_json": "runtime/research/answers/a.json" if save else "",
            "warnings": [],
        }

    def find_bundle(
        self,
        topic,
        *,
        scope="all",
        max_candidates=20,
        save=True,
        provider="auto",
        analysis_mode="find-bundle",
        tool_use=False,
    ):
        return {
            "mode": "find-bundle",
            "topic": topic,
            "provider": provider,
            "ai_applied": provider != "fallback",
            "provider_status": "fallback" if provider == "fallback" else "ai",
            "analysis_mode": analysis_mode,
            "tool_use": tool_use,
            "bundle_title": topic,
            "core_files": [],
            "supporting_files": [],
            "duplicates_or_versions": [],
            "missing_or_gap_hints": [],
            "next_actions": [],
            "sources": [],
            "saved_markdown": "runtime/research/bundles/b.md" if save else "",
            "saved_json": "runtime/research/bundles/b.json" if save else "",
            "warnings": [],
        }

    def find_bundle_selected(
        self,
        topic,
        selected_candidates,
        *,
        scope="all",
        save=True,
        provider="auto",
        analysis_mode="find-bundle",
        tool_use=False,
    ):
        return {
            "mode": "find-bundle",
            "topic": topic,
            "selected_candidates": selected_candidates,
            "provider": provider,
            "ai_applied": provider != "fallback",
            "provider_status": "fallback" if provider == "fallback" else "ai",
            "analysis_mode": analysis_mode,
            "tool_use": tool_use,
            "bundle_title": "selected bundle",
            "core_files": selected_candidates,
            "supporting_files": [],
            "duplicates_or_versions": [],
            "missing_or_gap_hints": [],
            "next_actions": [],
            "sources": selected_candidates,
            "saved_markdown": "runtime/research/bundles/b.md" if save else "",
            "saved_json": "runtime/research/bundles/b.json" if save else "",
            "warnings": [],
        }


def test_create_app_serves_working_interface():
    client = TestClient(create_app(service=FakeService()))

    response = client.get("/")

    assert response.status_code == 200
    assert "Local Research Assistant" in response.text
    assert "Find Bundle" in response.text
    assert "Preview Candidates" in response.text
    assert "Analyze Selected" in response.text
    assert "Extension" in response.text
    assert "Modified" in response.text
    assert "Score" in response.text
    assert "escapeHtml" in response.text
    assert "MiniMax M2.7" in response.text
    assert "Invoice Audit" in response.text
    assert "Use tool loop" in response.text
    assert "dashboardStatusText" in response.text
    assert "renderAiStatus" in response.text
    assert "MiniMax M2.7 Highspeed (plan required)" in response.text
    assert "Start job" in response.text
    assert "Cancel job" in response.text
    assert "pollJob" in response.text
    assert "renderReport" in response.text
    assert "renderDebugJson" in response.text
    assert "Start job uses checked candidates only" in response.text
    assert "selected-only packet" in response.text
    assert "Tool loop is not active in U1" in response.text
    assert "checkbox records intent only" in response.text


def test_health_route_returns_dependency_status():
    client = TestClient(create_app(service=FakeService()))

    response = client.get("/api/research/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["minimax"]["status"] == "ok"
    assert response.json()["active_provider"] == "minimax"


def test_health_route_adds_route_aware_dashboard_status_for_minimax_ready_copilot_unavailable():
    class MiniMaxReadyService(FakeService):
        def health(self):
            payload = super().health()
            payload.update(
                {
                    "status": "blocked",
                    "route_status": "ready",
                    "route_ready": True,
                    "active_provider": "minimax",
                    "copilot": {"status": "unavailable", "base_url": "http://127.0.0.1:3010"},
                    "minimax": {
                        "status": "ok",
                        "model": "MiniMax-M2.7",
                        "api_key_configured": True,
                    },
                }
            )
            return payload

    client = TestClient(create_app(service=MiniMaxReadyService()))

    response = client.get("/api/research/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "blocked"
    assert body["route_status"] == "ready"
    assert body["route_ready"] is True
    assert body["dashboard_status"] == (
        "Route: ready | Active: minimax | Everything: ok | "
        "MiniMax: ok (key ok, live not run) | Copilot: unavailable"
    )
    assert "blocked" not in body["dashboard_status"].lower()


def test_health_route_explains_minimax_restart_needed():
    class MiniMaxNeedsRestartService(FakeService):
        def health(self):
            payload = super().health()
            payload.update(
                {
                    "status": "ready",
                    "route_status": "ready",
                    "route_ready": True,
                    "active_provider": "fallback",
                    "minimax": {
                        "status": "unavailable",
                        "api_key_configured": False,
                        "api_key_current_process": False,
                        "api_key_registered_scopes": ["user"],
                        "setup_hint": (
                            "MINIMAX_API_KEY is registered but this server needs restart"
                        ),
                    },
                    "copilot": {"status": "unavailable"},
                }
            )
            return payload

    client = TestClient(create_app(service=MiniMaxNeedsRestartService()))

    response = client.get("/api/research/health")

    assert response.status_code == 200
    assert response.json()["dashboard_status"] == (
        "Route: ready | Active: fallback | Everything: ok | "
        "MiniMax: unavailable (restart needed) | Copilot: unavailable"
    )


def test_health_route_explains_minimax_key_missing():
    class MiniMaxMissingKeyService(FakeService):
        def health(self):
            payload = super().health()
            payload.update(
                {
                    "status": "ready",
                    "route_status": "ready",
                    "route_ready": True,
                    "active_provider": "fallback",
                    "minimax": {
                        "status": "unavailable",
                        "api_key_configured": False,
                        "api_key_current_process": False,
                        "api_key_registered_scopes": [],
                        "setup_hint": "Set MINIMAX_API_KEY and restart this server",
                    },
                    "copilot": {"status": "unavailable"},
                }
            )
            return payload

    client = TestClient(create_app(service=MiniMaxMissingKeyService()))

    response = client.get("/api/research/health")

    assert response.status_code == 200
    assert response.json()["dashboard_status"] == (
        "Route: ready | Active: fallback | Everything: ok | "
        "MiniMax: unavailable (set MINIMAX_API_KEY) | Copilot: unavailable"
    )


def test_remote_client_is_rejected_even_if_server_is_bound_wide():
    client = TestClient(create_app(service=FakeService()), client=("192.168.1.50", 50000))

    response = client.get("/")

    assert response.status_code == 403
    assert "loopback-only" in response.text


def test_ask_route_rejects_empty_question():
    client = TestClient(create_app(service=FakeService()))

    response = client.post("/api/research/ask", json={"question": " "})

    assert response.status_code == 422


def test_ask_route_returns_service_result():
    client = TestClient(create_app(service=FakeService()))

    response = client.post(
        "/api/research/ask",
        json={
            "question": "TR5 review",
            "provider": "minimax",
            "analysis_mode": "invoice-audit",
            "tool_use": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["mode"] == "ask"
    assert response.json()["question"] == "TR5 review"
    assert response.json()["provider"] == "minimax"
    assert response.json()["analysis_mode"] == "invoice-audit"
    assert response.json()["tool_use"] is True


def test_ask_route_rejects_unknown_provider():
    client = TestClient(create_app(service=FakeService()))

    response = client.post(
        "/api/research/ask",
        json={"question": "TR5 review", "provider": "unknown"},
    )

    assert response.status_code == 422


def test_ask_route_rejects_unknown_analysis_mode():
    client = TestClient(create_app(service=FakeService()))

    response = client.post(
        "/api/research/ask",
        json={"question": "TR5 review", "analysis_mode": "unknown"},
    )

    assert response.status_code == 422


def test_find_bundle_route_returns_service_result():
    client = TestClient(create_app(service=FakeService()))

    response = client.post("/api/research/find-bundle", json={"topic": "Globalmaritime"})

    assert response.status_code == 200
    assert response.json()["mode"] == "find-bundle"
    assert response.json()["bundle_title"] == "Globalmaritime"


def test_candidates_route_returns_preview_candidates():
    client = TestClient(create_app(service=FakeService()))

    response = client.post(
        "/api/research/candidates",
        json={"prompt": "Globalmaritime", "mode": "find-bundle", "max_candidates": 2},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "find-bundle"
    assert body["prompt"] == "Globalmaritime"
    assert len(body["candidates"]) == 2
    assert body["candidates"][0]["candidate_id"] == "abc"


def test_candidates_route_rejects_unknown_mode():
    client = TestClient(create_app(service=FakeService()))

    response = client.post(
        "/api/research/candidates",
        json={"prompt": "Globalmaritime", "mode": "unknown"},
    )

    assert response.status_code == 422


def test_ask_selected_route_rejects_empty_selection():
    client = TestClient(create_app(service=FakeService()))

    response = client.post(
        "/api/research/ask-selected",
        json={"question": "TR5", "selected_candidates": []},
    )

    assert response.status_code == 422


def test_ask_selected_route_returns_selected_result():
    client = TestClient(create_app(service=FakeService()))
    selected = [{"candidate_id": "abc", "path": "C:\\Docs\\a.txt"}]

    response = client.post(
        "/api/research/ask-selected",
        json={
            "question": "TR5",
            "selected_candidates": selected,
            "save": False,
            "provider": "minimax-highspeed",
            "analysis_mode": "extract-fields",
            "tool_use": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "ask"
    assert body["selected_candidates"] == selected
    assert body["saved_markdown"] == ""
    assert body["provider"] == "minimax-highspeed"
    assert body["analysis_mode"] == "extract-fields"
    assert body["tool_use"] is True


def test_find_bundle_selected_route_rejects_empty_selection():
    client = TestClient(create_app(service=FakeService()))

    response = client.post(
        "/api/research/find-bundle-selected",
        json={"topic": "Globalmaritime", "selected_candidates": []},
    )

    assert response.status_code == 422


def test_find_bundle_selected_route_returns_selected_result():
    client = TestClient(create_app(service=FakeService()))
    selected = [{"candidate_id": "abc", "path": "C:\\Docs\\a.txt"}]

    response = client.post(
        "/api/research/find-bundle-selected",
        json={
            "topic": "Globalmaritime",
            "selected_candidates": selected,
            "save": False,
            "provider": "copilot",
            "tool_use": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "find-bundle"
    assert body["selected_candidates"] == selected
    assert body["saved_json"] == ""
    assert body["provider"] == "copilot"
    assert body["tool_use"] is True


def test_job_route_returns_job_id_and_completed_report():
    client = TestClient(create_app(service=FakeService(), run_jobs_async=False))

    response = client.post(
        "/api/research/jobs",
        json={
            "mode": "ask",
            "prompt": "TR5",
            "provider": "minimax",
            "analysis_mode": "ask",
            "save": False,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["job_id"].startswith("jr_")
    assert body["status"] == "done"
    assert body["created_at"]
    assert body["report"]["sections"][0]["title"] == "Answer"
    assert body["result"]["saved_markdown"] == ""


def test_job_route_uses_selected_candidates_when_present():
    client = TestClient(create_app(service=FakeService(), run_jobs_async=False))
    selected = [{"candidate_id": "abc", "path": "C:\\Docs\\a.txt", "name": "a.txt"}]

    response = client.post(
        "/api/research/jobs",
        json={
            "mode": "find-bundle",
            "prompt": "TR5",
            "selected_candidates": selected,
            "provider": "fallback",
            "save": False,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "done"
    assert body["result"]["mode"] == "find-bundle"
    assert body["result"]["selected_candidates"] == selected
    assert body["report"]["title"] == "selected bundle"


def test_job_status_and_cancel_unknown_job_return_404():
    client = TestClient(create_app(service=FakeService(), run_jobs_async=False))

    status_response = client.get("/api/research/jobs/jr_missing")
    cancel_response = client.post("/api/research/jobs/jr_missing/cancel")

    assert status_response.status_code == 404
    assert cancel_response.status_code == 404


def test_job_cancel_route_returns_cancel_status():
    client = TestClient(create_app(service=FakeService(), run_jobs_async=True))
    response = client.post(
        "/api/research/jobs",
        json={"mode": "ask", "prompt": "TR5", "provider": "fallback", "save": False},
    )
    job_id = response.json()["job_id"]

    cancel_response = client.post(f"/api/research/jobs/{job_id}/cancel")

    assert cancel_response.status_code == 200
    assert cancel_response.json()["job_id"] == job_id
    assert cancel_response.json()["status"] in {"cancel_requested", "done", "cancelled"}


def test_script_file_exists_for_manual_server_start():
    assert Path("scripts/local_research_web.py").exists()
