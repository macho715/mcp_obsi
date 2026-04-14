import { readdir, readFile } from "node:fs/promises";
import { basename, extname, resolve } from "node:path";
import { dirname } from "node:path";
import { fileURLToPath } from "node:url";

export type StandaloneDocEntry = {
  key: string;
  label: string;
  path: string;
};

const moduleDir = dirname(fileURLToPath(import.meta.url));
const packageDir = resolve(moduleDir, "..");
const docsDir = resolve(packageDir, "docs");

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function titleFromFilename(filename: string): string {
  return filename.replace(/\.md$/i, "");
}

export async function listStandaloneDocs(): Promise<StandaloneDocEntry[]> {
  const entries: StandaloneDocEntry[] = [
    {
      key: "README.md",
      label: "README",
      path: resolve(packageDir, "README.md"),
    },
    {
      key: "OPERATIONS.md",
      label: "OPERATIONS",
      path: resolve(packageDir, "OPERATIONS.md"),
    },
    {
      key: "MIGRATION.md",
      label: "MIGRATION",
      path: resolve(packageDir, "MIGRATION.md"),
    },
  ];

  const docsFiles = await readdir(docsDir, { withFileTypes: true });
  for (const entry of docsFiles) {
    if (!entry.isFile() || extname(entry.name).toLowerCase() !== ".md") {
      continue;
    }
    entries.push({
      key: `docs/${entry.name}`,
      label: titleFromFilename(entry.name),
      path: resolve(docsDir, entry.name),
    });
  }

  return entries.sort((a, b) => a.key.localeCompare(b.key));
}

export async function getStandaloneDoc(key: string): Promise<StandaloneDocEntry | null> {
  const docs = await listStandaloneDocs();
  return docs.find((entry) => entry.key === key) ?? null;
}

export async function readStandaloneDoc(key: string): Promise<{ entry: StandaloneDocEntry; content: string } | null> {
  const entry = await getStandaloneDoc(key);
  if (!entry) {
    return null;
  }
  const content = await readFile(entry.path, "utf8");
  return { entry, content };
}

export function renderDocsIndexHtml(entries: StandaloneDocEntry[]): string {
  const items = entries
    .map(
      (entry) =>
        `<li><a href="/docs/view?file=${encodeURIComponent(entry.key)}">${escapeHtml(entry.label)}</a><code>${escapeHtml(entry.key)}</code></li>`,
    )
    .join("");

  return `<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Standalone Docs</title>
  <style>
    :root { color-scheme: light; }
    body { margin: 0; font-family: "Segoe UI", sans-serif; background: #f5f1e8; color: #1f2937; }
    main { max-width: 960px; margin: 0 auto; padding: 40px 20px 60px; }
    h1 { margin: 0 0 8px; font-size: 2rem; }
    p { margin: 0 0 24px; color: #4b5563; }
    ul { list-style: none; padding: 0; margin: 0; display: grid; gap: 12px; }
    li { display: flex; justify-content: space-between; gap: 16px; align-items: center; background: #fffdf8; border: 1px solid #e5dcc8; border-radius: 14px; padding: 14px 16px; }
    a { color: #7c2d12; font-weight: 600; text-decoration: none; }
    a:hover { text-decoration: underline; }
    code { color: #6b7280; font-size: 0.9rem; }
  </style>
</head>
<body>
  <main>
    <h1>Standalone Docs</h1>
    <p>브라우저에서 같은 창으로 문서를 보려면 아래 링크를 사용하십시오.</p>
    <ul>${items}</ul>
  </main>
</body>
</html>`;
}

