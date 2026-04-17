from __future__ import annotations

import json
import os
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

import requests

from scripts.local_research_schemas import validate_research_result
from scripts.local_wiki_copilot import DEFAULT_COPILOT_ENDPOINT, DEFAULT_COPILOT_MODEL

DEFAULT_MINIMAX_BASE_URL = "https://api.minimax.io/anthropic"
DEFAULT_MINIMAX_MODEL = "MiniMax-M2.7"
DEFAULT_MINIMAX_FAST_MODEL = "MiniMax-M2.7-highspeed"
DEFAULT_MINIMAX_MAX_TOKENS = 8192
DEFAULT_MINIMAX_TEMPERATURE = 0.2
DEFAULT_TIMEOUT_SECONDS = 300
COMPACT_RETRY_MAX_SOURCES = 3
COMPACT_RETRY_EXCERPT_CHARS = 1000
SUPPORTED_PROVIDERS = {"auto", "minimax", "minimax-highspeed", "copilot", "fallback"}

PostFn = Callable[..., Any]
CopilotFn = Callable[[dict[str, Any]], dict[str, Any]]


class ProviderError(RuntimeError):
    """Raised when a local research provider cannot produce an analysis."""


class LLMProvider(Protocol):
    provider_name: str
    model: str

    def health(self) -> dict[str, Any]:
        """Return provider health without exposing secrets."""

    def analyze(
        self,
        packet: dict[str, Any],
        *,
        provider: str,
        analysis_mode: str,
        tool_use: bool = False,
    ) -> dict[str, Any]:
        """Analyze a local research packet and return a normalized JSON payload."""


class FallbackProvider:
    def __init__(self, *, provider_name: str = "fallback", model: str = "deterministic") -> None:
        self.provider_name = provider_name
        self.model = model

    def health(self) -> dict[str, Any]:
        return {"status": "ok", "provider": self.provider_name, "model": self.model}

    def analyze(
        self,
        packet: dict[str, Any],
        *,
        provider: str = "fallback",
        analysis_mode: str = "ask",
        tool_use: bool = False,
    ) -> dict[str, Any]:
        mode = _bundle_or_ask(packet, analysis_mode)
        payload = _fallback_bundle(packet) if mode == "find-bundle" else _fallback_answer(packet)
        payload = _validate_research_payload(payload, packet=packet, analysis_mode=analysis_mode)
        return _with_provider_metadata(
            payload,
            provider=self.provider_name,
            model=self.model,
            analysis_mode=analysis_mode,
            tool_use=tool_use,
        )


class CopilotProvider:
    def __init__(
        self,
        *,
        copilot: CopilotFn | None = None,
        endpoint: str | None = None,
        model: str = DEFAULT_COPILOT_MODEL,
        token_env: str = "LOCAL_WIKI_COPILOT_TOKEN",
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
        post: PostFn | None = None,
    ) -> None:
        self.provider_name = "copilot"
        self.endpoint = (
            endpoint or os.getenv("LOCAL_RESEARCH_COPILOT_ENDPOINT") or DEFAULT_COPILOT_ENDPOINT
        )
        self.model = model
        self.token_env = token_env
        self.timeout = timeout
        self._copilot = copilot
        self._post = post or requests.post

    def health(self) -> dict[str, Any]:
        health_url = self.endpoint.rsplit("/", 1)[0] + "/health"
        try:
            response = requests.get(health_url, timeout=3)
            response.raise_for_status()
        except Exception as exc:
            return {"status": "unavailable", "base_url": self.endpoint, "error": str(exc)}
        return {
            "status": "ok",
            "base_url": self.endpoint.rsplit("/api/ai/chat", 1)[0],
            "model": self.model,
        }

    def analyze(
        self,
        packet: dict[str, Any],
        *,
        provider: str = "copilot",
        analysis_mode: str = "ask",
        tool_use: bool = False,
    ) -> dict[str, Any]:
        if self._copilot is not None:
            content = self._copilot(packet)
            content = _validate_research_payload(
                content,
                packet=packet,
                analysis_mode=analysis_mode,
            )
            return _with_provider_metadata(
                content,
                provider=self.provider_name,
                model=self.model,
                analysis_mode=analysis_mode,
                tool_use=tool_use,
            )

        token = os.getenv(self.token_env) or ""
        headers = {"Content-Type": "application/json; charset=utf-8"}
        if token:
            headers["x-ai-proxy-token"] = token
        body = {
            "model": self.model,
            "sensitivity": "internal",
            "messages": [
                {
                    "role": "system",
                    "content": _system_prompt(),
                },
                {
                    "role": "user",
                    "content": json.dumps(packet, ensure_ascii=False, separators=(",", ":")),
                },
            ],
        }
        envelope = _post_json(
            self._post, self.endpoint, json_body=body, headers=headers, timeout=self.timeout
        )
        result = envelope.get("result")
        if not isinstance(result, dict) or not isinstance(result.get("text"), str):
            raise ProviderError("Copilot response missing result.text")
        content = _parse_json_object(result["text"], provider_label="Copilot")
        content = _validate_research_payload(content, packet=packet, analysis_mode=analysis_mode)
        model = str(result.get("model") or self.model)
        return _with_provider_metadata(
            content,
            provider=self.provider_name,
            model=model,
            analysis_mode=analysis_mode,
            tool_use=tool_use,
        )


