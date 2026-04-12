# KG Dashboard Graph Visibility Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make regenerated graph changes visible in `kg-dashboard` by fixing analyses source selection, preserving analysis note metadata in the export, exposing issue-context lessons in dashboard slices, and allowing issue/lesson nodes to open the correct Obsidian note.

**Architecture:** The implementation splits cleanly into three boundaries. Python exporter code selects the analyses corpus, emits audit evidence, and adds analysis metadata to exported nodes. TypeScript graph-model code decides which lesson nodes remain visible in `summary`, `issues`, and `ego` slices. `NodeInspector` consumes exported metadata so note links open the correct Obsidian vault instead of assuming `mcp_obsidian`.

**Tech Stack:** Python 3, pandas, rdflib, pytest, React 19, TypeScript, Vitest, Vite

---

## File Structure

### Existing files to modify

- `scripts/build_dashboard_graph_data.py`
  - exporter entrypoint
  - analyses directory resolution
  - analysis metadata export
  - source audit payload
- `tests/test_dashboard_graph_export.py`
  - Python exporter contract tests
  - source selection assertions
  - analysis metadata assertions
- `kg-dashboard/src/utils/graph-model.ts`
  - summary/issues slice logic
  - issue-context lesson visibility
- `kg-dashboard/src/utils/graph-model.test.ts`
  - TypeScript slice behavior regression tests
- `kg-dashboard/src/components/NodeInspector.tsx`
  - Obsidian link construction for issue and lesson nodes

### New files to create

- `kg-dashboard/src/components/NodeInspector.test.tsx`
  - metadata-driven note link tests

### Generated artifacts to refresh

- `kg-dashboard/public/data/nodes.json`
- `kg-dashboard/public/data/edges.json`
- `runtime/audits/hvdc_ttl_source_audit.json`
- `runtime/audits/hvdc_ttl_mapping_audit.json`
- `runtime/audits/hvdc_ttl_projection_audit.json`
- `runtime/audits/hvdc_ttl_resolution_audit.json`

---

### Task 1: Lock analyses source selection and source audit contract

**Files:**
- Modify: `tests/test_dashboard_graph_export.py`
- Modify: `scripts/build_dashboard_graph_data.py`
- Test: `tests/test_dashboard_graph_export.py`

- [ ] **Step 1: Write the failing Python tests for external-first source selection**

Add these helpers and tests to `tests/test_dashboard_graph_export.py`:

