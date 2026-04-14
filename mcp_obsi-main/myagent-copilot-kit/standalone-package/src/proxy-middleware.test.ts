import assert from "node:assert/strict";
import test from "node:test";
import { createChatProxyHandler } from "./proxy-middleware.js";

function createMockResponse() {
  return {
    locals: {},
    statusCode: 200,
    payload: undefined as unknown,
    status(code: number) {
      this.statusCode = code;
      return this;
    },
    json(payload: unknown) {
      this.payload = payload;
      return this;
    },
  };
}

function createMockRequest(body: Record<string, unknown>) {
  return {
    body,
    header() {
      return undefined;
    },
  };
}

test("local route defaults to gemma4:e4b when model is omitted", async () => {
  let receivedModel = "";
  const handler = createChatProxyHandler({
    localRunner: async ({ model }) => {
      receivedModel = model;
      return { text: "ok", model, provider: "local-rag" };
    },
  });
  const req = createMockRequest({
    messages: [{ role: "user", content: "KB 요약해줘" }],
    sensitivity: "secret",
    scope: ["kb"],
  });
  const res = createMockResponse();

  await handler(req as any, res as any, (() => {}) as any);

  assert.equal(receivedModel, "gemma4:e4b");
  assert.equal(res.statusCode, 200);
});

test("local route keeps an explicit model override", async () => {
  let receivedModel = "";
  const handler = createChatProxyHandler({
    localRunner: async ({ model }) => {
      receivedModel = model;
      return { text: "ok", model, provider: "local-rag" };
    },
  });
  const req = createMockRequest({
    messages: [{ role: "user", content: "KB 요약해줘" }],
    sensitivity: "secret",
    scope: ["kb"],
    model: "gemma4:e2b",
  });
  const res = createMockResponse();

  await handler(req as any, res as any, (() => {}) as any);

  assert.equal(receivedModel, "gemma4:e2b");
  assert.equal(res.statusCode, 200);
});