class MiniMaxProvider:
    def __init__(
        self,
        *,
        provider_name: str = "minimax",
        model: str | None = None,
        base_url: str | None = None,
        max_tokens: int | None = None,
        timeout: int | None = None,
        post: PostFn | None = None,
    ) -> None:
        self.provider_name = provider_name
        self.model = model or _model_for_provider(provider_name)
        self.base_url = base_url or os.getenv("MINIMAX_BASE_URL") or DEFAULT_MINIMAX_BASE_URL
        self.max_tokens = int(
            max_tokens or os.getenv("MINIMAX_MAX_TOKENS") or DEFAULT_MINIMAX_MAX_TOKENS
        )
        self.timeout = int(timeout or os.getenv("MINIMAX_TIMEOUT") or DEFAULT_TIMEOUT_SECONDS)
        self._post = post or requests.post

    def health(self) -> dict[str, Any]:
        api_key = _minimax_api_key()
        registered_scopes = [] if api_key else _registered_env_var_scopes("MINIMAX_API_KEY")
        key_configured = {
            "status": "ok" if api_key else "missing",
            "configured": bool(api_key),
            "current_process": bool(api_key),
            "registered_scopes": registered_scopes,
        }
        setup_hint = ""
        if not api_key and registered_scopes:
            setup_hint = "MINIMAX_API_KEY is registered but this server needs restart"
        elif not api_key:
            setup_hint = "Set MINIMAX_API_KEY and restart this server"
        return {
            "status": "ok" if api_key else "unavailable",
            "provider": self.provider_name,
            "model": self.model,
            "base_url": self.base_url,
            "key_configured": key_configured,
            "live_smoke": self._live_smoke_health(api_key),
            "api_key_configured": bool(api_key),
            "api_key_current_process": bool(api_key),
            "api_key_registered_scopes": registered_scopes,
            "setup_hint": setup_hint,
        }

    def _live_smoke_health(self, api_key: str) -> dict[str, Any]:
        if not api_key:
            return {"status": "skipped", "enabled": False, "reason": "api key is not configured"}
        if os.getenv("MINIMAX_HEALTH_LIVE_SMOKE") != "1":
            return {
                "status": "not_run",
                "enabled": False,
                "reason": "set MINIMAX_HEALTH_LIVE_SMOKE=1 to probe the live API",
            }
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        }
        body = {
            "model": self.model,
            "max_tokens": 8,
            "temperature": DEFAULT_MINIMAX_TEMPERATURE,
            "system": "Reply with ok.",
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": "ok"}],
                }
            ],
        }
        try:
            envelope = _post_json(
                self._post,
                _anthropic_messages_endpoint(self.base_url),
                json_body=body,
                headers=headers,
                timeout=min(self.timeout, 15),
            )
            _extract_anthropic_text(envelope)
        except Exception as exc:
            return {"status": "failed", "enabled": True, "error": _safe_text(str(exc))}
        return {"status": "ok", "enabled": True, "model": str(envelope.get("model") or self.model)}

    def analyze(
        self,
        packet: dict[str, Any],
        *,
        provider: str = "minimax",
        analysis_mode: str = "ask",
        tool_use: bool = False,
    ) -> dict[str, Any]:
        api_key = _minimax_api_key()
        if not api_key:
            raise RuntimeError("MINIMAX_API_KEY is not configured")

        body = _minimax_request_body(
            packet,
            model=self.model,
            max_tokens=self.max_tokens,
            analysis_mode=analysis_mode,
            tool_use=tool_use,
        )
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        }
        try:
            envelope = _post_json(
                self._post,
                _anthropic_messages_endpoint(self.base_url),
                json_body=body,
                headers=headers,
                timeout=self.timeout,
            )
            provider_warnings: list[str] = []
        except ProviderError as exc:
            retry = self._compact_retry(
                packet,
                headers=headers,
                analysis_mode=analysis_mode,
                tool_use=tool_use,
                first_error=exc,
            )
            envelope = retry["envelope"]
            provider_warnings = retry["warnings"]
        model = str(envelope.get("model") or self.model)
        try:
            content = _parse_and_validate_minimax_envelope(
                envelope,
                packet=packet,
                analysis_mode=analysis_mode,
            )
        except ProviderError as exc:
            return self._repair_or_fallback(
                packet,
                body=body,
                headers=headers,
                analysis_mode=analysis_mode,
                tool_use=tool_use,
                first_error=exc,
            )
        return _with_provider_metadata(
            content,
            provider=self.provider_name,
            model=model,
            analysis_mode=analysis_mode,
            tool_use=tool_use,
            provider_warnings=provider_warnings,
        )

    def _compact_retry(
        self,
        packet: dict[str, Any],
        *,
        headers: dict[str, str],
        analysis_mode: str,
        tool_use: bool,
        first_error: ProviderError,
    ) -> dict[str, Any]:
        compact_packet = _compact_retry_packet(packet)
        compact_body = _minimax_request_body(
            compact_packet,
            model=self.model,
            max_tokens=min(self.max_tokens, DEFAULT_MINIMAX_MAX_TOKENS),
            analysis_mode=analysis_mode,
            tool_use=tool_use,
        )
        envelope = _post_json(
            self._post,
            _anthropic_messages_endpoint(self.base_url),
            json_body=compact_body,
            headers=headers,
            timeout=self.timeout,
        )
        return {
            "envelope": envelope,
            "warnings": [f"{self.provider_name} compact retry: {first_error}"],
        }

    def _repair_or_fallback(
        self,
        packet: dict[str, Any],
        *,
        body: dict[str, Any],
        headers: dict[str, str],
        analysis_mode: str,
        tool_use: bool,
        first_error: ProviderError,
    ) -> dict[str, Any]:
        repair_warning = f"{self.provider_name} repair retry: {first_error}"
        repair_body = _minimax_repair_body(
            body,
            error=str(first_error),
            mode=_bundle_or_ask(packet, analysis_mode),
        )
        try:
            envelope = _post_json(
                self._post,
                _anthropic_messages_endpoint(self.base_url),
                json_body=repair_body,
                headers=headers,
                timeout=self.timeout,
            )
            content = _parse_and_validate_minimax_envelope(
                envelope,
                packet=packet,
                analysis_mode=analysis_mode,
            )
        except ProviderError as exc:
            fallback = FallbackProvider().analyze(
                packet,
                provider="fallback",
                analysis_mode=analysis_mode,
                tool_use=tool_use,
            )
            fallback["provider_warnings"] = [
                repair_warning,
                f"{self.provider_name} repair failed: {exc}",
            ]
            return fallback

        result = _with_provider_metadata(
            content,
            provider=self.provider_name,
            model=str(envelope.get("model") or self.model),
            analysis_mode=analysis_mode,
            tool_use=tool_use,
        )
        result["provider_warnings"] = [repair_warning]
        return result