```python
import scripts.build_dashboard_graph_data as dashboard_export


def _write_status_excel(path: Path, ship_no: str = "SHIP-001") -> None:
    df = pd.DataFrame(
        [
            {
                "SCT SHIP NO.": ship_no,
                "PO No.": "PO-001",
                "VENDOR": "Vendor A",
                "VESSEL NAME/ FLIGHT No.": "Vessel A",
                "MOSB": "2026-04-01",
                "AGI": "2026-04-03",
            }
        ]
    )
    df.to_excel(path, index=False)


def _write_analysis_note(path: Path, slug: str, title: str = "Delay at AGI") -> None:
    path.write_text(
        f\"\"\"---
title: {title}
slug: {slug}
tags:
  - agi
---
Issue body
\"\"\",
        encoding="utf-8",
    )


def test_export_dashboard_graph_data_prefers_external_analyses_dir_and_reports_audit(
    tmp_path: Path, monkeypatch
):
    excel_path = tmp_path / "hvdc_status.xlsx"
    _write_status_excel(excel_path)

    external_vault = tmp_path / "external-vault"
    (external_vault / ".obsidian").mkdir(parents=True)
    external_dir = external_vault / "wiki" / "analyses"
    external_dir.mkdir(parents=True)
    _write_analysis_note(external_dir / "delay-at-agi.md", "delay-at-agi")

    fallback_vault = tmp_path / "fallback-vault"
    fallback_dir = fallback_vault / "vault" / "wiki" / "analyses"
    fallback_dir.mkdir(parents=True)
    _write_analysis_note(fallback_dir / "fallback-only.md", "fallback-only", "Fallback only")

    output_dir = tmp_path / "out"
    audit_dir = tmp_path / "audits"

    monkeypatch.setattr(dashboard_export, "PRIMARY_ANALYSES_DIR", external_dir)
    monkeypatch.setattr(dashboard_export, "DEFAULT_WIKI_DIR", fallback_dir)

    dashboard_export.export_dashboard_graph_data(
        excel_path=excel_path,
        wiki_dir=None,
        output_dir=output_dir,
        audit_dir=audit_dir,
        ttl_path=None,
    )

    source_audit = json.loads((audit_dir / "hvdc_ttl_source_audit.json").read_text(encoding="utf-8"))

    assert source_audit["selected_analyses_dir"] == str(external_dir.resolve())
    assert source_audit["analyses_dir_fallback_used"] is False
    assert source_audit["loaded_notes"] == 1


def test_export_dashboard_graph_data_falls_back_to_repo_local_analyses_dir(
    tmp_path: Path, monkeypatch
):
    excel_path = tmp_path / "hvdc_status.xlsx"
    _write_status_excel(excel_path, ship_no="SHIP-002")

    missing_external = tmp_path / "missing-external" / "wiki" / "analyses"
    fallback_vault = tmp_path / "fallback-vault"
    (fallback_vault / ".obsidian").mkdir(parents=True)
    fallback_dir = fallback_vault / "wiki" / "analyses"
    fallback_dir.mkdir(parents=True)
    _write_analysis_note(fallback_dir / "fallback-delay.md", "fallback-delay", "Fallback delay")

    output_dir = tmp_path / "out"
    audit_dir = tmp_path / "audits"

    monkeypatch.setattr(dashboard_export, "PRIMARY_ANALYSES_DIR", missing_external)
    monkeypatch.setattr(dashboard_export, "DEFAULT_WIKI_DIR", fallback_dir)

    dashboard_export.export_dashboard_graph_data(
        excel_path=excel_path,
        wiki_dir=None,
        output_dir=output_dir,
        audit_dir=audit_dir,
        ttl_path=None,
    )

    source_audit = json.loads((audit_dir / "hvdc_ttl_source_audit.json").read_text(encoding="utf-8"))

    assert source_audit["selected_analyses_dir"] == str(fallback_dir.resolve())
    assert source_audit["analyses_dir_fallback_used"] is True
    assert source_audit["loaded_notes"] == 1
```

- [ ] **Step 2: Run the targeted Python tests and confirm they fail**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_dashboard_graph_export.py -q
```

Expected:

- FAIL because `export_dashboard_graph_data(..., wiki_dir=None, ...)` is not supported yet
- or FAIL because `selected_analyses_dir` / `analyses_dir_fallback_used` are missing from `hvdc_ttl_source_audit.json`

- [ ] **Step 3: Implement deterministic analyses directory resolution and audit fields**

Update `scripts/build_dashboard_graph_data.py` with these additions:

```python
PRIMARY_ANALYSES_DIR = Path(r"C:\Users\jichu\Downloads\valut\wiki\analyses")


def _resolve_analyses_dir(wiki_dir: Path | None) -> tuple[Path | None, bool]:
    if wiki_dir is not None:
        return wiki_dir, False
    if PRIMARY_ANALYSES_DIR.exists():
        return PRIMARY_ANALYSES_DIR, False
    if DEFAULT_WIKI_DIR.exists():
        return DEFAULT_WIKI_DIR, True
    return None, False
```

Change the exporter signature and call site:

```python
def export_dashboard_graph_data(
    excel_path: Path = DEFAULT_EXCEL_PATH,
    wiki_dir: Path | None = None,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    ttl_path: Path | None = DEFAULT_TTL_PATH,
    warehouse_status_path: Path | None = None,
    jpt_reconciled_path: Path | None = None,
    inland_cost_path: Path | None = None,
    audit_dir: Path = DEFAULT_AUDIT_DIR,
) -> None:
    resolved_wiki_dir, fallback_used = _resolve_analyses_dir(wiki_dir)
    sources = _load_sources_bundle(
        excel_path=excel_path,
        warehouse_status_path=warehouse_status_path,
        jpt_reconciled_path=jpt_reconciled_path,
        inland_cost_path=inland_cost_path,
        analyses_dir=resolved_wiki_dir or DEFAULT_WIKI_DIR,
    )
