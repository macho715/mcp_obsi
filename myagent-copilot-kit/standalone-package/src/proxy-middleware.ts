import { randomUUID } from "node:crypto";
import type { NextFunction, Request, RequestHandler, Response } from "express";
import {
  CopilotBridgeError,
  runPromptWithRetry,
  type CopilotPromptMessage,
} from "./copilot-bridge.js";
import { scanMessagesForDlp, type DlpPolicy, type DlpScanResult } from "./dlp.js";
import {
  buildOperationalLog,
  toOperationalUsage,
  type ProxyOperationalLogger,
  type ProxyOperationalStage,
} from "./ops-log.js";
import { evaluateRequest, type PolicyResult } from "./policy-engine.js";
import {
  decideRoute,
  type RouteHint,
  resolveDataSensitivity,
  type DataSensitivity,
  type RoutingDecision,
  type RoutingPolicy,
} from "./routing.js";
import { searchMemory, type MemoryClientOptions, type MemorySearchItem } from "./mcp-memory-client.js";

export type ProxyChatMessage = {
  role: "system" | "user" | "assistant";
  content: string;
};

export type ProxyChatRequestBody = {
  messages?: ProxyChatMessage[];
  model?: string;
  sensitivity?: string;
  scope?: string[];
  mode?: string;
  routeHint?: string;
};

type ProxyContext = {
  requestId?: string;
  startedAtMs?: number;
  policy?: PolicyResult;
  dlp?: DlpScanResult;
  routing?: RoutingDecision;
};

export type ProxyLocalRunner = (params: {
  model: string;
  messages: ProxyChatMessage[];
  req: Request;
  requestId: string;
  scope: string[];
  mode: string;
  routeHint: RouteHint;
  kbContext?: string;
  kbSources?: MemorySearchItem[];
}) => Promise<{
  text: string;
  model?: string;
  provider?: string;
  sources?: Array<Record<string, unknown>>;
  riskFlags?: string[];
  latencyMs?: number;
}>;

const DEFAULT_MODEL = "github-copilot/gpt-5-mini";
const LOCAL_DEFAULT_MODEL = "gemma4:e4b";
const REQUEST_ID_HEADER = "x-request-id";
const CONTEXT_KEY = "__standaloneProxyContext";

function getProxyContext(res: Response): ProxyContext {
  const record = res.locals as Record<string, unknown>;
  if (!record[CONTEXT_KEY] || typeof record[CONTEXT_KEY] !== "object") {
    record[CONTEXT_KEY] = {};
  }
  return record[CONTEXT_KEY] as ProxyContext;
}

function resolveRequestId(req: Request): string {
  const fromHeader = req.header(REQUEST_ID_HEADER);
  return fromHeader?.trim() ? fromHeader.trim() : randomUUID();
}

function ensureRequestMeta(req: Request, ctx: ProxyContext): { requestId: string; startedAtMs: number } {
  if (!ctx.requestId) {
    ctx.requestId = resolveRequestId(req);
  }
  if (!ctx.startedAtMs) {
    ctx.startedAtMs = Date.now();
  }
  return {
    requestId: ctx.requestId,
    startedAtMs: ctx.startedAtMs,
  };
}

function emitLog(params: {
  logger?: ProxyOperationalLogger;
  stage: ProxyOperationalStage;
  outcome: "success" | "blocked" | "failed";
  route: RoutingDecision["route"] | "unknown";
  httpStatus: number;
  requestId: string;
  startedAtMs: number;
  model?: string;
  sensitivity?: DataSensitivity;
  reason?: string;
  ctx?: ProxyContext;
  usage?: {
    inputTokens?: number;
    outputTokens?: number;
    totalTokens?: number;
  };
  provider?: string;
  endpoint?: string;
  errorCode?: string;
  errorDetail?: string;
}) {
  if (!params.logger) {
    return;
  }
  try {
    params.logger(
      buildOperationalLog({
        requestId: params.requestId,
        stage: params.stage,
        outcome: params.outcome,
        route: params.route,
        httpStatus: params.httpStatus,
        startedAtMs: params.startedAtMs,
        model: params.model,
        sensitivity: params.sensitivity,
        reason: params.reason,
        dlpStatus: params.ctx?.dlp?.status ?? "unknown",
        dlpHighestSeverity: params.ctx?.dlp?.highestSeverity ?? "unknown",
        dlpFindingCount: params.ctx?.dlp?.findings.length ?? 0,
        sanitized: (params.ctx?.dlp?.status ?? "allow") === "sanitize",
        usage: params.usage,
        provider: params.provider,
        endpoint: params.endpoint,
        errorCode: params.errorCode,
        errorDetail: params.errorDetail,
      }),
    );
  } catch {
    // Logging must not break request handling.
  }
}

