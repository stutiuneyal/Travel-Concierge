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

const chatHistoryList = document.getElementById("chatHistoryList");
const newChatBtn = document.getElementById("newChatBtn");
const toggleHistoryBtn = document.getElementById("toggleHistoryBtn");
const historyNav = document.getElementById("historyNav");
const historyBackdrop = document.getElementById("historyBackdrop");
const mobileHistoryBtn = document.getElementById("mobileHistoryBtn");

const authOverlay = document.getElementById("authOverlay");
const emailStep = document.getElementById("emailStep");
const otpStep = document.getElementById("otpStep");
const emailInput = document.getElementById("emailInput");
const sendOtpBtn = document.getElementById("sendOtpBtn");
const verifyOtpBtn = document.getElementById("verifyOtpBtn");
const resendOtpBtn = document.getElementById("resendOtpBtn");
const changeEmailBtn = document.getElementById("changeEmailBtn");
const authMessage = document.getElementById("authMessage");
const otpBoxes = Array.from(document.querySelectorAll(".otp-box"));

const MAX_QUERY_LENGTH = 1600;
const SAMPLE_PROMPT =
  "I’m traveling to Japan next week. What time is it there right now, upcoming public holidays, INR to JPY rate, and basic facts I should know?";

const SESSION_STORAGE_KEY = "travel_concierge_session_id";
const HISTORY_NAV_STATE_KEY = "travel_concierge_history_nav_state";
const ONBOARDING_STORAGE_KEY = "travel_concierge_onboarding_seen";
const AUTH_TOKEN_STORAGE_KEY = "travel_concierge_access_token";
const AUTH_REFRESH_TOKEN_STORAGE_KEY = "travel_concierge_refresh_token";
const AUTH_EMAIL_STORAGE_KEY = "travel_concierge_email";

const logoutBtn = document.getElementById("logoutBtn");

const supabaseClient =
  window.supabase && window.SUPABASE_URL && window.SUPABASE_ANON_KEY
    ? window.supabase.createClient(window.SUPABASE_URL, window.SUPABASE_ANON_KEY)
    : null;

let pendingEmail = "";
let activeController = null;
let loadingMessageId = null;
let currentSessionId = null;
let tempTypingSessionId = null;
let tempTypingInterval = null;
let chatHistoryCache = [];
let hasUserInteracted = false;
let bootstrapRequestToken = 0;

let onboardingStepIndex = 0;
let onboardingEls = null;

let resendCooldownSeconds = 0;
let resendCooldownInterval = null;
let originalResendBtnText = "";

let sendCooldownSeconds = 0;
let sendCooldownInterval = null;
let originalSendOtpBtnText = "";

/* ----------------------------- UI ENHANCEMENTS ----------------------------- */

function injectEnhancementStyles() {
  if (document.getElementById("travel-concierge-enhancement-styles")) return;

  const style = document.createElement("style");
  style.id = "travel-concierge-enhancement-styles";
  style.textContent = `
    .tc-toast-stack {
      position: fixed;
      right: 18px;
      bottom: 22px;
      z-index: 9999;
      display: flex;
      flex-direction: column;
      gap: 10px;
      pointer-events: none;
    }

    .tc-toast {
      min-width: 220px;
      max-width: 360px;
      padding: 12px 14px;
      border-radius: 14px;
      color: #eef3ff;
      background: rgba(15, 21, 37, 0.94);
      border: 1px solid rgba(255, 255, 255, 0.1);
      box-shadow: 0 18px 40px rgba(0, 0, 0, 0.28);
      backdrop-filter: blur(12px);
      display: flex;
      align-items: center;
      gap: 10px;
      animation: tcToastIn 0.26s ease;
      pointer-events: auto;
      position: relative;
      overflow: hidden;
    }

    .tc-toast.tc-toast-success { border-color: rgba(116, 228, 166, 0.28); }
    .tc-toast.tc-toast-error { border-color: rgba(255, 107, 107, 0.3); }
    .tc-toast.tc-toast-info { border-color: rgba(109, 124, 255, 0.24); }

    .tc-toast-progress {
      position: absolute;
      inset: 0 auto auto 0;
      height: 3px;
      width: 100%;
      background: linear-gradient(90deg, rgba(117, 135, 255, 0.95), rgba(142, 125, 255, 0.95));
      transform-origin: left center;
      animation: tcToastProgress var(--toast-duration) linear forwards;
    }

    .tc-toast-paused .tc-toast-progress {
      animation-play-state: paused;
    }

    .tc-toast-icon {
      display: grid;
      place-items: center;
      flex-shrink: 0;
    }

    .tc-toast svg {
      width: 17px;
      height: 17px;
    }

    .tc-toast-content {
      min-width: 0;
      flex: 1;
    }

    .tc-toast-message {
      font-size: 0.95rem;
      line-height: 1.4;
      color: #eef3ff;
    }

    .tc-toast-close {
      width: 30px;
      height: 30px;
      border-radius: 10px;
      background: rgba(255, 255, 255, 0.04);
      color: #cdd7ff;
      border: 1px solid rgba(255, 255, 255, 0.06);
      display: grid;
      place-items: center;
      transition: 0.18s ease;
      cursor: pointer;
    }

    .tc-toast-close:hover {
      background: rgba(255, 255, 255, 0.08);
      transform: translateY(-1px);
    }

    .tc-toast-leaving {
      opacity: 0;
      transform: translateY(8px) scale(0.98);
      transition: opacity 0.2s ease, transform 0.2s ease;
    }

    .tc-button-copied {
      transform: translateY(-1px) scale(1.02);
    }

    .tc-pulse-once {
      animation: tcPulseOnce 0.65s ease;
    }

    .tc-wiggle-once {
      animation: tcWiggle 0.45s ease;
    }

    .tc-highlight-ring {
      position: relative;
      z-index: 10002 !important;
      box-shadow:
        0 0 0 2px rgba(109, 124, 255, 0.95),
        0 0 0 10px rgba(109, 124, 255, 0.16),
        0 18px 44px rgba(0, 0, 0, 0.32) !important;
      border-radius: 18px !important;
      transition: box-shadow 0.2s ease;
    }

    .tc-tour-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(4, 8, 18, 0.68);
      backdrop-filter: blur(6px);
      z-index: 10000;
      animation: tcFadeIn 0.2s ease;
    }

    .tc-tour-card {
      position: fixed;
      z-index: 10001;
      width: min(360px, calc(100vw - 28px));
      background: rgba(14, 20, 36, 0.96);
      color: #eef3ff;
      border: 1px solid rgba(255, 255, 255, 0.09);
      border-radius: 20px;
      box-shadow: 0 24px 60px rgba(0, 0, 0, 0.35);
      padding: 16px;
      animation: tcCardIn 0.24s ease;
    }

    .tc-tour-kicker {
      font-size: 0.75rem;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: #aeb8d9;
      margin-bottom: 8px;
    }

    .tc-tour-title {
      margin: 0 0 8px;
      font-size: 1rem;
      line-height: 1.25;
    }

    .tc-tour-text {
      margin: 0;
      color: #c7d1ee;
      font-size: 0.92rem;
      line-height: 1.55;
    }

    .tc-tour-footer {
      margin-top: 14px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
    }

    .tc-tour-progress {
      font-size: 0.82rem;
      color: #9eabd1;
    }

    .tc-tour-actions {
      display: flex;
      gap: 8px;
    }

    .tc-tour-btn {
      border: none;
      border-radius: 12px;
      padding: 9px 12px;
      font: inherit;
      cursor: pointer;
      transition: transform 0.18s ease, opacity 0.18s ease, background 0.18s ease;
    }

    .tc-tour-btn:hover {
      transform: translateY(-1px);
    }

    .tc-tour-btn-secondary {
      background: rgba(255, 255, 255, 0.06);
      color: #eef3ff;
      border: 1px solid rgba(255, 255, 255, 0.08);
    }

    .tc-tour-btn-primary {
      background: linear-gradient(135deg, #6d7cff, #7b61ff);
      color: #fff;
    }

    .tc-loading-shell {
      display: grid;
      gap: 12px;
    }

    .tc-shimmer-bar {
      height: 10px;
      border-radius: 999px;
      background: linear-gradient(
        90deg,
        rgba(255,255,255,0.04) 0%,
        rgba(255,255,255,0.11) 18%,
        rgba(255,255,255,0.04) 36%
      );
      background-size: 220% 100%;
      animation: tcShimmer 1.8s linear infinite;
    }

    .tc-shimmer-bar.s1 { width: 100%; }
    .tc-shimmer-bar.s2 { width: 88%; }
    .tc-shimmer-bar.s3 { width: 72%; }

    .tc-message-pop {
      animation: tcMessagePop 0.3s ease;
    }

    .copy-btn[data-copied="true"] {
      background: rgba(116, 228, 166, 0.14) !important;
      border-color: rgba(116, 228, 166, 0.26) !important;
      color: #ffffff !important;
    }

    .auth-overlay.hidden {
      display: none !important;
    }

    .auth-input:focus,
    .otp-box:focus {
      border-color: rgba(117, 135, 255, 0.34);
      box-shadow: 0 0 0 3px rgba(117, 135, 255, 0.18);
    }

    .auth-primary-btn:disabled,
    .auth-link-btn:disabled {
      opacity: 0.7;
      cursor: not-allowed;
    }

    .auth-message.success { color: #74e4a6; }
    .auth-message.error { color: #ff9aa5; }
    .auth-message.info { color: #cfd8f6; }

    @keyframes tcToastIn {
      from { opacity: 0; transform: translateY(10px) scale(0.98); }
      to { opacity: 1; transform: translateY(0) scale(1); }
    }

    @keyframes tcToastProgress {
      from { transform: scaleX(1); opacity: 1; }
      to { transform: scaleX(0); opacity: 0.9; }
    }

    @keyframes tcFadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }

    @keyframes tcCardIn {
      from { opacity: 0; transform: translateY(8px) scale(0.98); }
      to { opacity: 1; transform: translateY(0) scale(1); }
    }

    @keyframes tcPulseOnce {
      0% { transform: scale(1); }
      40% { transform: scale(1.035); }
      100% { transform: scale(1); }
    }

    @keyframes tcWiggle {
      0%, 100% { transform: rotate(0deg); }
      25% { transform: rotate(-4deg); }
      75% { transform: rotate(4deg); }
    }

    @keyframes tcShimmer {
      0% { background-position: 200% 0; }
      100% { background-position: -20% 0; }
    }

    @keyframes tcMessagePop {
      0% { opacity: 0; transform: translateY(8px) scale(0.99); }
      100% { opacity: 1; transform: translateY(0) scale(1); }
    }

    @media (max-width: 720px) {
      .tc-toast-stack {
        left: 14px;
        right: 14px;
        bottom: 16px;
      }
      .tc-toast {
        max-width: none;
      }
    }
  `;
  document.head.appendChild(style);
}

