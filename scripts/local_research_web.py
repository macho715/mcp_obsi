from __future__ import annotations

import argparse
import inspect
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel, Field, field_validator

from scripts.local_research_jobs import (
    JobRegistry,
    ResearchJob,
    ResearchJobRequest,
)
from scripts.local_research_service import ResearchService

LOOPBACK_CLIENTS = {"127.0.0.1", "localhost", "::1", "testclient"}
SUPPORTED_PROVIDERS = {"auto", "minimax", "minimax-highspeed", "copilot", "fallback"}
SUPPORTED_ANALYSIS_MODES = {
    "ask",
    "find-bundle",
    "extract-fields",
    "invoice-audit",
    "execution-package-audit",
    "compare-documents",
}


class ProviderOptions(BaseModel):
    provider: str = "auto"
    analysis_mode: str = "ask"
    tool_use: bool = False

    @field_validator("provider")
    @classmethod
    def provider_must_be_supported(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in SUPPORTED_PROVIDERS:
            raise ValueError(
                "provider must be one of auto, minimax, minimax-highspeed, copilot, fallback"
            )
        return normalized

    @field_validator("analysis_mode")
    @classmethod
    def analysis_mode_must_be_supported(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in SUPPORTED_ANALYSIS_MODES:
            raise ValueError("analysis_mode is not supported")
        return normalized


class AskRequest(ProviderOptions):
    question: str = Field(min_length=1)
    scope: str = "all"
    max_candidates: int = Field(default=10, ge=1, le=50)
    save: bool = True

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("question must not be blank")
        return stripped


class FindBundleRequest(ProviderOptions):
    topic: str = Field(min_length=1)
    scope: str = "all"
    max_candidates: int = Field(default=20, ge=1, le=100)
    save: bool = True
    analysis_mode: str = "find-bundle"

    @field_validator("topic")
    @classmethod
    def topic_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("topic must not be blank")
        return stripped


class PreviewCandidatesRequest(BaseModel):
    prompt: str = Field(min_length=1)
    mode: str = Field(default="ask")
    scope: str = "all"
    max_candidates: int = Field(default=10, ge=1, le=100)

    @field_validator("prompt")
    @classmethod
    def prompt_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("prompt must not be blank")
        return stripped

    @field_validator("mode")
    @classmethod
    def mode_must_be_supported(cls, value: str) -> str:
        if value not in {"ask", "find-bundle"}:
            raise ValueError("mode must be ask or find-bundle")
        return value


class AskSelectedRequest(ProviderOptions):
    question: str = Field(min_length=1)
    selected_candidates: list[dict[str, Any]] = Field(min_length=1)
    scope: str = "all"
    save: bool = True

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("question must not be blank")
        return stripped


class FindBundleSelectedRequest(ProviderOptions):
    topic: str = Field(min_length=1)
    selected_candidates: list[dict[str, Any]] = Field(min_length=1)
    scope: str = "all"
    save: bool = True
    analysis_mode: str = "find-bundle"

    @field_validator("topic")
    @classmethod
    def topic_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("topic must not be blank")
        return stripped


class ResearchJobApiRequest(ProviderOptions):
    mode: str = Field(default="ask")
    prompt: str = Field(min_length=1)
    selected_candidates: list[dict[str, Any]] = Field(default_factory=list)
    scope: str = "all"
    max_candidates: int = Field(default=10, ge=1, le=100)
    save: bool = True

    @field_validator("mode")
    @classmethod
    def mode_must_be_supported(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"ask", "find-bundle"}:
            raise ValueError("mode must be ask or find-bundle")
        return normalized

    @field_validator("prompt")
    @classmethod
    def prompt_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("prompt must not be blank")
        return stripped


def create_app(
    service: ResearchService | Any | None = None,
    *,
    job_registry: JobRegistry | None = None,
    run_jobs_async: bool = True,
) -> FastAPI:
    research_service = service or ResearchService()
    jobs = job_registry or JobRegistry()
    app = FastAPI(title="local-research-assistant")

    @app.middleware("http")
    async def enforce_loopback_client(request: Request, call_next):
        client_host = request.client.host if request.client else ""
        if client_host not in LOOPBACK_CLIENTS:
            return PlainTextResponse("Local Research Assistant is loopback-only", status_code=403)
        return await call_next(request)

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return _html()

    @app.get("/api/research/health")
    def health() -> dict[str, Any]:
        payload = dict(research_service.health())
        payload["dashboard_status"] = _dashboard_health_status(payload)
        return payload

    @app.post("/api/research/ask")
    def ask(payload: AskRequest) -> dict[str, Any]:
        return research_service.ask_research(
            payload.question,
            scope=payload.scope,
            max_candidates=payload.max_candidates,
            save=payload.save,
            provider=payload.provider,
            analysis_mode=payload.analysis_mode,
            tool_use=payload.tool_use,
        )

    @app.post("/api/research/find-bundle")
    def find_bundle(payload: FindBundleRequest) -> dict[str, Any]:
        return research_service.find_bundle(
            payload.topic,
            scope=payload.scope,
            max_candidates=payload.max_candidates,
            save=payload.save,
            provider=payload.provider,
            analysis_mode=payload.analysis_mode,
            tool_use=payload.tool_use,
        )

    @app.post("/api/research/candidates")
    def preview_candidates(payload: PreviewCandidatesRequest) -> dict[str, Any]:
        return research_service.preview_candidates(
            payload.prompt,
            mode=payload.mode,
            scope=payload.scope,
            max_candidates=payload.max_candidates,
        )

    @app.post("/api/research/ask-selected")
    def ask_selected(payload: AskSelectedRequest) -> dict[str, Any]:
        return research_service.ask_selected(
            payload.question,
            selected_candidates=payload.selected_candidates,
            scope=payload.scope,
            save=payload.save,
            provider=payload.provider,
            analysis_mode=payload.analysis_mode,
            tool_use=payload.tool_use,
        )

    @app.post("/api/research/find-bundle-selected")
    def find_bundle_selected(payload: FindBundleSelectedRequest) -> dict[str, Any]:
        return research_service.find_bundle_selected(
            payload.topic,
            selected_candidates=payload.selected_candidates,
            scope=payload.scope,
            save=payload.save,
            provider=payload.provider,
            analysis_mode=payload.analysis_mode,
            tool_use=payload.tool_use,
        )

    @app.post("/api/research/jobs")
    def create_research_job(payload: ResearchJobApiRequest) -> dict[str, Any]:
        request = ResearchJobRequest(
            mode=payload.mode,
            prompt=payload.prompt,
            selected_candidates=payload.selected_candidates,
            scope=payload.scope,
            max_candidates=payload.max_candidates,
            save=payload.save,
            provider=payload.provider,
            analysis_mode=_job_analysis_mode(payload.mode, payload.analysis_mode),
            tool_use=payload.tool_use,
        )
        job = jobs.submit(
            request,
            runner=lambda job_request, job_state: _run_research_job(
                research_service, job_request, job_state
            ),
            run_async=run_jobs_async,
        )
        return job.snapshot()

    @app.get("/api/research/jobs/{job_id}")
    def get_research_job(job_id: str) -> dict[str, Any]:
        try:
            return jobs.get(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="job not found") from exc

    @app.post("/api/research/jobs/{job_id}/cancel")
    def cancel_research_job(job_id: str) -> dict[str, Any]:
        try:
            return jobs.cancel(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="job not found") from exc

    return app


def _job_analysis_mode(mode: str, analysis_mode: str) -> str:
    if analysis_mode == "ask" and mode == "find-bundle":
        return "find-bundle"
    return analysis_mode


def _run_research_job(
    research_service: ResearchService | Any,
    request: ResearchJobRequest,
    job: ResearchJob,
) -> dict[str, Any]:
    if job.cancel_requested():
        raise RuntimeError("cancelled before research execution")
    job.update(
        stage="extracting" if request.selected_candidates else "searching",
        progress=10,
        message="Preparing evidence",
    )
    if job.cancel_requested():
        raise RuntimeError("cancelled before provider call")
    job.update(stage="calling_provider", progress=45, message="Calling provider")
    if request.mode == "ask":
        if request.selected_candidates:
            return _call_service_method(
                research_service.ask_selected,
                job,
                request.prompt,
                selected_candidates=request.selected_candidates,
                scope=request.scope,
                save=request.save,
                provider=request.provider,
                analysis_mode=request.analysis_mode,
                tool_use=request.tool_use,
            )
        return _call_service_method(
            research_service.ask_research,
            job,
            request.prompt,
            scope=request.scope,
            max_candidates=request.max_candidates,
            save=request.save,
            provider=request.provider,
            analysis_mode=request.analysis_mode,
            tool_use=request.tool_use,
        )
    if request.selected_candidates:
        return _call_service_method(
            research_service.find_bundle_selected,
            job,
            request.prompt,
            selected_candidates=request.selected_candidates,
            scope=request.scope,
            save=request.save,
            provider=request.provider,
            analysis_mode=request.analysis_mode,
            tool_use=request.tool_use,
        )
    return _call_service_method(
        research_service.find_bundle,
        job,
        request.prompt,
        scope=request.scope,
        max_candidates=request.max_candidates,
        save=request.save,
        provider=request.provider,
        analysis_mode=request.analysis_mode,
        tool_use=request.tool_use,
    )


def _call_service_method(
    method: Any, job: ResearchJob, *args: Any, **kwargs: Any
) -> dict[str, Any]:
    signature = inspect.signature(method)
    if "progress" in signature.parameters:
        kwargs["progress"] = lambda stage, percent, message: job.update(
            stage=stage,
            progress=percent,
            message=message,
        )
    if "is_cancelled" in signature.parameters:
        kwargs["is_cancelled"] = job.cancel_requested
    return method(*args, **kwargs)


def _dashboard_health_status(data: dict[str, Any]) -> str:
    parts = [
        f"Route: {_route_status(data)}",
        f"Active: {data.get('active_provider') or 'fallback'}",
        f"Everything: {_dependency_status(data, 'everything')}",
        f"MiniMax: {_dependency_status(data, 'minimax')}",
        f"Copilot: {_dependency_status(data, 'copilot')}",
    ]
    return " | ".join(parts)


def _route_status(data: dict[str, Any]) -> str:
    route_status = data.get("route_status")
    if route_status:
        return str(route_status)
    route_ready = data.get("route_ready")
    if isinstance(route_ready, bool):
        return "ready" if route_ready else "blocked"
    return str(data.get("status") or "unknown")


def _dependency_status(data: dict[str, Any], key: str) -> str:
    dependency = data.get(key)
    if isinstance(dependency, dict):
        if key == "minimax":
            status = str(dependency.get("status") or "unknown")
            if status == "ok":
                key_configured = dependency.get("key_configured")
                live_smoke = dependency.get("live_smoke")
                key_label = "key missing"
                live_label = "live not run"
                if isinstance(key_configured, dict):
                    key_label = "key ok" if key_configured.get("status") == "ok" else "key missing"
                elif dependency.get("api_key_configured"):
                    key_label = "key ok"
                if isinstance(live_smoke, dict):
                    live_status = live_smoke.get("status")
                    if live_status == "ok":
                        live_label = "live ok"
                    elif live_status == "failed":
                        live_label = "live failed"
                return f"ok ({key_label}, {live_label})"
            if status == "unavailable":
                current_process = dependency.get("api_key_current_process")
                registered_scopes = dependency.get("api_key_registered_scopes")
                if current_process is False and registered_scopes:
                    return "unavailable (restart needed)"
                if current_process is False and registered_scopes == []:
                    return "unavailable (set MINIMAX_API_KEY)"
        return str(dependency.get("status") or "unknown")
    return "unknown"


def _html() -> str:
    return """<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Local Research Assistant</title>
  <style>
    :root { color-scheme: light; font-family: Arial, sans-serif; }
    body { margin: 0; background: #f6f8fb; color: #17202a; }
    main { max-width: 1120px; margin: 0 auto; padding: 24px; }
    h1 { margin: 0 0 16px; font-size: 28px; }
    .bar, .result {
      background: white; border: 1px solid #d8dee8; border-radius: 8px; padding: 16px;
    }
    .grid { display: grid; grid-template-columns: 160px 1fr 160px; gap: 10px; }
    textarea { min-height: 96px; resize: vertical; }
    textarea, select, input, button {
      border: 1px solid #b8c2d2; border-radius: 6px; padding: 10px; font-size: 15px;
    }
    button { background: #1f6feb; color: white; border-color: #1f6feb; cursor: pointer; }
    button:disabled { background: #8aa8d8; cursor: wait; }
    .status { margin: 12px 0; font-size: 14px; }
    .ai-status { margin: 8px 0 12px; font-weight: 700; }
    .ai-status.fallback { color: #9a3412; }
    .ai-status.ai { color: #166534; }
    .job-controls { display: flex; gap: 10px; align-items: center; }
    .report-section { border-top: 1px solid #e5e9f0; margin-top: 12px; padding-top: 12px; }
    .report-section h3 { margin: 0 0 8px; font-size: 17px; }
    .debug-json { margin-top: 12px; }
    .result { margin-top: 16px; white-space: pre-wrap; overflow-wrap: anywhere; }
    table { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 14px; }
    th, td {
      border-bottom: 1px solid #e5e9f0; text-align: left; padding: 8px; vertical-align: top;
    }
    @media (max-width: 760px) { .grid { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
<main>
  <h1>Local Research Assistant</h1>
  <section class="bar">
    <div class="grid">
      <select id="mode">
        <option value="ask">Ask</option>
        <option value="find-bundle">Find Bundle</option>
      </select>
      <select id="provider">
        <option value="auto">Auto</option>
        <option value="minimax">MiniMax M2.7</option>
        <option value="minimax-highspeed">MiniMax M2.7 Highspeed (plan required)</option>
        <option value="copilot">Copilot standalone</option>
        <option value="fallback">Fallback only</option>
      </select>
      <select id="analysis-mode">
        <option value="ask">Ask</option>
        <option value="find-bundle">Find Bundle</option>
        <option value="extract-fields">Extract Fields</option>
        <option value="invoice-audit">Invoice Audit</option>
        <option value="execution-package-audit">Execution Package Audit</option>
        <option value="compare-documents">Compare Documents</option>
      </select>
      <label><input type="checkbox" id="tool-use"> Use tool loop</label>
      <textarea
        id="prompt"
        placeholder="내 PC 문서에 질문하거나 파일 묶음 주제를 입력하세요."
      ></textarea>
      <button id="preview">Preview Candidates</button>
      <button id="run">Run direct</button>
      <button id="run-selected">Analyze Selected</button>
      <div class="job-controls">
        <button id="start-job">Start job</button>
        <button id="cancel-job" disabled>Cancel job</button>
      </div>
    </div>
    <div class="status">
      Start job uses checked candidates only when candidates are previewed, creating a
      selected-only packet for provider analysis.
    </div>
    <div class="status" id="health">Checking route health...</div>
  </section>
  <section class="result" id="candidates">Candidate review is empty.</section>
  <section class="result" id="result">Ready.</section>
</main>
<script>
const health = document.getElementById('health');
const candidates = document.getElementById('candidates');
const result = document.getElementById('result');
const preview = document.getElementById('preview');
const run = document.getElementById('run');
const runSelected = document.getElementById('run-selected');
const startJobButton = document.getElementById('start-job');
const cancelJobButton = document.getElementById('cancel-job');
let currentCandidateList = [];
let activeJobId = '';
let pollTimer = null;

async function checkHealth() {
  try {
    const res = await fetch('/api/research/health');
    const data = await res.json();
    health.textContent = data.dashboard_status || dashboardStatusText(data);
  } catch (error) {
    health.textContent = `Health check failed: ${error}`;
  }
}

function dashboardStatusText(data) {
  return [
    `Route: ${routeStatus(data)}`,
    `Active: ${data.active_provider || 'fallback'}`,
    `Everything: ${dependencyStatus(data, 'everything')}`,
    `MiniMax: ${dependencyStatus(data, 'minimax')}`,
    `Copilot: ${dependencyStatus(data, 'copilot')}`,
  ].join(' | ');
}

function routeStatus(data) {
  if (data.route_status) return data.route_status;
  if (typeof data.route_ready === 'boolean') return data.route_ready ? 'ready' : 'blocked';
  return data.status || 'unknown';
}

function dependencyStatus(data, key) {
  const dependency = data[key] || {};
  if (key === 'minimax' && dependency.status === 'ok') {
    const keyStatus = dependency.key_configured || {};
    const liveSmoke = dependency.live_smoke || {};
    const keyLabel = keyStatus.status === 'ok' || dependency.api_key_configured
      ? 'key ok'
      : 'key missing';
    const liveLabel = liveSmoke.status === 'ok'
      ? 'live ok'
      : liveSmoke.status === 'failed'
        ? 'live failed'
        : 'live not run';
    return `ok (${keyLabel}, ${liveLabel})`;
  }
  if (key === 'minimax' && dependency.status === 'unavailable') {
    if (dependency.api_key_current_process === false &&
        Array.isArray(dependency.api_key_registered_scopes) &&
        dependency.api_key_registered_scopes.length > 0) {
      return 'unavailable (restart needed)';
    }
    if (dependency.api_key_current_process === false &&
        Array.isArray(dependency.api_key_registered_scopes) &&
        dependency.api_key_registered_scopes.length === 0) {
      return 'unavailable (set MINIMAX_API_KEY)';
    }
  }
  return dependency.status || 'unknown';
}

function renderSources(sources) {
  if (!sources || sources.length === 0) return '';
  const rows = sources.map(source =>
    `<tr><td>${escapeHtml(source.name || '')}</td>` +
    `<td>${escapeHtml(source.path || '')}</td>` +
    `<td>${escapeHtml(source.modified_at || '')}</td></tr>`
  ).join('');
  return (
    '<table><thead><tr><th>Name</th><th>Path</th><th>Modified</th></tr></thead>' +
    `<tbody>${rows}</tbody></table>`
  );
}

function renderAiStatus(data) {
  const provider = data.provider || 'unknown';
  const model = data.model || '';
  const status = data.ai_applied === false || data.provider_status === 'fallback'
    ? 'fallback'
    : 'ai';
  const label = status === 'ai'
    ? `AI applied via ${provider}${model ? ' / ' + model : ''}`
    : `AI not applied; showing deterministic evidence only via ${provider}`;
  return `<div class="ai-status ${status}">${escapeHtml(label)}</div>`;
}

function renderResult(data, fallbackTitle) {
  return (
    `<h2>${escapeHtml(data.short_answer || data.bundle_title || fallbackTitle)}</h2>` +
    renderAiStatus(data) +
    renderDebugJson(data) +
    renderSources(data.sources)
  );
}

function renderReport(report) {
  if (!report || !Array.isArray(report.sections)) return '';
  const sections = report.sections.map(section => {
    const items = (section.items || []).map(item => {
      const value = typeof item === 'string' ? item : JSON.stringify(item, null, 2);
      return `<li>${escapeHtml(value)}</li>`;
    }).join('');
    return (
      `<section class="report-section"><h3>${escapeHtml(section.title || '')}</h3>` +
      `<ul>${items}</ul></section>`
    );
  }).join('');
  return (
    `<h2>${escapeHtml(report.title || 'Research Report')}</h2>` +
    `<div class="ai-status">${escapeHtml(report.ai_status || '')}</div>` +
    sections
  );
}

function renderDebugJson(data) {
  return (
    '<details class="debug-json"><summary>Debug JSON</summary>' +
    `<pre>${escapeHtml(JSON.stringify(data, null, 2))}</pre></details>`
  );
}

function toolLoopNotice(toolUse) {
  return toolUse
    ? '<p>Tool loop is not active in U1; the checkbox records intent only ' +
      'and no local tools are executed.</p>'
    : '';
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function renderCandidates(items) {
  currentCandidateList = items || [];
  if (!items || items.length === 0) {
    candidates.innerHTML = '<h2>Candidate review</h2><p>No candidates yet.</p>';
    return;
  }
  const rows = items.map((item, index) => {
    const checked = item.selected_by_default !== false ? 'checked' : '';
    return (
      '<tr>' +
      `<td><input type="checkbox" class="candidate-check" data-index="${index}" ${checked}></td>` +
      `<td>${escapeHtml(item.name || '')}</td>` +
      `<td>${escapeHtml(item.path || '')}</td>` +
      `<td>${escapeHtml(item.extension || '')}</td>` +
      `<td>${escapeHtml(item.modified_at || '')}</td>` +
      `<td>${escapeHtml(item.score || '')}</td>` +
      `<td>${escapeHtml(item.rank_reason || item.reason || '')}</td>` +
      `<td>${escapeHtml(item.status || '')}</td>` +
      '</tr>'
    );
  }).join('');
  candidates.innerHTML = (
    '<h2>Candidate review</h2>' +
    '<table><thead><tr><th>Use</th><th>Name</th><th>Path</th>' +
    '<th>Extension</th><th>Modified</th><th>Score</th>' +
    '<th>Reason</th><th>Status</th></tr></thead>' +
    `<tbody>${rows}</tbody></table>`
  );
}

function getPromptAndMode() {
  return {
    mode: document.getElementById('mode').value,
    provider: document.getElementById('provider').value,
    analysisMode: document.getElementById('analysis-mode').value,
    toolUse: document.getElementById('tool-use').checked,
    prompt: document.getElementById('prompt').value.trim(),
  };
}

function getSelectedCandidates() {
  const rows = Array.from(candidates.querySelectorAll('.candidate-check'));
  return rows
    .filter(box => box.checked)
    .map(box => currentCandidateList[Number(box.dataset.index)])
    .filter(item => item);
}

async function previewCandidates() {
  const {mode, prompt} = getPromptAndMode();
  if (!prompt) {
    result.textContent = '질문 또는 주제를 입력하세요.';
    return;
  }
  preview.disabled = true;
  candidates.textContent = 'Previewing candidates...';
  try {
    const res = await fetch('/api/research/candidates', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({prompt, mode, scope: 'all', max_candidates: 10})
    });
    const data = await res.json();
    renderCandidates(data.candidates || []);
    result.innerHTML = `<h2>${escapeHtml(data.preview_title || 'Candidate preview')}</h2>` +
      `<pre>${escapeHtml(JSON.stringify(data, null, 2))}</pre>`;
  } catch (error) {
    candidates.textContent = `Preview failed: ${error}`;
  } finally {
    preview.disabled = false;
  }
}

async function execute() {
  const {mode, prompt, provider, analysisMode, toolUse} = getPromptAndMode();
  if (!prompt) {
    result.textContent = '질문 또는 주제를 입력하세요.';
    return;
  }
  run.disabled = true;
  result.textContent = 'Running...';
  const url = mode === 'ask' ? '/api/research/ask' : '/api/research/find-bundle';
  const common = {provider, analysis_mode: analysisMode, tool_use: toolUse};
  const body = mode === 'ask' ? {question: prompt, ...common} : {topic: prompt, ...common};
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    });
    const data = await res.json();
    result.innerHTML = renderResult(data, 'Result');
  } catch (error) {
    result.textContent = `Request failed: ${error}`;
  } finally {
    run.disabled = false;
  }
}

async function executeSelected() {
  const {mode, prompt, provider, analysisMode, toolUse} = getPromptAndMode();
  const selectedCandidates = getSelectedCandidates();
  if (!prompt) {
    result.textContent = '질문 또는 주제를 입력하세요.';
    return;
  }
  if (selectedCandidates.length === 0) {
    result.textContent = '선택한 후보를 하나 이상 고르세요.';
    return;
  }
  runSelected.disabled = true;
  result.textContent = 'Running selected candidates...';
  const url = mode === 'ask' ? '/api/research/ask-selected' : '/api/research/find-bundle-selected';
  const body = mode === 'ask'
    ? {
        question: prompt,
        selected_candidates: selectedCandidates,
        scope: 'all',
        save: true,
        provider,
        analysis_mode: analysisMode,
        tool_use: toolUse,
      }
    : {
        topic: prompt,
        selected_candidates: selectedCandidates,
        scope: 'all',
        save: true,
        provider,
        analysis_mode: analysisMode,
        tool_use: toolUse,
      };
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    });
    const data = await res.json();
    result.innerHTML = renderResult(data, 'Selected result');
  } catch (error) {
    result.textContent = `Selected request failed: ${error}`;
  } finally {
    runSelected.disabled = false;
  }
}

function renderJobStatus(job) {
  const report = job.report ? renderReport(job.report) : '';
  const raw = job.result ? renderDebugJson(job.result) : '';
  const error = job.error ? `<p>Error: ${escapeHtml(job.error)}</p>` : '';
  return (
    `<h2>Job ${escapeHtml(job.job_id || '')}</h2>` +
    `<p>Status: ${escapeHtml(job.status || '')} | Stage: ${escapeHtml(job.stage || '')} | ` +
    `Progress: ${escapeHtml(job.progress || 0)}%</p>` +
    `<p>${escapeHtml(job.message || '')}</p>` +
    report +
    error +
    raw
  );
}

async function startJob() {
  const {mode, prompt, provider, analysisMode, toolUse} = getPromptAndMode();
  if (!prompt) {
    result.textContent = '질문 또는 주제를 입력하세요.';
    return;
  }
  startJobButton.disabled = true;
  cancelJobButton.disabled = false;
  result.innerHTML = toolLoopNotice(toolUse) + '<p>Starting job...</p>';
  const body = {
    mode,
    prompt,
    selected_candidates: getSelectedCandidates(),
    scope: 'all',
    max_candidates: 10,
    save: true,
    provider,
    analysis_mode: analysisMode,
    tool_use: toolUse,
  };
  try {
    const res = await fetch('/api/research/jobs', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    });
    const job = await res.json();
    activeJobId = job.job_id;
    result.innerHTML = toolLoopNotice(toolUse) + renderJobStatus(job);
    pollJob();
  } catch (error) {
    result.textContent = `Job start failed: ${error}`;
    startJobButton.disabled = false;
    cancelJobButton.disabled = true;
  }
}

async function pollJob() {
  if (!activeJobId) return;
  try {
    const res = await fetch(`/api/research/jobs/${encodeURIComponent(activeJobId)}`);
    const job = await res.json();
    result.innerHTML = renderJobStatus(job);
    if (['done', 'failed', 'cancelled'].includes(job.status)) {
      startJobButton.disabled = false;
      cancelJobButton.disabled = true;
      activeJobId = '';
      return;
    }
    pollTimer = setTimeout(pollJob, 1000);
  } catch (error) {
    result.textContent = `Job poll failed: ${error}`;
    startJobButton.disabled = false;
    cancelJobButton.disabled = true;
  }
}

async function cancelJob() {
  if (!activeJobId) return;
  if (pollTimer) clearTimeout(pollTimer);
  try {
    const res = await fetch(`/api/research/jobs/${encodeURIComponent(activeJobId)}/cancel`, {
      method: 'POST'
    });
    const job = await res.json();
    result.innerHTML = renderJobStatus(job);
  } catch (error) {
    result.textContent = `Job cancel failed: ${error}`;
  }
}

preview.addEventListener('click', previewCandidates);
run.addEventListener('click', execute);
runSelected.addEventListener('click', executeSelected);
startJobButton.addEventListener('click', startJob);
cancelJobButton.addEventListener('click', cancelJob);
checkHealth();
</script>
</body>
</html>"""


app = create_app()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Local Research Assistant web UI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8090)
    args = parser.parse_args()
    if args.host not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit("Refusing to bind Local Research Assistant to a non-loopback host")

    import uvicorn

    uvicorn.run("scripts.local_research_web:app", host=args.host, port=args.port, reload=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
