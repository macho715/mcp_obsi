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
	TFile,
} from "obsidian";

const VIEW_TYPE_COPILOT = "copilot-sidebar";

interface CopilotPluginSettings {
	serverUrl: string;
	apiToken: string;
	requestTimeoutMs: number;
	maxVaultNotes: number;
	maxCharsPerNote: number;
	autoStartServer: boolean;
	serverCwd: string;
}

interface HealthResponse {
	ok?: boolean;
	status?: string;
}

interface ChatMessage {
	role: "system" | "user" | "assistant";
	content: string;
}

interface ChatRequestBody {
	message: string;
	context?: string;
	notePath?: string;
}

// Matches standalone /api/ai/chat response shape
interface ChatResponseBody {
	result?: {
		text?: string;
		model?: string | null;
		provider?: string;
		usage?: unknown;
	};
	requestId?: string;
	route?: string;
}

const DEFAULT_SETTINGS: CopilotPluginSettings = {
	serverUrl: "http://127.0.0.1:3010",
	apiToken: "",
	requestTimeoutMs: 30000,
	maxVaultNotes: 5,
	maxCharsPerNote: 2000,
	autoStartServer: false,
	serverCwd: "",
};

// ─── Vault search helpers ─────────────────────────────────────────────────────

/** 질문에서 의미 있는 단어만 추출 (조사·불용어 제거)
 *  한국어 단어는 1자도 핵심어일 수 있으므로 최소 길이를 1로 낮추고
 *  순수 영문·숫자는 2자 이상만 허용한다.
 */
function extractKeywords(query: string): string[] {
	const stopwords = new Set([
		"이", "가", "은", "는", "을", "를", "의", "에", "에서", "로", "으로",
		"와", "과", "도", "만", "이다", "있다", "없다", "하다", "되다",
		"the", "a", "an", "is", "are", "was", "were", "what", "how",
		"when", "where", "why", "who", "that", "this", "it", "in",
		"of", "for", "on", "with", "as", "by", "to", "and", "or",
	]);
	const isKorean = (w: string) => /[\uAC00-\uD7A3]/.test(w);
	return query
		.toLowerCase()
		.replace(/[?！？。.,!]/g, " ")
		.split(/\s+/)
		.map((w) => w.trim())
		.filter((w) => {
			if (!w) return false;
			if (stopwords.has(w)) return false;
			// 한국어 포함 토큰: 1자 이상 허용
			if (isKorean(w)) return w.length >= 1;
			// 영문·숫자만: 2자 이상
			return w.length >= 2;
		});
}

/** 텍스트 안에서 keyword와 일치하는 횟수를 점수로 반환 */
function scoreText(text: string, keywords: string[]): number {
	if (!keywords.length) return 0;
	const lower = text.toLowerCase();
	return keywords.reduce((sum, kw) => {
		let count = 0;
		let pos = 0;
		while ((pos = lower.indexOf(kw, pos)) !== -1) {
			count++;
			pos += kw.length;
		}
		return sum + count;
	}, 0);
}

/** 텍스트에서 keyword가 처음 등장하는 주변 snippet 추출 */
function extractSnippet(text: string, keywords: string[], maxChars: number): string {
	if (text.length <= maxChars) return text;
	const lower = text.toLowerCase();
	let firstHit = -1;
	for (const kw of keywords) {
		const pos = lower.indexOf(kw);
		if (pos !== -1 && (firstHit === -1 || pos < firstHit)) {
			firstHit = pos;
		}
	}
	const start = Math.max(0, (firstHit === -1 ? 0 : firstHit) - 200);
	return (start > 0 ? "..." : "") + text.slice(start, start + maxChars);
}

// ─── Sidebar View ─────────────────────────────────────────────────────────────

