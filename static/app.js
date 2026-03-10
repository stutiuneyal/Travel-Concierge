const askForm = document.getElementById("askForm");
const queryInput = document.getElementById("query");
const askBtn = document.getElementById("askBtn");
const sampleBtn = document.getElementById("sampleBtn");
const clearConversationBtn = document.getElementById("clearConversationBtn");
const statusEl = document.getElementById("status");
const queryError = document.getElementById("queryError");
const charCount = document.getElementById("charCount");
const btnLoader = document.getElementById("btnLoader");
const askBtnContent = document.getElementById("askBtnContent");
const chatFeed = document.getElementById("chatFeed");

const MAX_QUERY_LENGTH = 1600;
const SAMPLE_PROMPT =
  "I’m traveling to Japan next week. What time is it there right now, upcoming public holidays, INR to JPY rate, and basic facts I should know?";

const SESSION_STORAGE_KEY = "travel_concierge_session_id";

let activeController = null;
let loadingMessageId = null;

function generateSessionId() {
  if (window.crypto?.randomUUID) {
    return window.crypto.randomUUID();
  }
  return `session-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function getSessionId() {
  let sessionId = localStorage.getItem(SESSION_STORAGE_KEY);
  if (!sessionId) {
    sessionId = generateSessionId();
    localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
  }
  return sessionId;
}

function resetSessionId() {
  const newSessionId = generateSessionId();
  localStorage.setItem(SESSION_STORAGE_KEY, newSessionId);
  return newSessionId;
}

function escapeHtml(value = "") {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderMarkdownSafely(markdown = "") {
  if (!markdown || typeof markdown !== "string") {
    return "<p>No content available.</p>";
  }

  const rawHtml = marked.parse(markdown, {
    breaks: true,
    gfm: true
  });

  return DOMPurify.sanitize(rawHtml);
}

function scrollChatToBottom() {
  requestAnimationFrame(() => {
    window.scrollTo({
      top: document.body.scrollHeight,
      behavior: "smooth"
    });
  });
}

function createMessageWrapper(role, innerHtml, extraClass = "") {
  const wrapper = document.createElement("div");
  wrapper.className = `message ${role}-message ${extraClass}`.trim();
  wrapper.innerHTML = innerHtml;
  return wrapper;
}

function appendUserMessage(text) {
  const safeHtml = renderMarkdownSafely(text);
  const node = createMessageWrapper(
    "user",
    `
      <div class="message-avatar user-avatar">
        <i data-lucide="user"></i>
      </div>
      <div class="message-card">
        <div class="message-meta">You</div>
        <div class="message-body markdown-body">${safeHtml}</div>
      </div>
    `
  );

  chatFeed.appendChild(node);
  lucide.createIcons();
  scrollChatToBottom();
}

function appendLoadingMessage() {
  const id = `loading-${Date.now()}`;
  loadingMessageId = id;

  const node = createMessageWrapper(
    "assistant",
    `
      <div class="message-avatar assistant-avatar">
        <i data-lucide="sparkles"></i>
      </div>
      <div class="message-card" id="${id}">
        <div class="message-meta">Travel Concierge</div>
        <div class="message-body">
          <div class="loading-bubble">
            <span>Thinking</span>
            <span class="loading-dots">
              <span></span>
              <span></span>
              <span></span>
            </span>
          </div>
        </div>
      </div>
    `
  );

  chatFeed.appendChild(node);
  lucide.createIcons();
  scrollChatToBottom();
}

function replaceLoadingWithAssistantMessage(data) {
  if (!loadingMessageId) return;

  const target = document.getElementById(loadingMessageId);
  if (!target) return;

  const finalAnswerHtml = renderMarkdownSafely(data?.final_answer || "No answer available.");
  const classifications = Array.isArray(data?.classifications) ? data.classifications : [];
  const agentOutputs = Array.isArray(data?.agent_outputs) ? data.agent_outputs : [];
  const agentsUsed = Array.isArray(data?.agents_used) ? data.agents_used : [];
  const sources = Array.isArray(data?.sources) ? data.sources : [];

  let executionHtml = "";

  if (classifications.length > 0 || agentOutputs.length > 0) {
    const cards = [];

    if (classifications.length > 0) {
      cards.push(`
        <div class="execution-card">
          <h4>Classifications</h4>
          <div class="markdown-body">
            <p>${escapeHtml(classifications.join(", "))}</p>
          </div>
        </div>
      `);
    }

    agentOutputs.forEach((item) => {
      const name = escapeHtml(item?.name || "Agent");
      const content = renderMarkdownSafely(item?.content || "No output available.");

      cards.push(`
        <div class="execution-card">
          <h4>${name}</h4>
          <div class="markdown-body">${content}</div>
        </div>
      `);
    });

    executionHtml = `
      <div class="execution-block">
        <details class="execution-details">
          <summary>View workflow details</summary>
          <div class="execution-content">
            ${cards.join("")}
          </div>
        </details>
      </div>
    `;
  }

  let sourcesHtml = "";
  if (sources.length > 0) {
    sourcesHtml = `
      <div class="sources-list markdown-body">
        <p><strong>Sources</strong></p>
        <ul>
          ${sources.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
        </ul>
      </div>
    `;
  }

  const metaHtml = `
    <div class="meta-row">
      <span class="meta-pill">Freshness: ${escapeHtml(data?.freshness || "--")}</span>
      <span class="meta-pill">Response time: ${
        typeof data?.latency_ms === "number" ? `${data.latency_ms} ms` : "--"
      }</span>
      <span class="meta-pill">Agents used: ${
        agentsUsed.length > 0 ? escapeHtml(agentsUsed.join(", ")) : "--"
      }</span>
      <span class="meta-pill">Request ID: ${escapeHtml(data?.request_id || "--")}</span>
      <span class="meta-pill">Session ID: ${escapeHtml(data?.session_id || getSessionId())}</span>
    </div>
  `;

  target.innerHTML = `
    <div class="message-meta">Travel Concierge</div>
    <div class="message-body markdown-body">${finalAnswerHtml}</div>
    ${metaHtml}
    ${sourcesHtml}
    ${executionHtml}
    <div class="message-actions">
      <button class="copy-btn" type="button" data-copy="${escapeHtml(data?.final_answer || "")}">
        <i data-lucide="copy"></i>
        Copy Answer
      </button>
    </div>
  `;

  lucide.createIcons();
  scrollChatToBottom();
  loadingMessageId = null;
}

function replaceLoadingWithError(message) {
  if (!loadingMessageId) return;

  const target = document.getElementById(loadingMessageId);
  if (!target) return;

  target.innerHTML = `
    <div class="message-meta">Travel Concierge</div>
    <div class="message-body markdown-body">
      <p><strong>Something went wrong.</strong></p>
      <p>${escapeHtml(message || "Unable to process the request right now.")}</p>
      <p>Please try again in a moment.</p>
    </div>
  `;

  scrollChatToBottom();
  loadingMessageId = null;
}

function setLoading(isLoading) {
  askBtn.disabled = isLoading;
  sampleBtn.disabled = isLoading;
  btnLoader.classList.toggle("hidden", !isLoading);
  askBtnContent.classList.toggle("hidden", isLoading);
  statusEl.textContent = isLoading ? "Working on your travel request..." : "";
}

function resetFieldError() {
  queryError.textContent = "";
}

function showFieldError(message) {
  queryError.textContent = message;
}

function validateQuery(query) {
  const trimmed = query.trim();

  if (!trimmed) {
    return "Please enter a travel question.";
  }

  if (trimmed.length < 6) {
    return "Please enter a slightly more detailed question.";
  }

  if (trimmed.length > MAX_QUERY_LENGTH) {
    return `Please keep the question within ${MAX_QUERY_LENGTH} characters.`;
  }

  return "";
}

async function askTravelQuestion(query, signal) {
  const sessionId = getSessionId();

  const response = await fetch("/api/ask", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      query,
      session_id: sessionId
    }),
    signal
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}.`;

    try {
      const errorData = await response.json();
      if (errorData?.detail) {
        message = errorData.detail;
      } else if (errorData?.message) {
        message = errorData.message;
      }
    } catch (_) {
      // ignore
    }

    throw new Error(message);
  }

  return response.json();
}

