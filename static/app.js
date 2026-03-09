const askForm = document.getElementById("askForm");
const queryInput = document.getElementById("query");
const askBtn = document.getElementById("askBtn");
const sampleBtn = document.getElementById("sampleBtn");
const clearConversationBtn = document.getElementById("clearConversationBtn");
const statusEl = document.getElementById("status");
const finalAnswerEl = document.getElementById("finalAnswer");
const resultsEl = document.getElementById("results");
const sourcesBox = document.getElementById("sourcesBox");
const queryError = document.getElementById("queryError");
const charCount = document.getElementById("charCount");
const btnLoader = document.getElementById("btnLoader");
const answerMeta = document.getElementById("answerMeta");
const metaFreshness = document.getElementById("metaFreshness");
const metaLatency = document.getElementById("metaLatency");
const metaAgents = document.getElementById("metaAgents");
const answerActions = document.getElementById("answerActions");
const copyAnswerBtn = document.getElementById("copyAnswerBtn");

const MAX_QUERY_LENGTH = 1600;
const SAMPLE_PROMPT =
  "I’m traveling to Japan next week. What time is it there right now, upcoming public holidays, INR to JPY rate, and basic facts I should know?";

let currentAnswerText = "";

function escapeHtml(value = "") {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function normalizeMarkdown(markdown = "") {
  if (!markdown) return "";

  const lines = markdown.replace(/\t/g, "    ").split("\n");

  // Find minimum indentation across non-empty lines
  const indents = lines
    .filter((line) => line.trim().length > 0)
    .map((line) => {
      const match = line.match(/^(\s*)/);
      return match ? match[1].length : 0;
    });

  const minIndent = indents.length ? Math.min(...indents) : 0;

  if (minIndent > 0) {
    return lines.map((line) => line.slice(minIndent)).join("\n").trim();
  }

  return markdown.trim();
}

function renderMarkdownSafely(markdown = "") {
  if (!markdown || typeof markdown !== "string") {
    return "<p>No content available.</p>";
  }

  const normalized = normalizeMarkdown(markdown);

  const rawHtml = marked.parse(normalized, {
    breaks: true,
    gfm: true
  });

  return DOMPurify.sanitize(rawHtml);
}

/*
  Important note:
  For production, do NOT directly inject model-generated HTML.
  If you want Markdown rendering, use a trusted markdown parser plus a sanitizer
  like DOMPurify before assigning to innerHTML.
*/
function renderAnswer(text) {
  currentAnswerText = text || "";

  if (!currentAnswerText.trim()) {
    finalAnswerEl.className = "answer-body empty-state";
    finalAnswerEl.innerHTML = `
      <div class="empty-illustration">
        <i data-lucide="compass"></i>
      </div>
      <h4>No answer available</h4>
      <p>The request completed, but no response content was returned.</p>
    `;
    lucide.createIcons();
    answerActions.classList.add("hidden");
    return;
  }

  finalAnswerEl.className = "answer-body";
  finalAnswerEl.innerHTML = renderMarkdownSafely(currentAnswerText);
  answerActions.classList.remove("hidden");
  finalAnswerEl.focus();
}

function renderSources(sources = []) {
  if (!Array.isArray(sources) || sources.length === 0) {
    sourcesBox.innerHTML = `<div class="muted">No source information provided.</div>`;
    return;
  }

  sourcesBox.innerHTML = `
    <ul class="feature-list">
      ${sources.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
    </ul>
  `;
}

function renderAgentOutputs(agentOutputs = []) {
  if (!Array.isArray(agentOutputs) || agentOutputs.length === 0) {
    resultsEl.innerHTML = `<div class="muted">No execution details available.</div>`;
    return;
  }

  resultsEl.innerHTML = agentOutputs
    .map((item) => {
      const name = escapeHtml(item?.name || "Agent");
      const content = escapeHtml(item?.content || "No output available.");
      return `
        <div class="result-card">
          <h4>${name}</h4>
          <p>${content.replace(/\n/g, "<br />")}</p>
        </div>
      `;
    })
    .join("");
}

function setLoading(isLoading) {
  askBtn.disabled = isLoading;
  sampleBtn.disabled = isLoading;
  queryInput.disabled = isLoading;

  btnLoader.classList.toggle("hidden", !isLoading);

  if (isLoading) {
    statusEl.textContent = "Working on your travel request...";
    statusEl.classList.add("loading-dots");
  } else {
    statusEl.classList.remove("loading-dots");
  }
}

function resetFieldError() {
  queryError.textContent = "";
}

function showFieldError(message) {
  queryError.textContent = message;
}

function clearOutput() {
  currentAnswerText = "";
  answerMeta.classList.add("hidden");
  answerActions.classList.add("hidden");

  finalAnswerEl.className = "answer-body empty-state";
  finalAnswerEl.innerHTML = `
    <div class="empty-illustration">
      <i data-lucide="plane"></i>
    </div>
    <h4>Your travel answer will appear here</h4>
    <p>Ask a question to get a complete travel response assembled from the right agents and tools.</p>
  `;
  lucide.createIcons();
  resultsEl.innerHTML = `No execution details yet.`;
  sourcesBox.innerHTML = `Source details will appear here when available.`;
  statusEl.textContent = "";
}

function updateMeta({ freshness, latencyMs, agentsUsed }) {
  metaFreshness.textContent = `Freshness: ${freshness || "--"}`;
  metaLatency.textContent = `Response time: ${typeof latencyMs === "number" ? `${latencyMs} ms` : "--"
    }`;
  metaAgents.textContent = `Agents used: ${Array.isArray(agentsUsed) && agentsUsed.length > 0
      ? agentsUsed.join(", ")
      : "--"
    }`;

  answerMeta.classList.remove("hidden");
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

async function askTravelQuestion(query) {
  const response = await fetch("/api/ask", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ query })
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
    } catch {
      // ignore parse failure
    }

    throw new Error(message);
  }

  return response.json();
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

  setLoading(true);
  statusEl.textContent = "Working on your travel request...";
  finalAnswerEl.className = "answer-body empty-state";
  finalAnswerEl.innerHTML = `
    <div class="empty-illustration">
      <i data-lucide="loader"></i>
    </div>
    <h4>Generating your answer</h4>
    <p>Routing your request to the right agents and tools.</p>
  `;
  lucide.createIcons();
  resultsEl.innerHTML = `<div class="muted">Execution details will appear here once the workflow completes.</div>`;
  sourcesBox.innerHTML = `<div class="muted">Source details will appear here when available.</div>`;

  const start = performance.now();

  try {
    const data = await askTravelQuestion(query);
    const end = performance.now();
    const latencyMs = Math.round(end - start);

    renderAnswer(data?.final_answer || "");
    renderAgentOutputs(data?.agent_outputs || []);
    renderSources(data?.sources || []);

    updateMeta({
      freshness: data?.freshness || "live",
      latencyMs: data?.latency_ms ?? latencyMs,
      agentsUsed: data?.agents_used || []
    });

    statusEl.textContent = "Answer ready.";
  } catch (error) {
    finalAnswerEl.className = "answer-body";
    finalAnswerEl.innerHTML = `
      <p><strong>Something went wrong.</strong></p>
      <p>${escapeHtml(error.message || "Unable to process the request right now.")}</p>
      <p>Please try again in a moment.</p>
    `;

    resultsEl.innerHTML = `<div class="muted">No execution details available because the request failed.</div>`;
    sourcesBox.innerHTML = `<div class="muted">No source details available.</div>`;
    answerMeta.classList.add("hidden");
    answerActions.classList.add("hidden");
    statusEl.textContent = "Request failed.";
  } finally {
    setLoading(false);
  }
});

sampleBtn.addEventListener("click", () => {
  queryInput.value = SAMPLE_PROMPT;
  charCount.textContent = `${queryInput.value.length} / ${MAX_QUERY_LENGTH}`;
  queryInput.focus();
});

clearConversationBtn.addEventListener("click", () => {
  queryInput.value = "";
  charCount.textContent = `0 / ${MAX_QUERY_LENGTH}`;
  resetFieldError();
  clearOutput();
  queryInput.focus();
});

queryInput.addEventListener("input", () => {
  const length = queryInput.value.length;
  charCount.textContent = `${length} / ${MAX_QUERY_LENGTH}`;
  if (queryError.textContent) {
    resetFieldError();
  }
});

copyAnswerBtn.addEventListener("click", async () => {
  if (!currentAnswerText) return;

  try {
    await navigator.clipboard.writeText(currentAnswerText);
    statusEl.textContent = "Answer copied to clipboard.";
  } catch {
    statusEl.textContent = "Unable to copy answer.";
  }
});

document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    const prompt = chip.getAttribute("data-prompt") || "";
    queryInput.value = prompt;
    charCount.textContent = `${prompt.length} / ${MAX_QUERY_LENGTH}`;
    queryInput.focus();
  });
});

clearOutput();