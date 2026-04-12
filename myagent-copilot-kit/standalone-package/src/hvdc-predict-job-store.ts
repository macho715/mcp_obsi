import { randomUUID } from "node:crypto";
import { mkdir, readdir, readFile, writeFile } from "node:fs/promises";
import { basename, join } from "node:path";
import type { HvdcPredictJobRecord } from "./hvdc-predict-types.js";

const JOB_STATE_FILE = "job.json";
const DEFAULT_INPUT_NAME = "hvdc-status.xlsx";
const DEFAULT_OUTPUT_NAME = "hvdc_status_with_ai_prediction_v2.xlsx";
const DEFAULT_SUMMARY_NAME = "summary.json";
const DEFAULT_STDOUT_NAME = "stdout.log";
const DEFAULT_STDERR_NAME = "stderr.log";

export function getPredictRunsDir(baseDir: string): string {
  return join(baseDir, "runs");
}

export function getPredictJobDir(baseDir: string, jobId: string): string {
  return join(getPredictRunsDir(baseDir), jobId);
}

export function getPredictJobStatePath(baseDir: string, jobId: string): string {
  return join(getPredictJobDir(baseDir, jobId), JOB_STATE_FILE);
}

async function ensureDirectory(path: string): Promise<void> {
  await mkdir(path, { recursive: true });
}

export async function savePredictJobRecord(baseDir: string, job: HvdcPredictJobRecord): Promise<void> {
  await ensureDirectory(getPredictJobDir(baseDir, job.jobId));
  await writeFile(getPredictJobStatePath(baseDir, job.jobId), JSON.stringify(job, null, 2), "utf8");
}

export async function readPredictJobRecord(
  baseDir: string,
  jobId: string,
): Promise<HvdcPredictJobRecord | null> {
  try {
    const raw = await readFile(getPredictJobStatePath(baseDir, jobId), "utf8");
    return JSON.parse(raw) as HvdcPredictJobRecord;
  } catch {
    return null;
  }
}

export async function createPredictJob(params: {
  baseDir: string;
  fileBuffer: Buffer;
  originalFilename: string;
  sheetName: string;
}): Promise<HvdcPredictJobRecord> {
  const jobId = randomUUID();
  const jobDir = getPredictJobDir(params.baseDir, jobId);
  const inputDir = join(jobDir, "input");
  const outputDir = join(jobDir, "output");

  await ensureDirectory(inputDir);
  await ensureDirectory(outputDir);

  const inputFile = join(inputDir, DEFAULT_INPUT_NAME);
  const outputFile = join(outputDir, DEFAULT_OUTPUT_NAME);
  const summaryFile = join(jobDir, DEFAULT_SUMMARY_NAME);
  const stdoutFile = join(jobDir, DEFAULT_STDOUT_NAME);
  const stderrFile = join(jobDir, DEFAULT_STDERR_NAME);

  await writeFile(inputFile, params.fileBuffer);

  const job: HvdcPredictJobRecord = {
    jobId,
    status: "queued",
    createdAt: new Date().toISOString(),
    originalFilename: basename(params.originalFilename || DEFAULT_INPUT_NAME),
    sheetName: params.sheetName,
    inputFile,
    outputFile,
    summaryFile,
    stdoutFile,
    stderrFile,
    downloadName: DEFAULT_OUTPUT_NAME,
  };

  await savePredictJobRecord(params.baseDir, job);
  return job;
}

export async function markStalePredictJobsFailed(baseDir: string): Promise<void> {
  try {
    const runsDir = getPredictRunsDir(baseDir);
    const entries = await readdir(runsDir, { withFileTypes: true });
    const now = new Date().toISOString();

    for (const entry of entries) {
      if (!entry.isDirectory()) {
        continue;
      }
      const job = await readPredictJobRecord(baseDir, entry.name);
      if (!job) {
        continue;
      }
      if (job.status !== "queued" && job.status !== "running") {
        continue;
      }
      await savePredictJobRecord(baseDir, {
        ...job,
        status: "failed",
        finishedAt: now,
        error: "Standalone service restarted before the predict job finished.",
      });
    }
  } catch {
    // Fresh installs simply have no runs directory yet.
  }
}