export function renderChatHtml(): string {
  return `<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Standalone Chat</title>
  <style>
    :root { color-scheme: light; }
    body { margin: 0; font-family: "Segoe UI", sans-serif; background: #f5f1e8; color: #1f2937; }
    main { max-width: 900px; margin: 0 auto; padding: 24px 16px 48px; }
    h1 { margin: 0 0 8px; font-size: 1.8rem; }
    p { margin: 0 0 16px; color: #4b5563; }
    .card { background: #fffdf8; border: 1px solid #e5dcc8; border-radius: 14px; padding: 14px; margin-bottom: 12px; }
    textarea { width: 100%; min-height: 110px; resize: vertical; border: 1px solid #d8ccb3; border-radius: 10px; padding: 10px; font-size: 14px; box-sizing: border-box; }
    .controls { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
    .controls select { border: 1px solid #d8ccb3; border-radius: 10px; padding: 10px; font-size: 13px; }
    .controls input[type="password"] { flex: 1; min-width: 200px; border: 1px solid #d8ccb3; border-radius: 10px; padding: 10px; font-size: 13px; }
    button { border: 0; border-radius: 10px; background: #7c2d12; color: #fff; padding: 10px 14px; font-weight: 600; cursor: pointer; }
    button:disabled { opacity: 0.6; cursor: wait; }
    button.secondary { background: #6b7280; }
    button.clear-btn { background: #dc2626; }
    .status { color: #6b7280; font-size: 13px; }
    pre { white-space: pre-wrap; word-break: break-word; background: #fff; border: 1px solid #e5dcc8; border-radius: 10px; padding: 12px; min-height: 110px; }
    ul { margin: 0; padding-left: 18px; }
    code { color: #6b7280; }
    a { color: #7c2d12; text-decoration: none; }
    #error-banner { display: none; background: #fef2f2; border: 1px solid #fca5a5; border-radius: 10px; padding: 10px 14px; color: #991b1b; font-size: 13px; margin-bottom: 10px; }
    #chat-history { max-height: 400px; overflow-y: auto; margin-bottom: 10px; }
    .msg-user { text-align: right; margin-bottom: 8px; }
    .msg-user .bubble { display: inline-block; background: #7c2d12; color: #fff; border-radius: 12px 12px 4px 12px; padding: 8px 12px; max-width: 80%; text-align: left; }
    .msg-assistant .bubble { display: inline-block; background: #fff; border: 1px solid #e5dcc8; border-radius: 12px 12px 12px 4px; padding: 8px 12px; max-width: 80%; text-align: left; }
    .msg-role { font-size: 11px; color: #9ca3af; margin-bottom: 2px; }
    .spinner { display: none; width: 16px; height: 16px; border: 2px solid #e5dcc8; border-top-color: #7c2d12; border-radius: 50%; animation: spin 0.6s linear infinite; margin-right: 8px; vertical-align: middle; }
    @keyframes spin { to { transform: rotate(360deg); } }
  </style>
</head>
<body>
  <main>
    <h1>Standalone Chat</h1>
    <p>질문을 입력하면 <code>POST /api/ai/chat</code>로 바로 호출합니다. <a href="/docs">문서 보기</a></p>

    <div id="error-banner"></div>

    <div class="card">
      <div id="chat-history"></div>
      <textarea id="prompt" placeholder="예: HVDC 계획 문서 최근 내용 요약해줘"></textarea>
      <div class="controls" style="margin-top:10px">
        <select id="model-select" title="모델 선택">
          <option value="gemma4:e4b">gemma4:e4b (기본)</option>
          <option value="gemma4:e2b">gemma4:e2b (경량)</option>
        </select>
        <input id="token" type="password" placeholder="선택: x-ai-proxy-token (서버 auth 사용 시 입력)" />
        <button id="clear-chat" class="clear-btn" type="button">채팅 지우기</button>
      </div>
      <div class="controls" style="margin-top:10px">
        <button id="send" type="button">
          <span class="spinner" id="spinner"></span>
          질문 보내기
        </button>
        <span class="status" id="status">대기 중</span>
      </div>
    </div>
    <div class="card">
      <strong>응답</strong>
      <pre id="answer"></pre>
      <div style="margin-top:10px">
        <button id="save-memory" class="secondary" type="button" style="display:none">이 대화를 메모리에 저장</button>
        <span id="memory-indicator" style="display:none; color:#059669; font-size:13px; margin-left:10px"></span>
      </div>
    </div>
    <div class="card">
      <strong>Unified Search</strong>
      <div class="controls" style="margin-top:10px">
        <input id="search-query" type="text" placeholder="예: hazmat shu 2025-11-26" />
        <button id="run-search" class="secondary" type="button">검색</button>
      </div>
      <ul id="search-results" style="margin-top:10px"></ul>
    </div>
    <div class="card">
      <strong>근거 문서</strong>
      <ul id="sources"></ul>
    </div>
  </main>
  <script>
    const HISTORY_KEY = "chat_history_v1";
    const TOKEN_KEY = "chat_token_v1";
    const MODEL_KEY = "chat_model_v1";
    const MAX_HISTORY = 50;

    const chatHistoryEl = document.getElementById("chat-history");
    const promptEl = document.getElementById("prompt");
    const modelSelectEl = document.getElementById("model-select");
    const tokenEl = document.getElementById("token");
    const sendEl = document.getElementById("send");
    const clearEl = document.getElementById("clear-chat");
    const statusEl = document.getElementById("status");
    const answerEl = document.getElementById("answer");
    const sourcesEl = document.getElementById("sources");
    const errorBannerEl = document.getElementById("error-banner");
    const spinnerEl = document.getElementById("spinner");
    const saveMemEl = document.getElementById("save-memory");
    const memIndicatorEl = document.getElementById("memory-indicator");
    const searchQueryEl = document.getElementById("search-query");
    const runSearchEl = document.getElementById("run-search");
    const searchResultsEl = document.getElementById("search-results");

    // Load persisted state
    function loadHistory() {
      try {
        const raw = localStorage.getItem(HISTORY_KEY);
        return raw ? JSON.parse(raw) : [];
      } catch { return []; }
    }
    function saveHistory(msgs) {
      try { localStorage.setItem(HISTORY_KEY, JSON.stringify(msgs.slice(-MAX_HISTORY))); } catch {}
    }
    function loadToken() { return localStorage.getItem(TOKEN_KEY) || ""; }
    function saveToken(t) { try { localStorage.setItem(TOKEN_KEY, t); } catch {} }
    function loadModel() { return localStorage.getItem(MODEL_KEY) || "gemma4:e4b"; }

    // Render
    function renderHistory(msgs) {
      chatHistoryEl.innerHTML = "";
      msgs.forEach(function(msg) {
        var div = document.createElement("div");
        div.className = "msg-" + msg.role;
        var roleLabel = msg.role === "user" ? "사용자" : "AI";
        div.innerHTML = '<div class="msg-role">' + roleLabel + '</div><div class="bubble">' + escapeHtml(String(msg.content || "")) + "</div>";
        chatHistoryEl.appendChild(div);
      });
      chatHistoryEl.scrollTop = chatHistoryEl.scrollHeight;
    }

    function escapeHtml(v) {
      return v.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;");
    }

    function setBusy(isBusy) {
      sendEl.disabled = isBusy;
      spinnerEl.style.display = isBusy ? "inline-block" : "none";
      statusEl.textContent = isBusy ? "요청 중..." : "대기 중";
    }

    function showError(msg) {
      errorBannerEl.textContent = msg;
      errorBannerEl.style.display = "block";
    }
    function hideError() {
      errorBannerEl.style.display = "none";
    }

    function renderSources(sources) {
      sourcesEl.innerHTML = "";
      if (!Array.isArray(sources) || sources.length === 0) {
        var li = document.createElement("li");
        li.textContent = "없음";
        sourcesEl.appendChild(li);
        return;
      }
      sources.forEach(function(item) {
        var li = document.createElement("li");
        var file = item && typeof item.file === "string" ? item.file : "(unknown)";
        var score = item && typeof item.score !== "undefined" ? String(item.score) : "-";
        li.textContent = file + " (score: " + score + ")";
        sourcesEl.appendChild(li);
      });
    }

    function renderSearchResults(items, headers) {
      searchResultsEl.innerHTML = "";
      if (!Array.isArray(items) || items.length === 0) {
        var empty = document.createElement("li");
        empty.textContent = "검색 결과 없음";
        searchResultsEl.appendChild(empty);
        return;
      }
      items.forEach(function(item) {
        var li = document.createElement("li");
        li.style.marginBottom = "8px";
        var button = document.createElement("button");
        button.type = "button";
        button.className = "secondary";
        var badges = Array.isArray(item.badges) ? item.badges.map(function(badge) {
          return "[" + badge + "]";
        }).join("") : "";
        button.textContent = badges + " " + (item.title || "(untitled)");
        button.addEventListener("click", async function() {
          var route = item.source === "wiki"
            ? "/api/wiki/fetch?path=" + encodeURIComponent(String(item.path || "").replace(/\.md$/, ""))
            : "/api/memory/fetch?id=" + encodeURIComponent(String(item.id || ""));
          var fetchRes = await fetch(route, { headers: headers });
          var fetchPayload = await fetchRes.json();
          answerEl.textContent = fetchPayload.body || fetchPayload.text || JSON.stringify(fetchPayload, null, 2);
        });
        li.appendChild(button);
        if (item.path) {
          var meta = document.createElement("div");
          meta.className = "status";
          meta.textContent = String(item.path);
          li.appendChild(meta);
        }
        searchResultsEl.appendChild(li);
      });
    }

    // Init
    var messages = loadHistory();
    var lastAnswer = "";
    renderHistory(messages);
    var savedToken = loadToken();
    if (savedToken) { tokenEl.value = savedToken; }
    var savedModel = loadModel();
    modelSelectEl.value = savedModel;

    // Events
    sendEl.addEventListener("click", async function() {
      var text = promptEl.value.trim();
      if (!text) { statusEl.textContent = "질문을 입력하세요."; return; }
      hideError();
      setBusy(true);
      answerEl.textContent = "";
      sourcesEl.innerHTML = "";
      var userMsg = { role: "user", content: text };
      messages.push(userMsg);
      renderHistory(messages);
      saveHistory(messages);
      promptEl.value = "";
      try {
        var model = modelSelectEl.value || "gemma4:e4b";
        var tokenVal = tokenEl && typeof tokenEl.value === "string" ? tokenEl.value.trim() : "";
        if (tokenVal) { saveToken(tokenVal); } else { localStorage.removeItem(TOKEN_KEY); }
        localStorage.setItem(MODEL_KEY, model);
        var headers = { "Content-Type": "application/json" };
        if (tokenVal) { headers["x-ai-proxy-token"] = tokenVal; }
        var body = JSON.stringify({
          messages: [{ role: "user", content: text }],
          model: model,
          mode: "chat",
          routeHint: "local",
        });
        var response = await fetch("/api/ai/chat", { method: "POST", headers: headers, body: body });
        var payload = await response.json();
        if (!response.ok) {
          showError("오류: HTTP " + response.status + " — " + (payload && payload.error ? payload.error : JSON.stringify(payload)));
          statusEl.textContent = "오류";
          return;
        }
        var resultText = payload && payload.result && typeof payload.result.text === "string"
          ? payload.result.text
          : JSON.stringify(payload, null, 2);
        var assistantMsg = { role: "assistant", content: resultText };
        messages.push(assistantMsg);
        renderHistory(messages);
        saveHistory(messages);
        answerEl.textContent = resultText;
        lastAnswer = resultText;
        renderSources(payload ? payload.sources : []);
        statusEl.textContent = "완료";
        if (saveMemEl) { saveMemEl.style.display = "inline-block"; }
        if (memIndicatorEl) { memIndicatorEl.style.display = "none"; }
      } catch(error) {
        showError("네트워크 오류: " + String(error));
        statusEl.textContent = "네트워크 오류";
      } finally {
        setBusy(false);
      }
    });

    clearEl.addEventListener("click", function() {
      messages = [];
      saveHistory(messages);
      renderHistory(messages);
      answerEl.textContent = "";
      sourcesEl.innerHTML = "";
      searchResultsEl.innerHTML = "";
      hideError();
      statusEl.textContent = "채팅 지워짐";
      if (saveMemEl) { saveMemEl.style.display = "none"; }
      if (memIndicatorEl) { memIndicatorEl.style.display = "none"; }
    });

    runSearchEl && runSearchEl.addEventListener("click", async function() {
      var query = searchQueryEl && typeof searchQueryEl.value === "string" ? searchQueryEl.value.trim() : "";
      if (!query) { return; }
      hideError();
      var headers = {};
      var tokenVal = tokenEl && typeof tokenEl.value === "string" ? tokenEl.value.trim() : "";
      if (tokenVal) { headers["x-ai-proxy-token"] = tokenVal; }
      try {
        var response = await fetch("/api/search/unified?q=" + encodeURIComponent(query), { headers: headers });
        var payload = await response.json();
        if (!response.ok) {
          showError("검색 오류: HTTP " + response.status + " — " + (payload && payload.error ? payload.error : JSON.stringify(payload)));
          return;
        }
        renderSearchResults(payload.results || [], headers);
      } catch (error) {
        showError("검색 네트워크 오류: " + String(error));
      }
    });

    // Show save button when answer is ready
    var lastAnswer = "";
    var originalSetBusy = setBusy;
    // Intercept: when answer is set, show save button
    var answerText = "";
    Object.defineProperty(window, "__answerText", {
      get: function() { return answerText; },
      set: function(v) { answerText = v; if (v && v.trim()) { if (saveMemEl) { saveMemEl.style.display = "inline-block"; } } }
    });

    saveMemEl && saveMemEl.addEventListener("click", async function() {
      if (!lastAnswer || !messages.length) return;
      if (saveMemEl) { saveMemEl.disabled = true; saveMemEl.textContent = "저장 중..."; }
      try {
        var tokenVal2 = tokenEl && typeof tokenEl.value === "string" ? tokenEl.value.trim() : "";
        var saveHeaders = { "Content-Type": "application/json" };
        if (tokenVal2) { saveHeaders["x-ai-proxy-token"] = tokenVal2; }
        var lastUser = "";
        for (var i = messages.length - 1; i >= 0; i--) {
          if (messages[i].role === "user") { lastUser = messages[i].content; break; }
        }
        var saveBody = JSON.stringify({
          title: "[Chat] " + (lastUser ? lastUser.slice(0, 60) : "standalone chat"),
          content: "User: " + (lastUser || "N/A") + "\\n\\nAI: " + (lastAnswer || "N/A"),
          source: "standalone-chat",
          topics: ["standalone", "chat"],
        });
        var saveRes = await fetch("/api/memory/save", {
          method: "POST",
          headers: saveHeaders,
          body: saveBody,
        });
        if (saveRes.ok) {
          if (memIndicatorEl) { memIndicatorEl.textContent = "메모리에 저장됨 ✓"; memIndicatorEl.style.display = "inline"; }
          if (saveMemEl) { saveMemEl.style.display = "none"; }
        } else {
          var errJson = await saveRes.json().catch(function() { return {}; });
          if (memIndicatorEl) { memIndicatorEl.textContent = "저장 실패: HTTP " + saveRes.status; memIndicatorEl.style.color = "#dc2626"; memIndicatorEl.style.display = "inline"; }
        }
      } catch(ex) {
        if (memIndicatorEl) { memIndicatorEl.textContent = "저장 실패: " + String(ex); memIndicatorEl.style.color = "#dc2626"; memIndicatorEl.style.display = "inline"; }
      } finally {
        if (saveMemEl) { saveMemEl.disabled = false; saveMemEl.textContent = "이 대화를 메모리에 저장"; }
      }
    });
  </script>
</body>
</html>`;
}

