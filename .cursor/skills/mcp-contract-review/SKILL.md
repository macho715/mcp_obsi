---
name: mcp-contract-review
description: Review MCP routes, auth, and tool contracts before and after changes. Use when touching /mcp, auth middleware, or memory tool schemas.
---
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
5. Suggest follow-up tests if automated verification is incomplete.
