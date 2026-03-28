import { App, TFile, normalizePath } from "obsidian";

import {
  IndexEntry,
  MemoryNote,
  MemorySource,
  RawConversationNote,
} from "../types";
import { MemoryPluginSettings } from "../settings";

export class VaultStore {
  constructor(
    private app: App,
    private settings: MemoryPluginSettings,
  ) {}

  private async ensureFolder(path: string): Promise<void> {
    const normalized = normalizePath(path);
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

  private async getOrCreateFile(path: string, initial = ""): Promise<TFile> {
    const normalized = normalizePath(path);
    const existing = this.app.vault.getAbstractFileByPath(normalized);
    if (existing instanceof TFile) return existing;

    const dir = normalized.split("/").slice(0, -1).join("/");
    if (dir) await this.ensureFolder(dir);

    return await this.app.vault.create(normalized, initial);
  }

  private fmBlock(frontmatter: Record<string, unknown>): string {
    const lines = ["---"];
    for (const [key, value] of Object.entries(frontmatter)) {
      if (Array.isArray(value)) {
        lines.push(`${key}:`);
        for (const item of value) lines.push(`  - ${item}`);
      } else if (value === undefined || value === null) {
        continue;
      } else {
        lines.push(`${key}: ${String(value)}`);
      }
    }
    lines.push("---", "");
    return lines.join("\n");
  }

  private rawPath(note: RawConversationNote): string {
    return normalizePath(
      `${this.settings.rawRoot}/${note.source}/${note.conversation_date}/${note.mcp_id}.md`,
    );
  }

  private memoryPath(note: MemoryNote): string {
    const dt = note.created_at_utc.slice(0, 7).replace("-", "/");
    return normalizePath(
      `${this.settings.memoryRoot}/${note.memory_type}/${dt}/${note.memory_id}.md`,
    );
  }

  async saveRawConversation(note: RawConversationNote): Promise<string> {
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
      mcp_sig: note.mcp_sig,
    };

    const full = `${this.fmBlock(frontmatter)}${note.body_markdown.trim()}\n`;
    await this.app.vault.process(file, () => full);
    return path;
  }

  async saveMemory(note: MemoryNote): Promise<string> {
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
      mcp_sig: note.mcp_sig,
    };

    const full = `${this.fmBlock(frontmatter)}${note.content.trim()}\n`;
    await this.app.vault.process(file, () => full);
    return path;
  }

  async rebuildIndex(): Promise<string> {
    const files = this.app.vault.getFiles();
    const entries: IndexEntry[] = [];

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
        source: String(fm.source) as MemorySource,
        title: String(fm.title ?? fm.mcp_id ?? fm.memory_id),
        path: file.path,
        created_at_utc: String(fm.created_at_utc),
        tags: Array.isArray(fm.tags) ? fm.tags.map(String) : [],
        project: fm.project ? String(fm.project) : undefined,
      });
    }

    const outPath = normalizePath(`${this.settings.systemRoot}/memory_index.json`);
    const outFile = await this.getOrCreateFile(outPath, "[]\n");
    await this.app.vault.process(outFile, () => JSON.stringify(entries, null, 2));
    return outPath;
  }
}
