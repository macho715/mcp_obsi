export type HvdcPredictJobStatus = "queued" | "running" | "completed" | "failed" | "cancelled";

export type HvdcPredictSummary = {
  inputFile?: string;
  outputFile?: string;
  sheetName?: string;
  rows?: number;
  predictedHighRiskRows?: number;
  predictedExpediteRows?: number;
  validation?: {
    trainRows?: number;
    testRows?: number;
    accuracy?: number;
    rocAuc?: number | null;
    regressionMaeDays?: number;
  };
};

export type HvdcPredictJobRecord = {
  jobId: string;
  status: HvdcPredictJobStatus;
  createdAt: string;
  startedAt?: string;
  finishedAt?: string;
  originalFilename: string;
  sheetName: string;
  inputFile: string;
  outputFile: string;
  summaryFile: string;
  stdoutFile: string;
  stderrFile: string;
  downloadName: string;
  exitCode?: number | null;
  error?: string;
  summary?: HvdcPredictSummary;
};

export type HvdcPredictOptions = {
  enabled: boolean;
  baseDir: string;
  runsDir: string;
  scriptPath: string;
  pythonCommand: string;
  timeoutMs: number;
  maxUploadBytes: number;
  defaultSheetName: string;
};

export type HvdcPredictHealth = {
  enabled: boolean;
  configured: boolean;
  baseDir: string;
  runsDir: string;
  scriptPath: string;
  pythonCommand: string;
  timeoutMs: number;
  maxUploadMb: number;
  defaultSheetName: string;
  acceptedExtensions: string[];
  canCancel: boolean;
  modelVersion?: string;
  reason?: string;
};
