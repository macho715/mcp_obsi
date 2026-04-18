import json
import os

import pytest

from scripts.local_research_providers import (
    CopilotProvider,
    FallbackProvider,
    MiniMaxProvider,
    ProviderRouter,
)


def _packet():
    return {
        "mode": "ask",
        "prompt": "question",
        "sources": [{"source_path": "C:\\Docs\\a.md", "excerpt": "evidence"}],
    }


class RecordingProvider:
    def __init__(self, name, result=None, error=None):
        self.name = name
        self.result = result or {
            "short_answer": f"{name} answer",
            "findings": [],
            "gaps": [],
            "next_actions": [],
        }
        self.error = error
        self.calls = []

    def health(self):
        return {"status": "ok", "provider": self.name}

    def analyze(self, packet, *, provider, analysis_mode, tool_use=False):
        self.calls.append((packet, provider, analysis_mode, tool_use))
        if self.error:
            raise self.error
        output = dict(self.result)
        output["provider"] = self.name
        output["model"] = self.name
        return output


def test_router_uses_requested_minimax_provider():
    minimax = RecordingProvider("minimax")
    router = ProviderRouter(minimax=minimax, copilot=RecordingProvider("copilot"))

    result = router.analyze(_packet(), provider="minimax", analysis_mode="ask", tool_use=True)

    assert result["provider"] == "minimax"
    assert minimax.calls[0][3] is True


def test_router_uses_requested_copilot_provider():
    copilot = RecordingProvider("copilot")
    router = ProviderRouter(minimax=RecordingProvider("minimax"), copilot=copilot)

    result = router.analyze(_packet(), provider="copilot", analysis_mode="ask")

    assert result["provider"] == "copilot"
    assert len(copilot.calls) == 1


def test_router_falls_back_to_standard_minimax_when_highspeed_plan_unsupported():
    highspeed = RecordingProvider(
        "minimax-highspeed",
        error=RuntimeError(
            "your current token plan not support model, MiniMax-M2.7-highspeed (2061)"
        ),
    )
    minimax = RecordingProvider("minimax")
    router = ProviderRouter(minimax=minimax, minimax_highspeed=highspeed)

    result = router.analyze(_packet(), provider="minimax-highspeed", analysis_mode="ask")

    assert result["provider"] == "minimax"
    assert len(highspeed.calls) == 1
    assert len(minimax.calls) == 1
    assert result["provider_warnings"] == [
        (
            "minimax-highspeed failed: your current token plan not support model, "
            "MiniMax-M2.7-highspeed (2061); retried with minimax"
        )
    ]


def test_router_fallback_provider_makes_no_external_calls():
    minimax = RecordingProvider("minimax")
    copilot = RecordingProvider("copilot")
    router = ProviderRouter(minimax=minimax, copilot=copilot)

    result = router.analyze(_packet(), provider="fallback", analysis_mode="ask")

    assert result["provider"] == "fallback"
    assert minimax.calls == []
    assert copilot.calls == []


def test_router_auto_falls_back_in_order():
    minimax = RecordingProvider("minimax", error=RuntimeError("minimax down"))
    copilot = RecordingProvider("copilot")
    router = ProviderRouter(minimax=minimax, copilot=copilot)

    result = router.analyze(_packet(), provider="auto", analysis_mode="ask")

    assert result["provider"] == "copilot"
    assert result["provider_warnings"] == ["minimax failed: minimax down"]


def test_router_rejects_unknown_provider():
    router = ProviderRouter(
        minimax=RecordingProvider("minimax"), copilot=RecordingProvider("copilot")
    )

    with pytest.raises(ValueError, match="Unsupported provider"):
        router.analyze(_packet(), provider="unknown", analysis_mode="ask")


def test_minimax_health_masks_api_key(monkeypatch):
    monkeypatch.setenv("MINIMAX_API_KEY", "secret-value")
    monkeypatch.delenv("MINIMAX_HEALTH_LIVE_SMOKE", raising=False)
    provider = MiniMaxProvider()

    health = provider.health()

    assert health["status"] == "ok"
    assert health["api_key_configured"] is True
    assert health["key_configured"] == {
        "status": "ok",
        "configured": True,
        "current_process": True,
        "registered_scopes": [],
    }
    assert health["live_smoke"] == {
        "status": "not_run",
        "enabled": False,
        "reason": "set MINIMAX_HEALTH_LIVE_SMOKE=1 to probe the live API",
    }
    assert health["api_key_current_process"] is True
    assert "secret-value" not in str(health)


