import { Notice, Plugin } from "obsidian";

import { DEFAULT_SETTINGS, MemoryPluginSettings } from "./settings";
import { VaultStore } from "./services/vault-store";
import { MemoryNote, RawConversationNote } from "./types";

export default class ObsidianMemoryPlugin extends Plugin {
  settings!: MemoryPluginSettings;
  store!: VaultStore;

  async onload() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
    this.store = new VaultStore(this.app, this.settings);

    this.addCommand({
      id: "memory-rebuild-index",
      name: "Rebuild memory index",
      callback: async () => {
        const path = await this.store.rebuildIndex();
        new Notice(`Memory index rebuilt: ${path}`);
      },
    });

    this.addCommand({
      id: "memory-save-demo-raw",
      name: "Save demo raw conversation",
      callback: async () => {
        const note: RawConversationNote = {
          schema_type: "raw_conversation",
          mcp_id: `convo-${Date.now()}`,
          source: "chatgpt",
          created_by: this.settings.createdBy,
          created_at_utc: new Date().toISOString(),
          conversation_date: new Date().toISOString().slice(0, 10),
          project: "HVDC",
          tags: ["demo", "raw"],
          body_markdown:
            "## User\nExample raw conversation\n\n## Assistant\nExample response",
        };
        const path = await this.store.saveRawConversation(note);
        new Notice(`Raw conversation saved: ${path}`);
      },
    });

    this.addCommand({
      id: "memory-save-demo-item",
      name: "Save demo memory item",
      callback: async () => {
        const note: MemoryNote = {
          schema_type: "memory_item",
          memory_id: `MEM-${new Date().toISOString().slice(0, 10).replace(/-/g, "")}-000000-A1B2C3`,
          memory_type: "decision",
          source: "chatgpt",
          created_by: this.settings.createdBy,
          created_at_utc: new Date().toISOString(),
          title: "Demo decision",
          content: "Voyage 71 remains 20mm aggregate only.",
          project: "HVDC",
          tags: ["demo", "decision"],
          confidence: 0.92,
          status: "active",
        };
        const path = await this.store.saveMemory(note);
        new Notice(`Memory saved: ${path}`);
      },
    });
  }

  async onunload() {
    await this.saveData(this.settings);
  }
}
