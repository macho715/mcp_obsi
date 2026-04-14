import express from "express";
import multer from "multer";
import { resolveGithubAuth } from "./copilot-bridge.js";
import {
  defaultDocKey,
  displayTitleFromDoc,
  listStandaloneDocs,
  readStandaloneDoc,
  renderChatHtml,
  renderDocHtml,
  renderDocsIndexHtml,
} from "./docs-browser.js";
import { createHvdcPredictService } from "./hvdc-predict.js";
import { fetchLocalRagHealth, runLocalRagChat } from "./local-rag.js";
import {
  fetchWiki,
  getMemory,
  probeMemoryClient,
  saveMemory,
  searchMemory,
  searchWiki,
  type MemoryClientOptions,
} from "./mcp-memory-client.js";
import {
  createChatProxyHandler,
  createPolicyEngineMiddleware,
  createPreSendDlpMiddleware,
  createRoutingGateMiddleware,
} from "./proxy-middleware.js";
import { mergeSearchResults } from "./unified-search.js";
import { fetchMemoryServiceHealth } from "./memory-service.js";
import type { ProxyOperationalLogger } from "./ops-log.js";

export type StandaloneServerOptions = {
  host?: string;
  port?: number;
  enableOpsLogs?: boolean;
  allowSanitizedToCopilot?: boolean;
  corsOrigins?: string[];
  authToken?: string;
  localRagBaseUrl?: string;
  localRagTimeoutMs?: number;
  localRagToken?: string;
  memoryBaseUrl?: string;
  memoryMcpPath?: string;
  memoryBearerToken?: string;
  memoryTimeoutMs?: number;
  predictEnabled?: boolean;
  predictBaseDir?: string;
  predictPythonCommand?: string;
  predictTimeoutMs?: number;
  predictMaxUploadMb?: number;
  predictSheetName?: string;
};

const DEFAULT_ALLOWED_ORIGINS = [
  "http://127.0.0.1:4173",
  "http://127.0.0.1:18789",
  "http://localhost:4173",
  "http://localhost:18789",
];