class CopilotSidebarView extends ItemView {
	plugin: CopilotObsidianPlugin;
	private inputEl: HTMLTextAreaElement | null = null;
	private outputEl: HTMLDivElement | null = null;
	private sendButtonEl: HTMLButtonElement | null = null;
	private statusEl: HTMLDivElement | null = null;

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
			text: "Vault 노트 내용을 기반으로 질문에 답변합니다.",
		});
		descEl.addClass("copilot-muted");

		const actionsEl = contentEl.createDiv({ cls: "copilot-actions" });

		const healthBtn = actionsEl.createEl("button", {
			text: "서버 연결 테스트",
			cls: "mod-cta",
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

		const vaultStats = contentEl.createDiv({ cls: "copilot-file-info" });
		const fileCount = this.plugin.app.vault.getMarkdownFiles().length;
		vaultStats.setText(`Vault 노트 수: ${fileCount}개 검색 가능`);

		this.statusEl = contentEl.createDiv({ cls: "copilot-status" });
		this.statusEl.style.display = "none";

		this.inputEl = contentEl.createEl("textarea", {
			placeholder: "vault 내용에 대해 질문하세요 (Ctrl+Enter 전송)",
		});
		this.inputEl.addClass("copilot-input");

		this.sendButtonEl = contentEl.createEl("button", {
			text: "전송",
			cls: "mod-cta",
		});
		this.sendButtonEl.addClass("copilot-send");

		// 출력 헤더: 레이블 + 복사 버튼
		const outputHeaderEl = contentEl.createDiv({ cls: "copilot-output-header" });
		outputHeaderEl.createSpan({ text: "답변", cls: "copilot-output-label" });
		const copyBtn = outputHeaderEl.createEl("button", {
			text: "복사",
			cls: "copilot-copy-btn",
		});
		copyBtn.addEventListener("click", async () => {
			const text = this.outputEl?.getText() ?? "";
			if (!text || text === "응답이 여기에 표시됩니다.") {
				new Notice("복사할 내용이 없습니다.");
				return;
			}
			await navigator.clipboard.writeText(text);
			copyBtn.setText("✓ 복사됨");
			setTimeout(() => copyBtn.setText("복사"), 1500);
		});

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

	setStatus(text: string | null): void {
		if (!this.statusEl) return;
		if (text) {
			this.statusEl.setText(text);
			this.statusEl.style.display = "block";
		} else {
			this.statusEl.style.display = "none";
		}
	}

	private async handleSend(): Promise<void> {
		if (!this.inputEl || !this.outputEl || !this.sendButtonEl) return;

		const message = this.inputEl.value.trim();
		if (!message) {
			new Notice("질문을 입력하세요.");
			return;
		}

		this.sendButtonEl.disabled = true;

		try {
			// 1단계: vault에서 관련 노트 검색
			this.setStatus("🔍 Vault에서 관련 노트 검색 중...");
			this.outputEl.setText("");

			const { context, sourceNames } = await this.plugin.searchVaultContext(message);

			// 2단계: AI 답변 요청
			this.setStatus(
				`📚 ${sourceNames.length}개 노트 참고하여 답변 생성 중...`
			);

			const activeFile = this.plugin.app.workspace.getActiveFile();

			let reply: string;
			let usedSources = sourceNames;

			try {
				reply = await this.plugin.callChatApi({
					message,
					context,
					notePath: activeFile?.path,
				});
			} catch (firstError) {
				// DLP 차단 시 → vault 컨텍스트 제거하고 재시도
				const isDlp =
					firstError instanceof Error &&
					(firstError as Error & { isDlpBlocked?: boolean }).isDlpBlocked;

				if (!isDlp) throw firstError;

				this.setStatus(
					"⚠️ vault 내용에 민감 데이터 감지 — 컨텍스트 없이 재시도 중..."
				);
				usedSources = [];

				reply = await this.plugin.callChatApi({
					message,
					notePath: activeFile?.path,
				});
			}

			this.setStatus(null);

			// 참고 노트 목록 표시
			const sourceLine =
				usedSources.length > 0
					? `\n\n─── 참고 노트 (${usedSources.length}개) ───\n${usedSources.map((n) => `• ${n}`).join("\n")}`
					: "";

			this.outputEl.setText(reply + sourceLine);
		} catch (error) {
			const messageText =
				error instanceof Error ? error.message : String(error);
			this.setStatus(null);
			this.outputEl.setText(`오류: ${messageText}`);
			new Notice("채팅 요청 실패");
		} finally {
			if (this.sendButtonEl) {
				this.sendButtonEl.disabled = false;
			}
		}
	}
}

// ─── Settings Tab ─────────────────────────────────────────────────────────────

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
						this.plugin.settings.serverUrl = value
							.trim()
							.replace(/\/+$/, "");
						await this.plugin.saveSettings();
					})
			);

		new Setting(containerEl)
			.setName("API token")
			.setDesc("필요 시 Bearer token (MYAGENT_PROXY_AUTH_TOKEN)")
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

		new Setting(containerEl)
			.setName("Vault 검색: 최대 노트 수")
			.setDesc("질문과 관련된 노트를 최대 몇 개까지 참고할지 (기본 5)")
			.addText((text) =>
				text
					.setPlaceholder("5")
					.setValue(String(this.plugin.settings.maxVaultNotes))
					.onChange(async (value) => {
						const parsed = Number(value);
						this.plugin.settings.maxVaultNotes =
							Number.isFinite(parsed) && parsed > 0 && parsed <= 20
								? parsed
								: 5;
						await this.plugin.saveSettings();
					})
			);

		new Setting(containerEl)
			.setName("Vault 검색: 노트당 최대 글자 수")
			.setDesc("노트 1개당 AI에게 전달할 최대 글자 수 (기본 2000)")
			.addText((text) =>
				text
					.setPlaceholder("2000")
					.setValue(String(this.plugin.settings.maxCharsPerNote))
					.onChange(async (value) => {
						const parsed = Number(value);
						this.plugin.settings.maxCharsPerNote =
							Number.isFinite(parsed) && parsed >= 200
								? parsed
								: 2000;
						await this.plugin.saveSettings();
					})
			);

		containerEl.createEl("h3", { text: "서버 자동 시작" });

		new Setting(containerEl)
			.setName("Obsidian 시작 시 서버 자동 기동")
			.setDesc("플러그인 로드 시 standalone 서버를 자동으로 시작합니다. 아래 경로를 반드시 입력하세요.")
			.addToggle((toggle) =>
				toggle
					.setValue(this.plugin.settings.autoStartServer)
					.onChange(async (value) => {
						this.plugin.settings.autoStartServer = value;
						await this.plugin.saveSettings();
					})
			);

		new Setting(containerEl)
			.setName("서버 폴더 경로 (serverCwd)")
			.setDesc("standalone-package 폴더의 절대 경로 (예: C:\\Users\\SAMSUNG\\Downloads\\mcp_obsi-main\\myagent-copilot-kit\\standalone-package)")
			.addText((text) =>
				text
					.setPlaceholder("C:\\...\\standalone-package")
					.setValue(this.plugin.settings.serverCwd)
					.onChange(async (value) => {
						this.plugin.settings.serverCwd = value.trim();
						await this.plugin.saveSettings();
					})
			);
	}
}

