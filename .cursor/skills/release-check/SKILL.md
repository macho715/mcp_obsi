---
name: release-check
description: Run the minimum release-readiness checklist for this repo. Use before pushing a branch, opening a PR, or handing off work.
disable-model-invocation: true
---
# Release Check

## Checklist
1. Run `pytest -q`.
2. Run `ruff check .`.
3. Run `ruff format --check .`.
4. Confirm no secrets or real tokens were added.
5. Summarize files changed, commands run, and pass/fail/manual status.