function autoResizeTextarea() {
  queryInput.style.height = "auto";
  queryInput.style.height = `${Math.min(queryInput.scrollHeight, 220)}px`;
}

function resetChatFeedToIntro() {
  chatFeed.innerHTML = `
    <div class="message assistant-message intro-message">
      <div class="message-avatar assistant-avatar">
        <i data-lucide="sparkles"></i>
      </div>

      <div class="message-card">
        <div class="message-meta">Travel Concierge</div>
        <div class="message-body markdown-body">
          <p>Hello! Ask me about:</p>
          <ul>
            <li>Local time and timezone</li>
            <li>Exchange rates</li>
            <li>Public holidays</li>
            <li>Country facts</li>
            <li>Trip planning guidance</li>
          </ul>
        </div>
      </div>
    </div>
  `;
  lucide.createIcons();
}

askForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  resetFieldError();

  const query = queryInput.value;
  const validationMessage = validateQuery(query);

  if (validationMessage) {
    showFieldError(validationMessage);
    return;
  }

  if (activeController) {
    activeController.abort();
  }

  activeController = new AbortController();
  const { signal } = activeController;

  appendUserMessage(query);
  appendLoadingMessage();

  queryInput.value = "";
  charCount.textContent = `0 / ${MAX_QUERY_LENGTH}`;
  autoResizeTextarea();
  setLoading(true);

  try {
    const data = await askTravelQuestion(query, signal);
    replaceLoadingWithAssistantMessage(data);
    statusEl.textContent = "Answer ready.";
  } catch (error) {
    if (error.name === "AbortError") {
      replaceLoadingWithError("Previous request was cancelled.");
      statusEl.textContent = "Previous request cancelled.";
      return;
    }

    replaceLoadingWithError(error.message || "Unable to process the request right now.");
    statusEl.textContent = "Request failed.";
  } finally {
    setLoading(false);
    activeController = null;
  }
});

