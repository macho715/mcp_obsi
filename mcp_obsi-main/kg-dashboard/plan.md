# kg-dashboard Plan

기준 문서:
- `docs/superpowers/specs/2026-04-09-kg-visualization-design.md`
- `docs/superpowers/plans/2026-04-09-kg-visualization-plan.md`
- 현재 `kg-dashboard/` 구현 상태와 실행 결과

가정:
- 비용(AED)은 추가 호스팅, 외부 API, 별도 상용 도구 도입 기준의 거친 추정치다.
- 이번 계획은 `kg-dashboard` 범위만 다룬다. 루트 Python 스크립트의 상세 구현 계획은 승인 후 Phase 2에서 연결한다.

## Phase 1: Business Review

### 1.1 문제 정의

현재 상태 vs 목표 상태:
현재 `kg-dashboard`는 `public/data/nodes.json`과 `public/data/edges.json`을 읽어 1,365개 노드와 16,094개 엣지를 시각화하는 초기 Cytoscape 프로토타입이지만, TypeScript 빌드와 ESLint가 깨져 있고 데이터 갱신 경로가 대시보드 작업 흐름에 묶여 있지 않다. 목표 상태는 빌드 가능한 React 대시보드가 TTL 기반 그래프 자산을 반복 가능하게 시각화하고, 필터와 상세 패널이 설계 문서 수준까지 정리된 상태다.

영향 범위:
- 현재 데이터 규모: 1,365 nodes / 16,094 edges / 88 LogisticsIssue
- 현재 품질 상태: `npm run build` 실패 3건, `npm run lint` 실패 7건
- 현재 기능 공백: 설계 문서의 엔티티별 필터, 날짜/벤더 관점 필터, 데이터 재생성 절차, 배포 가능한 품질 기준이 아직 정리되지 않음

### 1.2 제안 옵션

| 옵션 | 설명 | 공수(일) | 리스크 | 비용(AED) |
|------|------|---------|--------|----------|
| A | `kg-dashboard` 프론트엔드만 안정화한다. 타입 오류와 린트 오류를 정리하고 현재 필터와 상세 패널만 다듬는다. | 1.5 | 중간 | 0 |
| B | 프론트엔드 안정화에 더해 TTL -> JSON 생성 흐름을 대시보드 사용 절차와 연결하고, 설계 문서의 핵심 필터 공백을 우선순위화한다. | 3 | 낮음 | 0 |
| C | 정적 MVP 정리 없이 바로 대화형 Graph 인터페이스로 확장한다. 자연어 질의, 서브그래프 렌더링, 백엔드 연동까지 같이 추진한다. | 6 | 높음 | 300 |

### 1.3 추천 & 근거

추천 옵션:
옵션 B

추천 이유:
- 현재 저장소에는 이미 `scripts/ttl_to_json.py`, `tests/test_ttl_to_json.py`, `kg-dashboard/public/data/*.json`이 있어 정적 Phase 1 경로가 부분적으로 존재한다.
- 지금 가장 큰 문제는 기능 부족보다 기본 빌드 실패와 데이터 갱신 절차 부재다.
- 옵션 B는 데모 가능한 상태를 가장 빨리 만들면서도 이후 대화형 Phase 2로 넘어갈 때 재사용 가능한 기반을 남긴다.

롤백 전략:
TTL 자산 연동 범위가 예상보다 커지면 이번 라운드에서는 옵션 A로 축소하고 `public/data/*.json` 스냅샷 기반 데모를 유지한다.

### 1.4 승인 요청

- [ ] Phase 1 승인

승인 전 보류:
- Phase 2 Engineering Review
- Mermaid 다이어그램
- 파일 변경 목록
- 의존성 순서
- 테스트 전략 상세
- 기술 리스크 완화안 상세
