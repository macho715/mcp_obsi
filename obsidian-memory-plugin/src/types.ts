export type MemorySource = "chatgpt" | "claude" | "grok" | "cursor" | "manual";
export type MemoryType =
  | "preference"
  | "project_fact"
  | "decision"
  | "person"
  | "todo"
  | "conversation_summary";

export interface RawConversationNote {
  schema_type: "raw_conversation";
  mcp_id: string;
  source: MemorySource;
  created_by: string;
  created_at_utc: string;
  conversation_date: string;
  project?: string;
  tags?: string[];
  mcp_sig?: string;
  body_markdown: string;
}

export interface MemoryNote {
  schema_type: "memory_item";
  memory_id: string;
  memory_type: MemoryType;
  source: MemorySource;
  created_by: string;
  created_at_utc: string;
  title: string;
  content: string;
  project?: string;
  tags?: string[];
  confidence?: number;
  status?: "active" | "superseded" | "archived";
  mcp_sig?: string;
}

export interface IndexEntry {
  id: string;
  schema_type: "raw_conversation" | "memory_item";
  source: MemorySource;
  title: string;
  path: string;
  created_at_utc: string;
  tags: string[];
  project?: string;
}
