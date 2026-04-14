**판정:** 예. 아래 버전은 `requestUrl`로 **실제 standalone 서버와 HTTP 연동**하는 최소 구현입니다. Obsidian 가이드는 플러그인에서 `fetch`/`axios` 대신 `requestUrl` 사용을 권장하며, 이는 **CORS 제약 없이 HTTP/HTTPS 요청**을 보낼 수 있는 API입니다. ([Developer Documentation][1])

**근거:** 현재 템플릿에선 `pingServer()`가 설정값만 확인했는데, 이를 `GET /health`와 `POST /api/ai/chat` 호출로 바꾸면 바로 서버 연결 테스트와 채팅 요청까지 이어집니다. 또 플러그인 데이터는 `loadData/saveData`로 관리하는 것이 Obsidian 권장 패턴입니다. ([Developer Documentation][2])

**다음행동:** 아래 3개만 교체하면 됩니다. `src/main.ts`를 전체 교체하고, 서버 쪽에 `GET /health`, `POST /api/ai/chat` 엔드포인트만 맞추십시오. 서버 스펙이 다르면 `callChatApi()`의 payload만 조정하면 됩니다.

## 전제 서버 스펙

아래 예시는 이 형태를 가정합니다.

### 1) 헬스체크

```http
GET /health
```

응답 예시:

```json
{
  "ok": true
}
```

### 2) 채팅

```http
POST /api/ai/chat
Content-Type: application/json
Authorization: Bearer <token>
```

요청 예시:

```json
{
  "message": "선택한 텍스트 요약해줘",
  "context": "현재 노트 내용 일부",
  "notePath": "folder/note.md"
}
```

응답 예시:

```json
{
  "reply": "요약 결과..."
}
```

---

## 교체본: `src/main.ts`

