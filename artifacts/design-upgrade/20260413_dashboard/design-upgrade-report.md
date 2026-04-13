# Design Upgrade Report: kg-dashboard

## 1. Baseline Diagnosis
- **Visual hierarchy**: Current hierarchy uses functional grid layouts but lacks strong typographic scale for key dashboard stats. `.dashboard-stat dd` looks like regular text.
- **Typography scale**: Topbar title is bold, but secondary elements lack clear distinction (muted vs. accent). 
- **Spacing and alignment**: Border radiuses and padding are consistent (8px/0.75rem), but empty states are a bit dry (`.dashboard-status-card`).
- **Interaction**: Chips and buttons (`.segmented-control__button`, `.infra-filter-chip`) have basic hover states but lack tactile feedback or scale.

## 2. Transferable Design Elements
1. **Goal-based Typography & Data Hierarchy**: Increase visual weight and tracking of the main dashboard statistics numbers. (Source: DesignRush Dashboard Trends)
2. **Interactive Data Visualization**: Make the `pill`, `chip`, and `button` interactions feel snappier using slight scale transforms (Source: Awwwards - Mathical).
3. **Actionable Empty States**: Center-align and soften the empty state cards with a light patterned or gray background to indicate a "stage" area without harsh errors (Source: BrowserLondon - Notion).

## 3. Patch Map
🔓 SCOPE LOCK: NOT ACTIVE — 모든 레이어에 변경 허용

| 파일 / 섹션 | 현재 문제 | 제안 변경 | 레퍼런스 URL | target_layer | 예상 임팩트 | 리스크 |
|-------------|-----------|-----------|--------------|--------------|--------------|--------|
| `App.css` `.dashboard-stat` | 통계 텍스트가 평범함 | `dd`에 큰 폰트 크기 및 타이트한 자간 적용 | DesignRush URL | TYPOGRAPHY | 대시보드 성격 강조 | 없음 |
| `App.css` `.segmented-control__button` | 호버 상태가 평면적임 | `transform: scale(1.02)` 적용 및 `transition` 수정 | Mathical (Awwwards) | ANIMATION | 인터랙션 피드백 향상 | 낮음 |
| `App.css` `.dashboard-status-card` | Empty State가 건조함 | `text-align: center`, 중앙 정렬 Flexbox 사용 | Notion (BrowserLondon) | LAYOUT | 초대하는 분위기 조성 | 없음 |

✅ 적용 예정: 3개 패치 (allowed_layers 내)
🚫 제외됨: 0개 패치 (scope 위반)

## 4. Applied Change Summary
적용된 변경: 3개 (모두 allowed layers 내)
scope 위반으로 제외: 0개
