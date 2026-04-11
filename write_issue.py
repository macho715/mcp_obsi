import os

path = 'C:/Users/jichu/Downloads/mcp_obsidian/vault/wiki/analyses/logistics_issue_project_lightning_2024-10-01_10.md'
content = '''---
slug: logistics_issue_project_lightning_2024-10-01_10
title: 저조위(Low Tide)로 인한 램프 접안 및 하역 지연 (JPT71)
tags: [LogisticsIssue, ProjectLightning, AGI, JPT71, TideDelay]
---

## 이슈 개요
- **발생 일자**: 2024년 10월 1일
- **발생 장소**: AGI (West Harbor Jetty #3)
- **관련 선박**: JPT71 (Jopetwil 71)
- **화물**: 5mm 골재 (640톤)
- **문제 상황**: 선박이 하역장(Jetty #3)에 진입했으나, 저조위(Low tide) 현상으로 인해 선박 램프의 위치가 부적절하여 즉시 하역을 시작하지 못하고 대기해야 하는 상황이 발생함.

## 타임라인
- **07:05**: 선박(JPT71)이 West Harbor Jetty #3에 진입. 곧 하역 시작 예정임을 통보.
- **07:29**: JPT71이 AGI에서 5mm 골재 640톤 하역 대기 중 확인. (이외 타 선박 JPT62, Thuraya, Taibah, Razan 동향 보고됨)
- **07:33**: 담당자가 저조위(Low tide)로 인해 램프 위치가 부적절함을 확인. 조위가 상승하여 올바른 램프 접안이 가능할 때까지 하역 대기 결정.
- **08:35**: 조위 정상화 확인 및 램프 접안 완료. 08:30부터 하역 작업 개시.

## 해결/조치
- 현장 조수간만의 차(Tide level)를 모니터링하며 대기.
- 수위가 정상화된 후 램프를 재조정하여 안전하게 하역 작업 시작 (약 1시간 25분 지연 후 개시).
- **교훈 및 권고사항 (Lessons Learned)**:
  - 조수간만의 차이가 큰 부두(Jetty)에서는 사전에 조석표(Tide table)를 확인하여 하역 가능 시간대를 선박 도착 시간과 동기화함으로써 불필요한 대기 시간을 최소화해야 함.
  - 이와 같은 조위 변동에 따른 일정 지연 시, 연관된 현장 및 하역팀에 즉각적인 상황 공유 체계 유지 필요.
'''

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