```

Update source audit payload:

```python
source_audit = {
    "dropped_rows": dropped_rows,
    "loaded_shipments": len(sources.shipment_rows),
    "loaded_notes": len(sources.analysis_notes),
    "selected_analyses_dir": str(resolved_wiki_dir.resolve()) if resolved_wiki_dir else None,
    "analyses_dir_fallback_used": fallback_used,
}
```

Also guard `_read_analysis_notes` so a missing directory returns `[]` without error:

```python
def _read_analysis_notes(analyses_dir: Path | None) -> list[dict[str, Any]]:
    if analyses_dir is None or not analyses_dir.exists():
        return []
```

- [ ] **Step 4: Re-run the targeted Python tests and confirm they pass**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_dashboard_graph_export.py -q
```

Expected:

- PASS for the two new source-selection tests
- existing export contract tests still PASS

- [ ] **Step 5: Commit the source-selection change**

```powershell
git add -- tests/test_dashboard_graph_export.py scripts/build_dashboard_graph_data.py
git commit -m "feat: prefer external analyses dir for dashboard export"
```

---

### Task 2: Export analysis note metadata for issue and lesson nodes

**Files:**
- Modify: `tests/test_dashboard_graph_export.py`
- Modify: `scripts/build_dashboard_graph_data.py`
- Test: `tests/test_dashboard_graph_export.py`

- [ ] **Step 1: Write the failing Python test for exported note metadata**

Append this test to `tests/test_dashboard_graph_export.py`:

```python
def test_export_dashboard_graph_data_exports_analysis_metadata_for_issue_and_lesson(
    tmp_path: Path, monkeypatch
):
    excel_path = tmp_path / "hvdc_status.xlsx"
    _write_status_excel(excel_path)

    external_vault = tmp_path / "external-vault"
    (external_vault / ".obsidian").mkdir(parents=True)
    analyses_dir = external_vault / "wiki" / "analyses"
    analyses_dir.mkdir(parents=True)
    _write_analysis_note(analyses_dir / "delay-at-agi.md", "delay-at-agi")

    output_dir = tmp_path / "out"
    audit_dir = tmp_path / "audits"

    monkeypatch.setattr(dashboard_export, "PRIMARY_ANALYSES_DIR", analyses_dir)
    monkeypatch.setattr(dashboard_export, "DEFAULT_WIKI_DIR", tmp_path / "unused-fallback")

    dashboard_export.export_dashboard_graph_data(
        excel_path=excel_path,
        wiki_dir=None,
        output_dir=output_dir,
        audit_dir=audit_dir,
        ttl_path=None,
    )

    nodes = json.loads((output_dir / "nodes.json").read_text(encoding="utf-8"))
    node_by_type = {}
    for node in nodes:
        node_by_type.setdefault(node["data"]["type"], []).append(node["data"])

    issue_node = node_by_type["LogisticsIssue"][0]
    lesson_node = node_by_type["IncidentLesson"][0]

    assert issue_node["analysisPath"] == "wiki/analyses/delay-at-agi.md"
    assert issue_node["analysisVault"] == "external-vault"
    assert lesson_node["analysisPath"] == "wiki/analyses/delay-at-agi.md"
    assert lesson_node["analysisVault"] == "external-vault"
```

- [ ] **Step 2: Run the targeted Python tests and confirm they fail**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_dashboard_graph_export.py -q
```

Expected:

- FAIL because issue and lesson node payloads do not yet include `analysisPath` and `analysisVault`

- [ ] **Step 3: Implement note metadata propagation in the exporter**

Add helper functions to `scripts/build_dashboard_graph_data.py`:

```python
def _find_obsidian_vault_root(path: Path | None) -> Path | None:
    if path is None:
        return None
    current = path.resolve()
    while True:
        if (current / ".obsidian").exists():
            return current
        if current.parent == current:
            return None
        current = current.parent