export function renderDocHtml(params: {
  title: string;
  key: string;
  content: string;
}): string {
  return `<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>${escapeHtml(params.title)}</title>
  <style>
    :root { color-scheme: light; }
    body { margin: 0; font-family: "Segoe UI", sans-serif; background: #f5f1e8; color: #111827; }
    header { position: sticky; top: 0; background: rgba(245, 241, 232, 0.96); backdrop-filter: blur(6px); border-bottom: 1px solid #e5dcc8; }
    .bar { max-width: 1100px; margin: 0 auto; padding: 14px 20px; display: flex; gap: 16px; align-items: center; justify-content: space-between; }
    .meta { display: flex; flex-direction: column; gap: 4px; }
    .meta strong { font-size: 1rem; }
    .meta code { color: #6b7280; }
    a { color: #7c2d12; text-decoration: none; font-weight: 600; }
    a:hover { text-decoration: underline; }
    main { max-width: 1100px; margin: 0 auto; padding: 24px 20px 48px; }
    pre { white-space: pre-wrap; word-break: break-word; background: #fffdf8; border: 1px solid #e5dcc8; border-radius: 16px; padding: 20px; line-height: 1.55; font-family: Consolas, "Courier New", monospace; font-size: 14px; overflow: auto; }
  </style>
</head>
<body>
  <header>
    <div class="bar">
      <div class="meta">
        <strong>${escapeHtml(params.title)}</strong>
        <code>${escapeHtml(params.key)}</code>
      </div>
      <a href="/docs">문서 목록</a>
    </div>
  </header>
  <main>
    <pre>${escapeHtml(params.content)}</pre>
  </main>
</body>
</html>`;
}

export function defaultDocKey(): string {
  return "docs/docs.md";
}

export function displayTitleFromDoc(entry: StandaloneDocEntry): string {
  return titleFromFilename(basename(entry.key));
}
