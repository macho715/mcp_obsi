**판정:** 예. 수동 설치용 최소 배포 단위는 보통 **`main.js` + `manifest.json` + `styles.css(선택)`** 입니다. 플러그인은 vault 내부 `.obsidian/plugins/<plugin-id>/`에 이 파일들을 두면 됩니다. ([GitHub][1])

**근거:** Obsidian 샘플 플러그인과 배포/제출 자료는 `manifest.json`을 필수로 전제하고, 수동 설치 안내들은 공통적으로 `main.js`, `manifest.json`, `styles.css` 복사를 기준으로 설명합니다. `styles.css`는 UI 스타일이 있을 때만 필요합니다. ([GitHub][1])

**다음행동:** 아래 구조 그대로 시작하면 됩니다. 먼저 `plugin-id`를 고정한 뒤, `manifest.json`과 폴더명이 일치하도록 맞추십시오. ([Developer Documentation][2])

## 최소 배포 구조

```text
<Vault>/
└── .obsidian/
    └── plugins/
        └── copilot-obsidian/
            ├── main.js
            ├── manifest.json
            └── styles.css
```

## 파일별 역할

| No | Item            | Value          | Risk                                        | Evidence                       |
| -- | --------------- | -------------- | ------------------------------------------- | ------------------------------ |
| 1  | `main.js`       | 플러그인 실행 파일, 필수 | 없으면 로드 불가                                   | ([GitHub][1])                  |
| 2  | `manifest.json` | 플러그인 메타데이터, 필수 | `id/version/minAppVersion` 불일치 시 설치·업데이트 문제 | ([Developer Documentation][2]) |
| 3  | `styles.css`    | UI 스타일, 선택     | 파일 없어도 동작 가능하나 UI 깨질 수 있음                   | ([Obsidian Forum][3])          |

## `manifest.json` 최소 예시

```json
{
  "id": "copilot-obsidian",
  "name": "Copilot Obsidian",
  "version": "0.0.1",
  "minAppVersion": "1.5.0",
  "description": "AI chat and editor actions for Obsidian.",
  "author": "MR.CHA",
  "isDesktopOnly": false
}
```

### 주의

* `id`는 폴더명과 같게 두는 편이 안전합니다.
* 릴리스할 때는 Git tag / release 버전과 `manifest.json.version`을 맞추는 관행이 일반적입니다. ([Medium][4])

## `main.js` 최소 예시

실제 배포본은 TypeScript를 빌드한 결과물이어야 하지만, 구조 이해용 최소 예시는 아래처럼 생각하면 됩니다.

```javascript
'use strict';

const obsidian = require('obsidian');

module.exports = class CopilotObsidianPlugin extends obsidian.Plugin {
  async onload() {
    console.log('Copilot Obsidian loaded');

    this.addCommand({
      id: 'open-copilot-test',
      name: 'Open Copilot Test',
      callback: () => {
        new obsidian.Notice('Copilot Obsidian is working');
      }
    });
  }

  onunload() {
    console.log('Copilot Obsidian unloaded');
  }
};
```

실무에서는 직접 손으로 `main.js`를 쓰기보다 `src/main.ts`를 작성하고 빌드해서 `main.js`를 생성합니다. Obsidian 샘플 플러그인도 TypeScript 기반입니다. ([GitHub][1])

## `styles.css` 최소 예시

```css
.copilot-obsidian-panel {
  padding: 12px;
}

.copilot-obsidian-muted {
  opacity: 0.7;
}
```

UI가 아직 없으면 비워 두거나 아예 생략해도 됩니다. ([Obsidian Forum][3])

## 수동 설치 절차

1. vault의 `.obsidian/plugins/`로 이동
2. `copilot-obsidian/` 폴더 생성
3. `main.js`, `manifest.json`, `styles.css` 복사
4. Obsidian 재시작 또는 플러그인 새로고침
5. **Settings → Community plugins**에서 활성화 ([Obsidian Forum][5])

## 개발용 권장 구조와 배포 구조는 분리

개발 저장소는 이렇게 두는 것이 일반적입니다.

