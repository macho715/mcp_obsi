export interface MemoryPluginSettings {
  rawRoot: string;
  memoryRoot: string;
  systemRoot: string;
  createdBy: string;
}

export const DEFAULT_SETTINGS: MemoryPluginSettings = {
  rawRoot: "mcp_raw",
  memoryRoot: "20_AI_Memory",
  systemRoot: "90_System",
  createdBy: "chaminkyu",
};
