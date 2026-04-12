import { execFile, spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import { constants, createWriteStream, existsSync } from "node:fs";
import { access, readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import {
  createPredictJob,
  getPredictRunsDir,
  markStalePredictJobsFailed,
  readPredictJobRecord,
  savePredictJobRecord,
} from "./hvdc-predict-job-store.js";
import type {
  HvdcPredictHealth,
  HvdcPredictJobRecord,
  HvdcPredictOptions,
  HvdcPredictSummary,
} from "./hvdc-predict-types.js";

const DEFAULT_TIMEOUT_MS = 15 * 60 * 1000;
const DEFAULT_MAX_UPLOAD_MB = 25;
const DEFAULT_SHEET_NAME = "hvdc all status";
const moduleDir = dirname(fileURLToPath(import.meta.url));
const DEFAULT_PREDICT_BASE_DIR = resolve(moduleDir, "../../..", "predict");

export type HvdcPredictServiceOverrides = {
  enabled?: boolean;
  baseDir?: string;
  scriptPath?: string;
  pythonCommand?: string;
  timeoutMs?: number;
  maxUploadBytes?: number;
  defaultSheetName?: string;
};

function parseInteger(value: string | undefined, fallback: number): number {
  const parsed = Number.parseInt(value ?? "", 10);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function resolveDefaultPythonCommand(baseDir: string): string {
  const windowsVenvPython = resolve(baseDir, ".venv", "Scripts", "python.exe");
  if (existsSync(windowsVenvPython)) {
    return windowsVenvPython;
  }
  const unixVenvPython = resolve(baseDir, ".venv", "bin", "python");
  if (existsSync(unixVenvPython)) {
    return unixVenvPython;
  }
  return process.platform === "win32" ? "python" : "python3";
}

async function pathExists(path: string): Promise<boolean> {
  try {
    await access(path, constants.F_OK);
    return true;
  } catch {
    return false;
  }
}

function looksLikePath(value: string): boolean {
  return value.includes("\\") || value.includes("/") || value.endsWith(".exe");
}

async function readSummaryFile(path: string): Promise<HvdcPredictSummary | undefined> {
  try {
    const raw = await readFile(path, "utf8");
    return JSON.parse(raw) as HvdcPredictSummary;
  } catch {
    return undefined;
  }
}

function buildTimeoutMessage(timeoutMs: number): string {
  return `Predict job exceeded timeout (${timeoutMs} ms).`;
}

async function canExecutePythonCommand(command: string): Promise<boolean> {
  return new Promise<boolean>((resolve) => {
    const child = execFile(command, ["--version"], { timeout: 3000 }, (error) => {
      resolve(!error);
    });
    child.on("error", () => resolve(false));
  });
}

export function resolveHvdcPredictOptionsFromEnv(
  env: NodeJS.ProcessEnv = process.env,
  overrides?: HvdcPredictServiceOverrides,
): HvdcPredictOptions {
  const enabled =
    overrides?.enabled ??
    (env.MYAGENT_HVDC_PREDICT_ENABLED?.trim()
      ? env.MYAGENT_HVDC_PREDICT_ENABLED.trim() !== "0"
      : true);
  const baseDir = resolve(overrides?.baseDir ?? env.MYAGENT_HVDC_PREDICT_DIR?.trim() ?? DEFAULT_PREDICT_BASE_DIR);
  const scriptPath = resolve(
    overrides?.scriptPath ?? env.MYAGENT_HVDC_PREDICT_SCRIPT?.trim() ?? resolve(baseDir, "predict2.py"),
  );
  const timeoutMs =
    overrides?.timeoutMs ??
    parseInteger(env.MYAGENT_HVDC_PREDICT_TIMEOUT_MS, DEFAULT_TIMEOUT_MS);
  const maxUploadBytes =
    overrides?.maxUploadBytes ??
    parseInteger(env.MYAGENT_HVDC_PREDICT_MAX_UPLOAD_MB, DEFAULT_MAX_UPLOAD_MB) * 1024 * 1024;
  const defaultSheetName =
    overrides?.defaultSheetName ?? env.MYAGENT_HVDC_PREDICT_SHEET_NAME?.trim() ?? DEFAULT_SHEET_NAME;
  const pythonCommand =
    overrides?.pythonCommand ?? env.MYAGENT_HVDC_PREDICT_PYTHON?.trim() ?? resolveDefaultPythonCommand(baseDir);

  return {
    enabled,
    baseDir,
    runsDir: getPredictRunsDir(baseDir),
    scriptPath,
    pythonCommand,
    timeoutMs,
    maxUploadBytes,
    defaultSheetName,
  };
}

async function buildPredictHealth(options: HvdcPredictOptions): Promise<HvdcPredictHealth> {
  const baseHealth = {
    baseDir: options.baseDir,
    runsDir: options.runsDir,
    scriptPath: options.scriptPath,
    pythonCommand: options.pythonCommand,
    timeoutMs: options.timeoutMs,
    maxUploadMb: Math.max(1, Math.round(options.maxUploadBytes / (1024 * 1024))),
    defaultSheetName: options.defaultSheetName,
    acceptedExtensions: [".xlsx"],
    canCancel: true,
  } satisfies Omit<HvdcPredictHealth, "enabled" | "configured" | "reason">;

  if (!options.enabled) {
    return {
      enabled: false,
      configured: false,
      ...baseHealth,
      reason: "Predict integration is disabled.",
    };
  }

  if (!(await pathExists(options.baseDir))) {
    return {
      enabled: true,
      configured: false,
      ...baseHealth,
      reason: "Predict base directory is missing.",
    };
  }

  if (!(await pathExists(options.scriptPath))) {
    return {
      enabled: true,
      configured: false,
      ...baseHealth,
      reason: "Predict worker script is missing.",
    };
  }

  if (looksLikePath(options.pythonCommand) && !(await pathExists(options.pythonCommand))) {
    return {
      enabled: true,
      configured: false,
      ...baseHealth,
      reason: "Configured Python executable was not found.",
    };
  }

  if (!(await canExecutePythonCommand(options.pythonCommand))) {
    return {
      enabled: true,
      configured: false,
      ...baseHealth,
      reason: "Python command could not be executed.",
    };
  }

  return {
    enabled: true,
    configured: true,
    ...baseHealth,
  };
}

async function updatePredictJob(
  options: HvdcPredictOptions,
  jobId: string,
  patch: Partial<HvdcPredictJobRecord>,
): Promise<HvdcPredictJobRecord | null> {
  const existing = await readPredictJobRecord(options.baseDir, jobId);
  if (!existing) {
    return null;
  }
  const updated = {
    ...existing,
    ...patch,
  };
  await savePredictJobRecord(options.baseDir, updated);
  return updated;
}

export function createHvdcPredictService(overrides?: HvdcPredictServiceOverrides) {
  const options = resolveHvdcPredictOptionsFromEnv(process.env, overrides);
  const activeChildren = new Map<string, ChildProcessWithoutNullStreams>();
  const cancelRequested = new Set<string>();

  async function markCancelled(jobId: string): Promise<HvdcPredictJobRecord | null> {
    cancelRequested.add(jobId);
    const cancelledAt = new Date().toISOString();
    const updated = await updatePredictJob(options, jobId, {
      status: "cancelled",
      finishedAt: cancelledAt,
      error: "Predict job cancelled by user.",
    });
    return updated;
  }

  async function runPredictJob(job: HvdcPredictJobRecord): Promise<void> {
    if (cancelRequested.has(job.jobId)) {
      await markCancelled(job.jobId);
      return;
    }

    const startedAt = new Date().toISOString();
    await updatePredictJob(options, job.jobId, {
      status: "running",
      startedAt,
      finishedAt: undefined,
      error: undefined,
      exitCode: undefined,
    });

    if (cancelRequested.has(job.jobId)) {
      await markCancelled(job.jobId);
      return;
    }

    const stdoutStream = createWriteStream(job.stdoutFile, { flags: "a" });
    const stderrStream = createWriteStream(job.stderrFile, { flags: "a" });

    const child = spawn(
      options.pythonCommand,
      [
        options.scriptPath,
        "--input",
        job.inputFile,
        "--output",
        job.outputFile,
        "--sheet-name",
        job.sheetName,
        "--summary-json",
        job.summaryFile,
      ],
      {
        cwd: options.baseDir,
        env: { ...process.env },
        windowsHide: true,
      },
    );
    activeChildren.set(job.jobId, child);

    let settled = false;
    let timedOut = false;
    const timeout = setTimeout(() => {
      timedOut = true;
      stderrStream.write(`${buildTimeoutMessage(options.timeoutMs)}\n`);
      child.kill();
    }, options.timeoutMs);

    child.stdout.on("data", (chunk) => {
      stdoutStream.write(chunk);
    });
    child.stderr.on("data", (chunk) => {
      stderrStream.write(chunk);
    });

    const finalize = async (params: {
      status: "completed" | "failed" | "cancelled";
      exitCode?: number | null;
      error?: string;
    }) => {
      if (settled) {
        return;
      }
      settled = true;
      clearTimeout(timeout);
      activeChildren.delete(job.jobId);
      const summary = await readSummaryFile(job.summaryFile);
      const existing = await readPredictJobRecord(options.baseDir, job.jobId);
      const finalStatus = existing?.status === "cancelled" || cancelRequested.has(job.jobId)
        ? "cancelled"
        : params.status;
      await updatePredictJob(options, job.jobId, {
        status: finalStatus,
        finishedAt: existing?.finishedAt ?? new Date().toISOString(),
        exitCode: params.exitCode ?? null,
        error: finalStatus === "cancelled" ? existing?.error ?? "Predict job cancelled by user." : params.error,
        summary,
      });
      cancelRequested.delete(job.jobId);
      await Promise.all([
        new Promise<void>((resolve) => stdoutStream.end(resolve)),
        new Promise<void>((resolve) => stderrStream.end(resolve)),
      ]);
    };

    child.on("error", async (error) => {
      await finalize({
        status: cancelRequested.has(job.jobId) ? "cancelled" : "failed",
        exitCode: null,
        error: error.message,
      });
    });

    child.on("close", async (code, signal) => {
      const outputExists = await pathExists(job.outputFile);
      if (cancelRequested.has(job.jobId)) {
        await finalize({
          status: "cancelled",
          exitCode: code,
          error: "Predict job cancelled by user.",
        });
        return;
      }
      if (timedOut) {
        await finalize({
          status: "failed",
          exitCode: code,
          error: buildTimeoutMessage(options.timeoutMs),
        });
        return;
      }

      if (code === 0 && outputExists) {
        await finalize({
          status: "completed",
          exitCode: code,
        });
        return;
      }

      const signalText = signal ? ` (signal: ${signal})` : "";
      await finalize({
        status: "failed",
        exitCode: code,
        error: `Predict worker failed with exit code ${code ?? "null"}${signalText}.`,
      });
    });
  }

  void markStalePredictJobsFailed(options.baseDir);

  return {
    options,
    async getHealth(): Promise<HvdcPredictHealth> {
      return buildPredictHealth(options);
    },
    async createJob(params: {
      fileBuffer: Buffer;
      originalFilename: string;
      sheetName?: string;
    }): Promise<HvdcPredictJobRecord> {
      const job = await createPredictJob({
        baseDir: options.baseDir,
        fileBuffer: params.fileBuffer,
        originalFilename: params.originalFilename,
        sheetName: params.sheetName?.trim() || options.defaultSheetName,
      });
      void runPredictJob(job);
      return job;
    },
    async getJob(jobId: string): Promise<HvdcPredictJobRecord | null> {
      return readPredictJobRecord(options.baseDir, jobId);
    },
    async cancelJob(jobId: string): Promise<HvdcPredictJobRecord | null> {
      const existing = await readPredictJobRecord(options.baseDir, jobId);
      if (!existing) {
        return null;
      }
      if (existing.status === "completed" || existing.status === "failed" || existing.status === "cancelled") {
        return existing;
      }
      const activeChild = activeChildren.get(jobId);
      const updated = await markCancelled(jobId);
      if (activeChild) {
        activeChild.kill();
      }
      return updated;
    },
  };
}