function stopSendCooldown() {
  if (sendCooldownInterval) {
    clearInterval(sendCooldownInterval);
    sendCooldownInterval = null;
  }

  sendCooldownSeconds = 0;

  if (sendOtpBtn) {
    sendOtpBtn.disabled = false;
    sendOtpBtn.classList.remove("cooldown");
    sendOtpBtn.textContent = originalSendOtpBtnText || "Send verification code";
  }
}

function startSendCooldown(seconds = 15) {
  if (!sendOtpBtn) return;

  stopSendCooldown();

  originalSendOtpBtnText =
    originalSendOtpBtnText || sendOtpBtn.textContent || "Send verification code";

  sendCooldownSeconds = seconds;
  sendOtpBtn.disabled = true;
  sendOtpBtn.classList.add("cooldown");
  sendOtpBtn.textContent = `Request again in ${sendCooldownSeconds}s`;

  sendCooldownInterval = setInterval(() => {
    sendCooldownSeconds -= 1;

    if (sendCooldownSeconds <= 0) {
      stopSendCooldown();
      return;
    }

    sendOtpBtn.textContent = `Request again in ${sendCooldownSeconds}s`;
  }, 1000);
}

function ensureToastStack() {
  let stack = document.querySelector(".tc-toast-stack");
  if (!stack) {
    stack = document.createElement("div");
    stack.className = "tc-toast-stack";
    document.body.appendChild(stack);
  }
  return stack;
}

function showToast(message, type = "info", icon = "sparkles", duration = 2200) {
  const stack = ensureToastStack();

  const toast = document.createElement("div");
  toast.className = `tc-toast tc-toast-${type}`;
  toast.style.setProperty("--toast-duration", `${duration}ms`);

  toast.innerHTML = `
    <div class="tc-toast-progress"></div>
    <div class="tc-toast-icon">
      <i data-lucide="${icon}"></i>
    </div>
    <div class="tc-toast-content">
      <div class="tc-toast-message">${escapeHtml(message)}</div>
    </div>
    <button class="tc-toast-close" type="button" aria-label="Dismiss notification">
      <i data-lucide="x"></i>
    </button>
  `;

  stack.appendChild(toast);
  createIcons();

  let removed = false;
  let timeoutId = null;

  const removeToast = () => {
    if (removed) return;
    removed = true;
    toast.classList.add("tc-toast-leaving");
    window.setTimeout(() => toast.remove(), 220);
  };

  const startTimer = (ms) => {
    timeoutId = window.setTimeout(removeToast, ms);
  };

  startTimer(duration);

  toast.querySelector(".tc-toast-close")?.addEventListener("click", () => {
    window.clearTimeout(timeoutId);
    removeToast();
  });

  toast.addEventListener("mouseenter", () => {
    window.clearTimeout(timeoutId);
    toast.classList.add("tc-toast-paused");
  });

  toast.addEventListener("mouseleave", () => {
    if (removed) return;
    toast.classList.remove("tc-toast-paused");
    window.clearTimeout(timeoutId);
    startTimer(1200);
  });
}

function setStatus(message, type = "info") {
  if (statusEl) {
    statusEl.textContent = message || "";
    statusEl.classList.remove("tc-status-success", "tc-status-error", "tc-status-info");
    if (message) {
      statusEl.classList.add(`tc-status-${type}`);
    }
  }

  if (message) {
    showToast(
      message,
      type,
      type === "success" ? "check" : type === "error" ? "circle-alert" : "sparkles"
    );
  }
}

