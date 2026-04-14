# WhatsApp 그룹 Master Policy (Revised)

**Last updated:** 2025-08-09 14:05 GST
**Owner:** Logistics PMO (SCT HVDC)
**Version:** v1.1 (clean)

본 문서는 UAE HVDC 프로젝트 내 WhatsApp 업무 그룹 운용의 **최상위 기준 (Source of Truth)** 입니다.

---

## 0) Governance

* **적용 범위:** 프로젝트 발주처·시공·서브컨·포워더·항만·해상운송 관련 모든 업무용 WhatsApp 그룹.
* **문서 위치:** Master Policy ↔ 각 그룹별 *지침서 / 요약표 / 채팅 프로필*은 본 문서에서만 참조.
* **권한:** Owner(편집) / Reviewer(코멘트) / Reader(조회). 변경은 Owner 승인 후 반영.
* **버전 정책:**

  * 마이너(v1.x): 표준명/용어/참조 링크 수정.
  * 메이저(v2.x): 역할, 보안, 프로세스 구조 변경.
* **감사 주기:** 매월 1주차 `/audit full` 실행 → 결과 요약을 PMO에 보고.

---

## 1) 적용 대상 그룹 — 주 문서(Authoritative)

> 관리 원칙: 아래 표가 **마스터**입니다. 복사본/하위문서는 반드시 이 표를 원본으로 참조하십시오.

| Group (표준명)                  | Guideline     | 요약표     | 채팅 프로필    |
| ------------------------------ | ---------     | ------- | --------- |
| AGI – Wall Panel – GCC Storage | 지침서(내부)   | 요약표(내부) | 프로필(JSON) |
| Abu Dhabi Logistics            | 지침서(내부)   | 요약표(내부) | 프로필(JSON) |
| DSV Delivery                   | 지침서(내부)   | 요약표(내부) | 프로필(JSON) |
| Jopetwil 71 Group              | 지침서(내부)   | 요약표(내부) | 프로필(JSON) |
| UPC – Precast Transportation   | 지침서(내부)   | 요약표(내부) | 프로필(JSON) |
| \[HVDC] Project Lightning      | 지침서(내부)   | 요약표(내부) | 프로필(JSON) |

> 참고: 실제 파일 경로는 내부 저장소 규칙에 따라 관리되며, 링크 명세는 \*\*채팅 프로필(JSON)\*\*의 `links` 블록에 유지합니다.

---

## 2) 그룹명 표기 — 표준 규칙 (Naming Standard v1.1)

* **구분자:** 조직·장소·기능 등 상위-하위 블록 구분에 **en dash(–)** 사용. *(예: `AGI – Wall Panel – GCC Storage`)*
* **하이픈 사용 금지:** 단어 내부 고유 하이픈(예: *Pre-cast*)이 아닌 경우 **하이픈(-)** 대신 en dash 사용.
* **대문자 규칙:** 약어/고유명(AGI, MOSB, DSV, HVDC)은 **대문자**, 일반명사는 **Title Case**.
* **이모지:** 표준 표기에서는 제거. 필요 시 프로필 `aliases`에 보존 *(예: `[HVDC]⚡️Project lightning⚡️` → Alias 저장)*.
* **브래킷 태그:** `[HVDC]`와 같은 태그는 **선두 유지**, 본문은 Title Case.
* **파일명 규칙:** 파일명에는 공백·이모지 제외(링크 안정성). **문서 내 표시명**은 표준 규칙 적용.

**표준명 적용 예시**

* `AGI- Wall panel-GCC Storage` → **AGI – Wall Panel – GCC Storage**
* `UPC – PRECAST TRANSPORTATION` → **UPC – Precast Transportation**
* `[HVDC]⚡️Project lightning⚡️` → **\[HVDC] Project Lightning** *(이모지는 `aliases`로 보존)*

---

## 3) 역할(Role) & 책임(RACI)

| 구분                | PMO(Owner) | 그룹 Admin | Functional Lead | Member |
| ----------------- | ---------- | -------- | --------------- | ------ |
| 표준명/프로필 유지        | R/A        | C        | C               | I      |
| 멤버 관리(Join/Leave) | C          | R/A      | C               | I      |
| 공지(핀·설문) 관리       | C          | R        | R               | I      |
| 로그 아카이브           | R/A        | R        | C               | I      |
| 감사(`/audit full`) | R/A        | C        | C               | I      |