def test_minimax_health_live_smoke_can_probe_api_without_exposing_key(monkeypatch):
    monkeypatch.setenv("MINIMAX_API_KEY", "secret-value")
    monkeypatch.setenv("MINIMAX_HEALTH_LIVE_SMOKE", "1")

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "content": [{"type": "text", "text": "ok"}],
                "model": "MiniMax-M2.7",
            }

    provider = MiniMaxProvider(post=lambda *args, **kwargs: Response())

    health = provider.health()

    assert health["status"] == "ok"
    assert health["key_configured"]["status"] == "ok"
    assert health["live_smoke"] == {
        "status": "ok",
        "enabled": True,
        "model": "MiniMax-M2.7",
    }
    assert "secret-value" not in str(health)


def test_minimax_health_reports_registered_key_not_loaded(monkeypatch):
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    monkeypatch.setattr(
        "scripts.local_research_providers._registered_env_var_scopes",
        lambda name: ["user"] if name == "MINIMAX_API_KEY" else [],
    )
    provider = MiniMaxProvider()

    health = provider.health()

    assert health["status"] == "unavailable"
    assert health["api_key_configured"] is False
    assert health["key_configured"]["status"] == "missing"
    assert health["live_smoke"]["status"] == "skipped"
    assert health["api_key_current_process"] is False
    assert health["api_key_registered_scopes"] == ["user"]
    assert health["setup_hint"] == "MINIMAX_API_KEY is registered but this server needs restart"


def test_minimax_health_reports_missing_key(monkeypatch):
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    monkeypatch.setattr(
        "scripts.local_research_providers._registered_env_var_scopes",
        lambda name: [],
    )
    provider = MiniMaxProvider()

    health = provider.health()

    assert health["status"] == "unavailable"
    assert health["api_key_registered_scopes"] == []
    assert health["setup_hint"] == "Set MINIMAX_API_KEY and restart this server"


def test_minimax_analyze_parses_anthropic_text_response(monkeypatch):
    monkeypatch.setenv("MINIMAX_API_KEY", "secret-value")
    captured = {}

    def fake_post(url, *, json, headers, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers

        class Response:
            def raise_for_status(self):
                return None

            def json(self):
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                '{"short_answer":"ok","findings":[],"gaps":[],"next_actions":[]}'
                            ),
                        }
                    ],
                    "model": "MiniMax-M2.7",
                }

        return Response()

    provider = MiniMaxProvider(post=fake_post)
    result = provider.analyze(_packet(), provider="minimax", analysis_mode="ask")

    assert result["short_answer"] == "ok"
    assert result["provider"] == "minimax"
    assert result["model"] == "MiniMax-M2.7"
    assert captured["url"].endswith("/v1/messages")
    assert "secret-value" not in str(captured["json"])
    assert captured["headers"]["x-api-key"] == "secret-value"


def test_minimax_request_body_includes_schema_and_specialist_instructions(monkeypatch):
    monkeypatch.setenv("MINIMAX_API_KEY", "secret-value")
    captured = {}

    def fake_post(url, *, json, headers, timeout):
        captured["json"] = json

        class Response:
            def raise_for_status(self):
                return None

            def json(self):
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                '{"short_answer":"invoice checked","findings":[],'
                                '"gaps":[],"next_actions":[],"structured_data":'
                                '{"invoice_number":"AE70066475"}}'
                            ),
                        }
                    ],
                    "model": "MiniMax-M2.7",
                }

        return Response()

    provider = MiniMaxProvider(post=fake_post)
    result = provider.analyze(_packet(), provider="minimax", analysis_mode="invoice-audit")

    packet_text = captured["json"]["messages"][0]["content"][0]["text"]
    packet = json.loads(packet_text)
    assert captured["json"]["temperature"] == 0.2
    assert "required_output_schema" in packet
    assert "specialist_instruction" in packet
    assert "invoice_number" in json.dumps(packet["required_output_schema"])
    assert "invoice" in packet["specialist_instruction"].lower()
    assert result["structured_data"]["invoice_number"] == "AE70066475"


def test_copilot_provider_uses_supplied_callable():
    provider = CopilotProvider(
        copilot=lambda packet: {
            "short_answer": "copilot ok",
            "findings": [],
            "gaps": [],
            "next_actions": [],
        }
    )

    result = provider.analyze(_packet(), provider="copilot", analysis_mode="ask")

    assert result["provider"] == "copilot"
    assert result["short_answer"] == "copilot ok"


def test_fallback_provider_returns_bundle_shape():
    provider = FallbackProvider()

    result = provider.analyze(_packet(), provider="fallback", analysis_mode="find-bundle")

    assert result["provider"] == "fallback"
    assert result["core_files"][0]["path"] == "C:\\Docs\\a.md"


def test_minimax_missing_key_raises_without_printing_secret(monkeypatch):
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    provider = MiniMaxProvider()

    with pytest.raises(RuntimeError, match="MINIMAX_API_KEY"):
        provider.analyze(_packet(), provider="minimax", analysis_mode="ask")

    assert os.getenv("MINIMAX_API_KEY") is None