class ProviderRouter:
    def __init__(
        self,
        *,
        minimax: LLMProvider | None = None,
        minimax_highspeed: LLMProvider | None = None,
        copilot: LLMProvider | None = None,
        fallback: LLMProvider | None = None,
        providers: dict[str, LLMProvider] | None = None,
    ) -> None:
        if providers is not None:
            self.providers = dict(providers)
            self.providers.setdefault("fallback", fallback or FallbackProvider())
            return
        self.providers: dict[str, LLMProvider] = {
            "minimax": minimax or MiniMaxProvider(),
            "minimax-highspeed": minimax_highspeed
            or MiniMaxProvider(provider_name="minimax-highspeed"),
            "copilot": copilot or CopilotProvider(),
            "fallback": fallback or FallbackProvider(),
        }

    def health(self) -> dict[str, Any]:
        health = {name: provider.health() for name, provider in self.providers.items()}
        health["active_provider"] = _active_provider(health)
        return health

    def analyze(
        self,
        packet: dict[str, Any],
        *,
        provider: str = "auto",
        analysis_mode: str = "ask",
        tool_use: bool = False,
    ) -> dict[str, Any]:
        normalized = _normalize_provider(provider)
        if normalized == "auto":
            return self._analyze_auto(packet, analysis_mode=analysis_mode, tool_use=tool_use)
        selected = self.providers.get(normalized)
        if selected is None:
            raise ValueError(f"Unsupported provider: {provider}")
        try:
            return selected.analyze(
                packet,
                provider=normalized,
                analysis_mode=analysis_mode,
                tool_use=tool_use,
            )
        except Exception as exc:
            if normalized == "minimax-highspeed" and _is_highspeed_plan_error(exc):
                fallback = self.providers.get("minimax")
                if fallback is not None:
                    payload = fallback.analyze(
                        packet,
                        provider="minimax",
                        analysis_mode=analysis_mode,
                        tool_use=tool_use,
                    )
                    payload_warnings = _string_list(payload.get("provider_warnings"))
                    payload["provider_warnings"] = [
                        (f"minimax-highspeed failed: {exc}; retried with minimax"),
                        *payload_warnings,
                    ]
                    return payload
            raise

    def _analyze_auto(
        self,
        packet: dict[str, Any],
        *,
        analysis_mode: str,
        tool_use: bool,
    ) -> dict[str, Any]:
        warnings: list[str] = []
        for name in ("minimax", "copilot", "fallback"):
            provider = self.providers.get(name)
            if provider is None:
                continue
            try:
                payload = provider.analyze(
                    packet,
                    provider=name,
                    analysis_mode=analysis_mode,
                    tool_use=tool_use,
                )
            except Exception as exc:
                warnings.append(f"{name} failed: {exc}")
                continue
            payload_warnings = _string_list(payload.get("provider_warnings"))
            payload["provider_warnings"] = [*warnings, *payload_warnings]
            return payload
        raise ProviderError("; ".join(warnings) or "no providers configured")