```ts
import {
	App,
	ItemView,
	Notice,
	Plugin,
	PluginSettingTab,
	Setting,
	WorkspaceLeaf,
	requestUrl,
	RequestUrlResponse,
	TFile
} from "obsidian";

const VIEW_TYPE_COPILOT = "copilot-sidebar";

interface CopilotPluginSettings {
	serverUrl: string;
	apiToken: string;
	requestTimeoutMs: number;
}

interface HealthResponse {
	ok?: boolean;
	status?: string;
}

interface ChatRequestBody {
	message: string;
	context?: string;
	notePath?: string;
}

interface ChatResponseBody {
	reply?: string;
	message?: string;
	output?: string;
	result?: string;
}

const DEFAULT_SETTINGS: CopilotPluginSettings = {
	serverUrl: "http://127.0.0.1:3010",
	apiToken: "",
	requestTimeoutMs: 30000
};

class CopilotSidebarView extends ItemView {
	plugin: CopilotObsidianPlugin;
	private inputEl: HTMLTextAreaElement | null = null;
	private outputEl: HTMLDivElement | null = null;
	private sendButtonEl: HTMLButtonElement | null = null;

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

		contentEl.createEl("h3", { text: "Copilot Chat" });

		const descEl = contentEl.createEl("div", {
			text: "Standalone 서버와 requestUrl로 연결되는 최소 채팅 패널"
		});
		descEl.addClass("copilot-muted");

		const actionsEl = contentEl.createDiv({ cls: "copilot-actions" });

		const healthBtn = actionsEl.createEl("button", {
			text: "서버 연결 테스트",
			cls: "mod-cta"
		});
		healthBtn.addEventListener("click", async () => {
			healthBtn.disabled = true;
			try {
				const ok = await this.plugin.pingServer();
				new Notice(ok ? "서버 연결 성공" : "서버 연결 실패");
			} finally {
				healthBtn.disabled = false;
			}
		});

		const activeFile = this.plugin.app.workspace.getActiveFile();
		const fileInfo = contentEl.createDiv({
			text: activeFile ? `현재 노트: ${activeFile.path}` : "현재 활성 노트 없음"
		});
		fileInfo.addClass("copilot-file-info");

		this.inputEl = contentEl.createEl("textarea", {
			placeholder: "질문을 입력하세요. 예: 현재 노트 핵심 3줄 요약"
		});
		this.inputEl.addClass("copilot-input");

		this.sendButtonEl = contentEl.createEl("button", {
			text: "전송",
			cls: "mod-cta"
		});
		this.sendButtonEl.addClass("copilot-send");

		this.outputEl = contentEl.createDiv({ cls: "copilot-output" });
		this.outputEl.setText("응답이 여기에 표시됩니다.");

		this.sendButtonEl.addEventListener("click", async () => {
			await this.handleSend();
		});

		this.inputEl.addEventListener("keydown", async (evt: KeyboardEvent) => {
			if (evt.key === "Enter" && (evt.ctrlKey || evt.metaKey)) {
				evt.preventDefault();
				await this.handleSend();
			}
		});
	}

	async onClose(): Promise<void> {
		this.contentEl.empty();
	}

	private async handleSend(): Promise<void> {
		if (!this.inputEl || !this.outputEl || !this.sendButtonEl) return;

		const message = this.inputEl.value.trim();
		if (!message) {
			new Notice("질문을 입력하세요.");
			return;
		}

		this.sendButtonEl.disabled = true;
		this.outputEl.setText("응답 생성 중...");

		try {
			const activeFile = this.plugin.app.workspace.getActiveFile();
			const context = await this.plugin.getActiveNoteContent(4000);

			const reply = await this.plugin.callChatApi({
				message,
				context,
				notePath: activeFile?.path
			});

			this.outputEl.setText(reply);
		} catch (error) {
			const messageText = error instanceof Error ? error.message : String(error);
			this.outputEl.setText(`오류: ${messageText}`);
			new Notice("채팅 요청 실패");
		} finally {
			this.sendButtonEl.disabled = false;
		}
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

		new Setting(containerEl)
			.setName("Server URL")
			.setDesc("예: http://127.0.0.1:3010")
			.addText((text) =>
				text
					.setPlaceholder("http://127.0.0.1:3010")
					.setValue(this.plugin.settings.serverUrl)
					.onChange(async (value) => {
						this.plugin.settings.serverUrl = value.trim().replace(/\/+$/, "");
						await this.plugin.saveSettings();
					})
			);

		new Setting(containerEl)
			.setName("API token")
			.setDesc("필요 시 Bearer token")
			.addText((text) =>
				text
					.setPlaceholder("token")
					.setValue(this.plugin.settings.apiToken)
					.onChange(async (value) => {
						this.plugin.settings.apiToken = value.trim();
						await this.plugin.saveSettings();
					})
			);

		new Setting(containerEl)
			.setName("Request timeout (ms)")
			.setDesc("HTTP 요청 제한 시간")
			.addText((text) =>
				text
					.setPlaceholder("30000")
					.setValue(String(this.plugin.settings.requestTimeoutMs))
					.onChange(async (value) => {
						const parsed = Number(value);
						this.plugin.settings.requestTimeoutMs =
							Number.isFinite(parsed) && parsed > 0 ? parsed : 30000;
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

		this.addRibbonIcon("bot", "Open Copilot chat", async () => {
			await this.activateSidebar();
		});

		this.addCommand({
			id: "open-copilot-chat",
			name: "Open chat sidebar",
			callback: async () => {
				await this.activateSidebar();
			}
		});

		this.addCommand({
			id: "test-server-connection",
			name: "Test server connection",
			callback: async () => {
				const ok = await this.pingServer();
				new Notice(ok ? "서버 연결 성공" : "서버 연결 실패");
			}
		});

		this.addCommand({
			id: "send-selected-text-to-ai",
			name: "Ask AI about selected text",
			editorCallback: async (editor) => {
				const selection = editor.getSelection().trim();
				if (!selection) {
					new Notice("먼저 텍스트를 선택하세요.");
					return;
				}

				try {
					const activeFile = this.app.workspace.getActiveFile();
					const reply = await this.callChatApi({
						message: `다음 텍스트를 분석해줘:\n\n${selection}`,
						context: selection,
						notePath: activeFile?.path
					});

					new Notice("응답을 사이드바에 표시합니다.");
					await this.activateSidebar();

					const leaf = this.app.workspace.getLeavesOfType(VIEW_TYPE_COPILOT)[0];
					if (leaf?.view instanceof CopilotSidebarView) {
						const view = leaf.view as CopilotSidebarView;
						view.contentEl.find(".copilot-output")?.setText(reply);
					}
				} catch (error) {
					const message =
						error instanceof Error ? error.message : String(error);
					new Notice(`AI 요청 실패: ${message}`);
				}
			}
		});

		this.addSettingTab(new CopilotSettingTab(this.app, this));
	}

	onunload(): void {
		this.app.workspace.detachLeavesOfType(VIEW_TYPE_COPILOT);
	}

	async loadSettings(): Promise<void> {
		this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
		this.settings.serverUrl = this.settings.serverUrl.replace(/\/+$/, "");
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
		const response = await this.safeRequest("/health", {
			method: "GET"
		});

		if (response.status >= 200 && response.status < 300) {
			try {
				const data = response.json as HealthResponse;
				if (typeof data?.ok === "boolean") return data.ok;
				return true;
			} catch {
				return true;
			}
		}

		return false;
	}

	async callChatApi(body: ChatRequestBody): Promise<string> {
		const response = await this.safeRequest("/api/ai/chat", {
			method: "POST",
			headers: {
				"Content-Type": "application/json"
			},
			body: JSON.stringify(body)
		});

		if (response.status < 200 || response.status >= 300) {
			throw new Error(`HTTP ${response.status}: ${response.text}`);
		}

		const data = response.json as ChatResponseBody;

		const reply =
			data.reply ??
			data.message ??
			data.output ??
			data.result;

		if (!reply || typeof reply !== "string") {
			throw new Error("응답 JSON에 reply/message/output/result 필드가 없습니다.");
		}

		return reply;
	}

	private async safeRequest(
		path: string,
		options: {
			method: string;
			headers?: Record<string, string>;
			body?: string;
		}
	): Promise<RequestUrlResponse> {
		const url = `${this.settings.serverUrl}${path}`;
		const headers: Record<string, string> = {
			...(options.headers ?? {})
		};

		if (this.settings.apiToken) {
			headers.Authorization = `Bearer ${this.settings.apiToken}`;
		}

		try {
			return await requestUrl({
				url,
				method: options.method,
				headers,
				body: options.body,
				throw: false,
				contentType: "application/json"
			});
		} catch (error) {
			const message = error instanceof Error ? error.message : String(error);
			throw new Error(`네트워크 요청 실패: ${message}`);
		}
	}

	async getActiveNoteContent(maxChars = 4000): Promise<string> {
		const file = this.app.workspace.getActiveFile();

		if (!(file instanceof TFile)) {
			return "";
		}

		const content = await this.app.vault.cachedRead(file);
		return content.length > maxChars ? content.slice(0, maxChars) : content;
	}
}
```

