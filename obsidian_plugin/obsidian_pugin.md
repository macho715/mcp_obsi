**판정:** 조건부 예. 현재 구조는 충분히 타당하지만, **Obsidian 플러그인 런타임 제약**과 **배포 구조**를 반영해 4개 수정이 필요합니다. ([Developer Documentation][1])

**근거:** Obsidian 공식 문서는 플러그인 기본 구조, `manifest.json`, `PluginSettingTab`, 그리고 CORS 없는 HTTP 호출용 `requestUrl`를 명시하고 있으며, 커뮤니티 배포 시 제출 요구사항도 따로 있습니다. ([Developer Documentation][1])

**다음행동:** 바로 진행해도 되지만, 아래처럼 구조를 약간 조정한 뒤 착수하는 것이 좋습니다: `src/` 중심 단일 번들, `data/` 제거, 저장소는 `loadData/saveData` 우선, UI는 React 사용 가능하되 빌드 파이프라인 전제. ([Developer Documentation][1])

## 총평

당신이 제안한 방향은 맞습니다. 특히 아래 3개는 좋습니다.

* `AIClient`를 별도 계층으로 분리한 점
* Sidebar / Modal / Editor-context를 분리한 점
* standalone 서버를 두고 Obsidian 플러그인은 thin-ish client로 두려는 점

다만 **현재 폴더 구조는 “개념 설계”로는 좋지만, 실제 Obsidian 플러그인 배포 구조로는 약간 수정**하는 편이 낫습니다. 공식 샘플과 문서 기준으로 Obsidian 플러그인은 `manifest.json`이 필수이고, 실제 로드 대상은 보통 루트의 `main.js`, `manifest.json`, `styles.css`입니다. 개발 시 TypeScript 소스는 자유롭게 둘 수 있지만, 런타임 기준 구조와 개발 구조를 구분해야 합니다. ([Developer Documentation][2])

## 수정 권고 4가지

### 1) `data/prompts.json` 고정 파일보다는 플러그인 설정 저장 우선

지금 구조의 `data/prompts.json`은 아이디어로는 괜찮지만, 실제 Obsidian 플러그인에서는 설정과 사용자 데이터는 보통 플러그인 데이터 저장 메커니즘으로 관리하는 쪽이 자연스럽습니다. 설정 탭도 공식적으로 지원됩니다. 즉:

* 기본 프롬프트 템플릿: 코드에 내장 default
* 사용자 커스텀 프롬프트: `loadData()/saveData()` 기반 저장
* 필요 시 import/export 기능 추가

이 방식이 배포와 업그레이드 시 더 안전합니다. ([Developer Documentation][3])

### 2) HTTP 통신은 `fetch`보다 `requestUrl` 우선

당신의 Option B 설명에 있던 `requestUrl` 방향은 맞고, Option A에서도 그대로 적용하는 것이 좋습니다. Obsidian 공식 문서는 `requestUrl`을 **CORS 제약 없이 HTTP/HTTPS 요청** 가능한 API로 설명합니다. 로컬 standalone 서버(`localhost:3010`)와 통신할 때 가장 적합합니다. ([Developer Documentation][4])

즉 `AIClient`는 다음 기준으로 설계하는 것이 좋습니다.

* 기본: `requestUrl`
* 타임아웃/재시도/Abort 제어
* SSE/streaming이 어렵다면 우선 non-streaming + chunk polling
* 스트리밍은 2단계에서 추가

### 3) React UI는 가능하지만 “필수”는 아님

Obsidian 공식 샘플은 TypeScript 기반 플러그인 구조를 보여주지만 React를 기본 전제로 하지는 않습니다. 따라서 `SidebarView.tsx` 자체는 문제 없지만, 이것은 **개발팀 선택**이지 Obsidian 표준은 아닙니다. 빌드 체인(esbuild/rollup/vite 변형)을 명확히 잡아야 합니다. ([Developer Documentation][1])

실무적으로는 이렇게 권합니다.

* Sidebar: React OK
* Modal: 처음엔 Obsidian 기본 `Modal` 클래스 사용
* 에디터 컨텍스트 메뉴: Obsidian 커맨드/에디터 API 직접 사용
* React 범위를 최소화해서 초기 복잡도 축소