def _post_json(
    post: PostFn,
    url: str,
    *,
    json_body: dict[str, Any],
    headers: dict[str, str],
    timeout: int,
) -> dict[str, Any]:
    try:
        response = post(url, json=json_body, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        raise ProviderError(f"provider request failed: {exc}") from exc
    try:
        response.raise_for_status()
    except Exception as exc:
        detail = _safe_provider_error_detail(str(getattr(response, "text", "")))
        suffix = f": {detail}" if detail else ""
        raise ProviderError(f"provider request failed: {exc}{suffix}") from exc
    try:
        payload = response.json()
    except ValueError as exc:
        raise ProviderError("provider response was not JSON") from exc
    if not isinstance(payload, dict):
        raise ProviderError("provider response must be a JSON object")
    return payload


def _safe_provider_error_detail(text: str) -> str:
    if not text:
        return ""
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return text[:500]
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict) and isinstance(error.get("message"), str):
            return error["message"][:500]
        if isinstance(payload.get("message"), str):
            return str(payload["message"])[:500]
    return text[:500]


def _safe_text(text: str, *, limit: int = 500) -> str:
    sanitized = text
    for marker in ("sk-", "Bearer ", "x-api-key", "MINIMAX_API_KEY"):
        sanitized = sanitized.replace(marker, "***")
    return sanitized[:limit]