function parseMessages(body: unknown): ProxyChatMessage[] | null {
  if (!body || typeof body !== "object") {
    return null;
  }
  const messages = (body as ProxyChatRequestBody).messages;
  if (!Array.isArray(messages) || messages.length === 0) {
    return null;
  }
  const parsed: ProxyChatMessage[] = [];
  for (const message of messages) {
    if (!message || typeof message !== "object") {
      return null;
    }
    const role = (message as ProxyChatMessage).role;
    const content = (message as ProxyChatMessage).content;
    if (
      (role !== "system" && role !== "user" && role !== "assistant") ||
      typeof content !== "string" ||
      !content.trim()
    ) {
      return null;
    }
    parsed.push({ role, content });
  }
  return parsed;
}

function parseChatRequest(
  req: Request,
): { messages: ProxyChatMessage[]; model: string; explicitModel: boolean } | null {
  const body = req.body as ProxyChatRequestBody | undefined;
  const messages = parseMessages(body);
  if (!messages) {
    return null;
  }
  if (body?.scope !== undefined) {
    if (!Array.isArray(body.scope) || body.scope.some((item) => typeof item !== "string")) {
      return null;
    }
  }
  const explicitModel = typeof body?.model === "string" && body.model.trim().length > 0;
  const model = explicitModel ? body.model!.trim() : DEFAULT_MODEL;
  return { messages, model, explicitModel };
}

function ensureChatRequest(
  req: Request,
  res: Response,
): { messages: ProxyChatMessage[]; model: string; explicitModel: boolean } | null {
  const parsed = parseChatRequest(req);
  if (parsed) {
    return parsed;
  }
  res.status(400).json({
    error: "INVALID_REQUEST",
    detail: "`messages` must be a non-empty array of { role, content }.",
  });
  return null;
}

function applySanitizedMessages(req: Request, dlp: DlpScanResult): void {
  const body = req.body as ProxyChatRequestBody;
  if (!Array.isArray(body.messages)) {
    return;
  }
  body.messages = body.messages.map((message, index) => ({
    ...message,
    content: dlp.messageScans[index]?.sanitizedContent ?? message.content,
  }));
}

function toBridgeMessages(messages: ProxyChatMessage[]): CopilotPromptMessage[] {
  return messages.map((message) => ({
    role: message.role,
    content: message.content,
  }));
}

function normalizeRouteHint(value: string | undefined): RouteHint {
  const normalized = value?.trim().toLowerCase();
  if (normalized === "local" || normalized === "copilot") {
    return normalized;
  }
  return "auto";
}

const RAG_KEYWORDS = [
  "요약",
  "근거",
  "문서",
  "첨부",
  "dem/det",
  "dem",
  "det",
  "통관",
  "hs",
  "리스크",
];

function requestLooksLikeRag(body: ProxyChatRequestBody | undefined, messages: ProxyChatMessage[]): boolean {
  if (Array.isArray(body?.scope) && body.scope.length > 0) {
    return true;
  }
  for (const message of [...messages].reverse()) {
    if (message.role !== "user") {
      continue;
    }
    const lowered = message.content.toLowerCase();
    return RAG_KEYWORDS.some((keyword) => lowered.includes(keyword));
  }
  return false;
}