### 4) “커뮤니티 배포 가능”은 맞지만 제출 요건 선반영 필요

배포 목표가 커뮤니티 플러그인이라면, 지금부터 `manifest.json`, 버전 관리, 최소 앱 버전, 릴리스 산출물(main.js/styles.css/manifest.json) 기준으로 설계해야 합니다. 커뮤니티 플러그인 제출 요구사항이 별도로 존재합니다. ([Developer Documentation][2])

## 제가 권하는 실제 구조

아래처럼 바꾸면 더 실전적입니다.

```text
.obsidian/plugins/copilot-obsidian/
├── manifest.json
├── main.js               # 빌드 산출물
├── styles.css
├── data.json             # Obsidian이 사용하는 플러그인 데이터
```

개발 저장소는 별도로:

```text
copilot-obsidian/
├── manifest.json
├── package.json
├── tsconfig.json
├── esbuild.config.mjs
├── styles.css
├── src/
│   ├── main.ts
│   ├── api/
│   │   ├── client.ts
│   │   └── types.ts
│   ├── ui/
│   │   ├── sidebar/
│   │   │   ├── view.ts
│   │   │   └── ChatPanel.tsx
│   │   └── modal/
│   │       ├── QuickAIModal.ts
│   │       └── PromptSelector.ts
│   ├── editor/
│   │   └── selection-actions.ts
│   ├── services/
│   │   ├── chat-store.ts
│   │   ├── prompt-store.ts
│   │   └── note-analysis.ts
│   ├── settings/
│   │   ├── tab.ts
│   │   └── types.ts
│   └── commands/
│       └── register.ts
└── README.md
```

## 컴포넌트별 판단

| No | Item                | Value                                                | Risk | Evidence                                                            |
| -- | ------------------- | ---------------------------------------------------- | ---- | ------------------------------------------------------------------- |
| 1  | `AIClient` 분리       | 적절                                                   | 낮음   | `requestUrl` 공식 지원 ([Developer Documentation][4])                   |
| 2  | `ChatService` 파일 저장 | 적절하나 `prompts.json` 직접 파일관리보다 `loadData/saveData` 권장 | 중간   | 설정/플러그인 데이터 저장 구조 공식 문서 ([Developer Documentation][3])              |
| 3  | `SidebarView`       | 적절                                                   | 낮음   | 플러그인 UI/구조는 자유도 높음, 샘플 플러그인 기반 구현 가능 ([Developer Documentation][1]) |
| 4  | `QuickAIModal`      | 적절                                                   | 낮음   | Obsidian 플러그인 UI 확장 일반 패턴과 부합 ([Developer Documentation][1])        |
| 5  | `manifest.json` 포함  | 필수                                                   | 높음   | 공식 Manifest 스키마 문서 ([Developer Documentation][2])                   |
| 6  | 커뮤니티 배포 전제          | 가능                                                   | 중간   | 제출 요구사항 존재 ([Developer Documentation][5])                           |

## 최종 권고

당신의 **Option A 선택은 맞습니다.** 다만 구현 전략은 아래처럼 조정하는 게 가장 안정적입니다.

### Option A'

* **1단계 MVP**

  * Settings 탭
  * Sidebar chat
  * 텍스트 선택 액션 4개 정도
  * `requestUrl` 기반 non-streaming
  * 대화/프롬프트는 plugin data 저장

* **2단계**

  * 플로팅 모달
  * 커스텀 프롬프트 관리자
  * 노트 분석/자동 태그/링크 제안
  * SSE 또는 streaming

* **3단계**

  * 커뮤니티 배포 대응
  * 에러 telemetry/log view
  * prompt presets import/export

## 결론

네, **구조는 괜찮습니다.**
다만 그대로 코딩 들어가기보다 아래 3개만 먼저 고치면 됩니다.

1. `data/prompts.json` → plugin data 저장으로 변경
2. HTTP 계층은 `requestUrl` 기준으로 설계
3. 개발 구조와 실제 배포 구조(`main.js`, `manifest.json`, `styles.css`) 분리