def _parse_json_object(text: str, *, provider_label: str) -> dict[str, Any]:
    stripped = text.strip()
    candidates = [
        match.group(1).strip()
        for match in re.finditer(r"```(?:json)?\s*(.*?)\s*```", stripped, flags=re.DOTALL | re.I)
    ]
    candidates.append(stripped)
    for candidate in candidates:
        parsed = _load_json_object(candidate)
        if parsed is not None:
            return parsed
    raise ProviderError(f"{provider_label} response was not valid JSON")


def _load_json_object(text: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict):
        return parsed

    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            parsed, _end = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def _parse_and_validate_minimax_envelope(
    envelope: dict[str, Any],
    *,
    packet: dict[str, Any],
    analysis_mode: str,
) -> dict[str, Any]:
    text = _extract_anthropic_text(envelope)
    content = _parse_json_object(text, provider_label="MiniMax")
    return _validate_research_payload(content, packet=packet, analysis_mode=analysis_mode)


def _validate_research_payload(
    payload: dict[str, Any],
    *,
    packet: dict[str, Any],
    analysis_mode: str,
) -> dict[str, Any]:
    try:
        return validate_research_result(payload, mode=_bundle_or_ask(packet, analysis_mode))
    except ValueError as exc:
        raise ProviderError(str(exc)) from exc


def _extract_anthropic_text(envelope: dict[str, Any]) -> str:
    content = envelope.get("content")
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        raise ProviderError("MiniMax response missing content")
    text_blocks: list[str] = []
    for block in content:
        if (
            isinstance(block, dict)
            and block.get("type") == "text"
            and isinstance(block.get("text"), str)
        ):
            text_blocks.append(block["text"])
    if not text_blocks:
        raise ProviderError("MiniMax response missing text content")
    return "\n".join(text_blocks)


def _fallback_answer(packet: dict[str, Any]) -> dict[str, Any]:
    sources = _sources(packet)
    return {
        "mode": "ask",
        "question": str(packet.get("prompt") or ""),
        "short_answer": "AI provider unavailable. Showing extracted evidence for manual review.",
        "findings": [
            {
                "text": "Candidate file is available for manual review.",
                "source_path": source["path"],
            }
            for source in sources[:5]
        ],
        "sources": sources,
        "gaps": ["Provider analysis is unavailable, so final judgment needs manual review."],
        "next_actions": ["Open the listed source paths and verify the original files."],
    }


def _fallback_bundle(packet: dict[str, Any]) -> dict[str, Any]:
    sources = _sources(packet)
    return {
        "mode": "find-bundle",
        "bundle_title": str(packet.get("prompt") or ""),
        "core_files": [{"path": source["path"], "role": "candidate"} for source in sources[:5]],
        "supporting_files": [
            {"path": source["path"], "role": "candidate"} for source in sources[5:]
        ],
        "duplicates_or_versions": [],
        "missing_or_gap_hints": [
            {
                "hint": (
                    "Provider analysis is unavailable, so missing-file judgment needs "
                    "manual review."
                )
            }
        ],
        "next_actions": ["Review core_files against the original document package."],
        "sources": sources,
    }


def _sources(packet: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for source in packet.get("sources") or []:
        if not isinstance(source, dict):
            continue
        path = str(source.get("source_path") or source.get("path") or "")
        if not path:
            continue
        result.append(
            {
                "path": path,
                "name": str(source.get("name") or Path(path).name),
                "extension": str(source.get("extension") or Path(path).suffix).lower(),
                "snippet": str(source.get("excerpt") or source.get("snippet") or "")[:500],
            }
        )
    return result


def _minimax_request_body(
    packet: dict[str, Any],
    *,
    model: str,
    max_tokens: int,
    analysis_mode: str,
    tool_use: bool,
) -> dict[str, Any]:
    mode = _bundle_or_ask(packet, analysis_mode)
    request_packet = {
        **packet,
        "analysis_mode": analysis_mode,
        "tool_use_requested": tool_use,
        "required_output_schema": _required_output_schema(mode, analysis_mode),
        "specialist_instruction": _specialist_instruction(analysis_mode),
    }
    return {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": float(os.getenv("MINIMAX_TEMPERATURE") or DEFAULT_MINIMAX_TEMPERATURE),
        "system": _system_prompt(),
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(
                            request_packet, ensure_ascii=False, separators=(",", ":")
                        ),
                    }
                ],
            }
        ],
    }