/** Runs before DLP. Blocks requests that violate policy (e.g. auto-decision keywords). */
export function createPolicyEngineMiddleware(opts?: { logger?: ProxyOperationalLogger }): RequestHandler {
  return (req, res, next) => {
    const ctx = getProxyContext(res);
    const meta = ensureRequestMeta(req, ctx);
    const parsed = ensureChatRequest(req, res);
    if (!parsed) {
      emitLog({
        logger: opts?.logger,
        stage: "pre_dlp",
        outcome: "failed",
        route: "unknown",
        httpStatus: 400,
        requestId: meta.requestId,
        startedAtMs: meta.startedAtMs,
        reason: "Invalid request payload.",
        ctx,
        errorCode: "INVALID_REQUEST",
      });
      return;
    }

    const body = req.body as ProxyChatRequestBody;
    const policyResult = evaluateRequest({
      messages: body.messages,
      mode: body.mode,
      routeHint: body.routeHint,
      scope: body.scope,
    });
    ctx.policy = policyResult;

    if (!policyResult.allow) {
      res.status(403).json({
        requestId: meta.requestId,
        error: "POLICY_BLOCKED",
        detail: policyResult.blockReason ?? "Request blocked by policy.",
        flags: policyResult.flags,
      });
      emitLog({
        logger: opts?.logger,
        stage: "pre_dlp",
        outcome: "blocked",
        route: "blocked",
        httpStatus: 403,
        requestId: meta.requestId,
        startedAtMs: meta.startedAtMs,
        reason: policyResult.blockReason ?? "Policy engine blocked request.",
        ctx,
        errorCode: "POLICY_BLOCKED",
      });
      return;
    }

    next();
  };
}

export function createPreSendDlpMiddleware(opts?: {
  policy?: Partial<DlpPolicy>;
  logger?: ProxyOperationalLogger;
}): RequestHandler {
  return (req, res, next) => {
    const ctx = getProxyContext(res);
    const meta = ensureRequestMeta(req, ctx);
    const parsed = ensureChatRequest(req, res);
    if (!parsed) {
      emitLog({
        logger: opts?.logger,
        stage: "pre_dlp",
        outcome: "failed",
        route: "unknown",
        httpStatus: 400,
        requestId: meta.requestId,
        startedAtMs: meta.startedAtMs,
        reason: "Invalid request payload.",
        ctx,
        errorCode: "INVALID_REQUEST",
      });
      return;
    }

    const scan = scanMessagesForDlp(parsed.messages, { policy: opts?.policy });
    ctx.dlp = scan;

    if (scan.status === "block") {
      res.status(422).json({
        requestId: meta.requestId,
        error: "DLP_BLOCKED",
        detail: "Request contains sensitive data blocked by pre-send policy.",
        highestSeverity: scan.highestSeverity,
        findingCount: scan.findings.length,
      });
      emitLog({
        logger: opts?.logger,
        stage: "pre_dlp",
        outcome: "blocked",
        route: "blocked",
        httpStatus: 422,
        requestId: meta.requestId,
        startedAtMs: meta.startedAtMs,
        model: parsed.model,
        reason: "Request blocked by DLP policy.",
        ctx,
        errorCode: "DLP_BLOCKED",
      });
      return;
    }

    if (scan.status === "sanitize") {
      applySanitizedMessages(req, scan);
    }
    next();
  };
}

export function createRoutingGateMiddleware(opts?: {
  policy?: Partial<RoutingPolicy>;
  logger?: ProxyOperationalLogger;
}): RequestHandler {
  return (req, res, next) => {
    const ctx = getProxyContext(res);
    const meta = ensureRequestMeta(req, ctx);
    const parsed = ensureChatRequest(req, res);
    if (!parsed) {
      emitLog({
        logger: opts?.logger,
        stage: "routing_gate",
        outcome: "failed",
        route: "unknown",
        httpStatus: 400,
        requestId: meta.requestId,
        startedAtMs: meta.startedAtMs,
        reason: "Invalid request payload.",
        ctx,
        errorCode: "INVALID_REQUEST",
      });
      return;
    }

    const body = req.body as ProxyChatRequestBody;
    const dlp = ctx.dlp ?? scanMessagesForDlp(parsed.messages);
    const sensitivity = resolveDataSensitivity({
      headerValue: req.header("x-ai-sensitivity") ?? undefined,
      bodyValue: body.sensitivity,
      fallback: opts?.policy?.defaultSensitivity,
    });
    const decision = decideRoute({
      dlp,
      sensitivity,
      policy: opts?.policy,
      routeHint: body.routeHint,
      policyRouteHintOverride: ctx.policy?.routeHintOverride,
      hasScope: Array.isArray(body.scope) && body.scope.length > 0,
      ragRequested: requestLooksLikeRag(body, parsed.messages),
    });
    ctx.routing = decision;

    if (decision.route === "blocked") {
      res.status(403).json({
        requestId: meta.requestId,
        error: "ROUTING_BLOCKED",
        detail: decision.reason,
        sensitivity,
      });
      emitLog({
        logger: opts?.logger,
        stage: "routing_gate",
        outcome: "blocked",
        route: "blocked",
        httpStatus: 403,
        requestId: meta.requestId,
        startedAtMs: meta.startedAtMs,
        model: parsed.model,
        sensitivity,
        reason: decision.reason,
        ctx,
        errorCode: "ROUTING_BLOCKED",
      });
      return;
    }

    next();
  };
}