---

## 4) 운영 규칙

* **공지 고정:** 운영/안전/보안 필수 공지는 *핀*으로 상단 고정(최대 3개).
* **언어:** 영·한 혼용 허용, 번호/수치는 국제 표준(ISO) 표기 준수.
* **파일:** PDF/이미지 우선. 편집파일은 저장소 링크로 공유.
* **메타태그:** 메시지 첫 줄에 `[SITREP]`, `[OSDR]`, `[URGENT]` 등 접두 사용.
* **금지:** 개인정보 과다 공유, 외부 비승인 링크, 사적 대화(업무 외).

---

## 5) 보안·컴플라이언스

* **PII 처리:** PII는 마스킹(SHA-256) 후 공유. 보존기간 90일, 이후 자동 삭제 정책 준수.
* **GDPR/PDPL:** 대외 전송 전 프로젝트 PDPL 체크리스트 확인. 민감자료는 링크 공유만.
* **감사 로그:** 그룹 초대/퇴장, 공지 변경, 파일 삭제는 월별 로그로 백업.

---

## 6) KPI & 상태판(색상 코드)

* **Green:** 응답 < 10분, 미처리 건 0\~1건
* **Amber:** 응답 10~~30분, 미처리 2~~5건
* **Red:** 응답 > 30분 또는 미처리 ≥ 6건

**자동 요약 트리거**

* `/scan` : 지난 24시간 WhatsApp 로그 → 담당자별 Action 목록 생성
* `/main` : 주간 핵심 이슈 5건·리스크 3건·의사결정 3건 카드 생성
* `/audit full` : 그룹 규정 준수율·파일 정합성·멤버 리스트 싱크 검증

---

## 7) 용어집(Glossary)

| 약어              | 의미 / 프로젝트 맥락                                           |
| --------------- | ------------------------------------------------------ |
| **HVDC**        | High Voltage Direct Current (프로그램 명)                   |
| **AGI**         | 프로젝트 야드/제티 코드(AGI)                                     |
| **MOSB**        | Mussafah Offshore Supply Base                          |
| **DSV**         | DSV Logistics (운송/포워더)                                 |
| **ALS**         | ADNOC Logistics & Services                             |
| **OFCO**        | Port/Operations 관련 담당 조직(프로젝트 내 역할명)                   |
| **RORO**        | Roll-On/Roll-Off 적하 방식                                 |
| **LOLO**        | Lift-On/Lift-Off 적하 방식                                 |
| **LCT**         | Landing Craft (소형 화물선)                                 |
| **FR/OT**       | Flat Rack / Open Top 컨테이너                              |
| **CCU**         | Cargo Carrying Unit                                    |
| **NOC**         | No Objection Certificate                               |
| **CICPA**       | Critical Infrastructure & Coastal Protection Authority |
| **TPI**         | Third-Party Inspection                                 |
| **TÜV**         | 제3자 인증기관                                               |
| **Mulkiya**     | 차량 등록증(UAE)                                            |
| **PL/Manifest** | Packing List / 선적명세                                    |
| **OSDR**        | Overage/Shortage/Damage Report                         |
| **SITREP**      | Situation Report(상황보고)                                 |

---

## 8) 변경 이력(Changelog)

* 2025-08-09 — 표준명 규칙·Glossary 용어 정의 정비, KPI 색상 정의 명확화, 보안·PDPL 조항 추가, 감사 주기·트리거 명시.

---

## 9) 부록 — 채팅 프로필(JSON) 스키마

```json
{
  "name": "[HVDC] Project Lightning",
  "aliases": ["[HVDC]⚡️Project lightning⚡️"],
  "links": {
    "guideline": "internal://...",
    "summary": "internal://...",
    "profile": "internal://..."
  },
  "kpi": {"sla_min": 10, "thresholds": {"green": [0,1], "amber": [2,5], "red": [6, 999]}},
  "owners": ["PMO"],
  "admins": ["GroupAdmin"],
  "tags": ["SITREP", "OSDR", "URGENT"]
}
```