```text
copilot-obsidian/
├── src/
│   └── main.ts
├── manifest.json
├── styles.css
├── package.json
├── tsconfig.json
└── esbuild.config.mjs
```

빌드 후 vault에 복사되는 최종 산출물은 이것만 있으면 됩니다.

```text
copilot-obsidian/
├── main.js
├── manifest.json
└── styles.css
```

## 바로 써먹을 실무 기준

### MVP 1차

* `main.js`
* `manifest.json`
* `styles.css`
* 명령어 1개만 탑재

### 2차

* Settings 탭 추가
* 사이드바 뷰 추가
* `requestUrl` 기반 서버 호출 추가

### 3차

* 선택 텍스트 액션
* 모달
* 스트리밍 응답

## cmd3

```bash
mkdir -p "<VAULT>/.obsidian/plugins/copilot-obsidian"
cp main.js manifest.json styles.css "<VAULT>/.obsidian/plugins/copilot-obsidian/"
# 이후 Obsidian에서 Community plugins 활성화
```

원하시면 다음 단계로 바로 **`manifest.json + src/main.ts + esbuild.config.mjs + package.json`까지 포함한 “빌드 가능한 최소 플러그인 템플릿”**을 드리겠습니다.

[1]: https://github.com/obsidianmd/obsidian-sample-plugin?utm_source=chatgpt.com "obsidianmd/obsidian-sample-plugin"
[2]: https://docs.obsidian.md/Plugins/Releasing/Submission%2Brequirements%2Bfor%2Bplugins?utm_source=chatgpt.com "Submission requirements for plugins"
[3]: https://forum.obsidian.md/t/plugins-mini-faq/7737?utm_source=chatgpt.com "Plugins mini FAQ - Basement"
[4]: https://medium.com/%40lukasbach/a-more-streamlined-development-workflow-for-obsidian-plugins-2a74b0c57c0f?utm_source=chatgpt.com "A more streamlined development workflow for Obsidian ..."
[5]: https://forum.obsidian.md/t/plugin-inbox-processor/101243?utm_source=chatgpt.com "Plugin: Inbox Processor - Share & showcase"

**판정:** 예. 아래 템플릿은 **바로 `npm i` → `npm run dev`/`npm run build` 가능한 최소 Obsidian 플러그인 골격**입니다. Obsidian 공식 가이드와 샘플 플러그인이 `src`, `esbuild.config.mjs`, `manifest.json`, `package.json` 구조와 수동 설치 대상 파일 `main.js`, `manifest.json`, `styles.css`를 기준으로 안내합니다. ([Developer Documentation][1])

**근거:** 샘플 플러그인은 `npm run dev`로 `main.ts`를 `main.js`로 컴파일하고, 수동 설치 시 `main.js`, `styles.css`, `manifest.json`을 vault의 `.obsidian/plugins/<plugin-id>/`에 복사하라고 명시합니다. ([GitHub][2])

**다음행동:** 아래 6개 파일을 그대로 만든 뒤, `manifest.json`의 `id`와 폴더명을 동일하게 맞추십시오. 그 다음 `npm i`, `npm run dev`, Obsidian 재로드 순서로 테스트하면 됩니다. ([GitHub][2])

## 최소 폴더 구조

```text
copilot-obsidian/
├── manifest.json
├── package.json
├── esbuild.config.mjs
├── styles.css
└── src/
    └── main.ts
```

## 1) manifest.json

```json
{
  "id": "copilot-obsidian",
  "name": "Copilot Obsidian",
  "version": "0.0.1",
  "minAppVersion": "1.5.0",
  "description": "Minimal Obsidian plugin template with command and sidebar view.",
  "author": "MR.CHA",
  "isDesktopOnly": false
}
```

## 2) package.json

```json
{
  "name": "copilot-obsidian",
  "version": "0.0.1",
  "private": true,
  "description": "Minimal buildable Obsidian plugin template",
  "main": "main.js",
  "scripts": {
    "dev": "node esbuild.config.mjs",
    "build": "node esbuild.config.mjs production"
  },
  "devDependencies": {
    "@types/node": "^22.15.3",
    "builtin-modules": "^4.0.0",
    "esbuild": "^0.25.4",
    "obsidian": "^1.8.10",
    "tslib": "^2.8.1",
    "typescript": "^5.8.3"
  }
}
```

