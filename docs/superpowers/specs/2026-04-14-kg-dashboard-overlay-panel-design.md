# kg-dashboard Overlay Panel Design

**Date:** 2026-04-14  
**Status:** Approved  
**Scope:** Layout restructure — canvas-first with overlay controls panel

---

## Problem

The current dashboard uses a fixed 3-column grid (`220px | 1fr | 240px`).  
The graph canvas is compressed to roughly 280px height, leaving insufficient space for the primary visualization. Controls and Inspector panels always occupy screen real estate even when not in use.

## Decision

**Canvas-first layout with single overlay panel.**

- Graph canvas fills 100% of the viewport (below toolbar).
- Controls + Inspector live in a single overlay panel (360px wide, left-side).
- Overlay opens via a "⚙ Controls" button in the toolbar.
- Overlay closes via backdrop click or ✕ button.
- Node selection auto-opens the overlay and switches to Inspector tab.

---

## Layout Structure

```
┌──────────────────────────────────────────────┐
│  TOOLBAR  kg-dashboard | VISIBLE | HIDDEN  ⚙ │  ← 고정 상단바
├──────────────────────────────────────────────┤
│  [Graph][Table][Timeline][Schema]             │  ← 뷰 탭 행
├──────────────────────────────────────────────┤
│                                              │
│           GRAPH CANVAS  (100% × 100%)        │  ← 항상 전체 차지
│                                              │
│  ┌──────────────────┐                        │
│  │ Controls Inspector│ ✕                     │  ← 오버레이 패널
│  │──────────────────│                        │
│  │  SEARCH ...      │                        │
│  │  VIEW MODE ...   │                        │
│  └──────────────────┘                        │
│  [반투명 백드롭]──────────────────────────── │
└──────────────────────────────────────────────┘
```

---

## Overlay Behavior

| Trigger | Result |
|---------|--------|
| ⚙ Controls 버튼 클릭 | 오버레이 오픈, Controls 탭 포커스 |
| 그래프 노드 클릭 | 오버레이 오픈, Inspector 탭 자동 전환 |
| 백드롭 클릭 | 오버레이 닫힘 |
| ✕ 버튼 클릭 | 오버레이 닫힘 |
| Esc 키 | 오버레이 닫힘 |

## Overlay Spec

- **Width:** 360px
- **Height:** 100% (toolbar 아래부터 화면 하단까지)
- **Position:** `position: fixed; left: 0; top: 0; z-index: 100`
- **Animation:** `transform: translateX(-100%) → translateX(0)`, 200ms ease
- **Backdrop:** `position: fixed; inset: 0; background: rgba(0,0,0,0.25); z-index: 99`

---

## UX Improvement: Disabled Action Buttons

Pin / Hide / Expand 1-hop 버튼은 노드 미선택 시 숨김 처리.  
`canPinSelection = false` 일 때 해당 버튼 섹션 렌더링하지 않음.

---

## Files Changed

| File | Change |
|------|--------|
| `src/App.tsx` | `panelOpen` state 추가, `handleNodeSelect`에 `setPanelOpen(true)`, overlay JSX 구조 |
| `src/App.css` | shell → relative/absolute, overlay + backdrop 신규, compact-panel-slot 제거 |
| `src/components/DashboardToolbar.tsx` | `onOpenPanel` prop + ⚙ Controls 버튼 |
| `src/components/CompactPanelToggle.tsx` | `onClose` prop 추가, 오버레이 헤더 역할 |

**신규 파일:** 없음  
**삭제 파일:** 없음 (기존 컴포넌트 재사용)
