type LocalRagMessage = {
  role: "system" | "user" | "assistant";
  content: string;
};

type LocalRagSource = {
  file: string;
  score: number;
  doc_type?: string | null;
  source_path?: string | null;
  snippet?: string | null;
};

export type LocalRagRunnerParams = {
  baseUrl: string;
  timeoutMs: number;
  sharedSecret?: string;
  requestId: string;
  messages: LocalRagMessage[];
  scope: string[];
  mode: string;
  routeHint: "auto" | "local" | "copilot";
  model: string;
};

export type LocalRagRunnerResult = {
  text: string;
  model?: string;
  provider: "local-rag";
  sources: LocalRagSource[];
  riskFlags: string[];
  latencyMs: number;
};

export type LocalRagHealth = {
  status: string;
  api?: string;
  ollama: string;
  vectorstore: string;
  telegram?: string;
  documents: number;
  chatRouteReady?: boolean;
  error?: string;
};

type FetchJsonResult = {
  ok: boolean;
  status: number;
  data?: unknown;
  text?: string;
};

function resolveBaseUrl(baseUrl: string): string {
  return baseUrl.replace(/\/+$/, "");
}

async function fetchJson(url: string, init: RequestInit, timeoutMs: number): Promise<FetchJsonResult> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, { ...init, signal: controller.signal });
    const text = await response.text();
    let data: unknown;
    try {
      data = text ? JSON.parse(text) : undefined;
    } catch {
      data = undefined;
    }
    return {
      ok: response.ok,
      status: response.status,
      ...(data !== undefined ? { data } : {}),
      ...(text ? { text } : {}),
    };
  } finally {
    clearTimeout(timeout);
  }
}

function asObject(value: unknown): Record<string, unknown> | null {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : null;
}

export async function runLocalRagChat(params: LocalRagRunnerParams): Promise<LocalRagRunnerResult> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "x-request-id": params.requestId,
  };
  if (params.sharedSecret?.trim()) {
    headers["x-local-rag-token"] = params.sharedSecret.trim();
  }
  const result = await fetchJson(
    `${resolveBaseUrl(params.baseUrl)}/api/internal/ai/chat-local`,
    {
      method: "POST",
      headers,
      body: JSON.stringify({
        messages: params.messages,
        scope: params.scope,
        mode: params.mode,
        routeHint: params.routeHint,
        model: params.model,
      }),
    },
    params.timeoutMs,
  );

  if (!result.ok) {
    throw new Error(
      `Local RAG request failed: HTTP ${result.status}${result.text ? ` - ${result.text.slice(0, 280)}` : ""}`,
    );
  }

  const payload = asObject(result.data);
  if (!payload || typeof payload.text !== "string") {
    throw new Error("Local RAG response is missing text.");
  }

  return {
    text: payload.text,
    model: typeof payload.model === "string" ? payload.model : undefined,
    provider: "local-rag",
    sources: Array.isArray(payload.sources) ? (payload.sources as LocalRagSource[]) : [],
    riskFlags: Array.isArray(payload.riskFlags) ? (payload.riskFlags as string[]) : [],
    latencyMs: typeof payload.latencyMs === "number" ? payload.latencyMs : 0,
  };
}

export async function fetchLocalRagHealth(
  baseUrl: string,
  timeoutMs: number,
  sharedSecret?: string,
): Promise<LocalRagHealth> {
  try {
    const result = await fetchJson(`${resolveBaseUrl(baseUrl)}/health`, { method: "GET" }, timeoutMs);
    const payload = asObject(result.data);
    if (!result.ok || !payload) {
      return {
        status: "down",
        ollama: "down",
        vectorstore: "down",
        documents: 0,
        error: result.text ?? `HTTP ${result.status}`,
      };
    }
    const readyHeaders: Record<string, string> = {};
    if (sharedSecret?.trim()) {
      readyHeaders["x-local-rag-token"] = sharedSecret.trim();
    }
    const readyResult = await fetchJson(
      `${resolveBaseUrl(baseUrl)}/api/internal/ai/chat-local/ready`,
      { method: "GET", headers: readyHeaders },
      timeoutMs,
    );
    return {
      status: typeof payload.status === "string" ? payload.status : "unknown",
      api: typeof payload.api === "string" ? payload.api : undefined,
      ollama: typeof payload.ollama === "string" ? payload.ollama : "unknown",
      vectorstore: typeof payload.vectorstore === "string" ? payload.vectorstore : "unknown",
      telegram: typeof payload.telegram === "string" ? payload.telegram : undefined,
      documents: typeof payload.documents === "number" ? payload.documents : 0,
      chatRouteReady: readyResult.ok,
      ...(readyResult.ok ? {} : { error: readyResult.text ?? `HTTP ${readyResult.status}` }),
    };
  } catch (error) {
    return {
      status: "down",
      ollama: "down",
      vectorstore: "down",
      documents: 0,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}
