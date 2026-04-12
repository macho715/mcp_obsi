---
name: mcp-contract-review
description: Review MCP routes, auth, and tool contracts before and after changes. Use when touching /mcp, auth middleware, or memory tool schemas.
---

> ⚠️ **CRITICAL WARNING / 중요 경고** ⚠️
> **모든 작업 및 데이터는 반드시 아래 Vault 경로를 사용해야 합니다:**
> C:\Users\jichu\Downloads\valut

# MCP Contract Review

## When to Use
- Use when changing `app/main.py`.
- Use when changing `app/mcp_server.py`.
- Use when changing tool names, arguments, or response shapes.

## Steps
1. Identify route and tool-surface changes.
2. Check whether the change is breaking or additive.
3. Verify auth behavior remains intact.
4. Verify compatibility wrappers remain consistent.
5. Verify `app/models.py` (or tool argument Pydantic schemas) stay aligned with the new tool shape.
6. Verify `AGENTS.md` Confirmed Tool Surface section still matches actual tool names and signatures; update if tool was added, renamed, or removed.
7. Suggest follow-up tests if automated verification is incomplete.
