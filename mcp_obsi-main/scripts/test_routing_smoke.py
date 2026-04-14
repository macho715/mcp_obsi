"""
Routing smoke check: verify that obsidian-ingest, obsidian-query, and obsidian-lint
SKILL.md files follow the Pointer Template Policy defined in AGENTS.md.

Run from repo root:
    .venv\\Scripts\\python scripts/test_routing_smoke.py

Checks:
  1. Each SKILL has a save_memory payload with required pointer fields.
  2. `projects` includes "mcp_obsidian".
  3. `tags` includes "kb".
  4. `content` references [[wiki/...]] link (not a raw note body dump).
  5. `roles` uses only approved values: fact, summary, audit.
  6. kb-core.mdc includes vault/raw/ in its routing table.
  7. AGENTS.md contains KB Routing Policy and Pointer Template Policy sections.
  8. docs/storage-routing.md exists and contains the routing diagram.
"""

from __future__ import annotations

import pathlib
import re
import sys

REPO = pathlib.Path(".")
SKILLS = ["obsidian-ingest", "obsidian-query", "obsidian-lint"]
APPROVED_ROLES = {"fact", "summary", "audit"}

failures: list[str] = []
passes: list[str] = []


def check(condition: bool, name: str, detail: str = "") -> None:
    if condition:
        passes.append(name)
        print(f"  PASS  {name}")
    else:
        failures.append(name)
        print(f"  FAIL  {name}" + (f" — {detail}" if detail else ""))


# ── Check 1-5: SKILL pointer payload fields ───────────────────────────────────
for skill in SKILLS:
    path = REPO / ".cursor" / "skills" / skill / "SKILL.md"
    if not path.exists():
        check(False, f"{skill}/SKILL.md exists", "file not found")
        continue
    text = path.read_text(encoding="utf-8")

    check(
        bool(re.search(r'"projects".*mcp_obsidian', text, re.DOTALL)),
        f"{skill}: projects includes mcp_obsidian",
    )

    check('"kb"' in text or '"kb"' in text, f"{skill}: tags includes kb")

    check(bool(re.search(r"\[\[wiki/", text)), f"{skill}: content references [[wiki/...]] link")

    # roles must only be approved values
    role_matches = re.findall(r'"roles":\s*\[([^\]]+)\]', text)
    skill_roles: set[str] = set()
    for rm in role_matches:
        for r in re.findall(r'"(\w+)"', rm):
            skill_roles.add(r)
    bad_roles = skill_roles - APPROVED_ROLES
    check(
        not bad_roles,
        f"{skill}: roles only approved values",
        f"bad roles: {bad_roles}" if bad_roles else "",
    )

    check('"projects"' in text, f"{skill}: projects field present in payload")

# ── Check 6: kb-core.mdc has vault/raw/ ───────────────────────────────────────
kb_core = REPO / ".cursor" / "rules" / "kb-core.mdc"
if kb_core.exists():
    kc_text = kb_core.read_text(encoding="utf-8")
    check("vault/raw/" in kc_text, "kb-core.mdc: vault/raw/ in routing table")
    check(
        "save_memory" in kc_text and "pointer" in kc_text.lower(),
        "kb-core.mdc: pointer template reference",
    )
else:
    check(False, "kb-core.mdc exists", "file not found")

# ── Check 7: AGENTS.md sections ───────────────────────────────────────────────
agents_md = REPO / "AGENTS.md"
if agents_md.exists():
    ag_text = agents_md.read_text(encoding="utf-8")
    check("KB Routing Policy" in ag_text, "AGENTS.md: KB Routing Policy section")
    check("Pointer Template Policy" in ag_text, "AGENTS.md: Pointer Template Policy section")
    check("Approval Gates" in ag_text, "AGENTS.md: Approval Gates section")
else:
    check(False, "AGENTS.md exists", "file not found")

# ── Check 8: docs/storage-routing.md ─────────────────────────────────────────
routing_doc = REPO / "docs" / "storage-routing.md"
check(routing_doc.exists(), "docs/storage-routing.md exists")
if routing_doc.exists():
    rd_text = routing_doc.read_text(encoding="utf-8")
    check("mermaid" in rd_text, "docs/storage-routing.md: Mermaid diagram present")
    check(
        "Pointer Template" in rd_text or "pointer" in rd_text.lower(),
        "docs/storage-routing.md: pointer template section",
    )
    check("vault/raw" in rd_text, "docs/storage-routing.md: vault/raw/ documented")

# ── Summary ───────────────────────────────────────────────────────────────────
total = len(passes) + len(failures)
print(f"\n{'─' * 50}")
print(f"  PASS {len(passes)}/{total}  FAIL {len(failures)}/{total}")
if failures:
    print("\n  Failed checks:")
    for f in failures:
        print(f"    - {f}")
    sys.exit(1)
else:
    print("\n  All routing smoke checks PASS")
    sys.exit(0)