## 3) esbuild.config.mjs

```javascript
import esbuild from "esbuild";
import process from "node:process";
import builtins from "builtin-modules";

const prod = process.argv[2] === "production";

const context = await esbuild.context({
  entryPoints: ["src/main.ts"],
  bundle: true,
  external: [
    "obsidian",
    "electron",
    "@codemirror/autocomplete",
    "@codemirror/collab",
    "@codemirror/commands",
    "@codemirror/language",
    "@codemirror/lint",
    "@codemirror/search",
    "@codemirror/state",
    "@codemirror/view",
    ...builtins
  ],
  format: "cjs",
  target: "es2018",
  sourcemap: prod ? false : "inline",
  treeShaking: true,
  outfile: "main.js",
  logLevel: "info"
});

if (prod) {
  await context.rebuild();
  await context.dispose();
} else {
  await context.watch();
  console.log("[copilot-obsidian] watching for changes...");
}
```

## 4) src/main.ts

```ts
import {
	App,
	ItemView,
	Notice,
	Plugin,
	PluginSettingTab,
	Setting,
	WorkspaceLeaf
} from "obsidian";

const VIEW_TYPE_COPILOT = "copilot-obsidian-sidebar";

interface CopilotPluginSettings {
	serverUrl: string;
	apiToken: string;
}

const DEFAULT_SETTINGS: CopilotPluginSettings = {
	serverUrl: "http://127.0.0.1:3010",
	apiToken: ""
};

class CopilotSidebarView extends ItemView {
	plugin: CopilotObsidianPlugin;

	constructor(leaf: WorkspaceLeaf, plugin: CopilotObsidianPlugin) {
		super(leaf);
		this.plugin = plugin;
	}

	getViewType(): string {
		return VIEW_TYPE_COPILOT;
	}

	getDisplayText(): string {
		return "Copilot Chat";
	}

	getIcon(): string {
		return "messages-square";
	}

	async onOpen(): Promise<void> {
		const { contentEl } = this;
		contentEl.empty();

		contentEl.createEl("h3", { text: "Copilot Obsidian" });

		const desc = contentEl.createEl("p", {
			text: "최소 템플릿입니다. 이후 채팅 UI와 서버 연동을 붙이면 됩니다."
		});
		desc.addClass("copilot-obsidian-muted");

		const button = contentEl.createEl("button", {
			text: "연결 테스트"
		});
		button.addClass("mod-cta");

		button.addEventListener("click", async () => {
			const result = await this.plugin.pingServer();
			new Notice(result ? "서버 연결 성공" : "서버 연결 실패");
		});
	}

	async onClose(): Promise<void> {
		this.contentEl.empty();
	}
}

class CopilotSettingTab extends PluginSettingTab {
	plugin: CopilotObsidianPlugin;

	constructor(app: App, plugin: CopilotObsidianPlugin) {
		super(app, plugin);
		this.plugin = plugin;
	}

	display(): void {
		const { containerEl } = this;
		containerEl.empty();

		containerEl.createEl("h2", { text: "Copilot Obsidian Settings" });

		new Setting(containerEl)
			.setName("Server URL")
			.setDesc("Standalone AI 서버 주소")
			.addText((text) =>
				text
					.setPlaceholder("http://127.0.0.1:3010")
					.setValue(this.plugin.settings.serverUrl)
					.onChange(async (value) => {
						this.plugin.settings.serverUrl = value.trim();
						await this.plugin.saveSettings();
					})
			);

		new Setting(containerEl)
			.setName("API Token")
			.setDesc("필요한 경우 Bearer token 저장")
			.addText((text) =>
				text
					.setPlaceholder("token")
					.setValue(this.plugin.settings.apiToken)
					.onChange(async (value) => {
						this.plugin.settings.apiToken = value.trim();
						await this.plugin.saveSettings();
					})
			);
	}
}

export default class CopilotObsidianPlugin extends Plugin {
	settings: CopilotPluginSettings;

	async onload(): Promise<void> {
		await this.loadSettings();

		this.registerView(
			VIEW_TYPE_COPILOT,
			(leaf) => new CopilotSidebarView(leaf, this)
		);

		this.addRibbonIcon("bot", "Open Copilot Sidebar", async () => {
			await this.activateSidebar();
		});

		this.addCommand({
			id: "open-copilot-sidebar",
			name: "Open Copilot Sidebar",
			callback: async () => {
				await this.activateSidebar();
			}
		});

		this.addCommand({
			id: "copilot-test-notice",
			name: "Run Copilot Test",
			callback: async () => {
				const ok = await this.pingServer();
				new Notice(ok ? "Copilot test OK" : "Copilot test failed");
			}
		});

		this.addSettingTab(new CopilotSettingTab(this.app, this));
	}

	onunload(): void {
		this.app.workspace.detachLeavesOfType(VIEW_TYPE_COPILOT);
	}

	async loadSettings(): Promise<void> {
		this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
	}

	async saveSettings(): Promise<void> {
		await this.saveData(this.settings);
	}

	async activateSidebar(): Promise<void> {
		const { workspace } = this.app;

		let leaf = workspace.getLeavesOfType(VIEW_TYPE_COPILOT)[0];
		if (!leaf) {
			leaf = workspace.getRightLeaf(false);
			if (!leaf) {
				new Notice("사이드바를 열 수 없습니다.");
				return;
			}
			await leaf.setViewState({
				type: VIEW_TYPE_COPILOT,
				active: true
			});
		}

		workspace.revealLeaf(leaf);
	}

	async pingServer(): Promise<boolean> {
		try {
			// MVP 단계: 네트워크가 아니라 설정값만 최소 검증
			// 실제 연결 시에는 requestUrl(...)로 교체
			return this.settings.serverUrl.length > 0;
		} catch (error) {
			console.error("[copilot-obsidian] ping failed", error);
			return false;
		}
	}
}
```