def _analysis_note_metadata(note_path: Path, analyses_dir: Path | None) -> dict[str, str | None]:
    vault_root = _find_obsidian_vault_root(analyses_dir)
    if vault_root is None:
        return {
            "analysisPath": None,
            "analysisVault": None,
        }
    return {
        "analysisPath": note_path.resolve().relative_to(vault_root).as_posix(),
        "analysisVault": vault_root.name,
    }
```

Extend `_read_analysis_notes` so every note record carries metadata:

```python
def _read_analysis_notes(analyses_dir: Path | None) -> list[dict[str, Any]]:
    if analyses_dir is None or not analyses_dir.exists():
        return []

    notes: list[dict[str, Any]] = []
    for path in sorted(analyses_dir.glob("*.md")):
        metadata = _analysis_note_metadata(path, analyses_dir)
        notes.append(
            {
                "path": str(path),
                "frontmatter": _read_frontmatter(path),
                "body": path.read_text(encoding="utf-8"),
                "analysis_path": metadata["analysisPath"],
                "analysis_vault": metadata["analysisVault"],
            }
        )
    return notes
```

Propagate metadata into issue nodes:

```python
nodes[issue_id] = {
    "data": {
        "id": issue_id,
        "label": title,
        "type": "LogisticsIssue",
        "rdf-schema#label": title,
        "analysisPath": note.get("analysis_path"),
        "analysisVault": note.get("analysis_vault"),
    }
}
```

Propagate metadata into canonical lesson records and dashboard lesson payloads:

```python
lesson_record["analysisPath"] = note.get("analysis_path")
lesson_record["analysisVault"] = note.get("analysis_vault")
```

```python
dashboard_lessons = [
    {
        **lesson,
        "id": _safe_uri(lesson.get("id")),
        "shipment_id": _legacy_dashboard_id(_safe_uri(lesson.get("shipment_id"))),
        "location_id": _legacy_dashboard_id(_safe_uri(lesson.get("location_id"))),
        "carrier_id": _legacy_dashboard_id(_safe_uri(lesson.get("carrier_id"))),
        "pattern_id": _legacy_dashboard_id(_safe_uri(lesson.get("pattern_id"))),
        "analysisPath": lesson.get("analysisPath"),
        "analysisVault": lesson.get("analysisVault"),
    }
    for lesson in canonical_lessons
]
```

- [ ] **Step 4: Re-run the targeted Python tests and confirm they pass**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_dashboard_graph_export.py -q
```

Expected:

- PASS for metadata export
- PASS for source-selection tests from Task 1

- [ ] **Step 5: Commit the metadata export change**

```powershell
git add -- tests/test_dashboard_graph_export.py scripts/build_dashboard_graph_data.py
git commit -m "feat: export analysis metadata for dashboard notes"
```

---

### Task 3: Make summary and issues views keep issue-context lessons only

**Files:**
- Modify: `kg-dashboard/src/utils/graph-model.test.ts`
- Modify: `kg-dashboard/src/utils/graph-model.ts`
- Test: `kg-dashboard/src/utils/graph-model.test.ts`

- [ ] **Step 1: Write the failing TypeScript tests for issue-context lesson slices**

Append these tests to `kg-dashboard/src/utils/graph-model.test.ts`:

