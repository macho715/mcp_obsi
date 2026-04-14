---
name: release-check
description: Run the minimum release-readiness checklist for this repo. Use before pushing a branch, opening a PR, or handing off work.
disable-model-invocation: true
---

> ⚠️ **CRITICAL WARNING / 중요 경고** ⚠️
> **모든 작업 및 데이터는 반드시 아래 Vault 경로를 사용해야 합니다:**
> C:\Users\jichu\Downloads\valut

# Release Check

> Note: `disable-model-invocation: true` prevents auto-attachment but the checklist
> must still be executed by the agent when the user requests it in any language
> ("PR 올리기 전에 체크리스트", "릴리스 체크", "run checks before merge", etc.).

## Checklist
1. Run `pytest -q`.
2. Run `ruff check .`.
3. Run `ruff format --check .`.
4. Confirm no secrets or real tokens were added.
5. Summarize files changed, commands run, and pass/fail/manual status.