---

## `styles.css` 보강본

```css
.copilot-muted {
	opacity: 0.72;
	margin-bottom: 12px;
}

.copilot-actions {
	display: flex;
	gap: 8px;
	margin-bottom: 12px;
}

.copilot-file-info {
	margin-bottom: 8px;
	font-size: var(--font-ui-smaller);
	color: var(--text-muted);
}

.copilot-input {
	width: 100%;
	min-height: 120px;
	resize: vertical;
	margin-bottom: 12px;
}

.copilot-send {
	margin-bottom: 12px;
}

.copilot-output {
	white-space: pre-wrap;
	border: 1px solid var(--background-modifier-border);
	border-radius: 8px;
	padding: 12px;
	background: var(--background-secondary);
	min-height: 120px;
}

.workspace-leaf-content[data-type="copilot-sidebar"] .view-content {
	padding: 16px;
}
```

---

## 바뀐 핵심

### 1) `pingServer()`가 실제 HTTP 호출

이제 설정값 검사가 아니라 `GET /health`를 실제로 호출합니다.

### 2) `callChatApi()` 추가

사이드바 입력값과 현재 노트 컨텍스트를 서버로 보냅니다.

### 3) 선택 텍스트 명령 추가

에디터에서 선택 후 커맨드 실행하면 AI 요청이 가능합니다.

---

## 서버가 FastAPI/Express일 때 최소 예시

### Express

```js
app.get("/health", (req, res) => {
  res.json({ ok: true });
});

app.post("/api/ai/chat", async (req, res) => {
  const { message, context, notePath } = req.body;
  const reply = `받은 질문: ${message}\n노트: ${notePath ?? "-"}\n컨텍스트 길이: ${context?.length ?? 0}`;
  res.json({ reply });
});
```

### FastAPI

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class ChatBody(BaseModel):
    message: str
    context: str | None = None
    notePath: str | None = None

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/api/ai/chat")
def chat(body: ChatBody):
    return {
        "reply": f"받은 질문: {body.message}\n노트: {body.notePath or '-'}\n컨텍스트 길이: {len(body.context or '')}"
    }
```

---

## 설치·테스트 순서

1. `src/main.ts` 교체
2. `styles.css` 교체
3. `npm run build` 또는 `npm run dev`
4. 생성된 `main.js`를 vault의 `.obsidian/plugins/copilot-obsidian/`에 반영
5. Obsidian 재로드
6. Settings에서 `Server URL` 입력
7. `Test server connection` 실행

---

## 실무 주의점

* Obsidian 플러그인에서는 `fetch`보다 `requestUrl` 사용이 권장됩니다. ([Developer Documentation][2])
* 플러그인 설정값과 내부 데이터는 직접 파일 I/O보다 `loadData/saveData` 사용이 권장됩니다. ([Developer Documentation][2])
* 배포 시 저장소에 `main.js`를 항상 커밋하는 방식보다, 릴리스 산출물로 관리하는 패턴이 Obsidian 체크리스트에 더 가깝습니다. ([Developer Documentation][2])

원하면 다음 단계로 **스트리밍 응답(SSE/청크 폴링) 붙인 버전**까지 이어서 드리겠습니다.

[1]: https://docs.obsidian.md/Reference/TypeScript%2BAPI/requestUrl?utm_source=chatgpt.com "requestUrl - Developer Documentation"
[2]: https://docs.obsidian.md/oo/plugin "Obsidian October plugin self-critique checklist - Developer Documentation"