def test_minimax_http_error_includes_safe_provider_message(monkeypatch):
    monkeypatch.setenv("MINIMAX_API_KEY", "secret-value")

    class Response:
        status_code = 500
        text = '{"type":"error","error":{"message":"insufficient balance (1008)"}}'

        def raise_for_status(self):
            raise RuntimeError("500 Server Error")

        def json(self):
            raise AssertionError("json should not be called after HTTP failure")

    provider = MiniMaxProvider(post=lambda *args, **kwargs: Response())

    with pytest.raises(RuntimeError, match="insufficient balance"):
        provider.analyze(_packet(), provider="minimax", analysis_mode="ask")


def test_minimax_retries_http_error_with_compact_packet(monkeypatch):
    monkeypatch.setenv("MINIMAX_API_KEY", "secret-value")
    calls = []
    packet = {
        "mode": "ask",
        "prompt": "question",
        "sources": [
            {
                "source_path": f"C:\\Docs\\source-{index}.md",
                "excerpt": "evidence " * 500,
            }
            for index in range(6)
        ],
    }

    class ErrorResponse:
        status_code = 500
        text = '{"type":"error","error":{"message":"internal server error"}}'

        def raise_for_status(self):
            raise RuntimeError("500 Server Error")

    class SuccessResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "content": [
                    {
                        "type": "text",
                        "text": (
                            '{"short_answer":"compact ok","findings":[],'
                            '"gaps":[],"next_actions":[]}'
                        ),
                    }
                ],
                "model": "MiniMax-M2.7",
            }

    def fake_post(url, *, json, headers, timeout):
        calls.append(json)
        if len(calls) == 1:
            return ErrorResponse()
        return SuccessResponse()

    provider = MiniMaxProvider(post=fake_post)
    result = provider.analyze(packet, provider="minimax", analysis_mode="ask")

    assert result["provider"] == "minimax"
    assert result["short_answer"] == "compact ok"
    assert result["provider_warnings"] == [
        "minimax compact retry: provider request failed: 500 Server Error: internal server error"
    ]
    compact_packet = json.loads(calls[1]["messages"][0]["content"][0]["text"])
    assert len(compact_packet["sources"]) == 3
    assert all(len(source["excerpt"]) <= 1000 for source in compact_packet["sources"])
    assert "secret-value" not in str(calls)


def test_minimax_repairs_schema_invalid_response_once(monkeypatch):
    monkeypatch.setenv("MINIMAX_API_KEY", "secret-value")
    calls = []

    class Response:
        def __init__(self, text):
            self._text = text

        def raise_for_status(self):
            return None

        def json(self):
            return {"content": [{"type": "text", "text": self._text}], "model": "MiniMax-M2.7"}

    def fake_post(url, *, json, headers, timeout):
        calls.append(json)
        if len(calls) == 1:
            return Response('{"findings":[]}')
        return Response('{"short_answer":"repaired","findings":[],"gaps":[],"next_actions":[]}')

    provider = MiniMaxProvider(post=fake_post)
    result = provider.analyze(_packet(), provider="minimax", analysis_mode="ask")

    assert result["short_answer"] == "repaired"
    assert len(calls) == 2
    assert result["provider_warnings"] == ["minimax repair retry: short_answer field required"]
    assert "secret-value" not in str(calls)
    original_packet = json.loads(calls[1]["messages"][0]["content"][0]["text"])
    assert original_packet["prompt"] == "question"
    assert original_packet["sources"][0]["source_path"] == "C:\\Docs\\a.md"


def test_minimax_extracts_json_inside_text_and_code_fence(monkeypatch):
    monkeypatch.setenv("MINIMAX_API_KEY", "secret-value")

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "content": [
                    {
                        "type": "thinking",
                        "thinking": "hidden chain of thought",
                    },
                    {
                        "type": "text",
                        "text": (
                            "Here is the result:\n```json\n"
                            '{"short_answer":"ok","findings":[],"gaps":[],"next_actions":[]}'
                            "\n```"
                        ),
                    },
                ],
                "model": "MiniMax-M2.7",
            }

    provider = MiniMaxProvider(post=lambda *args, **kwargs: Response())
    result = provider.analyze(_packet(), provider="minimax", analysis_mode="ask")

    assert result["short_answer"] == "ok"
    assert "hidden chain of thought" not in str(result)


def test_minimax_returns_deterministic_fallback_when_repair_fails(monkeypatch):
    monkeypatch.setenv("MINIMAX_API_KEY", "secret-value")

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"content": [{"type": "text", "text": '{"findings":[]}'}]}

    provider = MiniMaxProvider(post=lambda *args, **kwargs: Response())
    result = provider.analyze(_packet(), provider="minimax", analysis_mode="ask")

    assert result["provider"] == "fallback"
    assert result["short_answer"].startswith("AI provider unavailable")
    assert any("minimax repair failed" in warning for warning in result["provider_warnings"])