function pulseElement(el, cls = "tc-pulse-once") {
  if (!el) return;
  el.classList.remove(cls);
  void el.offsetWidth;
  el.classList.add(cls);
  window.setTimeout(() => el.classList.remove(cls), 700);
}

function createIcons() {
  if (window.lucide && typeof window.lucide.createIcons === "function") {
    window.lucide.createIcons();
  }
}

/* --------------------------------- HELPERS -------------------------------- */

function generateSessionId() {
  if (window.crypto?.randomUUID) return window.crypto.randomUUID();
  return `session-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function getSessionId() {
  const stored = localStorage.getItem(SESSION_STORAGE_KEY);
  currentSessionId = stored || null;
  return currentSessionId;
}

function setSessionId(sessionId) {
  currentSessionId = sessionId || null;
  if (sessionId) localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
}

function resetSessionId() {
  currentSessionId = null;
  localStorage.removeItem(SESSION_STORAGE_KEY);
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

  const rawHtml = window.marked.parse(markdown, {
    breaks: true,
    gfm: true
  });

  return window.DOMPurify.sanitize(rawHtml);
}

function formatRelativeTime(timestampSec) {
  if (!timestampSec) return "Just now";

  const diffMs = Date.now() - timestampSec * 1000;
  const diffMin = Math.floor(diffMs / 60000);

  if (diffMin <= 0) return "Just now";
  if (diffMin < 60) return `${diffMin}m ago`;

  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;

  const diffDay = Math.floor(diffHr / 24);
  if (diffDay < 7) return `${diffDay}d ago`;

  return new Date(timestampSec * 1000).toLocaleDateString([], {
    day: "numeric",
    month: "short"
  });
}

function generateTitleFromQuery(query) {
  const cleaned = String(query || "").trim().replace(/\s+/g, " ");
  if (!cleaned) return "New Chat";

  const lower = cleaned.toLowerCase();

  const topicHints = [
    ["itinerary", "Itinerary"],
    ["budget", "Budget"],
    ["visa", "Visa"],
    ["weather", "Weather"],
    ["holiday", "Holidays"],
    ["holidays", "Holidays"],
    ["currency", "Currency"],
    ["exchange", "Exchange Rate"],
    ["rate", "Exchange Rate"],
    ["time", "Local Time"],
    ["timezone", "Local Time"],
    ["flight", "Flights"],
    ["flights", "Flights"],
    ["hotel", "Hotels"],
    ["hotels", "Hotels"],
    ["places", "Places to Visit"],
    ["facts", "Travel Facts"],
    ["trip", "Trip Plan"],
    ["travel", "Travel Plan"]
  ];

  let topic = null;
  for (const [key, label] of topicHints) {
    if (new RegExp(`\\b${key}\\b`, "i").test(lower)) {
      topic = label;
      break;
    }
  }

  const properNounPattern = /\b(?:to|for|in)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\b/;
  const destinationMatch = cleaned.match(properNounPattern);
  let destination = destinationMatch ? destinationMatch[1].trim() : null;

  if (!destination) {
    const knownPlaces = [
      "Japan", "Thailand", "Dubai", "Bali", "Singapore", "Vietnam", "France",
      "Italy", "Spain", "Goa", "Bangalore", "Delhi", "London", "Paris"
    ];
    destination =
      knownPlaces.find((place) => new RegExp(`\\b${place}\\b`, "i").test(cleaned)) || null;
  }

  if (destination && topic) return `${destination} ${topic}`.slice(0, 48);
  if (destination) return `${destination} Trip`.slice(0, 48);
  if (topic) return topic;

  const stopwords = new Set([
    "i", "im", "i’m", "am", "the", "a", "an", "to", "for", "of", "on", "in",
    "my", "me", "please", "tell", "give", "show", "what", "how", "when",
    "is", "are", "was", "were", "next", "this", "that", "about", "and",
    "or", "with", "trip", "traveling", "travelling", "need", "want", "help"
  ]);

  const filtered =
    cleaned.match(/[A-Za-z]+/g)?.filter((word) => !stopwords.has(word.toLowerCase())) || [];

  return (filtered.slice(0, 4).join(" ") || "New Chat").slice(0, 48);
}

function createMessageWrapper(role, innerHtml, extraClass = "") {
  const wrapper = document.createElement("div");
  wrapper.className = `message ${role}-message tc-message-pop ${extraClass}`.trim();
  wrapper.innerHTML = innerHtml;
  return wrapper;
}

function scrollChatToBottom(force = false) {
  const behavior = force ? "auto" : "smooth";
  window.requestAnimationFrame(() => {
    window.scrollTo({
      top: document.body.scrollHeight,
      behavior
    });
  });
}

function isIntroState() {
  return !!chatFeed?.querySelector(".intro-message");
}

function validateQuery(query) {
  const cleaned = String(query || "").trim();
  if (!cleaned) return "Please enter a travel question.";
  if (cleaned.length > MAX_QUERY_LENGTH) {
    return `Please keep your question within ${MAX_QUERY_LENGTH} characters.`;
  }
  return "";
}

function showFieldError(message) {
  if (queryError) queryError.textContent = message || "";
  pulseElement(queryInput, "tc-wiggle-once");
}

function resetFieldError() {
  if (queryError) queryError.textContent = "";
}

function autoResizeTextarea() {
  if (!queryInput) return;
  queryInput.style.height = "auto";
  queryInput.style.height = `${Math.min(queryInput.scrollHeight, 220)}px`;
}

function setLoading(isLoading) {
  if (askBtn) askBtn.disabled = isLoading;
  if (sampleBtn) sampleBtn.disabled = isLoading;

  if (askBtnContent) askBtnContent.classList.toggle("hidden", isLoading);
  if (btnLoader) btnLoader.classList.toggle("hidden", !isLoading);

  if (isLoading && askBtn) pulseElement(askBtn);
}

/* --------------------------------- AUTH ----------------------------------- */

function setAuthMessage(message = "", type = "info") {
  if (!authMessage) return;
  authMessage.textContent = message;
  authMessage.classList.remove("success", "error", "info");
  if (message) authMessage.classList.add(type);
}

function openAuthModal() {
  if (!authOverlay) return;
  authOverlay.classList.remove("hidden");
  authOverlay.setAttribute("aria-hidden", "false");
  document.body.style.overflow = "hidden";
  showEmailStep();
}

function extractCooldownSeconds(message = "") {
  const match = String(message).match(/after\s+(\d+)\s+seconds?/i);
  return match ? Number(match[1]) : null;
}

function closeAuthModal() {
  if (!authOverlay) return;
  authOverlay.classList.add("hidden");
  authOverlay.setAttribute("aria-hidden", "true");
  document.body.style.overflow = "";
  setAuthMessage("");
}

function showEmailStep() {
  emailStep?.classList.remove("hidden");
  otpStep?.classList.add("hidden");
  setAuthMessage("");
  stopResendCooldown();
  window.setTimeout(() => emailInput?.focus(), 60);
}

function showOtpStep() {
  emailStep?.classList.add("hidden");
  otpStep?.classList.remove("hidden");
  setAuthMessage(`We sent a verification code to ${pendingEmail}`, "info");
  clearOtpBoxes();
  window.setTimeout(() => otpBoxes[0]?.focus(), 60);
}

function clearOtpBoxes() {
  otpBoxes.forEach((box) => {
    box.value = "";
  });
}

function getOtpValue() {
  return otpBoxes.map((box) => box.value.trim()).join("");
}

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(email || "").trim());
}

function storeSession(session) {
  if (!session?.access_token || !session?.refresh_token) return;

  localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, session.access_token);
  localStorage.setItem(AUTH_REFRESH_TOKEN_STORAGE_KEY, session.refresh_token);

  if (session?.user?.email) {
    localStorage.setItem(AUTH_EMAIL_STORAGE_KEY, session.user.email);
  }
}

function clearSession() {
  localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
  localStorage.removeItem(AUTH_REFRESH_TOKEN_STORAGE_KEY);
  localStorage.removeItem(AUTH_EMAIL_STORAGE_KEY);
}

async function restoreSupabaseSession() {
  if (!supabaseClient) return null;

  const accessToken = localStorage.getItem(AUTH_TOKEN_STORAGE_KEY);
  const refreshToken = localStorage.getItem(AUTH_REFRESH_TOKEN_STORAGE_KEY);

  if (!accessToken || !refreshToken) return null;

  const { data, error } = await supabaseClient.auth.setSession({
    access_token: accessToken,
    refresh_token: refreshToken
  });

  if (error || !data?.session) {
    clearSession();
    return null;
  }

  storeSession(data.session);
  return data.session;
}

async function getAccessToken() {
  const { data, error } = await supabaseClient.auth.getSession();

  if (error) {
    throw new Error(error.message || "Unable to read auth session.");
  }

  return data?.session?.access_token || null;
}

function stopResendCooldown() {
  if (resendCooldownInterval) {
    clearInterval(resendCooldownInterval);
    resendCooldownInterval = null;
  }

  resendCooldownSeconds = 0;

  if (resendOtpBtn) {
    resendOtpBtn.disabled = false;
    resendOtpBtn.textContent = originalResendBtnText || "Resend Code";
  }
}

function startResendCooldown(seconds = 15) {
  if (!resendOtpBtn) return;

  stopResendCooldown();

  originalResendBtnText = originalResendBtnText || resendOtpBtn.textContent || "Resend Code";
  resendCooldownSeconds = seconds;
  resendOtpBtn.disabled = true;
  resendOtpBtn.textContent = `Resend in ${resendCooldownSeconds}s`;

  resendCooldownInterval = setInterval(() => {
    resendCooldownSeconds -= 1;

    if (resendCooldownSeconds <= 0) {
      stopResendCooldown();
      return;
    }

    resendOtpBtn.textContent = `Resend in ${resendCooldownSeconds}s`;
  }, 1000);
}

async function authenticatedFetch(url, options = {}) {
  const token = await getAccessToken();

  if (!token) {
    openAuthModal();
    throw new Error("You are not logged in. Please sign in again.");
  }

  const headers = new Headers(options.headers || {});
  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(url, {
    ...options,
    headers
  });

  if (response.status === 401) {
    openAuthModal();
  }

  return response;
}

async function sendOtp(email) {
  if (!supabaseClient) throw new Error("Supabase client is not available.");

  const { error } = await supabaseClient.auth.signInWithOtp({
    email,
    options: {
      shouldCreateUser: true
    }
  });

  if (error) throw new Error(error.message || "Unable to send verification code.");
}

async function verifyOtp(email, token) {
  const { data, error } = await supabaseClient.auth.verifyOtp({
    email,
    token,
    type: "email"
  });

  if (error) throw error;
  if (!data?.session?.access_token || !data?.session?.refresh_token) {
    throw new Error("Login succeeded but session was not created.");
  }

  return data.session;
}

function initOtpInputs() {
  otpBoxes.forEach((box, index) => {
    box.addEventListener("input", (event) => {
      const value = event.target.value.replace(/\D/g, "").slice(0, 1);
      event.target.value = value;
      if (value && index < otpBoxes.length - 1) otpBoxes[index + 1].focus();
    });

    box.addEventListener("keydown", (event) => {
      if (event.key === "Backspace" && !box.value && index > 0) {
        otpBoxes[index - 1].focus();
      }
      if (event.key === "ArrowLeft" && index > 0) otpBoxes[index - 1].focus();
      if (event.key === "ArrowRight" && index < otpBoxes.length - 1) otpBoxes[index + 1].focus();
    });

    box.addEventListener("paste", (event) => {
      event.preventDefault();
      const pasted = (event.clipboardData?.getData("text") || "")
        .replace(/\D/g, "")
        .slice(0, otpBoxes.length);

      pasted.split("").forEach((char, i) => {
        if (otpBoxes[i]) otpBoxes[i].value = char;
      });

      const nextIndex = Math.min(pasted.length, otpBoxes.length - 1);
      otpBoxes[nextIndex]?.focus();
    });
  });
}

async function handleSendOtp() {
  const email = emailInput?.value?.trim()?.toLowerCase();

  if (!isValidEmail(email)) {
    setAuthMessage("Please enter a valid email address.", "error");
    emailInput?.focus();
    return;
  }

  if (sendCooldownSeconds > 0) {
    return;
  }

  if (sendOtpBtn) sendOtpBtn.disabled = true;
  setAuthMessage("Sending verification code...", "info");

  try {
    await sendOtp(email);
    pendingEmail = email;
    showOtpStep();
    startResendCooldown(15);
    startSendCooldown(15);
  } catch (error) {
    const message = error.message || "Unable to send verification code.";
    const cooldown = extractCooldownSeconds(message);

    setAuthMessage(message, "error");

    if (cooldown) {
      startSendCooldown(cooldown);
    } else if (sendOtpBtn) {
      sendOtpBtn.disabled = false;
    }
  }
}

async function handleVerifyOtp() {
  const otp = getOtpValue();

  if (!pendingEmail) {
    showEmailStep();
    setAuthMessage("Please enter your email again.", "error");
    return;
  }

  if (!/^\d{6}$/.test(otp)) {
    setAuthMessage("Please enter the 6-digit verification code.", "error");
    otpBoxes[0]?.focus();
    return;
  }

  if (verifyOtpBtn) verifyOtpBtn.disabled = true;
  setAuthMessage("Verifying code...", "info");

  try {
    await verifyOtp(pendingEmail, otp);
    closeAuthModal();
    setStatus("Logged in successfully.", "success");
    await bootstrapAppAfterAuth();
  } catch (error) {
    setAuthMessage(error.message || "Invalid verification code.", "error");
  } finally {
    if (verifyOtpBtn) verifyOtpBtn.disabled = false;
  }
}

async function bootstrapAppAfterAuth() {
  await loadChatHistory();

  const sessionId = getSessionId();
  if (sessionId) {
    try {
      await openChat(sessionId, { silent: true });
      return;
    } catch (_) {
      resetSessionId();
    }
  }

  resetChatFeedToIntro();
}

async function ensureAuthenticated() {
  const restored = await restoreSupabaseSession();
  if (restored?.user) {
    await bootstrapAppAfterAuth();
    return true;
  }

  if (supabaseClient) {
    const { data } = await supabaseClient.auth.getSession();
    if (data?.session?.user) {
      storeSession(data.session);
      await bootstrapAppAfterAuth();
      return true;
    }
  }

  openAuthModal();
  return false;
}

async function logout() {
  try {
    if (supabaseClient) await supabaseClient.auth.signOut();
  } catch (_) {
    // ignore
  }

  stopResendCooldown();
  stopSendCooldown();
  clearSession();
  resetSessionId();
  chatHistoryCache = [];
  renderChatHistory([]);
  resetChatFeedToIntro();
  openAuthModal();
}

/* ---------------------------------- API ----------------------------------- */

async function askTravelQuestion(query, signal) {
  const response = await authenticatedFetch("/api/ask", {
    method: "POST",
    body: JSON.stringify({
      query,
      session_id: currentSessionId || undefined
    }),
    signal
  });

  if (!response.ok) {
    let message = "Unable to process the request right now.";
    try {
      const data = await response.json();
      if (data?.detail) message = data.detail;
    } catch (_) {
      // ignore
    }
    throw new Error(message);
  }

  return response.json();
}

async function fetchChats() {
  const response = await authenticatedFetch("/api/chats");
  if (!response.ok) throw new Error("Unable to load chat history.");
  return response.json();
}

async function fetchChat(sessionId) {
  const response = await authenticatedFetch(`/api/chats/${encodeURIComponent(sessionId)}`);
  if (!response.ok) throw new Error("Unable to load selected chat.");
  return response.json();
}

async function deleteChatRequest(sessionId) {
  const response = await authenticatedFetch(`/api/chats/${encodeURIComponent(sessionId)}`, {
    method: "DELETE"
  });

  if (!response.ok) throw new Error("Unable to delete chat.");
}

/* ------------------------------- CHAT HISTORY ------------------------------ */

function renderChatHistory(chats = chatHistoryCache) {
  if (!chatHistoryList) return;

  const allChats = Array.isArray(chats) ? [...chats] : [...chatHistoryCache];

  if (tempTypingSessionId && !allChats.find((chat) => chat.session_id === tempTypingSessionId)) {
    allChats.unshift({
      session_id: tempTypingSessionId,
      title: document.body.dataset.tempTypingTitle || "New Chat",
      updated_at: Date.now() / 1000,
      __temp: true
    });
  }

  if (!allChats.length) {
    chatHistoryList.innerHTML = `
      <div class="empty-history">
        <div class="empty-history-icon"><i data-lucide="message-square"></i></div>
        <p>No chats yet</p>
      </div>
    `;
    createIcons();
    return;
  }

  chatHistoryList.innerHTML = allChats
    .map((chat) => {
      const activeClass = chat.session_id === currentSessionId ? "active" : "";
      const safeTitle = escapeHtml(chat.title || "New Chat");
      const meta = chat.__temp ? "Creating..." : formatRelativeTime(chat.updated_at);
      const titleClass = chat.__temp ? "chat-history-title typing-title" : "chat-history-title";

      return `
        <div class="chat-history-row">
          <button
            class="chat-history-item ${activeClass}"
            type="button"
            data-session-id="${escapeHtml(chat.session_id)}"
            title="${safeTitle}"
          >
            <i class="chat-history-icon" data-lucide="message-square"></i>
            <div class="chat-history-content">
              <span class="${titleClass}">${safeTitle}</span>
              <span class="chat-history-meta">
                ${chat.__temp
          ? `
                      <span class="history-typing-dot">
                        <span></span><span></span><span></span>
                      </span>
                    `
          : escapeHtml(meta)
        }
              </span>
            </div>
          </button>
          ${chat.__temp
          ? ""
          : `
                <button
                  class="chat-history-delete"
                  type="button"
                  data-delete-session-id="${escapeHtml(chat.session_id)}"
                  title="Delete chat"
                >
                  <i data-lucide="trash-2"></i>
                </button>
              `
        }
        </div>
      `;
    })
    .join("");

  createIcons();
}

async function loadChatHistory() {
  try {
    const chats = await fetchChats();
    chatHistoryCache = Array.isArray(chats) ? chats : [];
    renderChatHistory(chatHistoryCache);
  } catch (error) {
    if (chatHistoryList) {
      chatHistoryList.innerHTML = `<div class="empty-history"><p>Unable to load chats</p></div>`;
    }
  }
}

/* -------------------------------- MESSAGES -------------------------------- */

function resetChatFeedToIntro() {
  if (!chatFeed) return;

  chatFeed.innerHTML = `
    <div class="message assistant-message intro-message tc-message-pop">
      <div class="message-avatar assistant-avatar">
        <i data-lucide="sparkles"></i>
      </div>
      <div class="message-card intro-card">
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
  createIcons();
}