function readCsvList(value: string | undefined): string[] {
  if (!value?.trim()) {
    return [];
  }
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function getRequestAuthToken(req: express.Request): string {
  const direct = req.header("x-ai-proxy-token");
  if (typeof direct === "string" && direct.trim()) {
    return direct.trim();
  }
  const authorization = req.header("authorization");
  const match = authorization?.match(/^Bearer\s+(.+)$/i);
  return match?.[1]?.trim() || "";
}

function createAuthTokenMiddleware(authToken: string): express.RequestHandler {
  const requiredToken = authToken.trim();
  if (!requiredToken) {
    return (_req, _res, next) => next();
  }
  return (req, res, next) => {
    const providedToken = getRequestAuthToken(req);
    if (!providedToken || providedToken !== requiredToken) {
      res.status(401).json({
        error: "PROXY_AUTH_REQUIRED",
        detail: "Missing or invalid AI proxy token.",
      });
      return;
    }
    next();
  };
}

function buildPredictJobResponse(job: {
  jobId: string;
  status: string;
  createdAt: string;
  startedAt?: string;
  finishedAt?: string;
  error?: string;
  summary?: Record<string, unknown>;
  downloadName?: string;
}): Record<string, unknown> {
  return {
    jobId: job.jobId,
    status: job.status,
    createdAt: job.createdAt,
    startedAt: job.startedAt ?? null,
    finishedAt: job.finishedAt ?? null,
    outputFile: job.downloadName ?? null,
    downloadUrl: `/api/hvdc/predict/${job.jobId}/download`,
    statusUrl: `/api/hvdc/predict/${job.jobId}`,
    error: job.error ?? null,
    ...(job.summary ? { summary: job.summary } : {}),
  };
}

function readSingleValue(value: unknown): string {
  if (Array.isArray(value)) {
    const first = value[0];
    return typeof first === "string" ? first.trim() : "";
  }
  return typeof value === "string" ? value.trim() : "";
}

function isLoopbackHost(host: string): boolean {
  const value = host.trim().toLowerCase();
  return value === "127.0.0.1" || value === "localhost" || value === "::1";
}

function isLoopbackOrigin(origin: string): boolean {
  try {
    const url = new URL(origin);
    const hostname = url.hostname.trim().toLowerCase();
    return hostname === "127.0.0.1" || hostname === "localhost" || hostname === "::1";
  } catch {
    return false;
  }
}

export function resolveServerOptionsFromEnv(
  env: NodeJS.ProcessEnv = process.env,
): Required<StandaloneServerOptions> {
  const host = env.MYAGENT_PROXY_HOST?.trim() || "127.0.0.1";
  const port = Number.parseInt(env.MYAGENT_PROXY_PORT ?? "3010", 10);
  const enableOpsLogs = env.MYAGENT_PROXY_OPS_LOGS?.trim() !== "0";
  const allowSanitizedToCopilot =
    env.MYAGENT_PROXY_ALLOW_SANITIZED_TO_COPILOT?.trim() === "1";
  const authToken = env.MYAGENT_PROXY_AUTH_TOKEN?.trim() || "";
  const localRagBaseUrl = env.MYAGENT_LOCAL_RAG_BASE_URL?.trim() || "http://127.0.0.1:8010";
  const localRagTimeoutMs = Number.parseInt(env.MYAGENT_LOCAL_RAG_TIMEOUT_MS ?? "120000", 10);
  const localRagToken =
    env.MYAGENT_LOCAL_RAG_TOKEN?.trim() || env.LOCAL_RAG_SHARED_SECRET?.trim() || "";
  const memoryBaseUrl = env.MYAGENT_MEMORY_BASE_URL?.trim() || "http://127.0.0.1:8000";
  const memoryMcpPath = env.MYAGENT_MEMORY_MCP_PATH?.trim() || "/chatgpt-mcp-write";
  const memoryBearerToken =
    env.MYAGENT_MEMORY_TOKEN?.trim() || env.MYAGENT_MEMORY_BEARER_TOKEN?.trim() || env.MCP_API_TOKEN?.trim() || "";
  const memoryTimeoutMs = Number.parseInt(env.MYAGENT_MEMORY_TIMEOUT_MS ?? "5000", 10);
  const predictEnabled = env.MYAGENT_HVDC_PREDICT_ENABLED?.trim()
    ? env.MYAGENT_HVDC_PREDICT_ENABLED.trim() !== "0"
    : true;
  const predictBaseDir = env.MYAGENT_HVDC_PREDICT_DIR?.trim() || "";
  const predictPythonCommand = env.MYAGENT_HVDC_PREDICT_PYTHON?.trim() || "";
  const predictTimeoutMs = Number.parseInt(env.MYAGENT_HVDC_PREDICT_TIMEOUT_MS ?? "900000", 10);
  const predictMaxUploadMb = Number.parseInt(env.MYAGENT_HVDC_PREDICT_MAX_UPLOAD_MB ?? "25", 10);
  const predictSheetName = env.MYAGENT_HVDC_PREDICT_SHEET_NAME?.trim() || "hvdc all status";
  const corsOrigins = Array.from(
    new Set([...DEFAULT_ALLOWED_ORIGINS, ...readCsvList(env.MYAGENT_PROXY_CORS_ORIGINS)]),
  );
  return {
    host,
    port: Number.isFinite(port) ? port : 3010,
    enableOpsLogs,
    allowSanitizedToCopilot,
    corsOrigins,
    authToken,
    localRagBaseUrl,
    localRagTimeoutMs: Number.isFinite(localRagTimeoutMs) ? localRagTimeoutMs : 120000,
    localRagToken,
    memoryBaseUrl,
    memoryMcpPath,
    memoryBearerToken,
    memoryTimeoutMs: Number.isFinite(memoryTimeoutMs) ? memoryTimeoutMs : 5000,
    predictEnabled,
    predictBaseDir,
    predictPythonCommand,
    predictTimeoutMs: Number.isFinite(predictTimeoutMs) ? predictTimeoutMs : 900000,
    predictMaxUploadMb: Number.isFinite(predictMaxUploadMb) ? predictMaxUploadMb : 25,
    predictSheetName,
  };
}

export function createStandaloneServer(opts?: StandaloneServerOptions) {
  const resolved = {
    ...resolveServerOptionsFromEnv(),
    ...(opts ?? {}),
  };
  if (!isLoopbackHost(resolved.host) && !resolved.authToken.trim()) {
    throw new Error("MYAGENT_PROXY_AUTH_TOKEN is required when binding beyond loopback.");
  }
  const allowedOrigins = new Set(resolved.corsOrigins.map((origin) => origin.trim()).filter(Boolean));
  const requireAuthToken = resolved.authToken.trim().length > 0;
  const logger: ProxyOperationalLogger | undefined = resolved.enableOpsLogs
    ? (entry) => {
        console.log(JSON.stringify(entry));
      }
    : undefined;
  const authTokenMiddleware = createAuthTokenMiddleware(resolved.authToken);
  const memoryClientOptions: MemoryClientOptions = {
    baseUrl: resolved.memoryBaseUrl,
    mcpPath: resolved.memoryMcpPath,
    bearerToken: resolved.memoryBearerToken,
    timeoutMs: resolved.memoryTimeoutMs,
  };
  const predictService = createHvdcPredictService({
    enabled: resolved.predictEnabled,
    ...(resolved.predictBaseDir ? { baseDir: resolved.predictBaseDir } : {}),
    ...(resolved.predictPythonCommand ? { pythonCommand: resolved.predictPythonCommand } : {}),
    timeoutMs: resolved.predictTimeoutMs,
    maxUploadBytes: resolved.predictMaxUploadMb * 1024 * 1024,
    defaultSheetName: resolved.predictSheetName,
  });
  const predictUpload = multer({
    storage: multer.memoryStorage(),
    limits: {
      fileSize: predictService.options.maxUploadBytes,
      files: 1,
    },
    fileFilter: (_req, file, callback) => {
      if (file.originalname.toLowerCase().endsWith(".xlsx")) {
        callback(null, true);
        return;
      }
      callback(new Error("Only .xlsx uploads are supported for HVDC predict jobs."));
    },
  }).single("file");

  const app = express();
  app.use(express.json({ limit: "1mb" }));

  app.use((req, res, next) => {
    const origin = req.header("origin");
    const hasOrigin = typeof origin === "string" && origin.trim().length > 0;
    const normalizedOrigin = hasOrigin ? origin.trim() : "";
    const isLoopbackDevOrigin =
      hasOrigin && isLoopbackHost(resolved.host) && isLoopbackOrigin(normalizedOrigin);
    const isAllowedOrigin =
      hasOrigin && (allowedOrigins.has(normalizedOrigin) || isLoopbackDevOrigin);

    if (hasOrigin && !isAllowedOrigin) {
      res.status(403).json({
        error: "CORS_ORIGIN_DENIED",
        detail: "Origin is not allowed for this proxy.",
      });
      return;
    }

    if (isAllowedOrigin && origin) {
      res.setHeader("Access-Control-Allow-Origin", normalizedOrigin);
      res.setHeader("Vary", "Origin");
    }

    res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
    res.setHeader(
      "Access-Control-Allow-Headers",
      "Content-Type, x-request-id, x-ai-sensitivity, x-ai-proxy-token, ngrok-skip-browser-warning, Authorization",
    );

    if (req.method.toUpperCase() === "OPTIONS") {
      res.status(204).end();
      return;
    }

    next();
  });

  app.get("/api/ai/health", async (req, res) => {
    let copilot: Record<string, unknown>;
    try {
      const auth = resolveGithubAuth();
      copilot = {
        configured: true,
        source: auth.source,
        ...(auth.profileId ? { profileId: auth.profileId } : {}),
      };
    } catch (error) {
      copilot = {
        configured: false,
        error: error instanceof Error ? error.message : String(error),
      };
    }

    const localRag = await fetchLocalRagHealth(
      resolved.localRagBaseUrl,
      resolved.localRagTimeoutMs,
      resolved.localRagToken,
    );
    const memoryService = await fetchMemoryServiceHealth(resolved.memoryBaseUrl, resolved.memoryTimeoutMs);
    let memory: Record<string, unknown> = memoryService;
    let memoryOk = false;
    try {
      const probe = await probeMemoryClient(memoryClientOptions);
      memoryOk = probe.ok;
      memory = {
        ...memoryService,
        probe: "mcp-readonly",
        tools: probe.tools,
      };
    } catch (error) {
      memory = {
        ...memoryService,
        probe: "mcp-readonly",
        error: error instanceof Error ? error.message : String(error),
      };
    }
    const predict = await predictService.getHealth();
    const copilotChatOk = Boolean(copilot.configured as boolean | undefined);
    const localOnlyChatOk = localRag.status === "ok" && localRag.chatRouteReady === true;
    const partialChatOk = copilotChatOk || localOnlyChatOk;
    const chatOk = copilotChatOk && localOnlyChatOk;
    const predictOk = !predict.enabled || predict.configured;
    const basePayload = {
      ok: chatOk && predictOk,
      chatOk,
      partialChatOk,
      copilotChatOk,
      localOnlyChatOk,
      memoryOk,
      predictOk,
      service: "myagent-copilot-standalone",
    };
    const canViewDiagnostics =
      !requireAuthToken || getRequestAuthToken(req) === resolved.authToken;
    if (!canViewDiagnostics) {
      res.json(basePayload);
      return;
    }
    res.json({
      ...basePayload,
      gateway: "up",
      host: resolved.host,
      port: resolved.port,
      authTokenRequired: requireAuthToken,
      origins: Array.from(allowedOrigins),
      copilot,
      localRag,
      memory,
      predict,
    });
  });

  app.get("/api/memory/health", authTokenMiddleware, async (_req, res) => {
    const memoryService = await fetchMemoryServiceHealth(resolved.memoryBaseUrl, resolved.memoryTimeoutMs);
    try {
      const probe = await probeMemoryClient(memoryClientOptions);
      const ok = memoryService.status === "ok" && probe.ok;
      res.status(ok ? 200 : 503).json({
        ok,
        service: "myagent-copilot-standalone-memory-bridge",
        memory: {
          ...memoryService,
          probe: "mcp-readonly",
          tools: probe.tools,
        },
      });
    } catch (error) {
      res.status(503).json({
        ok: false,
        service: "myagent-copilot-standalone-memory-bridge",
        memory: {
          ...memoryService,
          probe: "mcp-readonly",
          error: error instanceof Error ? error.message : String(error),
        },
      });
    }
  });

  app.get("/api/memory/search", authTokenMiddleware, async (req, res) => {
    const query = readSingleValue(req.query.q);
    if (!query) {
      res.status(400).json({
        error: "MEMORY_QUERY_REQUIRED",
        detail: "Pass a non-empty `q` query string.",
      });
      return;
    }
    try {
      const payload = await searchMemory(memoryClientOptions, {
        query,
      });
      res.json(payload);
    } catch (error) {
      res.status(502).json({
        error: "MEMORY_SEARCH_FAILED",
        detail: error instanceof Error ? error.message : String(error),
      });
    }
  });

  app.get("/api/memory/fetch", authTokenMiddleware, async (req, res) => {
    const memoryId = readSingleValue(req.query.id);
    if (!memoryId) {
      res.status(400).json({
        error: "MEMORY_ID_REQUIRED",
        detail: "Pass a non-empty `id` query string.",
      });
      return;
    }
    try {
      const payload = await getMemory(memoryClientOptions, memoryId);
      const isNotFound =
        payload.metadata?.status === "not_found" ||
        (typeof payload.url === "string" && !payload.url && payload.title === "Not found");
      res.status(isNotFound ? 404 : 200).json(payload);
    } catch (error) {
      res.status(502).json({
        error: "MEMORY_FETCH_FAILED",
        detail: error instanceof Error ? error.message : String(error),
      });
    }
  });

  app.get("/api/wiki/search", authTokenMiddleware, async (req, res) => {
    const query = readSingleValue(req.query.q);
    if (!query) {
      res.status(400).json({
        error: "WIKI_QUERY_REQUIRED",
        detail: "Pass a non-empty `q` query string.",
      });
      return;
    }
    try {
      const payload = await searchWiki(memoryClientOptions, {
        query,
        pathPrefix: "wiki/analyses",
        limit: 8,
      });
      res.json(payload);
    } catch (error) {
      res.status(502).json({
        error: "WIKI_SEARCH_FAILED",
        detail: error instanceof Error ? error.message : String(error),
      });
    }
  });

  app.get("/api/wiki/fetch", authTokenMiddleware, async (req, res) => {
    const path = readSingleValue(req.query.path);
    const slug = readSingleValue(req.query.slug);
    if (!path && !slug) {
      res.status(400).json({
        error: "WIKI_PATH_OR_SLUG_REQUIRED",
        detail: "Pass a non-empty `path` or `slug` query string.",
      });
      return;
    }
    try {
      const payload = await fetchWiki(memoryClientOptions, path ? { path } : { slug });
      const isNotFound = payload.status === "not_found";
      res.status(isNotFound ? 404 : 200).json(payload);
    } catch (error) {
      res.status(502).json({
        error: "WIKI_FETCH_FAILED",
        detail: error instanceof Error ? error.message : String(error),
      });
    }
  });

  app.get("/api/search/unified", authTokenMiddleware, async (req, res) => {
    const query = readSingleValue(req.query.q);
    if (!query) {
      res.status(400).json({
        error: "SEARCH_QUERY_REQUIRED",
        detail: "Pass a non-empty `q` query string.",
      });
      return;
    }
    try {
      const [memory, wiki] = await Promise.all([
        searchMemory(memoryClientOptions, { query }),
        searchWiki(memoryClientOptions, {
          query,
          pathPrefix: "wiki/analyses",
          limit: 8,
        }),
      ]);
      const results = mergeSearchResults({
        memory: memory.results,
        wiki: wiki.results,
        limit: 10,
      });
      res.json({
        query,
        results,
        meta: {
          sources_searched: ["memory", "wiki"],
          memory_result_count: memory.results.length,
          wiki_result_count: wiki.results.length,
          merge_strategy: "memory_priority",
        },
      });
    } catch (error) {
      res.status(502).json({
        error: "UNIFIED_SEARCH_FAILED",
        detail: error instanceof Error ? error.message : String(error),
      });
    }
  });

  app.post("/api/memory/save", authTokenMiddleware, async (req, res) => {
    try {
      const body = req.body as Record<string, unknown>;
      if (!body || typeof body.title !== "string" || !body.title.trim()) {
        res.status(400).json({ error: "MEMORY_TITLE_REQUIRED", detail: "title is required and must be non-empty." });
        return;
      }
      if (!body || typeof body.content !== "string" || !body.content.trim()) {
        res.status(400).json({ error: "MEMORY_CONTENT_REQUIRED", detail: "content is required and must be non-empty." });
        return;
      }
      const result = await saveMemory(memoryClientOptions, {
        title: String(body.title).trim(),
        content: String(body.content).trim(),
        source: typeof body.source === "string" ? body.source : "standalone-chat",
        memory_type: typeof body.memory_type === "string" ? body.memory_type : "conversation_summary",
        topics: Array.isArray(body.topics) ? body.topics.map(String) : [],
        entities: Array.isArray(body.entities) ? body.entities.map(String) : [],
        tags: Array.isArray(body.tags) ? body.tags.map(String) : ["standalone", "chat"],
        confidence: typeof body.confidence === "number" ? body.confidence : 0.8,
        sensitivity: typeof body.sensitivity === "string" ? body.sensitivity : "p1",
      });
      res.status(200).json(result);
    } catch (error) {
      res.status(502).json({
        error: "MEMORY_SAVE_FAILED",
        detail: error instanceof Error ? error.message : String(error),
      });
    }
  });

  app.get("/docs", async (_req, res) => {
    const docs = await listStandaloneDocs();
    res.type("html").send(renderDocsIndexHtml(docs));
  });

  app.get("/", (_req, res) => {
    res.type("html").send(renderChatHtml());
  });

  app.get("/chat", (_req, res) => {
    res.type("html").send(renderChatHtml());
  });

  app.get("/docs/view", async (req, res) => {
    const file = readSingleValue(req.query.file);
    const key = file || defaultDocKey();
    const doc = await readStandaloneDoc(key);
    if (!doc) {
      res.status(404).type("html").send(renderDocHtml({
        title: "Document not found",
        key,
        content: `Document not found: ${key}`,
      }));
      return;
    }
    res.type("html").send(
      renderDocHtml({
        title: displayTitleFromDoc(doc.entry),
        key: doc.entry.key,
        content: doc.content,
      }),
    );
  });

  app.post(
    "/api/ai/chat",
    authTokenMiddleware,
    createPolicyEngineMiddleware({ logger }),
    createPreSendDlpMiddleware({
      policy: {
        sanitizeAtOrAbove: "medium",
        blockAtOrAbove: "high",
      },
      logger,
    }),
    createRoutingGateMiddleware({
      policy: {
        defaultSensitivity: "internal",
        minSensitivityForLocalOnly: "secret",
        allowSanitizedToCopilot: resolved.allowSanitizedToCopilot,
      },
      logger,
    }),
    createChatProxyHandler({
      defaultModel: "github-copilot/gpt-5-mini",
      localRunner: async ({ messages, requestId, scope, mode, routeHint, model }) =>
        runLocalRagChat({
          baseUrl: resolved.localRagBaseUrl,
          timeoutMs: resolved.localRagTimeoutMs,
          sharedSecret: resolved.localRagToken,
          requestId,
          messages,
          scope,
          mode,
          routeHint,
          model,
        }),
      logger,
    }),
  );

  app.post("/api/hvdc/predict", authTokenMiddleware, async (req, res) => {
    const predictHealth = await predictService.getHealth();
    if (!predictHealth.enabled || !predictHealth.configured) {
      res.status(503).json({
        error: "PREDICT_UNAVAILABLE",
        detail: predictHealth.reason ?? "Predict worker is not configured.",
      });
      return;
    }

    predictUpload(req, res, async (error) => {
      if (error) {
        const detail =
          error instanceof multer.MulterError && error.code === "LIMIT_FILE_SIZE"
            ? `Excel upload exceeds the ${predictHealth.maxUploadMb} MB limit.`
            : error instanceof Error
              ? error.message
              : "Predict upload failed.";
        res.status(400).json({
          error: "INVALID_PREDICT_UPLOAD",
          detail,
        });
        return;
      }

      if (!req.file) {
        res.status(400).json({
          error: "PREDICT_FILE_REQUIRED",
          detail: "Attach one .xlsx file in the `file` field.",
        });
        return;
      }

      const sheetName = readSingleValue(req.body?.sheetName);

      try {
        const job = await predictService.createJob({
          fileBuffer: req.file.buffer,
          originalFilename: req.file.originalname,
          ...(sheetName ? { sheetName } : {}),
        });
        res.status(202).json(buildPredictJobResponse(job));
      } catch (createError) {
        res.status(500).json({
          error: "PREDICT_JOB_CREATE_FAILED",
          detail: createError instanceof Error ? createError.message : String(createError),
        });
      }
    });
  });

  app.get("/api/hvdc/predict/:jobId", authTokenMiddleware, async (req, res) => {
    const jobId = readSingleValue(req.params.jobId);
    if (!jobId) {
      res.status(400).json({
        error: "PREDICT_JOB_ID_REQUIRED",
        detail: "A predict job id is required.",
      });
      return;
    }

    const job = await predictService.getJob(jobId);
    if (!job) {
      res.status(404).json({
        error: "PREDICT_JOB_NOT_FOUND",
        detail: "Predict job was not found.",
      });
      return;
    }

    res.json(buildPredictJobResponse(job));
  });

  app.post("/api/hvdc/predict/:jobId/cancel", authTokenMiddleware, async (req, res) => {
    const jobId = readSingleValue(req.params.jobId);
    if (!jobId) {
      res.status(400).json({
        error: "PREDICT_JOB_ID_REQUIRED",
        detail: "A predict job id is required.",
      });
      return;
    }

    const job = await predictService.cancelJob(jobId);
    if (!job) {
      res.status(404).json({
        error: "PREDICT_JOB_NOT_FOUND",
        detail: "Predict job was not found.",
      });
      return;
    }

    res.json(buildPredictJobResponse(job));
  });

  app.get("/api/hvdc/predict/:jobId/download", authTokenMiddleware, async (req, res) => {
    const jobId = readSingleValue(req.params.jobId);
    if (!jobId) {
      res.status(400).json({
        error: "PREDICT_JOB_ID_REQUIRED",
        detail: "A predict job id is required.",
      });
      return;
    }

    const job = await predictService.getJob(jobId);
    if (!job) {
      res.status(404).json({
        error: "PREDICT_JOB_NOT_FOUND",
        detail: "Predict job was not found.",
      });
      return;
    }

    if (job.status !== "completed") {
      res.status(409).json({
        error: "PREDICT_JOB_NOT_READY",
        detail: `Predict job is currently ${job.status}.`,
      });
      return;
    }

    res.download(job.outputFile, job.downloadName);
  });

  return {
    app,
    options: resolved,
    start() {
      return new Promise<express.Express["listen"] extends (...args: never[]) => infer T ? T : never>(
        (resolve) => {
          const server = app.listen(resolved.port, resolved.host, () => {
            console.log(`myagent standalone proxy listening: http://${resolved.host}:${resolved.port}`);
            console.log(
              `allow sanitized to copilot: ${resolved.allowSanitizedToCopilot ? "on" : "off"}`,
            );
            console.log(`allowed origins: ${Array.from(allowedOrigins).join(", ")}`);
            console.log(`auth token required: ${requireAuthToken ? "on" : "off"}`);
            console.log(`predict enabled: ${resolved.predictEnabled ? "on" : "off"}`);
            console.log("GET  /");
            console.log("GET  /chat");
            console.log("GET  /docs");
            console.log("GET  /docs/view?file=...");
            console.log("POST /api/ai/chat");
            console.log("GET  /api/ai/health");
            console.log("GET  /api/memory/health");
            console.log("GET  /api/memory/search?q=...");
            console.log("GET  /api/memory/fetch?id=...");
            console.log("GET  /api/wiki/search?q=...");
            console.log("GET  /api/wiki/fetch?path=...");
            console.log("GET  /api/search/unified?q=...");
            console.log("POST /api/hvdc/predict");
            console.log("GET  /api/hvdc/predict/:jobId");
            console.log("POST /api/hvdc/predict/:jobId/cancel");
            console.log("GET  /api/hvdc/predict/:jobId/download");
            resolve(server);
          });
        },
      );
    },
  };
}
