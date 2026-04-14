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
  default: () => ObsidianMemoryPlugin
});
module.exports = __toCommonJS(main_exports);
var import_obsidian2 = require("obsidian");

// src/settings.ts
var DEFAULT_SETTINGS = {
  rawRoot: "mcp_raw",
  memoryRoot: "20_AI_Memory",
  systemRoot: "90_System",
  createdBy: "chaminkyu"
};

// src/services/vault-store.ts
var import_obsidian = require("obsidian");
var VaultStore = class {
  constructor(app, settings) {
    this.app = app;
    this.settings = settings;
  }
  async ensureFolder(path) {
    const normalized = (0, import_obsidian.normalizePath)(path);
    const parts = normalized.split("/").filter(Boolean);
    let current = "";
    for (const part of parts) {
      current = current ? `${current}/${part}` : part;
      const existing = this.app.vault.getAbstractFileByPath(current);
      if (!existing) {
        await this.app.vault.createFolder(current);
      }
    }
  }
  async getOrCreateFile(path, initial = "") {
    const normalized = (0, import_obsidian.normalizePath)(path);
    const existing = this.app.vault.getAbstractFileByPath(normalized);
    if (existing instanceof import_obsidian.TFile) return existing;
    const dir = normalized.split("/").slice(0, -1).join("/");
    if (dir) await this.ensureFolder(dir);
    return await this.app.vault.create(normalized, initial);
  }
  fmBlock(frontmatter) {
    const lines = ["---"];
    for (const [key, value] of Object.entries(frontmatter)) {
      if (Array.isArray(value)) {
        lines.push(`${key}:`);
        for (const item of value) lines.push(`  - ${item}`);
      } else if (value === void 0 || value === null) {
        continue;
      } else {
        lines.push(`${key}: ${String(value)}`);
      }
    }
    lines.push("---", "");
    return lines.join("\n");
  }
  rawPath(note) {
    return (0, import_obsidian.normalizePath)(
      `${this.settings.rawRoot}/${note.source}/${note.conversation_date}/${note.mcp_id}.md`
    );
  }
  memoryPath(note) {
    const dt = note.created_at_utc.slice(0, 7).replace("-", "/");
    return (0, import_obsidian.normalizePath)(
      `${this.settings.memoryRoot}/${note.memory_type}/${dt}/${note.memory_id}.md`
    );
  }
  async saveRawConversation(note) {
    const path = this.rawPath(note);
    const file = await this.getOrCreateFile(path);
    const frontmatter = {
      schema_type: note.schema_type,
      mcp_id: note.mcp_id,
      source: note.source,
      created_by: note.created_by,
      created_at_utc: note.created_at_utc,
      conversation_date: note.conversation_date,
      project: note.project,
      tags: note.tags ?? [],
      mcp_sig: note.mcp_sig
    };
    const full = `${this.fmBlock(frontmatter)}${note.body_markdown.trim()}
`;
    await this.app.vault.process(file, () => full);
    return path;
  }
  async saveMemory(note) {
    const path = this.memoryPath(note);
    const file = await this.getOrCreateFile(path);
    const frontmatter = {
      schema_type: note.schema_type,
      memory_id: note.memory_id,
      memory_type: note.memory_type,
      source: note.source,
      created_by: note.created_by,
      created_at_utc: note.created_at_utc,
      title: note.title,
      project: note.project,
      tags: note.tags ?? [],
      confidence: note.confidence ?? 0.8,
      status: note.status ?? "active",
      mcp_sig: note.mcp_sig
    };
    const full = `${this.fmBlock(frontmatter)}${note.content.trim()}
`;
    await this.app.vault.process(file, () => full);
    return path;
  }
  async rebuildIndex() {
    const files = this.app.vault.getFiles();
    const entries = [];
    for (const file of files) {
      const cache = this.app.metadataCache.getFileCache(file);
      const fm = cache?.frontmatter;
      if (!fm) continue;
      if (fm.schema_type !== "raw_conversation" && fm.schema_type !== "memory_item") {
        continue;
      }
      entries.push({
        id: String(fm.mcp_id ?? fm.memory_id),
        schema_type: fm.schema_type,
        source: String(fm.source),
        title: String(fm.title ?? fm.mcp_id ?? fm.memory_id),
        path: file.path,
        created_at_utc: String(fm.created_at_utc),
        tags: Array.isArray(fm.tags) ? fm.tags.map(String) : [],
        project: fm.project ? String(fm.project) : void 0
      });
    }
    const outPath = (0, import_obsidian.normalizePath)(`${this.settings.systemRoot}/memory_index.json`);
    const outFile = await this.getOrCreateFile(outPath, "[]\n");
    await this.app.vault.process(outFile, () => JSON.stringify(entries, null, 2));
    return outPath;
  }
};

// src/main.ts
var ObsidianMemoryPlugin = class extends import_obsidian2.Plugin {
  async onload() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
    this.store = new VaultStore(this.app, this.settings);
    this.addCommand({
      id: "memory-rebuild-index",
      name: "Rebuild memory index",
      callback: async () => {
        const path = await this.store.rebuildIndex();
        new import_obsidian2.Notice(`Memory index rebuilt: ${path}`);
      }
    });
    this.addCommand({
      id: "memory-save-demo-raw",
      name: "Save demo raw conversation",
      callback: async () => {
        const note = {
          schema_type: "raw_conversation",
          mcp_id: `convo-${Date.now()}`,
          source: "chatgpt",
          created_by: this.settings.createdBy,
          created_at_utc: (/* @__PURE__ */ new Date()).toISOString(),
          conversation_date: (/* @__PURE__ */ new Date()).toISOString().slice(0, 10),
          project: "HVDC",
          tags: ["demo", "raw"],
          body_markdown: "## User\nExample raw conversation\n\n## Assistant\nExample response"
        };
        const path = await this.store.saveRawConversation(note);
        new import_obsidian2.Notice(`Raw conversation saved: ${path}`);
      }
    });
    this.addCommand({
      id: "memory-save-demo-item",
      name: "Save demo memory item",
      callback: async () => {
        const note = {
          schema_type: "memory_item",
          memory_id: `MEM-${(/* @__PURE__ */ new Date()).toISOString().slice(0, 10).replace(/-/g, "")}-000000-A1B2C3`,
          memory_type: "decision",
          source: "chatgpt",
          created_by: this.settings.createdBy,
          created_at_utc: (/* @__PURE__ */ new Date()).toISOString(),
          title: "Demo decision",
          content: "Voyage 71 remains 20mm aggregate only.",
          project: "HVDC",
          tags: ["demo", "decision"],
          confidence: 0.92,
          status: "active"
        };
        const path = await this.store.saveMemory(note);
        new import_obsidian2.Notice(`Memory saved: ${path}`);
      }
    });
  }
  async onunload() {
    await this.saveData(this.settings);
  }
};