function appendUserMessage(query) {
  if (!chatFeed) return;

  if (isIntroState()) chatFeed.innerHTML = "";

  const node = createMessageWrapper(
    "user",
    `
      <div class="message-avatar user-avatar">
        <i data-lucide="user"></i>
      </div>
      <div class="message-card">
        <div class="message-meta">You</div>
        <div class="message-body markdown-body">${renderMarkdownSafely(query)}</div>
      </div>
    `
  );

  chatFeed.appendChild(node);
  createIcons();
  scrollChatToBottom();
}

function appendLoadingMessage() {
  if (!chatFeed) return;

  const messageId = `loading-${Date.now()}`;

  const node = createMessageWrapper(
    "assistant",
    `
      <div class="message-avatar assistant-avatar">
        <i data-lucide="sparkles"></i>
      </div>
      <div class="message-card" id="${messageId}">
        <div class="message-meta">Travel Concierge</div>
        <div class="message-body">
          <div class="loading-bubble">
            <span class="loading-dots"><span></span><span></span><span></span></span>
            Thinking through your trip details...
          </div>
          <div class="tc-loading-shell" style="margin-top:14px;">
            <div class="tc-shimmer-bar s1"></div>
            <div class="tc-shimmer-bar s2"></div>
            <div class="tc-shimmer-bar s3"></div>
          </div>
        </div>
      </div>
    `,
    "loading-message"
  );

  chatFeed.appendChild(node);
  loadingMessageId = messageId;
  createIcons();
  scrollChatToBottom();
}