```ts
it('keeps issue-context lessons in summary and hides unrelated lessons', () => {
  const nodes: GraphNode[] = [
    node('issue/a', 'Delay at AGI', 'LogisticsIssue'),
    node('site/agi', 'AGI', 'Site'),
    node('warehouse/dsv', 'DSV Indoor', 'Warehouse'),
    node('lesson/agi', 'AGI lesson', 'IncidentLesson'),
    node('shipment/1', 'Shipment 1', 'Shipment'),
    node('lesson/shipment', 'Shipment-only lesson', 'IncidentLesson'),
  ];
  const edges: GraphEdge[] = [
    edge('issue/a', 'site/agi', 'occursAt'),
    edge('site/agi', 'lesson/agi', 'relatedToLesson'),
    edge('shipment/1', 'lesson/shipment', 'relatedToLesson'),
  ];

  const summary = buildSummaryView(nodes, edges);

  expect(summary.nodes.map((item) => item.data.id)).toContain('lesson/agi');
  expect(summary.nodes.map((item) => item.data.id)).not.toContain('lesson/shipment');
  expect(summary.edges.map(edgeKey)).toContain('site/agi|lesson/agi|relatedToLesson');
});

it('keeps issue-context lessons in issues view without pulling unrelated lessons', () => {
  const nodes: GraphNode[] = [
    node('issue/a', 'Delay at AGI', 'LogisticsIssue'),
    node('site/agi', 'AGI', 'Site'),
    node('lesson/agi', 'AGI lesson', 'IncidentLesson'),
    node('hub/mosb', 'MOSB', 'Hub'),
    node('lesson/mosb', 'MOSB unrelated lesson', 'IncidentLesson'),
  ];
  const edges: GraphEdge[] = [
    edge('issue/a', 'site/agi', 'occursAt'),
    edge('site/agi', 'lesson/agi', 'relatedToLesson'),
    edge('hub/mosb', 'lesson/mosb', 'relatedToLesson'),
  ];

  const issues = buildIssueView(nodes, edges);

  expect(issues.nodes.map((item) => item.data.id)).toContain('lesson/agi');
  expect(issues.nodes.map((item) => item.data.id)).not.toContain('lesson/mosb');
  expect(issues.edges.map(edgeKey)).toContain('site/agi|lesson/agi|relatedToLesson');
});

it('keeps directly attached lessons in ego view for the selected node', () => {
  const nodes: GraphNode[] = [
    node('shipment/1', 'Shipment 1', 'Shipment'),
    node('lesson/shipment', 'Shipment lesson', 'IncidentLesson'),
    node('site/agi', 'AGI', 'Site'),
    node('lesson/site', 'Site lesson', 'IncidentLesson'),
  ];
  const edges: GraphEdge[] = [
    edge('shipment/1', 'lesson/shipment', 'relatedToLesson'),
    edge('site/agi', 'lesson/site', 'relatedToLesson'),
  ];

  const ego = buildEgoView(nodes, edges, 'shipment/1', 8);

  expect(ego.nodes.map((item) => item.data.id)).toContain('lesson/shipment');
  expect(ego.nodes.map((item) => item.data.id)).not.toContain('lesson/site');
});
```

- [ ] **Step 2: Run the TypeScript test file and confirm summary/issues tests fail**

Run:

```powershell
cd kg-dashboard
npm test -- --run src/utils/graph-model.test.ts
```

Expected:

- FAIL because `buildSummaryView` and `buildIssueView` currently exclude `IncidentLesson`
- the `ego` regression test may already pass; keep it as a guardrail

- [ ] **Step 3: Implement issue-context lesson selection in `graph-model.ts`**

Add lesson constants and helpers to `kg-dashboard/src/utils/graph-model.ts`:

```ts
const LESSON_TYPE: GraphNodeType = 'IncidentLesson';

function collectIssueContextLessonIds(
  keptNodes: GraphNode[],
  index: GraphIndex,
): Set<string> {
  const keptIds = new Set(keptNodes.map((node) => node.data.id));
  const issueIds = new Set(
    keptNodes.filter((node) => node.data.type === ISSUE_TYPE).map((node) => node.data.id),
  );
  const lessonIds = new Set<string>();

  keptNodes.forEach((node) => {
    if (!INFRA_TYPES.has(node.data.type)) {
      return;
    }

    const neighbors = [...(index.adjacency.get(node.data.id) ?? [])];
    const hasVisibleIssueNeighbor = neighbors.some((neighborId) => issueIds.has(neighborId));
    if (!hasVisibleIssueNeighbor) {
      return;
    }

    neighbors.forEach((neighborId) => {
      const neighbor = index.nodeById.get(neighborId);
      if (neighbor?.data.type === LESSON_TYPE) {
        lessonIds.add(neighborId);
      }
    });
  });

  return lessonIds;
}
```

