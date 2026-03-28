@AGENTS.md

## Claude Code
- Treat `AGENTS.md` as the shared project SSOT. Keep this file as Claude-specific delta only.
- Never reintroduce folder-based semantic classification. Folders are chronological storage only.
- When editing storage contracts, metadata schema, auth flow, or MCP tool shapes, use plan mode first and keep diffs narrow.
- If Claude-specific always-on rules grow, move them into `.claude/rules/` instead of expanding this file.
- Put deterministic enforcement into `.claude/settings.json` hooks, not prose instructions.
- Put repeatable extraction, review, or reindex workflows into `.claude/skills/` so they load only when relevant.
- Before reporting completion, list files touched, commands run, verification status, and any remaining assumptions.