function replaceLoadingWithError(message) {
  const loadingNode = loadingMessageId ? document.getElementById(loadingMessageId) : null;
  if (!loadingNode) return;

  loadingNode.innerHTML = `
    <div class="message-meta">Travel Concierge</div>
    <div class="message-body markdown-body">
      <p><strong>Something went wrong.</strong></p>
      <p>${escapeHtml(message || "Unable to process the request right now.")}</p>
    </div>
  `;
  loadingMessageId = null;
  scrollChatToBottom();
}

function buildAssistantMeta(data) {
  const classifications = Array.isArray(data?.classifications) ? data.classifications : [];
  const agentsUsed = Array.isArray(data?.agents_used) ? data.agents_used : [];

  if (!classifications.length && !agentsUsed.length && typeof data?.latency_ms !== "number") {
    return "";
  }

  return `
    <div class="message-actions" style="margin-top: 12px; flex-wrap: wrap;">
      ${typeof data?.latency_ms === "number"
      ? `<span class="copy-btn" style="cursor:default;">⚡ ${escapeHtml(`${data.latency_ms} ms`)}</span>`
      : ""
    }
      ${classifications.length
      ? `<span class="copy-btn" style="cursor:default;">🧭 ${escapeHtml(classifications.join(", "))}</span>`
      : ""
    }
      ${agentsUsed.length
      ? `<span class="copy-btn" style="cursor:default;">🤖 ${escapeHtml(agentsUsed.join(", "))}</span>`
      : ""
    }
    </div>
  `;
}

