type JsonRpcRequest = {
  jsonrpc: "2.0";
  id?: number;
  method: string;
  params?: Record<string, unknown>;
};

type JsonRpcResponse<T> = {
  jsonrpc?: string;
  id?: number | string | null;
  result?: T;
  error?: {
    code?: number;
    message?: string;
    data?: unknown;
  };
};

export type MemoryClientOptions = {
  baseUrl: string;
  mcpPath: string;
  bearerToken?: string;
  timeoutMs: number;
};

export type MemorySearchItem = {
  id: string;
  title: string;
  url: string;
};

export type MemoryRecord = {
  id: string;
  title: string;
  text: string;
  url: string;
  metadata: Record<string, unknown>;
};

export type WikiSearchItem = {
  source: "wiki";
  id: string;
  title: string;
  slug?: string | null;
  path?: string | null;
  category?: string | null;
  tags?: string[];
  snippet?: string | null;
  score: number;
  fetch_route: "fetch_wiki";
  related_memory_id?: string | null;
};

let requestCounter = 0;

function nextRequestId(): number {
  requestCounter += 1;
  return requestCounter;
}

function resolveBaseUrl(baseUrl: string): string {
  return baseUrl.replace(/\/+$/, "");
}

function resolveMcpUrl(baseUrl: string, mcpPath: string): string {
  const normalizedPath = mcpPath.startsWith("/") ? mcpPath : `/${mcpPath}`;
  return `${resolveBaseUrl(baseUrl)}${normalizedPath.replace(/\/?$/, "/")}`;
}

function buildHeaders(token: string | undefined, sessionId?: string): HeadersInit {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json, text/event-stream",
  };
  if (token?.trim()) {
    headers.Authorization = token.startsWith("Bearer ") ? token : `Bearer ${token}`;
  }
  if (sessionId) {
    headers["Mcp-Session-Id"] = sessionId;
  }
  return headers;
}

function parseSsePayload<T>(text: string, requestId?: number): JsonRpcResponse<T> {
  const events = text.split(/\r?\n\r?\n/);
  for (const event of events) {
    const data = event
      .split(/\r?\n/)
      .filter((line) => line.startsWith("data:"))
      .map((line) => line.slice(5).trim())
      .join("\n")
      .trim();
    if (!data) {
      continue;
    }
    try {
      const parsed = JSON.parse(data) as JsonRpcResponse<T>;
      if (requestId === undefined || parsed.id === requestId) {
        return parsed;
      }
    } catch {
      continue;
    }
  }
  throw new Error("MCP server returned an unreadable SSE payload.");
}

async function readSseRpcResponse<T>(
  response: Response,
  requestId?: number,
): Promise<JsonRpcResponse<T>> {
  if (!response.body) {
    return parseSsePayload<T>(await response.text(), requestId);
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (value) {
        buffer += decoder.decode(value, { stream: !done });
        const events = buffer.split(/\r?\n\r?\n/);
        buffer = events.pop() ?? "";
        for (const event of events) {
          try {
            return parseSsePayload<T>(event, requestId);
          } catch {
            continue;
          }
        }
      }
      if (done) {
        break;
      }
    }
  } finally {
    reader.releaseLock();
  }
  if (!buffer.trim()) {
    return {};
  }
  return parseSsePayload<T>(buffer, requestId);
}

async function parseRpcResponse<T>(response: Response, requestId?: number): Promise<JsonRpcResponse<T>> {
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("text/event-stream")) {
    return readSseRpcResponse<T>(response, requestId);
  }
  const text = await response.text();
  if (!text.trim()) {
    return {};
  }
  if (contentType.includes("application/json")) {
    return JSON.parse(text) as JsonRpcResponse<T>;
  }
  try {
    return JSON.parse(text) as JsonRpcResponse<T>;
  } catch {
    throw new Error(`Unexpected MCP response content-type: ${contentType || "unknown"}`);
  }
}

async function postRpc<T>(
  url: string,
  request: JsonRpcRequest,
  token: string | undefined,
  timeoutMs: number,
  sessionId?: string,
): Promise<{ response: JsonRpcResponse<T>; sessionId?: string }> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const httpResponse = await fetch(url, {
      method: "POST",
      headers: buildHeaders(token, sessionId),
      body: JSON.stringify(request),
      signal: controller.signal,
    });
    const rpcResponse = await parseRpcResponse<T>(httpResponse, request.id);
    if (!httpResponse.ok) {
      const detail = rpcResponse.error?.message ?? `${httpResponse.status} ${httpResponse.statusText}`.trim();
      throw new Error(`MCP request failed: ${detail}`);
    }
    if (rpcResponse.error) {
      throw new Error(rpcResponse.error.message ?? "MCP server returned an error.");
    }
    return {
      response: rpcResponse,
      sessionId: httpResponse.headers.get("Mcp-Session-Id") ?? sessionId,
    };
  } finally {
    clearTimeout(timeout);
  }
}

async function initializeSession(options: MemoryClientOptions): Promise<string | undefined> {
  const url = resolveMcpUrl(options.baseUrl, options.mcpPath);
  const init = await postRpc<Record<string, unknown>>(
    url,
    {
      jsonrpc: "2.0",
      id: nextRequestId(),
      method: "initialize",
      params: {
        protocolVersion: "2025-03-26",
        capabilities: {},
        clientInfo: {
          name: "myagent-copilot-standalone",
          version: "0.1.0",
        },
      },
    },
    options.bearerToken,
    options.timeoutMs,
  );
  await postRpc<void>(
    url,
    {
      jsonrpc: "2.0",
      method: "notifications/initialized",
    },
    options.bearerToken,
    options.timeoutMs,
    init.sessionId,
  );
  return init.sessionId;
}

