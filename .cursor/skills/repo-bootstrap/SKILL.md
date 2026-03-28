---
name: repo-bootstrap
description: Initialize the local Python environment, create .env from .env.example, and verify the basic repo scaffold. Use when bootstrapping the project on a new machine.
disable-model-invocation: true
---
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