function buildAgentOutputs(data) {
  const agentOutputs = Array.isArray(data?.agent_outputs) ? data.agent_outputs : [];
  if (!agentOutputs.length) return "";

  const cards = agentOutputs
    .map(
      (item) => `
        <div style="margin-top:12px; padding:12px; border-radius:14px; background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.06);">
          <div class="message-meta" style="margin-bottom:8px;">${escapeHtml(item?.name || "Agent")}</div>
          <div class="message-body markdown-body">${renderMarkdownSafely(item?.content || "")}</div>
        </div>
      `
    )
    .join("");

  return `
    <details class="execution-details" style="margin-top:14px;">
      <summary>View workflow details</summary>
      <div class="execution-content">
        ${cards}
      </div>
    </details>
  `;
}

function replaceLoadingWithAssistantMessage(data) {
  const loadingNode = loadingMessageId ? document.getElementById(loadingMessageId) : null;
  if (!loadingNode) return;

  const finalAnswer = data?.final_answer || "No answer available.";
  const pdfUrl = data?.pdf_url || "";

  loadingNode.innerHTML = `
    <div class="message-meta">Travel Concierge</div>
    <div class="message-body markdown-body">${renderMarkdownSafely(finalAnswer)}</div>
    ${buildAssistantMeta(data)}
    ${buildAgentOutputs(data)}
    <div class="message-actions">
      <button class="copy-btn" type="button" data-copy="${escapeHtml(finalAnswer)}">
        <i data-lucide="copy"></i>
        <span class="copy-btn-label">Copy Answer</span>
      </button>
      ${pdfUrl
      ? `
            <a class="copy-btn" href="${escapeHtml(pdfUrl)}" target="_blank" rel="noopener noreferrer">
              <i data-lucide="file-text"></i>
              <span>Open PDF</span>
            </a>
          `
      : ""
    }
    </div>
  `;

  loadingMessageId = null;
  createIcons();
  scrollChatToBottom();
}

function renderMessages(messages = []) {
  if (!chatFeed) return;

  chatFeed.innerHTML = "";

  if (!messages.length) {
    resetChatFeedToIntro();
    return;
  }

  messages.forEach((message) => {
    if (message.role === "user") {
      const userNode = createMessageWrapper(
        "user",
        `
          <div class="message-avatar user-avatar">
            <i data-lucide="user"></i>
          </div>
          <div class="message-card">
            <div class="message-meta">You</div>
            <div class="message-body markdown-body">${renderMarkdownSafely(message.content || "")}</div>
          </div>
        `
      );
      chatFeed.appendChild(userNode);
      return;
    }

    const assistantNode = createMessageWrapper(
      "assistant",
      `
        <div class="message-avatar assistant-avatar">
          <i data-lucide="sparkles"></i>
        </div>
        <div class="message-card">
          <div class="message-meta">Travel Concierge</div>
          <div class="message-body markdown-body">${renderMarkdownSafely(message.content || "")}</div>
          <div class="message-actions">
            <button class="copy-btn" type="button" data-copy="${escapeHtml(message.content || "")}">
              <i data-lucide="copy"></i>
              <span class="copy-btn-label">Copy Answer</span>
            </button>
            ${message?.pdf_url
        ? `
                  <a class="copy-btn" href="${escapeHtml(message.pdf_url)}" target="_blank" rel="noopener noreferrer">
                    <i data-lucide="file-text"></i>
                    <span>Open PDF</span>
                  </a>
                `
        : ""
      }
          </div>
        </div>
      `
    );
    chatFeed.appendChild(assistantNode);
  });

  createIcons();
  scrollChatToBottom(true);
}

async function openChat(sessionId, options = {}) {
  try {
    const chat = await fetchChat(sessionId);
    setSessionId(chat.session_id);
    renderMessages(chat.messages || []);
    await loadChatHistory();

    if (!options.silent) {
      setStatus("Loaded chat history.", "success");
    }
  } catch (error) {
    if (!options.silent) {
      setStatus(error.message || "Unable to load chat.", "error");
    }
    throw error;
  }
}

function stopTypingHistoryTitle() {
  if (tempTypingInterval) {
    clearInterval(tempTypingInterval);
    tempTypingInterval = null;
  }
  tempTypingSessionId = null;
  delete document.body.dataset.tempTypingTitle;
}

function startTypingHistoryTitle(sessionId, fullTitle) {
  stopTypingHistoryTitle();

  tempTypingSessionId = sessionId;
  document.body.dataset.tempTypingTitle = "";

  let index = 0;
  tempTypingInterval = setInterval(() => {
    index += 1;
    document.body.dataset.tempTypingTitle = fullTitle.slice(0, index);
    renderChatHistory(chatHistoryCache);
    if (index >= fullTitle.length) {
      clearInterval(tempTypingInterval);
      tempTypingInterval = null;
    }
  }, 34);
}

function startNewChat() {
  hasUserInteracted = true;
  stopTypingHistoryTitle();

  if (activeController) {
    activeController.abort();
    activeController = null;
  }

  resetSessionId();
  resetChatFeedToIntro();
  if (queryInput) queryInput.value = "";
  if (charCount) charCount.textContent = `0 / ${MAX_QUERY_LENGTH}`;
  resetFieldError();
  autoResizeTextarea();
  renderChatHistory(chatHistoryCache);
  setStatus("Started a new chat.", "info");
  pulseElement(queryInput);
  queryInput?.focus();
}

async function handleDeleteChat(sessionId) {
  try {
    await deleteChatRequest(sessionId);

    if (sessionId === currentSessionId) {
      resetSessionId();
      resetChatFeedToIntro();
    }

    chatHistoryCache = chatHistoryCache.filter((chat) => chat.session_id !== sessionId);
    renderChatHistory(chatHistoryCache);
    setStatus("Chat deleted.", "success");
  } catch (error) {
    setStatus(error.message || "Unable to delete chat.", "error");
  }
}

/* --------------------------------- COPY ----------------------------------- */

async function handleCopy(copyButton) {
  const text = copyButton?.getAttribute("data-copy") || "";
  if (!text) return;

  const label = copyButton.querySelector(".copy-btn-label");
  const originalLabel = label ? label.textContent : "";

  try {
    await navigator.clipboard.writeText(text);

    copyButton.setAttribute("data-copied", "true");
    copyButton.classList.add("tc-button-copied");
    if (label) label.textContent = "Copied!";

    const iconEl = copyButton.querySelector("i");
    if (iconEl) iconEl.setAttribute("data-lucide", "check");
    createIcons();

    pulseElement(copyButton);
    setStatus("Copied to clipboard.", "success");

    window.setTimeout(() => {
      copyButton.removeAttribute("data-copied");
      copyButton.classList.remove("tc-button-copied");
      if (label) label.textContent = originalLabel || "Copy Answer";
      const resetIcon = copyButton.querySelector("i");
      if (resetIcon) resetIcon.setAttribute("data-lucide", "copy");
      createIcons();
    }, 1400);
  } catch (_) {
    setStatus("Unable to copy answer.", "error");
  }
}