async function callTool<T>(
  options: MemoryClientOptions,
  name: string,
  args: Record<string, unknown>,
): Promise<T> {
  const url = resolveMcpUrl(options.baseUrl, options.mcpPath);
  const sessionId = await initializeSession(options);
  const result = await postRpc<T>(
    url,
    {
      jsonrpc: "2.0",
      id: nextRequestId(),
      method: "tools/call",
      params: {
        name,
        arguments: args,
      },
    },
    options.bearerToken,
    options.timeoutMs,
    sessionId,
  );
  if (result.response.result === undefined) {
    throw new Error(`MCP tool "${name}" returned no result.`);
  }
  return result.response.result;
}

type ToolContentText = {
  type?: string;
  text?: string;
};

type ToolEnvelope<T> = {
  structuredContent?: T;
  content?: ToolContentText[];
};

function unwrapToolResult<T>(envelope: ToolEnvelope<T>): T {
  if (envelope.structuredContent !== undefined) {
    return envelope.structuredContent;
  }
  const first = envelope.content?.[0];
  if (typeof first?.text === "string" && first.text.trim()) {
    return JSON.parse(first.text) as T;
  }
  throw new Error("MCP tool result did not include structuredContent or JSON text.");
}

export async function listMemoryTools(options: MemoryClientOptions): Promise<string[]> {
  const url = resolveMcpUrl(options.baseUrl, options.mcpPath);
  const sessionId = await initializeSession(options);
  const result = await postRpc<{ tools?: Array<{ name?: string }> }>(
    url,
    {
      jsonrpc: "2.0",
      id: nextRequestId(),
      method: "tools/list",
    },
    options.bearerToken,
    options.timeoutMs,
    sessionId,
  );
  return (result.response.result?.tools ?? [])
    .map((tool) => tool.name?.trim() ?? "")
    .filter(Boolean);
}

export async function probeMemoryClient(options: MemoryClientOptions): Promise<{ ok: boolean; tools: string[] }> {
  const tools = await listMemoryTools(options);
  const allowedTools = new Set(["search", "fetch", "list_recent_memories"]);
  const hasOnlyReadonlyTools = tools.every((tool) => allowedTools.has(tool));
  return {
    ok: tools.includes("search") && tools.includes("fetch") && hasOnlyReadonlyTools,
    tools,
  };
}

export async function searchMemory(
  options: MemoryClientOptions,
  params: { query: string },
): Promise<{ results: MemorySearchItem[] }> {
  const envelope = await callTool<ToolEnvelope<{ results: MemorySearchItem[] }>>(
    options,
    "search",
    {
      query: params.query,
    },
  );
  return unwrapToolResult(envelope);
}

export async function getMemory(
  options: MemoryClientOptions,
  memoryId: string,
): Promise<MemoryRecord> {
  const envelope = await callTool<ToolEnvelope<MemoryRecord>>(
    options,
    "fetch",
    {
      id: memoryId,
    },
  );
  return unwrapToolResult(envelope);
}

export async function searchWiki(
  options: MemoryClientOptions,
  params: { query: string; pathPrefix?: string; limit?: number },
): Promise<{ results: WikiSearchItem[] }> {
  const envelope = await callTool<ToolEnvelope<{ results: WikiSearchItem[] }>>(
    options,
    "search_wiki",
    {
      query: params.query,
      path_prefix: params.pathPrefix ?? "wiki/analyses",
      limit: params.limit ?? 8,
    },
  );
  return unwrapToolResult(envelope);
}

export async function fetchWiki(
  options: MemoryClientOptions,
  params: { path?: string; slug?: string },
): Promise<Record<string, unknown>> {
  const envelope = await callTool<ToolEnvelope<Record<string, unknown>>>(
    options,
    "fetch_wiki",
    params.path ? { path: params.path } : { slug: params.slug },
  );
  return unwrapToolResult(envelope);
}

export type SaveMemoryParams = {
  title: string;
  content: string;
  source?: string;
  memory_type?: string;
  roles?: string[];
  topics?: string[];
  entities?: string[];
  projects?: string[];
  tags?: string[];
  confidence?: number;
  sensitivity?: string;
  status?: string;
  language?: string;
};

export type SaveMemoryResult = {
  id: string;
  url: string;
  title: string;
};

export async function saveMemory(
  options: MemoryClientOptions,
  params: SaveMemoryParams,
): Promise<SaveMemoryResult> {
  const envelope = await callTool<ToolEnvelope<SaveMemoryResult>>(
    options,
    "save_memory",
    {
      title: params.title,
      content: params.content,
      source: params.source ?? "standalone-package",
      memory_type: params.memory_type ?? "conversation_summary",
      roles: params.roles ?? [],
      topics: params.topics ?? [],
      entities: params.entities ?? [],
      projects: params.projects ?? [],
      tags: params.tags ?? ["standalone", "chat"],
      confidence: params.confidence ?? 0.8,
      sensitivity: params.sensitivity ?? "p1",
      status: params.status ?? "active",
      language: params.language ?? "ko",
    },
  );
  return unwrapToolResult(envelope);
}
