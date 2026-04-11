# [AGENTS.md](http://AGENTS.md)

## Mandatory

- This repository builds the **HVDC Logistics Dashboard**, which is a **program-wide logistics control tower**, not a warehouse dashboard.
- Always design for the **full shipment journey across all sites** first.
- Apply the installed React / Next.js best-practices guidance when changing dashboard code.
- Before changing UI, data model, API, labels, filters, or drilldowns, check whether the change improves **full-chain shipment visibility**.
- Prefer **route_type / stage language / shipment history** over warehouse-only interpretation.
- Do not add business-truth hardcoding when config, API, DB view, or i18n should own it.
- If the requested change risks turning Overview into a warehouse-first screen, stop and correct the design before coding.

---

## 1. Product Definition

The product is a **program-level HVDC logistics dashboard**.

It must help users understand:

- what the cargo is
- where it came from
- where it is now
- where it must go next
- whether it arrived
- when it arrived
- what happened before now

The dashboard must never be treated as:

- warehouse-only dashboard
- warehouse operations board
- warehouse storage board
- warehouse aging board

Warehouse is only **one stage** in the chain.

---

## 2. Core Journey Contract

The default logistics chain is:

Origin → Port / Air Entry → Customs → Warehouse → MOSB / Offshore Leg → Site Delivery

All main dashboard logic must preserve this chain.

When implementing or reviewing any component, ask:

1. Does this help users understand the full cargo journey?
2. Does this show where cargo came from?
3. Does this show where cargo is now?
4. Does this show where cargo must go next?
5. Does this preserve milestone timing and history?

If not, it does not belong in Overview.

---

## 3. Overview Guardrail

Overview is **voyage-first / shipment-first / all-sites-first**.

Overview must prioritize:

- total shipment visibility
- stage distribution across the full chain
- current location
- next movement
- site delivery readiness
- cross-site visibility
- shipment lookup and history entry

Overview must not be dominated by:

- warehouse rows
- warehouse-only KPIs
- warehouse-only labels
- warehouse-only filters
- warehouse-only interpretation of status

If warehouse content is needed, it must stay in:

- Cargo
- warehouse detail
- case drilldown
- site detail
- operational tabs

---

## 4. No Shipment Evaluation Rule

There is **no approved shipment evaluation model** in this product.

Do not create or expose:

- shipment score
- shipment grade
- shipment rating
- shipment performance score
- shipment health score
- shipment evaluation card
- arbitrary anomaly judgment
- traffic-light evaluation without approved business rule

Allowed shipment information:

- factual stage
- factual location
- timestamps
- dwell
- leadtime
- missing milestone note
- current stage
- next stage
- route_type
- source confidence
- record gap note

If no explicit business-approved formula exists, shipment detail must remain **fact-only**.

---

## 5. Shipment Detail Contract

A shipment detail view must focus on **traceability**, not judgment.

Every shipment detail must prioritize:

### 5.1 Identity

- SCT SHIP NO
- HVDC reference
- Packing No / Package No
- invoice / shipment reference
- case no when available
- vendor
- ship mode

### 5.2 Current State

- current stage
- current location
- last confirmed timestamp
- destination site
- next required stage

### 5.3 Route

- origin
- entry point
- customs stage
- warehouse stage
- MOSB / offshore stage
- site stage
- route_type

### 5.4 Movement History

- origin timestamp
- entry timestamp
- customs cleared timestamp
- warehouse in timestamp
- warehouse out timestamp
- MOSB / offshore timestamp if applicable
- site arrival timestamp
- final delivered timestamp if applicable

### 5.5 Duration

- warehouse dwell days
- customs dwell days
- dispatch leadtime
- total elapsed days when available

### 5.6 Data Quality

- missing milestone note
- missing location note
- source system
- source confidence

Do not default shipment detail to evaluation panels.

---

## 6. History Lookup Is Mandatory

The dashboard must support shipment history lookup by:

- Packing No
- Package No
- HVDC reference
- SCT SHIP NO
- Shipment Invoice No
- BL / CI reference when available
- case no when available

A search result must not stop at “current status”.

It must make it possible to see:

- where the cargo was before
- how long it stayed there
- when it moved
- when it reached site
- what stage is still pending

History must be **timeline-first**.

---

## 7. Search Contract

Search is a logistics traceability function, not a warehouse row finder.

Search must prioritize:

1. shipment identity lookup
2. current location lookup
3. next movement lookup
4. shipment history lookup
5. site / vendor / route drilldown

Search result and deep link behavior must preserve:

- shipment id
- SCT SHIP NO
- site
- vendor
- route_type
- stage context

A drilldown must answer:

- what it is
- where it is
- where it came from
- what happened before
- what happens next

---

## 8. Warehouse Bias Prevention