def _minimax_repair_body(body: dict[str, Any], *, error: str, mode: str) -> dict[str, Any]:
    repair_body = dict(body)
    messages = list(body.get("messages") or [])
    messages.append(
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "repair_instruction": (
                                "Use the document packet already provided above. Return one "
                                "valid JSON object only. Fix the previous response to satisfy "
                                "the required local research schema. Do not say documents are "
                                "missing when sources were provided above."
                            ),
                            "required_mode": mode,
                            "schema_error": error,
                        },
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                }
            ],
        }
    )
    repair_body["messages"] = messages
    return repair_body


def _compact_retry_packet(packet: dict[str, Any]) -> dict[str, Any]:
    compact = dict(packet)
    sources = []
    for source in packet.get("sources") or []:
        if not isinstance(source, dict):
            continue
        compact_source = dict(source)
        if "excerpt" in compact_source:
            compact_source["excerpt"] = str(compact_source.get("excerpt") or "")[
                :COMPACT_RETRY_EXCERPT_CHARS
            ]
        if "snippet" in compact_source:
            compact_source["snippet"] = str(compact_source.get("snippet") or "")[
                :COMPACT_RETRY_EXCERPT_CHARS
            ]
        sources.append(compact_source)
        if len(sources) >= COMPACT_RETRY_MAX_SOURCES:
            break
    compact["sources"] = sources
    compact["packet_variant"] = "compact_retry"
    return compact


def _with_provider_metadata(
    payload: dict[str, Any],
    *,
    provider: str,
    model: str,
    analysis_mode: str,
    tool_use: bool,
    provider_warnings: list[str] | None = None,
) -> dict[str, Any]:
    output = dict(payload)
    output["provider"] = provider
    output["model"] = model
    output["analysis_mode"] = analysis_mode
    output["tool_use"] = tool_use
    output["provider_warnings"] = [
        *(provider_warnings or []),
        *_string_list(output.get("provider_warnings")),
    ]
    return output


def _normalize_provider(provider: str) -> str:
    normalized = str(provider or "auto").strip().lower()
    if normalized not in SUPPORTED_PROVIDERS:
        raise ValueError(f"Unsupported provider: {provider}")
    return normalized


def _bundle_or_ask(packet: dict[str, Any], analysis_mode: str) -> str:
    if analysis_mode == "find-bundle" or packet.get("mode") == "find-bundle":
        return "find-bundle"
    return "ask"


def _active_provider(health: dict[str, Any]) -> str:
    for name in ("minimax", "copilot", "fallback"):
        status = health.get(name)
        if isinstance(status, dict) and status.get("status") == "ok":
            return name
    return "fallback"


def _is_highspeed_plan_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return "minimax-m2.7-highspeed" in message and (
        "not support model" in message or "2061" in message
    )


def _model_for_provider(provider_name: str) -> str:
    if provider_name == "minimax-highspeed":
        return os.getenv("MINIMAX_FAST_MODEL") or DEFAULT_MINIMAX_FAST_MODEL
    return os.getenv("MINIMAX_MODEL") or DEFAULT_MINIMAX_MODEL


def _minimax_api_key() -> str:
    return os.getenv("MINIMAX_API_KEY") or ""


def _registered_env_var_scopes(name: str) -> list[str]:
    if os.name != "nt":
        return []
    try:
        import winreg
    except ImportError:
        return []

    scopes: list[str] = []
    registry_locations = [
        (
            "user",
            winreg.HKEY_CURRENT_USER,
            "Environment",
        ),
        (
            "machine",
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
        ),
    ]
    for scope, root, path in registry_locations:
        try:
            with winreg.OpenKey(root, path) as key:
                winreg.QueryValueEx(key, name)
        except OSError:
            continue
        scopes.append(scope)
    return scopes


