from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import Lock, Thread
from typing import Any
from uuid import uuid4

from scripts.local_research_reports import build_research_report

RunnerFn = Callable[["ResearchJobRequest", "ResearchJob"], dict[str, Any]]


@dataclass(frozen=True)
class ResearchJobRequest:
    mode: str
    prompt: str
    selected_candidates: list[dict[str, Any]] = field(default_factory=list)
    scope: str = "all"
    max_candidates: int = 10
    save: bool = True
    provider: str = "auto"
    analysis_mode: str = "ask"
    tool_use: bool = False


class ResearchJob:
    def __init__(self, request: ResearchJobRequest) -> None:
        self.job_id = f"jr_{uuid4().hex[:16]}"
        self.request = request
        self.created_at = _now()
        self.updated_at = self.created_at
        self.status = "queued"
        self.stage = "queued"
        self.progress = 0
        self.message = "Queued"
        self.events: list[dict[str, Any]] = []
        self.result: dict[str, Any] | None = None
        self.report: dict[str, Any] | None = None
        self.error = ""
        self._lock = Lock()
        self._record_event_locked()

    def update(
        self,
        *,
        status: str | None = None,
        stage: str | None = None,
        progress: int | None = None,
        message: str | None = None,
    ) -> None:
        with self._lock:
            if status is not None:
                self.status = status
            if stage is not None:
                self.stage = stage
            if progress is not None:
                self.progress = max(0, min(100, int(progress)))
            if message is not None:
                self.message = message
            self.updated_at = _now()
            self._record_event_locked()

    def cancel_requested(self) -> bool:
        with self._lock:
            return self.status == "cancel_requested"

    def mark_cancel_requested(self) -> None:
        with self._lock:
            if self.status in {"done", "failed", "cancelled"}:
                return
            self.status = "cancel_requested"
            self.message = "Cancel requested"
            self.updated_at = _now()
            self._record_event_locked()

    def mark_cancelled(self) -> None:
        with self._lock:
            self.status = "cancelled"
            self.stage = "cancelled"
            self.progress = 100
            self.message = "Cancelled"
            self.updated_at = _now()
            self._record_event_locked()

    def mark_done(self, result: dict[str, Any]) -> None:
        report = build_research_report(result)
        with self._lock:
            self.status = "done"
            self.stage = "done"
            self.progress = 100
            self.message = "Done"
            self.result = result
            self.report = report
            self.updated_at = _now()
            self._record_event_locked()

    def mark_failed(self, exc: Exception) -> None:
        with self._lock:
            self.status = "failed"
            self.stage = "failed"
            self.progress = 100
            self.message = "Failed"
            self.error = _safe_error(exc)
            self.updated_at = _now()
            self._record_event_locked()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "job_id": self.job_id,
                "status": self.status,
                "stage": self.stage,
                "progress": self.progress,
                "message": self.message,
                "events": list(self.events),
                "result": self.result,
                "report": self.report,
                "error": self.error,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
            }

    def _record_event_locked(self) -> None:
        self.events.append(
            {
                "status": self.status,
                "stage": self.stage,
                "progress": self.progress,
                "message": self.message,
                "time": self.updated_at,
            }
        )


class JobRegistry:
    def __init__(self) -> None:
        self._jobs: dict[str, ResearchJob] = {}
        self._lock = Lock()

    def create(self, request: ResearchJobRequest) -> ResearchJob:
        job = ResearchJob(request)
        with self._lock:
            self._jobs[job.job_id] = job
        return job

    def submit(
        self,
        request: ResearchJobRequest,
        *,
        runner: RunnerFn,
        run_async: bool = True,
    ) -> ResearchJob:
        job = self.create(request)
        if run_async:
            thread = Thread(
                target=self.run,
                args=(job.job_id,),
                kwargs={"runner": runner},
                daemon=True,
            )
            thread.start()
        else:
            self.run(job.job_id, runner=runner)
        return job

    def run(self, job_id: str, *, runner: RunnerFn) -> None:
        job = self._job(job_id)
        if job.cancel_requested():
            job.mark_cancelled()
            return
        job.update(status="running", stage="running", progress=1, message="Running")
        try:
            if job.cancel_requested():
                job.mark_cancelled()
                return
            result = runner(job.request, job)
            if job.cancel_requested() and job.stage != "calling_provider":
                job.mark_cancelled()
                return
            job.update(stage="rendering_report", progress=90, message="Rendering report")
            job.mark_done(result)
        except Exception as exc:
            if job.cancel_requested():
                job.mark_cancelled()
            else:
                job.mark_failed(exc)

    def cancel(self, job_id: str) -> dict[str, Any]:
        job = self._job(job_id)
        if job.status == "queued":
            job.mark_cancel_requested()
        elif job.status in {"running", "cancel_requested"}:
            job.mark_cancel_requested()
        return job.snapshot()

    def get(self, job_id: str) -> dict[str, Any]:
        return self._job(job_id).snapshot()

    def _job(self, job_id: str) -> ResearchJob:
        with self._lock:
            job = self._jobs.get(job_id)
        if job is None:
            raise KeyError(f"unknown job_id: {job_id}")
        return job


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _safe_error(exc: Exception) -> str:
    text = str(exc)
    for marker in ("sk-", "Bearer ", "x-api-key"):
        text = text.replace(marker, "***")
    return text[:500]
