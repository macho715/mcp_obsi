type FetchJsonResult = {
  ok: boolean;
  status: number;
  data?: unknown;
  text?: string;
};

export type MemoryServiceHealth = {
  status: "ok" | "down";
  service?: string;
  error?: string;
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

export async function fetchMemoryServiceHealth(
  baseUrl: string,
  timeoutMs: number,
): Promise<MemoryServiceHealth> {
  try {
    const result = await fetchJson(`${resolveBaseUrl(baseUrl)}/healthz`, { method: "GET" }, timeoutMs);
    const payload = asObject(result.data);
    if (!result.ok || !payload) {
      return {
        status: "down",
        error: result.text ?? `HTTP ${result.status}`,
      };
    }
    const ok = payload.ok === true;
    return {
      status: ok ? "ok" : "down",
      service: typeof payload.service === "string" ? payload.service : undefined,
      ...(ok ? {} : { error: result.text ?? "Memory service reported non-ok status." }),
    };
  } catch (error) {
    return {
      status: "down",
      error: error instanceof Error ? error.message : String(error),
    };
  }
}
