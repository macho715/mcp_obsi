from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


class AskResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    mode: str = "ask"
    question: str = ""
    short_answer: str
    findings: list[dict[str, Any]] = Field(default_factory=list)
    sources: list[dict[str, Any]] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)

    @field_validator("findings", mode="before")
    @classmethod
    def _normalize_findings(cls, value: Any) -> list[dict[str, Any]]:
        return _dict_list(value, string_key="text")

    @field_validator("sources", mode="before")
    @classmethod
    def _normalize_sources(cls, value: Any) -> list[dict[str, Any]]:
        return _dict_list(value, string_key="path")

    @field_validator("gaps", "next_actions", mode="before")
    @classmethod
    def _normalize_string_lists(cls, value: Any) -> list[str]:
        return _string_list(value)


class FindBundleResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    mode: str = "find-bundle"
    bundle_title: str
    core_files: list[dict[str, Any]] = Field(default_factory=list)
    supporting_files: list[dict[str, Any]] = Field(default_factory=list)
    duplicates_or_versions: list[dict[str, Any]] = Field(default_factory=list)
    missing_or_gap_hints: list[dict[str, Any]] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    sources: list[dict[str, Any]] = Field(default_factory=list)

    @field_validator("core_files", "supporting_files", mode="before")
    @classmethod
    def _normalize_file_refs(cls, value: Any) -> list[dict[str, Any]]:
        return _file_ref_list(value)

    @field_validator("duplicates_or_versions", mode="before")
    @classmethod
    def _normalize_duplicates(cls, value: Any) -> list[dict[str, Any]]:
        return _dict_list(value, string_key="path")

    @field_validator("missing_or_gap_hints", mode="before")
    @classmethod
    def _normalize_gap_hints(cls, value: Any) -> list[dict[str, Any]]:
        return _dict_list(value, string_key="hint")

    @field_validator("sources", mode="before")
    @classmethod
    def _normalize_sources(cls, value: Any) -> list[dict[str, Any]]:
        return _dict_list(value, string_key="path")

    @field_validator("next_actions", mode="before")
    @classmethod
    def _normalize_next_actions(cls, value: Any) -> list[str]:
        return _string_list(value)


def validate_research_result(payload: dict[str, Any], *, mode: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("research result must be a JSON object")

    normalized_mode = "find-bundle" if mode == "find-bundle" else "ask"
    model_type = FindBundleResult if normalized_mode == "find-bundle" else AskResult
    required_field = "bundle_title" if normalized_mode == "find-bundle" else "short_answer"
    if required_field not in payload:
        raise ValueError(f"{required_field} field required")

    try:
        result = model_type.model_validate({**payload, "mode": normalized_mode})
    except ValidationError as exc:
        raise ValueError(_format_validation_error(exc)) from exc
    return result.model_dump(mode="python")


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)]


def _dict_list(value: Any, *, string_key: str) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, str):
        return [{string_key: value}]
    if isinstance(value, dict):
        return [dict(value)]
    if not isinstance(value, list):
        return [{string_key: str(value)}]

    normalized: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, str):
            normalized.append({string_key: item})
        elif isinstance(item, dict):
            normalized.append(dict(item))
        elif item is not None:
            normalized.append({string_key: str(item)})
    return normalized


def _file_ref_list(value: Any) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for item in _dict_list(value, string_key="path"):
        output = dict(item)
        if "path" not in output and "source_path" in output:
            output["path"] = output["source_path"]
        normalized.append(output)
    return normalized


def _format_validation_error(exc: ValidationError) -> str:
    first = exc.errors()[0]
    field = ".".join(str(part) for part in first.get("loc", ()) if part != "__root__")
    message = str(first.get("msg") or "invalid")
    if message.lower() == "field required" and field:
        return f"{field} field required"
    return f"{field}: {message}" if field else message
