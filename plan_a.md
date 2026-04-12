# Standalone Chat UX Patch — Implementation Plan

**Date:** 2026-04-08
**Source:** `docs/STANDALONE_CHAT_UX_STUDIO.md`
**Status:** Phase 1 — awaiting approval

---

## Phase 1 — Business Review

### 1.1 Problem Definition

| | |
|---|---|
| **Current state** | Standalone Chat (`renderChatHtml()`) has 10+ WCAG 2.2 AA violations — missing `aria-*` attributes, `role`, `aria-live` regions, and `aria-busy`/`aria-disabled` state. It is the only UI surface of the local AI stack and is currently inaccessible to keyboard-only and screen-reader users. |
| **Target state** | All interactive components pass WCAG 2.2 AA at component level: `role`, `aria-live`, `aria-label`, `aria-busy`, `aria-disabled` present on all interactive elements. |
| **Impact scope** | Single-user local desktop app; no SLA; keyboard-a11y and screen-reader a11y are blocking for users with visual impairments. |

### 1.2 Options

| Option | Description | Effort (days) | Risk | Cost (AED) |
|--------|-------------|--------------|------|------------|
| **A — Inline A11y Patch** | Add `aria-*` attributes directly inside the existing `renderChatHtml()` string template; minimal JS state updates. No file restructuring. | 0.5 | Low — string-only change | 0 |
| **B — Extract to TS modules** | Separate HTML template, CSS block, and JS logic into dedicated TypeScript module files under `standalone-package/src/ui/`. Full refactor. | 3–5 | Medium — breaks existing Express route wiring | 0 (internal) |
| **C — Hybrid (A now, B later)** | Do Option A immediately; schedule Option B as a separate tracked task (`feat/standalone-ui-upgrade`). | 0.5 + 3–5 later | Low (now) | 0 |

### 1.3 Recommendation

**Option C — Hybrid.**

理由: The A11y patch is a 30-minute string edit with near-zero risk. Delivering it now unblocks screen-reader users immediately. The structural refactor (Option B) is a separate concern that belongs in a dedicated `feat/standalone-ui-upgrade` branch, not mixed into a quick patch.

失敗時 롤백: `git checkout` to pre-patch commit — the change is a single targeted string edit inside one function.

### 1.4 Approval Request

```
[ ] Phase 1 approved — proceed to Phase 2 engineering review
[ ] Phase 1 approved — proceed to Phase 2 AND implement Option A immediately
[ ] Phase 1 rejected —理由: ___________
```

---

## Phase 2 — Engineering Review

### 2.1 Architecture (Mermaid)

```mermaid
graph TD
  subgraph standalone-package
    DB[docs-browser.ts<br/>renderChatHtml()]
    DB --> HTML_CHAT["<inline HTML string> — target for aria patch"]
    DB --> JS_LOGIC["<inline <script> — setBusy / showError / saveMem handlers"]
  end

  subgraph a11y-patch
    P1["#error-banner<br/>role='alert' aria-live='assertive'"]
    P2["#chat-history<br/>aria-label aria-live='polite'"]
    P3["#prompt<br/><label for='prompt'> (sr-only)"]
    P4["#send<br/>aria-busy={busy}"]
    P5["#save-memory<br/>aria-disabled={saving}"]
    P6["#sources<br/>aria-label='Source documents'"]
    P7["#memory-indicator<br/>aria-live='polite'"]
  end

  HTML_CHAT --> P1
  HTML_CHAT --> P2
  HTML_CHAT --> P3
  HTML_CHAT --> P4
  HTML_CHAT --> P5
  HTML_CHOT --> P6
  HTML_CHAT --> P7
  JS_LOGIC --> P4
  JS_LOGIC --> P5
```

### 2.2 File Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `myagent-copilot-kit/standalone-package/src/docs-browser.ts` | modify | A11y patch: add `role`, `aria-live`, `aria-label`, `aria-busy`, `aria-disabled` attributes to 7 components; update JS state handlers |
| `docs/STANDALONE_CHAT_UX_STUDIO.md` | modify | Mark OQ-1 resolved, update feasibility Gate to **Go** |
| `docs/STANDALONE_CHAT_UX_PATCH_NOTES.md` | create | Changelog of exact attribute changes for future reference |

> **⚠️ File exists check**: `docs-browser.ts` exists at the path above (restored from `72dc920`). No naming conflict on new file `STANDALONE_CHAT_UX_PATCH_NOTES.md`.

### 2.3 Dependency & Order

```
Step 1: Edit docs-browser.ts (Option A inline patch)
  ↓
Step 2: pnpm --dir myagent-copilot-kit/standalone-package build
  ↓
Step 3: Manual browser smoke (Tab order, aria attributes in DevTools)
  ↓
Step 4: Commit + push to feat/standalone-ui-upgrade branch
  ↓
Step 5: (Deferred) Option B structural refactor as separate task
```

**No shared modules are affected.** This change is scoped to one render function inside `docs-browser.ts` only.

### 2.4 Test Strategy

| Test Type | Scope | Method |
|-----------|-------|--------|
| **Build** | `pnpm build` passes | `pnpm --dir myagent-copilot-kit/standalone-package build` |
| **Smoke (keyboard)** | Tab order, focus visible | Manual: open `http://127.0.0.1:3010/`, press Tab 8 times |
| **Smoke (DevTools)** | aria attributes present | Manual: Inspect elements, verify `role`, `aria-live`, `aria-label` |
| **Regression** | Existing chat + memory save flow | Manual: send 1 query → save to memory → verify 200 + green indicator |
| **Existing tests** | None expected to break | `pnpm test` (if test script exists) |

No unit test changes required — the change is inside a single render function string.

### 2.5 Risks & Mitigation

| Risk | Category | Mitigation |
|------|----------|------------|
| `aria-live="assertive"` causes screen reader to interrupt mid-flow | Compatibility | Use `aria-live="polite"` for `#chat-history`; only `#error-banner` gets `assertive` |
| `aria-busy` not recognized by all AT | Compatibility | Keep `disabled` attribute as primary signal; `aria-busy` is additive |
| String edit accidentally breaks HTML syntax | Integrity | Wrap attribute additions in clearly delimited comment block; verify `pnpm build` |
| DevTools `role` inspection shows correct but screen reader still silent | AT variance | Note in patch notes: NVDA vs JAWS behavior differs; validate with both if available |

---

## Open Questions (to be resolved during implementation)

| OQ | Question | Resolution Plan |
|----|----------|----------------|
| OQ-1 | Separate branch? | Yes — `feat/standalone-ui-upgrade` |
| OQ-2 | `aria-live` placement | `#error-banner` → `role="alert" aria-live="assertive"`; all others → `polite` |
| OQ-3 | Rollback on memory save failure? | Out of scope for this patch; deferred to future task |
| OQ-4 | Model routing verified? | Out of scope for this patch; separate verification ticket |
| OQ-5 | TS module extraction? | Deferred to Option B structural refactor task |