function resolveSensitivity(req: Request, routing: RoutingDecision | undefined): DataSensitivity {
  if (routing) {
    return routing.sensitivity;
  }
  const body = req.body as ProxyChatRequestBody | undefined;
  return resolveDataSensitivity({
    headerValue: req.header("x-ai-sensitivity") ?? undefined,
    bodyValue: body?.sensitivity,
  });
}

export function createChatProxyHandler(opts?: {
  defaultModel?: string;
  localRunner?: ProxyLocalRunner;
  logger?: ProxyOperationalLogger;
  memoryClientOptions?: MemoryClientOptions;
}): RequestHandler {
  return async (req, res) => {
    const ctx = getProxyContext(res);
    const meta = ensureRequestMeta(req, ctx);
    const parsed = ensureChatRequest(req, res);
    if (!parsed) {
      emitLog({
        logger: opts?.logger,
        stage: "handler",
        outcome: "failed",
        route: "unknown",
        httpStatus: 400,
        requestId: meta.requestId,
        startedAtMs: meta.startedAtMs,
        reason: "Invalid request payload.",
        ctx,
        errorCode: "INVALID_REQUEST",
      });
      return;
    }

    const model = parsed.model || opts?.defaultModel || DEFAULT_MODEL;
    const routing = ctx.routing;
    const sensitivity = resolveSensitivity(req, routing);

    if (routing?.route === "local" || (!routing && sensitivity === "secret")) {
      const localModel = parsed.explicitModel ? model : LOCAL_DEFAULT_MODEL;
      if (!opts?.localRunner) {
        res.status(409).json({
          requestId: meta.requestId,
          error: "LOCAL_ROUTE_REQUIRED",
          detail:
            routing?.reason ??
            "Request requires local-only route but no local runner is configured.",
          sensitivity,
        });
        emitLog({
          logger: opts?.logger,
          stage: "handler",
          outcome: "failed",
          route: "local",
          httpStatus: 409,
          requestId: meta.requestId,
          startedAtMs: meta.startedAtMs,
          model: localModel,
          sensitivity,
          reason:
            routing?.reason ??
            "Request requires local-only route but no local runner is configured.",
          ctx,
          errorCode: "LOCAL_ROUTE_REQUIRED",
        });
        return;
      }

      try {
        const body = req.body as ProxyChatRequestBody | undefined;
        const routeHint = normalizeRouteHint(body?.routeHint);

        // Memory enrichment: if RAG keywords detected, fetch KB context from memory
        let kbContext = "";
        let kbSources: MemorySearchItem[] = [];
        const ragDetected = requestLooksLikeRag(body, parsed.messages);
        if (ragDetected && opts?.memoryClientOptions) {
          const lastUserMessage = [...parsed.messages].reverse().find((m) => m.role === "user");
          if (lastUserMessage?.content?.trim()) {
            try {
              const memResult = await searchMemory(opts.memoryClientOptions, {
                query: lastUserMessage.content.trim().slice(0, 300),
              });
              if (memResult.results.length > 0) {
                kbSources = memResult.results;
                const sourceLines = memResult.results
                  .map((r) => `- [${r.title}](${r.url})`)
                  .join("\n");
                kbContext = `\n\nRelevant knowledge from memory:\n${sourceLines}\n\nUse the above knowledge when it is relevant to the question.`;
              }
            } catch {
              // Memory lookup failed — continue without KB context, RAG still works
            }
          }
        }

        const enrichedMessages = kbContext
          ? [{ role: "system" as const, content: kbContext }, ...parsed.messages]
          : parsed.messages;
        const localResponse = await opts.localRunner({
          model: localModel,
          messages: enrichedMessages,
          req,
          requestId: meta.requestId,
          scope: Array.isArray(body?.scope) ? body.scope : [],
          mode: typeof body?.mode === "string" && body.mode.trim() ? body.mode.trim() : "read_only",
          routeHint,
          kbContext,
          kbSources,
        });
        const mergedSources = [
          ...(kbSources.length > 0
            ? kbSources.map((s) => ({ type: "memory", id: s.id, title: s.title, url: s.url, score: 1 }))
            : []),
          ...(localResponse.sources ?? []),
        ];
        res.json({
          requestId: meta.requestId,
          route: "local",
          sensitivity,
          result: {
            text: localResponse.text,
            model: localResponse.model ?? null,
            provider: localResponse.provider ?? "local",
            usage: null,
          },
          sources: mergedSources,
          kbEnriched: kbContext.length > 0,
          riskFlags: localResponse.riskFlags ?? [],
          latencyMs: localResponse.latencyMs ?? 0,
          guard: {
            dlpStatus: ctx.dlp?.status ?? "allow",
            reason: routing?.reason ?? "Local runner selected.",
          },
        });
        emitLog({
          logger: opts?.logger,
          stage: "handler",
          outcome: "success",
          route: "local",
          httpStatus: 200,
          requestId: meta.requestId,
          startedAtMs: meta.startedAtMs,
          model: localModel,
          sensitivity,
          reason: routing?.reason ?? "Local runner selected.",
          ctx,
          provider: localResponse.provider ?? "local",
        });
      } catch (error) {
        const detail = error instanceof Error ? error.message : String(error);
        res.status(500).json({
          requestId: meta.requestId,
          error: "LOCAL_RUNNER_FAILED",
          detail,
        });
        emitLog({
          logger: opts?.logger,
          stage: "handler",
          outcome: "failed",
          route: "local",
          httpStatus: 500,
          requestId: meta.requestId,
          startedAtMs: meta.startedAtMs,
          model: localModel,
          sensitivity,
          reason: "Local runner failed.",
          ctx,
          errorCode: "LOCAL_RUNNER_FAILED",
          errorDetail: detail,
        });
      }
      return;
    }

    try {
      const result = await runPromptWithRetry({
        model,
        messages: toBridgeMessages(parsed.messages),
      });

      res.json({
        requestId: meta.requestId,
        route: "copilot",
        sensitivity,
        result: {
          text: result.response.text,
          model: result.response.model,
          provider: result.response.provider,
          endpoint: result.response.endpoint,
          usage: result.response.usage ?? null,
        },
        sources: [],
        riskFlags: [],
        latencyMs: null,
        guard: {
          dlpStatus: ctx.dlp?.status ?? "allow",
          reason: routing?.reason ?? "Request is eligible for Copilot route.",
        },
      });

      emitLog({
        logger: opts?.logger,
        stage: "handler",
        outcome: "success",
        route: "copilot",
        httpStatus: 200,
        requestId: meta.requestId,
        startedAtMs: meta.startedAtMs,
        model,
        sensitivity,
        reason: routing?.reason ?? "Request is eligible for Copilot route.",
        ctx,
        usage: toOperationalUsage(result.response),
        provider: result.response.provider,
        endpoint: result.response.endpoint,
      });
    } catch (error) {
      const bridgeError =
        error instanceof CopilotBridgeError
          ? error
          : new CopilotBridgeError({
              code: "unknown",
              message: error instanceof Error ? error.message : String(error),
              cause: error,
            });
      const status = bridgeError.status ?? (bridgeError.code === "rate_limit" ? 429 : 502);
      res.status(status).json({
        requestId: meta.requestId,
        error: "COPILOT_PROXY_FAILED",
        detail: bridgeError.message,
        code: bridgeError.code,
      });
      emitLog({
        logger: opts?.logger,
        stage: "handler",
        outcome: "failed",
        route: "copilot",
        httpStatus: status,
        requestId: meta.requestId,
        startedAtMs: meta.startedAtMs,
        model,
        sensitivity,
        reason: "Copilot request failed.",
        ctx,
        errorCode: bridgeError.code,
        errorDetail: bridgeError.message,
      });
    }
  };
}
