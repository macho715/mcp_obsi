import time

from scripts.local_research_jobs import JobRegistry, ResearchJobRequest


def test_job_registry_runs_successful_job_and_builds_report():
    registry = JobRegistry()

    def runner(request, job):
        job.update(stage="calling_provider", progress=65, message="Calling provider")
        return {
            "mode": "ask",
            "question": request.prompt,
            "provider": "minimax",
            "model": "MiniMax-M2.7",
            "ai_applied": True,
            "short_answer": "done",
            "findings": [],
            "gaps": [],
            "next_actions": [],
            "sources": [],
        }

    job = registry.submit(
        ResearchJobRequest(mode="ask", prompt="question", save=False),
        runner=runner,
        run_async=False,
    )

    snapshot = registry.get(job.job_id)
    assert snapshot["status"] == "done"
    assert snapshot["stage"] == "done"
    assert snapshot["progress"] == 100
    assert snapshot["result"]["short_answer"] == "done"
    assert snapshot["report"]["sections"][0]["title"] == "Answer"


def test_job_registry_marks_failure_with_safe_error():
    registry = JobRegistry()

    def runner(request, job):
        raise RuntimeError("provider exploded")

    job = registry.submit(
        ResearchJobRequest(mode="ask", prompt="question"),
        runner=runner,
        run_async=False,
    )

    snapshot = registry.get(job.job_id)
    assert snapshot["status"] == "failed"
    assert snapshot["stage"] == "failed"
    assert snapshot["progress"] == 100
    assert "provider exploded" in snapshot["error"]


def test_job_registry_cancel_before_run_prevents_provider_call():
    registry = JobRegistry()
    calls = []

    def runner(request, job):
        calls.append("called")
        return {"mode": "ask", "short_answer": "should not run"}

    job = registry.create(ResearchJobRequest(mode="ask", prompt="question"))
    registry.cancel(job.job_id)
    registry.run(job.job_id, runner=runner)

    snapshot = registry.get(job.job_id)
    assert calls == []
    assert snapshot["status"] == "cancelled"
    assert snapshot["stage"] == "cancelled"


def test_job_registry_cancel_during_provider_call_records_cancel_requested():
    registry = JobRegistry()

    def runner(request, job):
        job.update(stage="calling_provider", progress=65, message="Calling provider")
        registry.cancel(job.job_id)
        return {
            "mode": "ask",
            "question": request.prompt,
            "short_answer": "completed after provider",
            "findings": [],
            "gaps": [],
            "next_actions": [],
            "sources": [],
        }

    job = registry.submit(
        ResearchJobRequest(mode="ask", prompt="question"),
        runner=runner,
        run_async=False,
    )

    snapshot = registry.get(job.job_id)
    assert any(event["status"] == "cancel_requested" for event in snapshot["events"])
    assert snapshot["status"] in {"done", "cancelled"}


def test_job_save_false_does_not_create_runtime_or_vault_files(tmp_path):
    registry = JobRegistry()
    protected_dirs = [
        tmp_path / "vault" / "wiki",
        tmp_path / "vault" / "memory",
        tmp_path / "vault" / "mcp_raw",
    ]
    for protected_dir in protected_dirs:
        protected_dir.mkdir(parents=True)
        (protected_dir / "sentinel.txt").write_text("unchanged", encoding="utf-8")

    def runner(request, job):
        return {
            "mode": "ask",
            "question": request.prompt,
            "short_answer": "no write",
            "findings": [],
            "gaps": [],
            "next_actions": [],
            "sources": [],
            "saved_markdown": "",
            "saved_json": "",
        }

    registry.submit(
        ResearchJobRequest(mode="ask", prompt="question", save=False),
        runner=runner,
        run_async=False,
    )

    assert not (tmp_path / "runtime").exists()
    for protected_dir in protected_dirs:
        assert [path.name for path in protected_dir.iterdir()] == ["sentinel.txt"]


def test_job_registry_async_submit_returns_queued_or_running_immediately():
    registry = JobRegistry()

    def runner(request, job):
        time.sleep(0.05)
        return {
            "mode": "ask",
            "question": request.prompt,
            "short_answer": "async done",
            "findings": [],
            "gaps": [],
            "next_actions": [],
            "sources": [],
        }

    job = registry.submit(ResearchJobRequest(mode="ask", prompt="question"), runner=runner)
    first = registry.get(job.job_id)
    assert first["status"] in {"queued", "running", "done"}

    deadline = time.time() + 2
    while time.time() < deadline:
        snapshot = registry.get(job.job_id)
        if snapshot["status"] == "done":
            break
        time.sleep(0.02)

    assert registry.get(job.job_id)["status"] == "done"