Update `buildSummaryView`:

```ts
const baseNodes = nodes.filter(
  (node) => node.data.type === ISSUE_TYPE || INFRA_TYPES.has(node.data.type),
);
const index = buildGraphIndex(nodes, edges);
const lessonIds = collectIssueContextLessonIds(baseNodes, index);
const keptIds = new Set([...baseNodes.map((node) => node.data.id), ...lessonIds]);
const keptNodes = nodes.filter((node) => keptIds.has(node.data.id));
const keptEdges = edges.filter(
  (edge) => keptIds.has(edge.data.source) && keptIds.has(edge.data.target),
);
```

Update `buildIssueView`:

```ts
const baseNodes = nodes.filter(
  (node) => node.data.type === ISSUE_TYPE || INFRA_TYPES.has(node.data.type),
);
const index = buildGraphIndex(nodes, edges);
const lessonIds = collectIssueContextLessonIds(baseNodes, index);
const keptIds = new Set([...baseNodes.map((node) => node.data.id), ...lessonIds]);
const keptNodes = nodes.filter((node) => keptIds.has(node.data.id));
const keptEdges = edges.filter((edge) => {
  if (!keptIds.has(edge.data.source) || !keptIds.has(edge.data.target)) {
    return false;
  }
  return (
    nodeHasType(edge.data.source, ISSUE_TYPE, keptNodes) ||
    nodeHasType(edge.data.target, ISSUE_TYPE, keptNodes) ||
    nodeHasType(edge.data.source, LESSON_TYPE, keptNodes) ||
    nodeHasType(edge.data.target, LESSON_TYPE, keptNodes)
  );
});
```

- [ ] **Step 4: Re-run the TypeScript graph-model tests and confirm they pass**

Run:

```powershell
cd kg-dashboard
npm test -- --run src/utils/graph-model.test.ts
```

Expected:

- PASS for the three new slice tests
- existing graph-model tests still PASS

- [ ] **Step 5: Commit the graph slice change**

```powershell
git add -- kg-dashboard/src/utils/graph-model.ts kg-dashboard/src/utils/graph-model.test.ts
git commit -m "feat: surface issue-context lessons in dashboard slices"
```

---

### Task 4: Make NodeInspector open issue and lesson notes from exported metadata

**Files:**
- Create: `kg-dashboard/src/components/NodeInspector.test.tsx`
- Modify: `kg-dashboard/src/components/NodeInspector.tsx`
- Test: `kg-dashboard/src/components/NodeInspector.test.tsx`

- [ ] **Step 1: Write the failing inspector tests**

Create `kg-dashboard/src/components/NodeInspector.test.tsx` with this content:

```tsx
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { NodeInspector } from './NodeInspector';

describe('NodeInspector analysis links', () => {
  it('uses exported analysis metadata for issue nodes', () => {
    const markup = renderToStaticMarkup(
      <NodeInspector
        node={{
          data: {
            id: 'http://hvdc.logistics/ontology/issue/delay-at-agi',
            label: 'Delay at AGI',
            type: 'LogisticsIssue',
            analysisVault: 'external-vault',
            analysisPath: 'wiki/analyses/delay-at-agi.md',
          },
        }}
        degree={4}
        onClose={() => {}}
      />,
    );

    expect(markup).toContain('obsidian://open?vault=external-vault&amp;file=wiki%2Fanalyses%2Fdelay-at-agi.md');
  });

  it('uses exported analysis metadata for lesson nodes', () => {
    const markup = renderToStaticMarkup(
      <NodeInspector
        node={{
          data: {
            id: 'http://hvdc.logistics/ontology/lesson/delay-at-agi',
            label: 'Delay at AGI lesson',
            type: 'IncidentLesson',
            analysisVault: 'external-vault',
            analysisPath: 'wiki/analyses/delay-at-agi.md',
          },
        }}
        degree={2}
        onClose={() => {}}
      />,
    );

    expect(markup).toContain('obsidian://open?vault=external-vault&amp;file=wiki%2Fanalyses%2Fdelay-at-agi.md');
  });
});
```