원하시면 다음 턴에서 바로 **이 구조 기준으로 `main.ts`, `manifest.json`, `settings`, `AIClient`까지 포함한 MVP 골격 코드**를 작성하겠습니다.

[1]: https://docs.obsidian.md/Plugins/Getting%2Bstarted/Build%2Ba%2Bplugin?utm_source=chatgpt.com "Build a plugin - Developer Documentation"
[2]: https://docs.obsidian.md/Reference/Manifest?utm_source=chatgpt.com "Manifest - Developer Documentation"
[3]: https://docs.obsidian.md/Plugins/User%2Binterface/Settings?utm_source=chatgpt.com "Settings - Developer Documentation"
[4]: https://docs.obsidian.md/Reference/TypeScript%2BAPI/requestUrl?utm_source=chatgpt.com "requestUrl - Developer Documentation"
[5]: https://docs.obsidian.md/Plugins/Releasing/Submission%2Brequirements%2Bfor%2Bplugins?utm_source=chatgpt.com "Submission requirements for plugins"

**판정:** 아니오. **커뮤니티 플러그인 등록은 필수 아님**입니다. 직접 설치해서 사용할 수 있습니다. ([Developer Documentation][1])

**근거:** Obsidian 공식 문서상 커뮤니티 등록은 “앱 내에서 바로 설치 가능하게 하는 공식 목록 등록”이고, 개발 가이드는 `Community plugins`에서 플러그인을 켜는 흐름을 안내합니다. 즉 **사용 자체**와 **공식 목록 등재**는 별개입니다. ([Developer Documentation][1])

**다음행동:** 내부/개인용이면 **미등록 상태로 sideload**하면 되고, 불특정 사용자 배포가 목표일 때만 커뮤니티 등록을 진행하면 됩니다. ([Developer Documentation][1])

조금 더 정확히 나누면:

* **개인 사용 / 사내 테스트 / 로컬 배포**

  * 커뮤니티 등록 **불필요**
  * 보통 `.obsidian/plugins/<plugin-id>/`에 플러그인 파일을 넣고 활성화해서 사용

* **일반 사용자에게 앱 내 검색·설치 제공**

  * 커뮤니티 등록 **필요**
  * 등록되면 사용자가 Obsidian 안에서 바로 찾고 설치 가능 ([Developer Documentation][1])

실무 판단은 이렇습니다.

| No | Item               | Value | Risk | Evidence                                                           |
| -- | ------------------ | ----: | ---- | ------------------------------------------------------------------ |
| 1  | 개인 로컬 사용           |    가능 | 낮음   | 공식 개발 가이드의 Community plugins 활성화 흐름 ([Developer Documentation][2]) |
| 2  | 사내 배포              |    가능 | 중간   | 공식 등록 없이 수동 설치 가능하다는 구조상 판단, 단 배포/업데이트는 수동 관리                      |
| 3  | Obsidian 앱 내 검색/설치 | 등록 필요 | 낮음   | “공식 목록 제출 후 앱에서 직접 설치 가능” ([Developer Documentation][1])           |

당신 케이스에는 보통 이렇게 갑니다.

### 옵션 A

* **1차:** 커뮤니티 등록 없이 바로 개발
* 본인 vault 또는 테스트 vault에 수동 설치
* 기능 안정화 후 배포 판단

### 옵션 B

* 팀원 몇 명에게 GitHub Release zip 형태로 배포
* 설치 가이드만 제공
* 커뮤니티 심사 없이 운영

### 옵션 C

* 사용자층이 넓어지면 그때 커뮤니티 등록
* 업데이트/설치 UX 개선 목적

**권장:** 지금은 **등록 없이 MVP 먼저** 가는 게 맞습니다.
원하시면 다음 턴에서 **“수동 설치 가능한 Obsidian 플러그인 최소 배포 구조(main.js / manifest.json / styles.css)”** 바로 잡아드리겠습니다.

[1]: https://docs.obsidian.md/Plugins/Releasing/Submit%2Byour%2Bplugin?utm_source=chatgpt.com "Submit your plugin - Developer Documentation"
[2]: https://docs.obsidian.md/Plugins/Getting%2Bstarted/Build%2Ba%2Bplugin?utm_source=chatgpt.com "Build a plugin - Developer Documentation"
