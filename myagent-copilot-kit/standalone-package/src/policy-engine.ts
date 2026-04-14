import type { RouteHint } from "./routing.js";

export type PolicyResult = {
  allow: boolean;
  blockReason?: string;
  routeHintOverride?: RouteHint;
  flags: string[];
};

const DISALLOWED_KEYWORDS = [
  "승인",
  "결재",
  "통관 확정",
  "결정해줘",
  "허가",
  "release cargo",
  "approve",
  "authorize",
  "customs clearance decision",
];

function getLastUserContent(body: { messages?: Array<{ role?: string; content?: string }> }): string {
  const messages = body.messages;
  if (!Array.isArray(messages) || messages.length === 0) return "";
  for (let i = messages.length - 1; i >= 0; i--) {
    const m = messages[i];
    if (m?.role === "user" && typeof m.content === "string") {
      return m.content;
    }
  }
  return "";
}

function hasDisallowedKeyword(text: string): boolean {
  const lowered = text.toLowerCase();
  return DISALLOWED_KEYWORDS.some((kw) => lowered.includes(kw.toLowerCase()));
}

/**
 * Evaluate request against policy: read-only enforcement, auto-decision block, flags.
 * Runs before DLP and routing. Blocked requests must receive 403 and not be sent to Copilot or Local RAG.
 */
export function evaluateRequest(body: {
  messages?: Array<{ role?: string; content?: string }>;
  mode?: string;
  routeHint?: string;
  scope?: unknown;
}): PolicyResult {
  const lastContent = getLastUserContent(body);
  const flags: string[] = [];

  if (body.mode !== undefined && body.mode !== "read_only" && String(body.mode).trim().toLowerCase() !== "read_only") {
    flags.push("read_only_enforced");
  }

  if (hasDisallowedKeyword(lastContent)) {
    flags.push("approval_required");
    return {
      allow: false,
      blockReason:
        "AMBER: 승인, 통관 확정, 비용 결정은 자동화할 수 없습니다. 근거 문서 검토 후 담당자 판단과 승인 절차로 넘기십시오.",
      routeHintOverride: "local",
      flags,
    };
  }

  return { allow: true, flags };
}