/* ------------------------------- ONBOARDING -------------------------------- */

function getOnboardingSteps() {
  return [
    {
      target: "#newChatBtn",
      title: "Start fresh here",
      text: "Use New Chat any time you want to ask a completely new trip question without mixing it with an older conversation."
    },
    {
      target: "#chatHistoryList",
      title: "Your chats stay here",
      text: "All previous conversations appear in the left sidebar so you can jump back, compare answers, or delete older chats."
    },
    {
      target: ".hero-mini",
      title: "Quick prompts to get started",
      text: "These prompt chips are handy when someone lands on the site for the first time and wants an example of what the assistant can do."
    },
    {
      target: ".composer-box",
      title: "Ask anything travel-related",
      text: "Type your question here. Press Enter to send, Shift + Enter for a new line, or use Sample if you want a ready-made prompt."
    },
    {
      target: "#clearConversationBtn",
      title: "Clear the current chat",
      text: "This resets the active conversation view quickly without touching your other saved chat history."
    }
  ];
}

function ensureOnboardingUi() {
  if (onboardingEls) return onboardingEls;

  const backdrop = document.createElement("div");
  backdrop.className = "tc-tour-backdrop";
  backdrop.style.display = "none";

  const card = document.createElement("div");
  card.className = "tc-tour-card";
  card.style.display = "none";

  card.innerHTML = `
    <div class="tc-tour-kicker">Quick tour</div>
    <h3 class="tc-tour-title"></h3>
    <p class="tc-tour-text"></p>
    <div class="tc-tour-footer">
      <span class="tc-tour-progress"></span>
      <div class="tc-tour-actions">
        <button class="tc-tour-btn tc-tour-btn-secondary" type="button" data-tour-action="skip">Skip</button>
        <button class="tc-tour-btn tc-tour-btn-primary" type="button" data-tour-action="next">Next</button>
      </div>
    </div>
  `;

  document.body.appendChild(backdrop);
  document.body.appendChild(card);

  onboardingEls = { backdrop, card };
  return onboardingEls;
}

function clearTourHighlight() {
  document.querySelectorAll(".tc-highlight-ring").forEach((el) => {
    el.classList.remove("tc-highlight-ring");
  });
}

function positionTourCard(card, target) {
  const rect = target.getBoundingClientRect();
  const cardWidth = Math.min(360, window.innerWidth - 28);
  const viewportPadding = 14;

  let top = rect.bottom + 14;
  let left = rect.left;

  if (left + cardWidth > window.innerWidth - viewportPadding) {
    left = window.innerWidth - cardWidth - viewportPadding;
  }

  if (left < viewportPadding) {
    left = viewportPadding;
  }

  const cardHeight = card.offsetHeight || 180;
  if (top + cardHeight > window.innerHeight - viewportPadding) {
    top = rect.top - cardHeight - 14;
  }

  if (top < viewportPadding) {
    top = viewportPadding;
  }

  card.style.left = `${left}px`;
  card.style.top = `${top}px`;
}

function closeOnboarding(markSeen = true) {
  const els = ensureOnboardingUi();
  clearTourHighlight();
  els.backdrop.style.display = "none";
  els.card.style.display = "none";
  if (markSeen) {
    localStorage.setItem(ONBOARDING_STORAGE_KEY, "true");
  }
}

function renderOnboardingStep() {
  const els = ensureOnboardingUi();
  const steps = getOnboardingSteps();

  if (onboardingStepIndex >= steps.length) {
    closeOnboarding(true);
    return;
  }

  const step = steps[onboardingStepIndex];
  const target = document.querySelector(step.target);

  if (!target) {
    onboardingStepIndex += 1;
    renderOnboardingStep();
    return;
  }

  clearTourHighlight();
  target.classList.add("tc-highlight-ring");
  target.scrollIntoView({ behavior: "smooth", block: "center", inline: "nearest" });

  const titleEl = els.card.querySelector(".tc-tour-title");
  const textEl = els.card.querySelector(".tc-tour-text");
  const progressEl = els.card.querySelector(".tc-tour-progress");
  const nextBtn = els.card.querySelector('[data-tour-action="next"]');

  titleEl.textContent = step.title;
  textEl.textContent = step.text;
  progressEl.textContent = `${onboardingStepIndex + 1} / ${steps.length}`;
  nextBtn.textContent = onboardingStepIndex === steps.length - 1 ? "Finish" : "Next";

  els.backdrop.style.display = "block";
  els.card.style.display = "block";

  window.requestAnimationFrame(() => {
    positionTourCard(els.card, target);
  });
}

function openOnboarding(force = false) {
  const seen = localStorage.getItem(ONBOARDING_STORAGE_KEY) === "true";
  if (!force && seen) return;

  onboardingStepIndex = 0;
  renderOnboardingStep();
}

function bindOnboardingEvents() {
  const els = ensureOnboardingUi();

  els.card.addEventListener("click", (event) => {
    const action = event.target.getAttribute("data-tour-action");
    if (action === "skip") {
      closeOnboarding(true);
      return;
    }

    if (action === "next") {
      onboardingStepIndex += 1;
      renderOnboardingStep();
    }
  });

  window.addEventListener("resize", () => {
    if (els.card.style.display === "none") return;
    const steps = getOnboardingSteps();
    const step = steps[onboardingStepIndex];
    const target = step ? document.querySelector(step.target) : null;
    if (target) positionTourCard(els.card, target);
  });
}

/* ------------------------------ HISTORY SIDEBAR ---------------------------- */

function setHistoryNavState(isCollapsed) {
  if (!historyNav) return;

  historyNav.classList.toggle("collapsed", isCollapsed);
  historyNav.classList.toggle("expanded", !isCollapsed);

  localStorage.setItem(HISTORY_NAV_STATE_KEY, isCollapsed ? "collapsed" : "expanded");

  const icon = toggleHistoryBtn?.querySelector("i");
  if (icon) {
    icon.setAttribute("data-lucide", isCollapsed ? "panel-left-open" : "panel-left-close");
  }

  createIcons();
}

function initHistoryNavState() {
  const saved = localStorage.getItem(HISTORY_NAV_STATE_KEY);
  setHistoryNavState(saved === "collapsed");
}

function openMobileHistory() {
  if (!historyNav) return;
  historyNav.classList.add("mobile-open");
  historyBackdrop?.classList.add("visible");
}

function closeMobileHistory() {
  if (!historyNav) return;
  historyNav.classList.remove("mobile-open");
  historyBackdrop?.classList.remove("visible");
}

async function logout() {
  try {
    if (supabaseClient) await supabaseClient.auth.signOut();
  } catch (_) {
    // ignore
  }

  clearSession();
  resetSessionId();
  chatHistoryCache = [];
  renderChatHistory([]);
  resetChatFeedToIntro();
  openAuthModal();
}