- [ ] **Step 2: Run the inspector tests and confirm they fail**

Run:

```powershell
cd kg-dashboard
npm test -- --run src/components/NodeInspector.test.tsx
```

Expected:

- FAIL because `NodeInspector` still hard-codes `vault=mcp_obsidian`
- FAIL because lesson nodes do not currently create a note link

- [ ] **Step 3: Implement metadata-first note linking in `NodeInspector.tsx`**

Replace the current slug-only link setup with this helper:

```tsx
function getAnalysisLink(node: GraphNode): { href: string; label: string } | null {
  const analysisPath =
    typeof node.data.analysisPath === 'string' && node.data.analysisPath
      ? node.data.analysisPath
      : null;
  const analysisVault =
    typeof node.data.analysisVault === 'string' && node.data.analysisVault
      ? node.data.analysisVault
      : null;

  if (analysisPath && analysisVault) {
    return {
      href: `obsidian://open?vault=${encodeURIComponent(analysisVault)}&file=${encodeURIComponent(analysisPath)}`,
      label: 'Open linked Obsidian note',
    };
  }

  const issueSlug = node.data.type === 'LogisticsIssue' ? getIssueSlug(node.data.id) : null;
  if (!issueSlug) {
    return null;
  }

  return {
    href: `obsidian://open?vault=mcp_obsidian&file=${encodeURIComponent(`vault/wiki/analyses/${issueSlug}.md`)}`,
    label: 'Open linked Obsidian note',
  };
}
```

Use it in the component:

```tsx
const analysisLink = getAnalysisLink(node);
```

```tsx
{analysisLink ? (
  <a className="obsidian-link" href={analysisLink.href} target="_blank" rel="noreferrer">
    {analysisLink.label}
  </a>
) : null}
```

- [ ] **Step 4: Re-run the inspector tests and confirm they pass**

Run:

```powershell
cd kg-dashboard
npm test -- --run src/components/NodeInspector.test.tsx
```

Expected:

- PASS for issue-node metadata link
- PASS for lesson-node metadata link

- [ ] **Step 5: Commit the inspector change**

```powershell
git add -- kg-dashboard/src/components/NodeInspector.tsx kg-dashboard/src/components/NodeInspector.test.tsx
git commit -m "feat: open dashboard issue and lesson notes from metadata"
```

---

### Task 5: Regenerate graph artifacts and verify the full contract

**Files:**
- Modify: `kg-dashboard/public/data/nodes.json`
- Modify: `kg-dashboard/public/data/edges.json`
- Modify: `runtime/audits/hvdc_ttl_source_audit.json`
- Modify: `runtime/audits/hvdc_ttl_mapping_audit.json`
- Modify: `runtime/audits/hvdc_ttl_projection_audit.json`
- Modify: `runtime/audits/hvdc_ttl_resolution_audit.json`
- Test: `tests/test_dashboard_graph_export.py`
- Test: `kg-dashboard/src/utils/graph-model.test.ts`
- Test: `kg-dashboard/src/components/NodeInspector.test.tsx`

- [ ] **Step 1: Regenerate dashboard data and audits**

Run:

```powershell
.venv\Scripts\python.exe scripts/build_dashboard_graph_data.py
```

Expected:

- `kg-dashboard/public/data/nodes.json` updated
- `kg-dashboard/public/data/edges.json` updated
- `runtime/audits/hvdc_ttl_source_audit.json` updated with `selected_analyses_dir`

- [ ] **Step 2: Run the exporter-side Python verification**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_dashboard_graph_export.py -q
```

Expected:

- PASS

- [ ] **Step 3: Run the full dashboard test and quality checks**

Run:

```powershell
cd kg-dashboard
npm test
npm run lint
npm run build
```

Expected:

- `vitest run` PASS
- ESLint PASS
- Vite production build PASS