## 5) styles.css

```css
.copilot-obsidian-muted {
	opacity: 0.72;
}

.workspace-leaf-content[data-type="copilot-obsidian-sidebar"] .view-content {
	padding: 16px;
}
```

## 6) 설치 및 빌드

```bash
npm i
npm run dev
```

빌드 결과로 생성된 `main.js`와 원본 `manifest.json`, `styles.css`를 아래 위치에 두면 수동 설치가 됩니다. Obsidian 샘플 플러그인도 동일한 수동 설치 방식을 안내합니다. ([GitHub][2])

```text
<VAULT>/.obsidian/plugins/copilot-obsidian/
├── main.js
├── manifest.json
└── styles.css
```

## 바로 다음 단계 권장

현재 템플릿은 “빌드 가능 + Obsidian에서 보이는 최소 상태”입니다. 다음 추가 순서는 이게 가장 안전합니다.

1. `pingServer()`를 `requestUrl` 기반 실제 호출로 교체
2. 선택 텍스트 명령 1개 추가
3. Sidebar에 입력창/응답창 추가
4. Settings에 custom prompt 저장 추가

## 참고

* Obsidian 공식 개발 가이드는 플러그인 빌드 시작 절차를 제공합니다. ([Developer Documentation][1])
* 공식 샘플 플러그인은 `src`, `esbuild.config.mjs`, `manifest.json`, `package.json`, `styles.css`를 포함한 템플릿입니다. ([GitHub][2])
* 수동 설치 대상은 `main.js`, `styles.css`, `manifest.json`입니다. ([GitHub][2])

원하시면 다음으로 **`requestUrl`까지 붙인 실제 서버 연동 버전**으로 이어서 작성하겠습니다.

[1]: https://docs.obsidian.md/Plugins/Getting%2Bstarted/Build%2Ba%2Bplugin?utm_source=chatgpt.com "Build a plugin - Developer Documentation"
[2]: https://github.com/obsidianmd/obsidian-sample-plugin "GitHub - obsidianmd/obsidian-sample-plugin: Template for Obsidian community plugins with build configuration and development best practices. · GitHub"
