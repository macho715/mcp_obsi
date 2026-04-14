"use strict";
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// src/main.ts
var main_exports = {};
__export(main_exports, {
  default: () => CopilotObsidianPlugin
});
module.exports = __toCommonJS(main_exports);
var import_obsidian = require("obsidian");
var VIEW_TYPE_COPILOT = "copilot-sidebar";
var DEFAULT_SETTINGS = {
  serverUrl: "http://127.0.0.1:3010",
  apiToken: "",
  requestTimeoutMs: 3e4,
  maxVaultNotes: 5,
  maxCharsPerNote: 2e3,
  autoStartServer: false,
  serverCwd: ""
};
function extractKeywords(query) {
  const stopwords = /* @__PURE__ */ new Set([
    "\uC774",
    "\uAC00",
    "\uC740",
    "\uB294",
    "\uC744",
    "\uB97C",
    "\uC758",
    "\uC5D0",
    "\uC5D0\uC11C",
    "\uB85C",
    "\uC73C\uB85C",
    "\uC640",
    "\uACFC",
    "\uB3C4",
    "\uB9CC",
    "\uC774\uB2E4",
    "\uC788\uB2E4",
    "\uC5C6\uB2E4",
    "\uD558\uB2E4",
    "\uB418\uB2E4",
    "the",
    "a",
    "an",
    "is",
    "are",
    "was",
    "were",
    "what",
    "how",
    "when",
    "where",
    "why",
    "who",
    "that",
    "this",
    "it",
    "in",
    "of",
    "for",
    "on",
    "with",
    "as",
    "by",
    "to",
    "and",
    "or"
  ]);
  const isKorean = (w) => /[\uAC00-\uD7A3]/.test(w);
  return query.toLowerCase().replace(/[?！？。.,!]/g, " ").split(/\s+/).map((w) => w.trim()).filter((w) => {
    if (!w) return false;
    if (stopwords.has(w)) return false;
    if (isKorean(w)) return w.length >= 1;
    return w.length >= 2;
  });
}
function scoreText(text, keywords) {
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
function extractSnippet(text, keywords, maxChars) {
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
var CopilotSidebarView = class extends import_obsidian.ItemView {
  constructor(leaf, plugin) {
    super(leaf);
    this.inputEl = null;
    this.outputEl = null;
    this.sendButtonEl = null;
    this.statusEl = null;
    this.plugin = plugin;
  }
  getViewType() {
    return VIEW_TYPE_COPILOT;
  }
  getDisplayText() {
    return "Copilot Chat";
  }
  getIcon() {
    return "messages-square";
  }
  async onOpen() {
    const { contentEl } = this;
    contentEl.empty();
    contentEl.createEl("h3", { text: "Copilot Chat" });
    const descEl = contentEl.createEl("div", {
      text: "Vault \uB178\uD2B8 \uB0B4\uC6A9\uC744 \uAE30\uBC18\uC73C\uB85C \uC9C8\uBB38\uC5D0 \uB2F5\uBCC0\uD569\uB2C8\uB2E4."
    });
    descEl.addClass("copilot-muted");
    const actionsEl = contentEl.createDiv({ cls: "copilot-actions" });
    const healthBtn = actionsEl.createEl("button", {
      text: "\uC11C\uBC84 \uC5F0\uACB0 \uD14C\uC2A4\uD2B8",
      cls: "mod-cta"
    });
    healthBtn.addEventListener("click", async () => {
      healthBtn.disabled = true;
      try {
        const ok = await this.plugin.pingServer();
        new import_obsidian.Notice(ok ? "\uC11C\uBC84 \uC5F0\uACB0 \uC131\uACF5" : "\uC11C\uBC84 \uC5F0\uACB0 \uC2E4\uD328");
      } finally {
        healthBtn.disabled = false;
      }
    });
    const vaultStats = contentEl.createDiv({ cls: "copilot-file-info" });
    const fileCount = this.plugin.app.vault.getMarkdownFiles().length;
    vaultStats.setText(`Vault \uB178\uD2B8 \uC218: ${fileCount}\uAC1C \uAC80\uC0C9 \uAC00\uB2A5`);
    this.statusEl = contentEl.createDiv({ cls: "copilot-status" });
    this.statusEl.style.display = "none";
    this.inputEl = contentEl.createEl("textarea", {
      placeholder: "vault \uB0B4\uC6A9\uC5D0 \uB300\uD574 \uC9C8\uBB38\uD558\uC138\uC694 (Ctrl+Enter \uC804\uC1A1)"
    });
    this.inputEl.addClass("copilot-input");
    this.sendButtonEl = contentEl.createEl("button", {
      text: "\uC804\uC1A1",
      cls: "mod-cta"
    });
    this.sendButtonEl.addClass("copilot-send");
    const outputHeaderEl = contentEl.createDiv({ cls: "copilot-output-header" });
    outputHeaderEl.createSpan({ text: "\uB2F5\uBCC0", cls: "copilot-output-label" });
    const copyBtn = outputHeaderEl.createEl("button", {
      text: "\uBCF5\uC0AC",
      cls: "copilot-copy-btn"
    });
    copyBtn.addEventListener("click", async () => {
      var _a, _b;
      const text = (_b = (_a = this.outputEl) == null ? void 0 : _a.getText()) != null ? _b : "";
      if (!text || text === "\uC751\uB2F5\uC774 \uC5EC\uAE30\uC5D0 \uD45C\uC2DC\uB429\uB2C8\uB2E4.") {
        new import_obsidian.Notice("\uBCF5\uC0AC\uD560 \uB0B4\uC6A9\uC774 \uC5C6\uC2B5\uB2C8\uB2E4.");
        return;
      }
      await navigator.clipboard.writeText(text);
      copyBtn.setText("\u2713 \uBCF5\uC0AC\uB428");
      setTimeout(() => copyBtn.setText("\uBCF5\uC0AC"), 1500);
    });
    this.outputEl = contentEl.createDiv({ cls: "copilot-output" });
    this.outputEl.setText("\uC751\uB2F5\uC774 \uC5EC\uAE30\uC5D0 \uD45C\uC2DC\uB429\uB2C8\uB2E4.");
    this.sendButtonEl.addEventListener("click", async () => {
      await this.handleSend();
    });
    this.inputEl.addEventListener("keydown", async (evt) => {
      if (evt.key === "Enter" && (evt.ctrlKey || evt.metaKey)) {
        evt.preventDefault();
        await this.handleSend();
      }
    });
  }
  async onClose() {
    this.contentEl.empty();
  }
  setStatus(text) {
    if (!this.statusEl) return;
    if (text) {
      this.statusEl.setText(text);
      this.statusEl.style.display = "block";
    } else {
      this.statusEl.style.display = "none";
    }
  }
  async handleSend() {
    if (!this.inputEl || !this.outputEl || !this.sendButtonEl) return;
    const message = this.inputEl.value.trim();
    if (!message) {
      new import_obsidian.Notice("\uC9C8\uBB38\uC744 \uC785\uB825\uD558\uC138\uC694.");
      return;
    }
    this.sendButtonEl.disabled = true;
    try {
      this.setStatus("\u{1F50D} Vault\uC5D0\uC11C \uAD00\uB828 \uB178\uD2B8 \uAC80\uC0C9 \uC911...");
      this.outputEl.setText("");
      const { context, sourceNames } = await this.plugin.searchVaultContext(message);
      this.setStatus(
        `\u{1F4DA} ${sourceNames.length}\uAC1C \uB178\uD2B8 \uCC38\uACE0\uD558\uC5EC \uB2F5\uBCC0 \uC0DD\uC131 \uC911...`
      );
      const activeFile = this.plugin.app.workspace.getActiveFile();
      let reply;
      let usedSources = sourceNames;
      try {
        reply = await this.plugin.callChatApi({
          message,
          context,
          notePath: activeFile == null ? void 0 : activeFile.path
        });
      } catch (firstError) {
        const isDlp = firstError instanceof Error && firstError.isDlpBlocked;
        if (!isDlp) throw firstError;
        this.setStatus(
          "\u26A0\uFE0F vault \uB0B4\uC6A9\uC5D0 \uBBFC\uAC10 \uB370\uC774\uD130 \uAC10\uC9C0 \u2014 \uCEE8\uD14D\uC2A4\uD2B8 \uC5C6\uC774 \uC7AC\uC2DC\uB3C4 \uC911..."
        );
        usedSources = [];
        reply = await this.plugin.callChatApi({
          message,
          notePath: activeFile == null ? void 0 : activeFile.path
        });
      }
      this.setStatus(null);
      const sourceLine = usedSources.length > 0 ? `

\u2500\u2500\u2500 \uCC38\uACE0 \uB178\uD2B8 (${usedSources.length}\uAC1C) \u2500\u2500\u2500
${usedSources.map((n) => `\u2022 ${n}`).join("\n")}` : "";
      this.outputEl.setText(reply + sourceLine);
    } catch (error) {
      const messageText = error instanceof Error ? error.message : String(error);
      this.setStatus(null);
      this.outputEl.setText(`\uC624\uB958: ${messageText}`);
      new import_obsidian.Notice("\uCC44\uD305 \uC694\uCCAD \uC2E4\uD328");
    } finally {
      if (this.sendButtonEl) {
        this.sendButtonEl.disabled = false;
      }
    }
  }
};
var CopilotSettingTab = class extends import_obsidian.PluginSettingTab {
  constructor(app, plugin) {
    super(app, plugin);
    this.plugin = plugin;
  }
  display() {
    const { containerEl } = this;
    containerEl.empty();
    new import_obsidian.Setting(containerEl).setName("Server URL").setDesc("\uC608: http://127.0.0.1:3010").addText(
      (text) => text.setPlaceholder("http://127.0.0.1:3010").setValue(this.plugin.settings.serverUrl).onChange(async (value) => {
        this.plugin.settings.serverUrl = value.trim().replace(/\/+$/, "");
        await this.plugin.saveSettings();
      })
    );
    new import_obsidian.Setting(containerEl).setName("API token").setDesc("\uD544\uC694 \uC2DC Bearer token (MYAGENT_PROXY_AUTH_TOKEN)").addText(
      (text) => text.setPlaceholder("token").setValue(this.plugin.settings.apiToken).onChange(async (value) => {
        this.plugin.settings.apiToken = value.trim();
        await this.plugin.saveSettings();
      })
    );
    new import_obsidian.Setting(containerEl).setName("Request timeout (ms)").setDesc("HTTP \uC694\uCCAD \uC81C\uD55C \uC2DC\uAC04").addText(
      (text) => text.setPlaceholder("30000").setValue(String(this.plugin.settings.requestTimeoutMs)).onChange(async (value) => {
        const parsed = Number(value);
        this.plugin.settings.requestTimeoutMs = Number.isFinite(parsed) && parsed > 0 ? parsed : 3e4;
        await this.plugin.saveSettings();
      })
    );
    new import_obsidian.Setting(containerEl).setName("Vault \uAC80\uC0C9: \uCD5C\uB300 \uB178\uD2B8 \uC218").setDesc("\uC9C8\uBB38\uACFC \uAD00\uB828\uB41C \uB178\uD2B8\uB97C \uCD5C\uB300 \uBA87 \uAC1C\uAE4C\uC9C0 \uCC38\uACE0\uD560\uC9C0 (\uAE30\uBCF8 5)").addText(
      (text) => text.setPlaceholder("5").setValue(String(this.plugin.settings.maxVaultNotes)).onChange(async (value) => {
        const parsed = Number(value);
        this.plugin.settings.maxVaultNotes = Number.isFinite(parsed) && parsed > 0 && parsed <= 20 ? parsed : 5;
        await this.plugin.saveSettings();
      })
    );
    new import_obsidian.Setting(containerEl).setName("Vault \uAC80\uC0C9: \uB178\uD2B8\uB2F9 \uCD5C\uB300 \uAE00\uC790 \uC218").setDesc("\uB178\uD2B8 1\uAC1C\uB2F9 AI\uC5D0\uAC8C \uC804\uB2EC\uD560 \uCD5C\uB300 \uAE00\uC790 \uC218 (\uAE30\uBCF8 2000)").addText(
      (text) => text.setPlaceholder("2000").setValue(String(this.plugin.settings.maxCharsPerNote)).onChange(async (value) => {
        const parsed = Number(value);
        this.plugin.settings.maxCharsPerNote = Number.isFinite(parsed) && parsed >= 200 ? parsed : 2e3;
        await this.plugin.saveSettings();
      })
    );
    containerEl.createEl("h3", { text: "\uC11C\uBC84 \uC790\uB3D9 \uC2DC\uC791" });
    new import_obsidian.Setting(containerEl).setName("Obsidian \uC2DC\uC791 \uC2DC \uC11C\uBC84 \uC790\uB3D9 \uAE30\uB3D9").setDesc("\uD50C\uB7EC\uADF8\uC778 \uB85C\uB4DC \uC2DC standalone \uC11C\uBC84\uB97C \uC790\uB3D9\uC73C\uB85C \uC2DC\uC791\uD569\uB2C8\uB2E4. \uC544\uB798 \uACBD\uB85C\uB97C \uBC18\uB4DC\uC2DC \uC785\uB825\uD558\uC138\uC694.").addToggle(
      (toggle) => toggle.setValue(this.plugin.settings.autoStartServer).onChange(async (value) => {
        this.plugin.settings.autoStartServer = value;
        await this.plugin.saveSettings();
      })
    );
    new import_obsidian.Setting(containerEl).setName("\uC11C\uBC84 \uD3F4\uB354 \uACBD\uB85C (serverCwd)").setDesc("standalone-package \uD3F4\uB354\uC758 \uC808\uB300 \uACBD\uB85C (\uC608: C:\\Users\\SAMSUNG\\Downloads\\mcp_obsi-main\\myagent-copilot-kit\\standalone-package)").addText(
      (text) => text.setPlaceholder("C:\\...\\standalone-package").setValue(this.plugin.settings.serverCwd).onChange(async (value) => {
        this.plugin.settings.serverCwd = value.trim();
        await this.plugin.saveSettings();
      })
    );
  }
};
var CopilotObsidianPlugin = class extends import_obsidian.Plugin {
  constructor() {
    super(...arguments);
    this.serverProc = null;
  }
  async onload() {
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
        new import_obsidian.Notice(ok ? "\uC11C\uBC84 \uC5F0\uACB0 \uC131\uACF5" : "\uC11C\uBC84 \uC5F0\uACB0 \uC2E4\uD328");
      }
    });
    this.addCommand({
      id: "send-selected-text-to-ai",
      name: "Ask AI about selected text",
      editorCallback: async (editor) => {
        var _a;
        const selection = editor.getSelection().trim();
        if (!selection) {
          new import_obsidian.Notice("\uBA3C\uC800 \uD14D\uC2A4\uD2B8\uB97C \uC120\uD0DD\uD558\uC138\uC694.");
          return;
        }
        try {
          const activeFile = this.app.workspace.getActiveFile();
          const { context } = await this.searchVaultContext(selection);
          const reply = await this.callChatApi({
            message: `\uB2E4\uC74C \uD14D\uC2A4\uD2B8\uB97C \uBD84\uC11D\uD574\uC918:

${selection}`,
            context,
            notePath: activeFile == null ? void 0 : activeFile.path
          });
          new import_obsidian.Notice("\uC751\uB2F5\uC744 \uC0AC\uC774\uB4DC\uBC14\uC5D0 \uD45C\uC2DC\uD569\uB2C8\uB2E4.");
          await this.activateSidebar();
          const leaf = this.app.workspace.getLeavesOfType(VIEW_TYPE_COPILOT)[0];
          if ((leaf == null ? void 0 : leaf.view) instanceof CopilotSidebarView) {
            (_a = leaf.view.contentEl.find(".copilot-output")) == null ? void 0 : _a.setText(reply);
          }
        } catch (error) {
          const message = error instanceof Error ? error.message : String(error);
          new import_obsidian.Notice(`AI \uC694\uCCAD \uC2E4\uD328: ${message}`);
        }
      }
    });
    this.addSettingTab(new CopilotSettingTab(this.app, this));
    if (this.settings.autoStartServer && this.settings.serverCwd.trim()) {
      this.app.workspace.onLayoutReady(() => {
        this.ensureServerRunning();
      });
    }
  }
  /** 서버가 응답 없으면 spawn으로 기동, 이미 살아있으면 스킵 */
  async ensureServerRunning() {
    const alive = await this.pingServer();
    if (alive) return;
    try {
      const { spawn } = require("child_process");
      this.serverProc = spawn(
        "npm",
        ["run", "serve:local"],
        {
          cwd: this.settings.serverCwd,
          detached: false,
          shell: true,
          windowsHide: true
        }
      );
      this.serverProc.on("error", (err) => {
        console.error("[Copilot] server spawn error:", err.message);
      });
      const MAX_WAIT_MS = 3e4;
      const INTERVAL_MS = 2e3;
      const steps = MAX_WAIT_MS / INTERVAL_MS;
      for (let i = 0; i < steps; i++) {
        await new Promise((r) => setTimeout(r, INTERVAL_MS));
        if (await this.pingServer()) {
          new import_obsidian.Notice("Copilot \uC11C\uBC84 \uC790\uB3D9 \uC2DC\uC791 \uC644\uB8CC");
          return;
        }
      }
      new import_obsidian.Notice("Copilot \uC11C\uBC84 \uC2DC\uC791 \uC2DC\uAC04 \uCD08\uACFC (30s) \u2014 \uC218\uB3D9\uC73C\uB85C \uD655\uC778\uD558\uC138\uC694.");
    } catch (err) {
      console.error("[Copilot] ensureServerRunning:", err);
    }
  }
  onunload() {
    this.app.workspace.detachLeavesOfType(VIEW_TYPE_COPILOT);
    if (this.serverProc) {
      try {
        this.serverProc.kill();
      } catch (e) {
      }
      this.serverProc = null;
    }
  }
  async loadSettings() {
    this.settings = Object.assign(
      {},
      DEFAULT_SETTINGS,
      await this.loadData()
    );
    this.settings.serverUrl = this.settings.serverUrl.replace(/\/+$/, "");
  }
  async saveSettings() {
    await this.saveData(this.settings);
  }
  async activateSidebar() {
    const { workspace } = this.app;
    let leaf = workspace.getLeavesOfType(VIEW_TYPE_COPILOT)[0];
    if (!leaf) {
      const rightLeaf = workspace.getRightLeaf(false);
      if (!rightLeaf) {
        new import_obsidian.Notice("\uC0AC\uC774\uB4DC\uBC14\uB97C \uC5F4 \uC218 \uC5C6\uC2B5\uB2C8\uB2E4.");
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
  async searchVaultContext(query) {
    const keywords = extractKeywords(query);
    const files = this.app.vault.getMarkdownFiles();
    if (!files.length) {
      return { context: "", sourceNames: [] };
    }
    const activeFile = this.app.workspace.getActiveFile();
    const scanLimit = Math.min(files.length, this.settings.maxVaultNotes * 10);
    const sortedFiles = [...files].sort((a, b) => {
      var _a, _b, _c, _d;
      return ((_b = (_a = b.stat) == null ? void 0 : _a.mtime) != null ? _b : 0) - ((_d = (_c = a.stat) == null ? void 0 : _c.mtime) != null ? _d : 0);
    });
    const sampleFiles = sortedFiles.slice(0, scanLimit);
    const candidates = [];
    for (const file of sampleFiles) {
      try {
        const content = await this.app.vault.cachedRead(file);
        const bonus = file.path === (activeFile == null ? void 0 : activeFile.path) ? 100 : 0;
        const score = scoreText(content, keywords) + scoreText(file.basename, keywords) * 3 + bonus;
        if (score > 0 || file.path === (activeFile == null ? void 0 : activeFile.path)) {
          candidates.push({ file, score, content });
        }
      } catch (e) {
      }
    }
    candidates.sort((a, b) => b.score - a.score);
    const topN = candidates.slice(0, this.settings.maxVaultNotes);
    if (!topN.length) {
      try {
        const fallback = activeFile ? await this.getActiveNoteContent(this.settings.maxCharsPerNote) : "";
        return {
          context: fallback,
          sourceNames: activeFile ? [activeFile.basename] : []
        };
      } catch (e) {
        return { context: "", sourceNames: [] };
      }
    }
    const parts = topN.map(({ file, content }) => {
      const snippet = extractSnippet(content, keywords, this.settings.maxCharsPerNote);
      return `--- [${file.basename}] ---
${snippet}`;
    });
    return {
      context: parts.join("\n\n"),
      sourceNames: topN.map(({ file }) => file.basename)
    };
  }
  // endpoint: /api/ai/health (standalone server contract)
  async pingServer() {
    const response = await this.safeRequest("/api/ai/health", {
      method: "GET"
    });
    if (response.status >= 200 && response.status < 300) {
      try {
        const data = response.json;
        if (typeof (data == null ? void 0 : data.ok) === "boolean") return data.ok;
        return true;
      } catch (e) {
        return true;
      }
    }
    return false;
  }
  // body: OpenAI messages array / response: data.result.text
  async callChatApi(body) {
    var _a;
    const systemParts = [];
    if (body.context) {
      systemParts.push(
        `\uC544\uB798\uB294 \uC0AC\uC6A9\uC790\uC758 Obsidian vault\uC5D0\uC11C \uC9C8\uBB38\uACFC \uAD00\uB828\uB41C \uB178\uD2B8 \uB0B4\uC6A9\uC785\uB2C8\uB2E4. \uC774\uB97C \uBC14\uD0D5\uC73C\uB85C \uB2F5\uBCC0\uD558\uC138\uC694.

${body.context}`
      );
    }
    if (body.notePath) {
      systemParts.push(`\uD604\uC7AC \uC5F4\uB9B0 \uB178\uD2B8: ${body.notePath}`);
    }
    const messages = [];
    if (systemParts.length > 0) {
      messages.push({ role: "system", content: systemParts.join("\n") });
    }
    messages.push({ role: "user", content: body.message });
    const response = await this.safeRequest("/api/ai/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      // routeHint: "copilot" → DLP sanitize 이후에도 local runner 우회, Copilot으로 강제 라우팅
      body: JSON.stringify({ messages, routeHint: "copilot" })
    });
    if (response.status === 422) {
      const errData = response.json;
      if ((errData == null ? void 0 : errData.error) === "DLP_BLOCKED") {
        const err = new Error("DLP_BLOCKED");
        err.isDlpBlocked = true;
        throw err;
      }
    }
    if (response.status < 200 || response.status >= 300) {
      throw new Error(`HTTP ${response.status}: ${response.text}`);
    }
    const data = response.json;
    const text = (_a = data == null ? void 0 : data.result) == null ? void 0 : _a.text;
    if (!text || typeof text !== "string") {
      throw new Error(
        "\uC751\uB2F5 JSON\uC5D0 result.text \uD544\uB4DC\uAC00 \uC5C6\uAC70\uB098 \uBE44\uC5B4\uC788\uC2B5\uB2C8\uB2E4."
      );
    }
    return text;
  }
  async safeRequest(path, options) {
    var _a;
    const url = `${this.settings.serverUrl}${path}`;
    const headers = { ...(_a = options.headers) != null ? _a : {} };
    if (this.settings.apiToken) {
      headers.Authorization = `Bearer ${this.settings.apiToken}`;
    }
    try {
      return await (0, import_obsidian.requestUrl)({
        url,
        method: options.method,
        headers,
        body: options.body,
        throw: false,
        contentType: "application/json"
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      throw new Error(`\uB124\uD2B8\uC6CC\uD06C \uC694\uCCAD \uC2E4\uD328: ${message}`);
    }
  }
  async getActiveNoteContent(maxChars = 4e3) {
    const file = this.app.workspace.getActiveFile();
    if (!(file instanceof import_obsidian.TFile)) return "";
    const content = await this.app.vault.cachedRead(file);
    return content.length > maxChars ? content.slice(0, maxChars) : content;
  }
};