- [ ] **Step 4: Run a local browser verification**

Run:

```powershell
cd kg-dashboard
npm run preview -- --host 127.0.0.1 --port 4175
```

Manual checks:

- summary view shows lesson changes only in issue context
- issues view shows issue-context lessons and their anchor edges
- selecting a shipment/site/carrier/pattern node in `ego` exposes directly attached lessons only
- clicking an issue or lesson node shows an Obsidian link that targets the selected analyses vault, not hard-coded `mcp_obsidian`

- [ ] **Step 5: Commit regenerated artifacts and final implementation**

```powershell
git add -- scripts/build_dashboard_graph_data.py tests/test_dashboard_graph_export.py kg-dashboard/src/utils/graph-model.ts kg-dashboard/src/utils/graph-model.test.ts kg-dashboard/src/components/NodeInspector.tsx kg-dashboard/src/components/NodeInspector.test.tsx kg-dashboard/public/data/nodes.json kg-dashboard/public/data/edges.json runtime/audits/hvdc_ttl_source_audit.json runtime/audits/hvdc_ttl_mapping_audit.json runtime/audits/hvdc_ttl_projection_audit.json runtime/audits/hvdc_ttl_resolution_audit.json
git commit -m "feat: align kg-dashboard graph visibility with exported lessons"
```

---

## Self-Review

### Spec coverage

- Analyses source selection: covered by Task 1
- Source audit path evidence: covered by Task 1
- Analysis note metadata export: covered by Task 2
- Summary/issues issue-context lesson visibility: covered by Task 3
- Ego lesson visibility: covered by Task 3
- Inspector note linking: covered by Task 4
- Artifact regeneration and end-to-end verification: covered by Task 5

### Placeholder scan

- No `TODO`
- No `TBD`
- No "write tests for the above" placeholders
- Every code-changing step includes concrete code snippets

### Type consistency

- Python audit fields: `selected_analyses_dir`, `analyses_dir_fallback_used`
- Node metadata fields: `analysisPath`, `analysisVault`
- TypeScript lesson node type: `IncidentLesson`
- Edge label used across exporter and UI tests: `relatedToLesson`

---

Plan complete and saved to `docs/superpowers/plans/2026-04-12-kg-dashboard-graph-visibility-alignment-implementation.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**

## Execution Update (2026-04-12)

The implementation has been executed in the current workspace and the plan is
now a historical record of what shipped.

### What actually shipped

- The exporter now prefers the external analyses corpus and records the chosen
  path in audit output.
- The exporter CLI default stays on `ttl_path=None`.
- Analysis note parsing tolerates malformed YAML frontmatter instead of
  crashing the export pass.
- The projection layer preserves `analysisPath` and `analysisVault` so linked
  note navigation survives graph slicing.
- Issue-context lesson slicing is implemented in the dashboard projection
  logic and verified in the view tests.
- `NodeInspector` now opens issue and lesson notes from exported metadata.

### Actual deviations from the original plan

- The plan described a staged fail-first implementation flow. The current
  workspace reflects the completed implementation rather than the intermediate
  failing checkpoints.
- The plan proposed adding a dedicated `NodeInspector.test.tsx` file during the
  work. That regression coverage exists in the current workspace and was
  verified as part of the completed implementation.
- The plan called for manual browser verification after regeneration. That
  check is now done, and the preview evidence is recorded below.

### Verification evidence

- Python contract test run: `5 passed`
- Dashboard tests: `18 passed`
- Lint/build: passed
- Browser preview: `http://127.0.0.1:4175` loaded successfully
- Playwright snapshot: Issues view visible node count dropped from `227` to
  `216` after switching from Summary to Issues
- Source audit: external analyses path selected, `loaded_notes = 115`
- Export metadata counts:
  - `113` issue nodes with metadata
  - `102` lesson nodes with metadata

### Resulting workspace state

The exporter, projection builder, graph model, and NodeInspector now work as a
single verified flow. The original plan items remain below for traceability,
but the implementation is complete in the current workspace.
