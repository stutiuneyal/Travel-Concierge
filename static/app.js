const form = document.getElementById("askForm");
const queryEl = document.getElementById("query");
const statusEl = document.getElementById("status");
const finalEl = document.getElementById("finalAnswer");
const resultsEl = document.getElementById("results");
const sampleBtn = document.getElementById("sampleBtn");

const sample =
  "I'm traveling to Japan next week—what time is it there right now, are there any upcoming public holidays, what's the current exchange rate from INR to JPY, and can you share some basic facts about Japan?";

sampleBtn.addEventListener("click", () => {
  queryEl.value = sample;
  queryEl.focus();
});

function escapeHtml(s) {
  return (s || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function renderResults(results) {
  if (!results || results.length === 0) {
    resultsEl.classList.add("muted");
    resultsEl.innerText = "No agent results returned.";
    return;
  }

  resultsEl.classList.remove("muted");
  resultsEl.innerHTML = results
    .map((r) => {
      const source = escapeHtml(r.source || "unknown");
      const body = escapeHtml(
        typeof r.result === "string" ? r.result : JSON.stringify(r.result, null, 2)
      );
      return `
        <div class="result">
          <div class="label">${source}</div>
          <div class="body">${body}</div>
        </div>
      `;
    })
    .join("");
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const q = queryEl.value.trim();
  if (!q) return;

  statusEl.innerText = "Running agents...";
  finalEl.classList.add("muted");
  resultsEl.classList.add("muted");

  finalEl.innerText = "Working...";
  resultsEl.innerText = "Working...";

  try {
    const resp = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: q }),
    });

    if (!resp.ok) {
      const t = await resp.text();
      throw new Error(`HTTP ${resp.status}: ${t}`);
    }

    const data = await resp.json();

    finalEl.classList.remove("muted");
    finalEl.innerHTML = marked.parse(data.final_answer || "(empty response)");

    renderResults(data.results);

    statusEl.innerText = "Done";
  } catch (err) {
    statusEl.innerText = "Error";
    finalEl.classList.remove("muted");
    finalEl.innerText = `Error: ${err.message}`;
    resultsEl.classList.add("muted");
    resultsEl.innerText = "";
  }
});