/* ------------------------------- EVENT HOOKS ------------------------------- */

logoutBtn?.addEventListener("click", async () => {
  await logout();
  setStatus("Logged out successfully.", "success");
});

sampleBtn?.addEventListener("click", () => {
  queryInput.value = SAMPLE_PROMPT;
  charCount.textContent = `${SAMPLE_PROMPT.length} / ${MAX_QUERY_LENGTH}`;
  autoResizeTextarea();
  queryInput.focus();
  pulseElement(sampleBtn);
  setStatus("Sample prompt added.", "info");
});

clearConversationBtn?.addEventListener("click", () => {
  startNewChat();
});

newChatBtn?.addEventListener("click", () => {
  startNewChat();
  closeMobileHistory();
});

toggleHistoryBtn?.addEventListener("click", () => {
  const isCollapsed = historyNav?.classList.contains("collapsed");
  setHistoryNavState(!isCollapsed);
});

mobileHistoryBtn?.addEventListener("click", openMobileHistory);
historyBackdrop?.addEventListener("click", closeMobileHistory);

queryInput?.addEventListener("input", () => {
  const value = queryInput.value || "";
  charCount.textContent = `${value.length} / ${MAX_QUERY_LENGTH}`;
  autoResizeTextarea();

  const errorMessage = validateQuery(value);
  if (errorMessage && value.trim()) {
    showFieldError(errorMessage);
  } else {
    resetFieldError();
  }
});

queryInput?.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    askForm?.requestSubmit();
  }
});

askForm?.addEventListener("submit", async (event) => {
  event.preventDefault();

  const token = await getAccessToken();
  if (!token) {
    openAuthModal();
    return;
  }

  const query = queryInput.value.trim();
  const errorMessage = validateQuery(query);

  if (errorMessage) {
    showFieldError(errorMessage);
    return;
  }

  resetFieldError();
  hasUserInteracted = true;

  if (activeController) {
    activeController.abort();
  }

  activeController = new AbortController();

  try {
    setLoading(true);
    appendUserMessage(query);
    appendLoadingMessage();

    if (!currentSessionId) {
      const tempId = generateSessionId();
      tempTypingSessionId = tempId;
      const predictedTitle = generateTitleFromQuery(query);
      startTypingHistoryTitle(tempId, predictedTitle);
      renderChatHistory(chatHistoryCache);
    }

    const data = await askTravelQuestion(query, activeController.signal);

    if (data?.session_id) {
      setSessionId(data.session_id);
    }

    stopTypingHistoryTitle();
    replaceLoadingWithAssistantMessage(data);

    queryInput.value = "";
    charCount.textContent = `0 / ${MAX_QUERY_LENGTH}`;
    autoResizeTextarea();

    await loadChatHistory();
  } catch (error) {
    if (error.name !== "AbortError") {
      stopTypingHistoryTitle();
      replaceLoadingWithError(error.message || "Unable to process request.");
      setStatus(error.message || "Unable to process request.", "error");
    }
  } finally {
    setLoading(false);
    activeController = null;
  }
});

document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    const prompt = chip.getAttribute("data-prompt") || "";
    queryInput.value = prompt;
    charCount.textContent = `${prompt.length} / ${MAX_QUERY_LENGTH}`;
    autoResizeTextarea();
    queryInput.focus();
    pulseElement(chip);
    setStatus("Prompt added to composer.", "info");
  });
});

document.addEventListener("click", async (event) => {
  const copyButton = event.target.closest(".copy-btn");
  if (copyButton && copyButton.hasAttribute("data-copy")) {
    await handleCopy(copyButton);
    return;
  }

  const historyButton = event.target.closest(".chat-history-item");
  if (historyButton) {
    const sessionId = historyButton.getAttribute("data-session-id");
    if (sessionId) {
      hasUserInteracted = true;
      stopTypingHistoryTitle();
      await openChat(sessionId);
      closeMobileHistory();
    }
    return;
  }

  const deleteButton = event.target.closest(".chat-history-delete");
  if (deleteButton) {
    event.stopPropagation();
    const sessionId = deleteButton.getAttribute("data-delete-session-id");
    if (sessionId) {
      await handleDeleteChat(sessionId);
    }
  }
});

/* ------------------------------- AUTH EVENTS ------------------------------- */

sendOtpBtn?.addEventListener("click", handleSendOtp);
verifyOtpBtn?.addEventListener("click", handleVerifyOtp);

resendOtpBtn?.addEventListener("click", async () => {
  if (!pendingEmail) {
    showEmailStep();
    return;
  }

  if (resendCooldownSeconds > 0) {
    return;
  }

  clearOtpBoxes();
  resendOtpBtn.disabled = true;
  setAuthMessage("Sending a fresh code. Please use only the newest email.", "info");

  try {
    const { error } = await supabaseClient.auth.signInWithOtp({
      email: pendingEmail,
      options: {
        shouldCreateUser: true
      }
    });

    if (error) throw error;

    setAuthMessage("A new verification code has been sent. Use only the latest code.", "success");
    startResendCooldown(15);
  } catch (error) {
    resendOtpBtn.disabled = false;
    setAuthMessage(error.message || "Unable to resend verification code.", "error");
  }
});

changeEmailBtn?.addEventListener("click", () => {
  pendingEmail = "";
  clearOtpBoxes();
  stopResendCooldown();
  stopSendCooldown();
  setAuthMessage("");
  showEmailStep();
});

emailInput?.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    handleSendOtp();
  }
});

initOtpInputs();

if (supabaseClient) {
  supabaseClient.auth.onAuthStateChange(async (_event, session) => {
    if (session) {
      storeSession(session);
      closeAuthModal();
    } else {
      clearSession();
      chatHistoryCache = [];
      renderChatHistory([]);
      resetChatFeedToIntro();
      openAuthModal();
    }
  });
}

async function bootstrapAuth() {
  const { data, error } = await supabaseClient.auth.getSession();

  if (error) {
    openAuthModal();
    return;
  }

  if (data?.session?.access_token) {
    closeAuthModal();
    await loadChatHistory();
  } else {
    openAuthModal();
  }
}

/* --------------------------------- BOOT ----------------------------------- */

document.addEventListener("DOMContentLoaded", async () => {
  injectEnhancementStyles();
  ensureOnboardingUi();
  bindOnboardingEvents();

  getSessionId();
  initHistoryNavState();
  lucide.createIcons();
  autoResizeTextarea();

  await bootstrapAuth();

  const sessionIdAtBoot = currentSessionId;
  const token = ++bootstrapRequestToken;

  if (!sessionIdAtBoot) {
    resetChatFeedToIntro();
    setTimeout(() => openOnboarding(false), 450);
    return;
  }

  try {
    const chat = await fetchChat(sessionIdAtBoot);

    if (token !== bootstrapRequestToken) return;
    if (hasUserInteracted) return;
    if (currentSessionId !== sessionIdAtBoot) return;

    renderMessages(chat.messages || []);
  } catch (_) {
    resetChatFeedToIntro();
  }

  setTimeout(() => openOnboarding(false), 450);
});