def _anthropic_messages_endpoint(base_url: str) -> str:
    return base_url.rstrip("/") + "/v1/messages"


def _system_prompt() -> str:
    return (
        "You are a local document research assistant. Answer only from the supplied file "
        "packets and cite source_path for factual claims. Return one JSON object only. "
        "Follow the required_output_schema in the user packet exactly. Never omit required "
        "top-level fields such as short_answer for ask mode or bundle_title for find-bundle "
        "mode. Do not include Markdown, code fences, raw thinking, or hidden reasoning. If "
        "sources are present, analyze their excerpts; do not claim that no documents were "
        "provided."
    )


def _required_output_schema(mode: str, analysis_mode: str) -> dict[str, Any]:
    if mode == "find-bundle":
        return {
            "mode": "find-bundle",
            "bundle_title": "short bundle name",
            "core_files": [
                {"path": "source_path", "role": "core|main|latest", "reason": "why core"}
            ],
            "supporting_files": [
                {"path": "source_path", "role": "supporting|reference", "reason": "why useful"}
            ],
            "duplicates_or_versions": [
                {"path": "source_path", "related_path": "source_path", "reason": "version relation"}
            ],
            "missing_or_gap_hints": [{"hint": "missing evidence or manual check needed"}],
            "next_actions": ["concrete next step"],
        }
    schema: dict[str, Any] = {
        "mode": "ask",
        "short_answer": "concise Korean answer grounded in sources",
        "findings": [
            {
                "text": "source-backed finding",
                "source_path": "source_path",
                "evidence": "short quote or paraphrase from excerpt",
            }
        ],
        "gaps": ["unknown or missing evidence"],
        "next_actions": ["concrete next step"],
    }
    if analysis_mode == "invoice-audit":
        schema["structured_data"] = {
            "invoice_number": "",
            "issue_date": "",
            "supplier": "",
            "buyer": "",
            "amount": "",
            "vat": "",
            "total": "",
            "currency": "",
            "source_path": "source_path",
        }
    elif analysis_mode == "extract-fields":
        schema["structured_data"] = {
            "fields": [{"name": "field name", "value": "field value", "source_path": "source_path"}]
        }
    elif analysis_mode == "execution-package-audit":
        schema["structured_data"] = {
            "core_files": [{"path": "source_path", "role": "required"}],
            "supporting_files": [{"path": "source_path", "role": "supporting"}],
            "missing_files": [{"name": "expected file", "reason": "why expected"}],
        }
    elif analysis_mode == "compare-documents":
        schema["structured_data"] = {
            "differences": [
                {
                    "topic": "changed item",
                    "left_source_path": "source_path",
                    "right_source_path": "source_path",
                    "summary": "difference",
                }
            ]
        }
    return schema


def _specialist_instruction(analysis_mode: str) -> str:
    instructions = {
        "invoice-audit": (
            "Extract invoice fields and identify missing or inconsistent invoice data. "
            "Include invoice_number, issue_date, supplier, buyer, amount, VAT, total, "
            "currency, and source evidence when present."
        ),
        "extract-fields": (
            "Extract explicit fields from the supplied excerpts only. Preserve source_path "
            "for every field and mark unknown values as empty strings rather than guessing."
        ),
        "execution-package-audit": (
            "Classify files into core, supporting, duplicate/version, and missing evidence "
            "groups. Focus on execution approval package completeness."
        ),
        "compare-documents": (
            "Compare selected documents. Report differences only when supported by cited "
            "source paths from the excerpts."
        ),
        "find-bundle": (
            "Build a source-backed document bundle. Prefer current, clean, non-cache files "
            "as core files and mark duplicates or older versions separately."
        ),
        "ask": "Answer the user question from supplied excerpts with source-backed findings.",
    }
    return instructions.get(analysis_mode, instructions["ask"])


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return []