// ─── Main Plugin ──────────────────────────────────────────────────────────────

export default class CopilotObsidianPlugin extends Plugin {
	settings!: CopilotPluginSettings;
	private serverProc: ReturnType<typeof import("child_process").spawn> | null = null;

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
			},
		});

		this.addCommand({
			id: "test-server-connection",
			name: "Test server connection",
			callback: async () => {
				const ok = await this.pingServer();
				new Notice(ok ? "서버 연결 성공" : "서버 연결 실패");
			},
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
					const { context } = await this.searchVaultContext(selection);
					const reply = await this.callChatApi({
						message: `다음 텍스트를 분석해줘:\n\n${selection}`,
						context,
						notePath: activeFile?.path,
					});

					new Notice("응답을 사이드바에 표시합니다.");
					await this.activateSidebar();

					const leaf =
						this.app.workspace.getLeavesOfType(VIEW_TYPE_COPILOT)[0];
					if (leaf?.view instanceof CopilotSidebarView) {
						(leaf.view as CopilotSidebarView).contentEl
							.find(".copilot-output")
							?.setText(reply);
					}
				} catch (error) {
					const message =
						error instanceof Error ? error.message : String(error);
					new Notice(`AI 요청 실패: ${message}`);
				}
			},
		});

		this.addSettingTab(new CopilotSettingTab(this.app, this));

		// 서버 자동 기동: 설정 활성화 + cwd 지정 + 서버가 아직 응답 없을 때만
		if (this.settings.autoStartServer && this.settings.serverCwd.trim()) {
			this.app.workspace.onLayoutReady(() => {
				this.ensureServerRunning();
			});
		}
	}

	/** 서버가 응답 없으면 spawn으로 기동, 이미 살아있으면 스킵 */
	private async ensureServerRunning(): Promise<void> {
		const alive = await this.pingServer();
		if (alive) return;

		try {
			const { spawn } = require("child_process") as typeof import("child_process");
			this.serverProc = spawn(
				"npm",
				["run", "serve:local"],
				{
					cwd: this.settings.serverCwd,
					detached: false,
					shell: true,
					windowsHide: true,
				}
			);

			this.serverProc.on("error", (err: Error) => {
				console.error("[Copilot] server spawn error:", err.message);
			});

			// 최대 30초간 2초마다 ping 재시도
			const MAX_WAIT_MS = 30_000;
			const INTERVAL_MS = 2_000;
			const steps = MAX_WAIT_MS / INTERVAL_MS;

			for (let i = 0; i < steps; i++) {
				await new Promise((r) => setTimeout(r, INTERVAL_MS));
				if (await this.pingServer()) {
					new Notice("Copilot 서버 자동 시작 완료");
					return;
				}
			}
			new Notice("Copilot 서버 시작 시간 초과 (30s) — 수동으로 확인하세요.");
		} catch (err) {
			console.error("[Copilot] ensureServerRunning:", err);
		}
	}

	onunload(): void {
		this.app.workspace.detachLeavesOfType(VIEW_TYPE_COPILOT);
		// 플러그인이 직접 띄운 서버는 같이 종료
		if (this.serverProc) {
			try { this.serverProc.kill(); } catch { /* ignore */ }
			this.serverProc = null;
		}
	}

	async loadSettings(): Promise<void> {
		this.settings = Object.assign(
			{},
			DEFAULT_SETTINGS,
			await this.loadData()
		);
		this.settings.serverUrl = this.settings.serverUrl.replace(/\/+$/, "");
	}

	async saveSettings(): Promise<void> {
		await this.saveData(this.settings);
	}

	async activateSidebar(): Promise<void> {
		const { workspace } = this.app;
		let leaf = workspace.getLeavesOfType(VIEW_TYPE_COPILOT)[0];

		if (!leaf) {
			const rightLeaf = workspace.getRightLeaf(false);
			if (!rightLeaf) {
				new Notice("사이드바를 열 수 없습니다.");
				return;
			}
			await rightLeaf.setViewState({ type: VIEW_TYPE_COPILOT, active: true });
			leaf = rightLeaf;
		}

		workspace.revealLeaf(leaf);
	}

	/**
	 * Vault 전체에서 질문과 관련된 노트를 키워드 검색으로 찾아
	 * AI 컨텍스트 문자열과 참고 노트 이름 목록을 반환한다.
	 */
	async searchVaultContext(query: string): Promise<{
		context: string;
		sourceNames: string[];
	}> {
		const keywords = extractKeywords(query);
		const files = this.app.vault.getMarkdownFiles();

		if (!files.length) {
			return { context: "", sourceNames: [] };
		}

		// 활성 노트는 항상 포함
		const activeFile = this.app.workspace.getActiveFile();

		// 점수 계산: 최근 수정 파일 우선 + maxVaultNotes*10 범위까지 스캔
		const scanLimit = Math.min(files.length, this.settings.maxVaultNotes * 10);
		// 최근 수정 순으로 정렬해 관련 가능성이 높은 파일을 먼저 스캔
		const sortedFiles = [...files]
			.sort((a, b) => (b.stat?.mtime ?? 0) - (a.stat?.mtime ?? 0));
		const sampleFiles = sortedFiles.slice(0, scanLimit);
		const candidates: Array<{ file: TFile; score: number; content: string }> = [];

		for (const file of sampleFiles) {
			try {
				const content = await this.app.vault.cachedRead(file);
				// 활성 노트는 score를 높게 줘서 항상 상위에
				const bonus = file.path === activeFile?.path ? 100 : 0;
				const score = scoreText(content, keywords) + scoreText(file.basename, keywords) * 3 + bonus;
				if (score > 0 || file.path === activeFile?.path) {
					candidates.push({ file, score, content });
				}
			} catch {
				// 읽기 실패 파일은 건너뜀
			}
		}

		// 점수 내림차순 정렬 후 상위 N개
		candidates.sort((a, b) => b.score - a.score);
		const topN = candidates.slice(0, this.settings.maxVaultNotes);

		if (!topN.length) {
			// 관련 노트 없으면 활성 노트만 반환
			try {
				const fallback = activeFile
					? await this.getActiveNoteContent(this.settings.maxCharsPerNote)
					: "";
				return {
					context: fallback,
					sourceNames: activeFile ? [activeFile.basename] : [],
				};
			} catch {
				return { context: "", sourceNames: [] };
			}
		}

		const parts = topN.map(({ file, content }) => {
			const snippet = extractSnippet(content, keywords, this.settings.maxCharsPerNote);
			return `--- [${file.basename}] ---\n${snippet}`;
		});

		return {
			context: parts.join("\n\n"),
			sourceNames: topN.map(({ file }) => file.basename),
		};
	}

	// endpoint: /api/ai/health (standalone server contract)
	async pingServer(): Promise<boolean> {
		const response = await this.safeRequest("/api/ai/health", {
			method: "GET",
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

	// body: OpenAI messages array / response: data.result.text
	async callChatApi(body: ChatRequestBody): Promise<string> {
		const systemParts: string[] = [];
		if (body.context) {
			systemParts.push(
				`아래는 사용자의 Obsidian vault에서 질문과 관련된 노트 내용입니다. 이를 바탕으로 답변하세요.\n\n${body.context}`
			);
		}
		if (body.notePath) {
			systemParts.push(`현재 열린 노트: ${body.notePath}`);
		}

		const messages: ChatMessage[] = [];
		if (systemParts.length > 0) {
			messages.push({ role: "system", content: systemParts.join("\n") });
		}
		messages.push({ role: "user", content: body.message });

		const response = await this.safeRequest("/api/ai/chat", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			// routeHint: "copilot" → DLP sanitize 이후에도 local runner 우회, Copilot으로 강제 라우팅
			body: JSON.stringify({ messages, routeHint: "copilot" }),
		});

		// DLP 차단은 별도 에러로 분리해 호출 측에서 재시도 가능하게 함
		if (response.status === 422) {
			const errData = response.json as { error?: string; detail?: string };
			if (errData?.error === "DLP_BLOCKED") {
				const err = new Error("DLP_BLOCKED") as Error & { isDlpBlocked: boolean };
				err.isDlpBlocked = true;
				throw err;
			}
		}

		if (response.status < 200 || response.status >= 300) {
			throw new Error(`HTTP ${response.status}: ${response.text}`);
		}

		const data = response.json as ChatResponseBody;
		const text = data?.result?.text;

		if (!text || typeof text !== "string") {
			throw new Error(
				"응답 JSON에 result.text 필드가 없거나 비어있습니다."
			);
		}

		return text;
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
		const headers: Record<string, string> = { ...(options.headers ?? {}) };

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
				contentType: "application/json",
			});
		} catch (error) {
			const message =
				error instanceof Error ? error.message : String(error);
			throw new Error(`네트워크 요청 실패: ${message}`);
		}
	}

	async getActiveNoteContent(maxChars = 4000): Promise<string> {
		const file = this.app.workspace.getActiveFile();
		if (!(file instanceof TFile)) return "";
		const content = await this.app.vault.cachedRead(file);
		return content.length > maxChars ? content.slice(0, maxChars) : content;
	}
}