sampleBtn.addEventListener("click", () => {
  queryInput.value = SAMPLE_PROMPT;
  charCount.textContent = `${queryInput.value.length} / ${MAX_QUERY_LENGTH}`;
  autoResizeTextarea();
  queryInput.focus();
});

clearConversationBtn.addEventListener("click", () => {
  if (activeController) {
    activeController.abort();
    activeController = null;
  }

  resetSessionId();
  resetChatFeedToIntro();

  queryInput.value = "";
  charCount.textContent = `0 / ${MAX_QUERY_LENGTH}`;
  resetFieldError();
  statusEl.textContent = "Chat cleared. Started a new session.";
  autoResizeTextarea();
});

queryInput.addEventListener("input", () => {
  charCount.textContent = `${queryInput.value.length} / ${MAX_QUERY_LENGTH}`;
  autoResizeTextarea();

  if (queryError.textContent) {
    resetFieldError();
  }
});

queryInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    askForm.requestSubmit();
  }
});

document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    const prompt = chip.getAttribute("data-prompt") || "";
    queryInput.value = prompt;
    charCount.textContent = `${prompt.length} / ${MAX_QUERY_LENGTH}`;
    autoResizeTextarea();
    queryInput.focus();
  });
});

document.addEventListener("click", async (event) => {
  const button = event.target.closest(".copy-btn");
  if (!button) return;

  const text = button.getAttribute("data-copy") || "";
  if (!text) return;

  try {
    await navigator.clipboard.writeText(text);
    statusEl.textContent = "Answer copied to clipboard.";
  } catch (_) {
    statusEl.textContent = "Unable to copy answer.";
  }
});

document.addEventListener("DOMContentLoaded", () => {
  getSessionId();
  lucide.createIcons();
  autoResizeTextarea();
});