Before adding any KPI, card, table, map layer, drawer, tooltip, or filter, verify:

“Is this helping users understand the whole shipment journey across all sites?”

If the answer is no, do not place it in Overview.

Warehouse-specific information must not dominate:

- top-level KPI rail
- overview map legend
- overview status labels
- shipment global search
- shipment detail header
- route interpretation

Warehouse-specific content belongs only in detail contexts.

---

## 9. Public Language Rule

Use public shipment language, not internal-only warehouse shorthand.

Prefer:

- Origin
- Port / Air Entry
- Customs
- Warehouse
- MOSB / Offshore
- Site Delivery
- route_type
- current stage
- next stage
- site arrival

Avoid exposing internal-only language when a public logistics term exists.

Overview-linked UI should prefer:

- route_type
- plain stage language
- shipment movement language

This matches the active component contract.

---

## 10. Hardcode Ban for Operational Truth

Do not hardcode operational facts in components.

Never hardcode:

- site list
- vendor list
- shipment status labels
- stage labels
- route labels
- KPI values
- totals
- leadtime values
- history labels tied to business truth
- evaluation labels
- business thresholds that belong to config or API

These must come from:

- API
- DB view
- shared config
- i18n dictionary
- typed constants with business ownership

Allowed hardcode only for:

- spacing
- layout size
- purely visual values
- skeleton counts
- non-business animation values

---

## 11. Data Source Priority

Use factual source priority.

Program-wide shipment summary:

- shipment-level SSOT
- overview / chain / pipeline aggregates

Hitachi / Siemens package detail:

- WH truth source where approved

Other vendors:

- HVDC shipment aggregate source

Do not fabricate case-level detail for vendors that only have shipment-level data.

If detail exists, label it clearly.

If only aggregate exists, label it clearly.

---

## 12. Acceptance Criteria for Any Dashboard Change

A dashboard change is incomplete unless all checks pass:

1. It improves or preserves full-program logistics visibility.
2. It does not turn Overview into a warehouse dashboard.
3. It does not add shipment evaluation without approved logic.
4. It preserves shipment history lookup behavior.
5. It helps show origin, current location, next destination, and arrival timing.
6. It uses dynamic data, not hardcoded business truth.
7. It preserves URL-restored drilldown behavior.
8. It documents source / fallback behavior.
9. It includes loading / empty / error / success handling.
10. It keeps user-facing stage language aligned with the active product contract.

---

## 13. Stop Rules

Stop implementation and ask for clarification if any of these occur:

- Overview starts becoming warehouse-first.
- A shipment evaluation / score / grade is requested without approved formula.
- Shipment history is omitted from detail view.
- Current location and next stage are not represented.
- Site arrival timing is ignored when data exists.
- Hardcoded business truth is added where config or API should own it.
- A change hides the full chain and only shows warehouse state.

---

## 14. Dashboard-Specific Review Questions

Before merging any dashboard change, answer all of these:

1. Is this still a full HVDC logistics dashboard, not a warehouse dashboard?
2. Does this show origin → current location → next stage → destination?
3. Did we avoid shipment scoring / evaluation UI?
4. Can users retrieve shipment history by Packing No / HVDC / SCT reference?
5. Are route labels public and factual?
6. Did we add any new hardcoded business truth?
7. If a user opens one shipment, can they understand its past, present, and next movement?

---

## 15. Output Format for Dashboard Work

For dashboard audits or implementation plans, return:

- Problem
- Scope
- Risks
- Data sources
- Hardcoded items to remove
- Required API / view changes
- UI changes
- Validation checklist
- Stop conditions



## Shipment History Minimum UX  
Any shipment detail must show current location, next stage, milestone history, warehouse dwell if applicable, and site arrival datetime if available.  
  
## Overview Priority  
Overview = whole program + whole chain + all sites.  
Cargo / WH = detail and warehouse operations.  
  
## No Shipment Evaluation
If no approved scoring model exists, show facts only.

---

## 16. Technical Quick Reference

> Full technical detail: `apps/logistics-dashboard/CLAUDE.md`

**Key commands:**
```bash
pnpm --filter @repo/logistics-dashboard dev        # dev server
pnpm --filter @repo/logistics-dashboard typecheck  # 0 errors required
pnpm --filter @repo/logistics-dashboard test       # 70 tests, all must pass
npx supabase db push                               # apply DB migrations
```

**SSOT files — never bypass these:**
- Numeric thresholds / page sizes → `lib/config/dashboardSettings.ts`
- Site list → `types/sites.ts` (`CORE_SITE_CODES`, `SITE_LAND_CODES`, `SITE_ISLAND_CODES`)
- UI labels → `lib/i18n/translations.ts`

**Deploy:** `git push origin main` → Vercel auto-deploys. No manual step needed.
