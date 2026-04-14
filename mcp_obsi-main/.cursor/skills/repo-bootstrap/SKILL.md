---
name: repo-bootstrap
description: Initialize the local Python environment, create .env from .env.example, and verify the basic repo scaffold. Use when bootstrapping the project on a new machine.
disable-model-invocation: true
---

> ⚠️ **CRITICAL WARNING / 중요 경고** ⚠️
> **모든 작업 및 데이터는 반드시 아래 Vault 경로를 사용해야 합니다:**
> C:\Users\jichu\Downloads\valut

# Repo Bootstrap

## When to Use
- Use when the user asks to initialize the repo locally.
- Use after cloning or extracting the project on Windows.

## Steps
1. Confirm the working directory is the project root.
2. Run `install_cursor_fullsetup.ps1` on Windows.
3. Verify `.venv`, `.env`, and `.git` exist.
4. Run `pytest -q`.
5. Report exact pass/fail/manual status.

## Outputs
- Installed environment status
- Files created
- Commands run
- Remaining manual actions
