console.log("ScamGuard background loaded");
// ===============================
// ScamGuard Background Service
// ===============================

// Backend endpoint
const BACKEND_URL = "scamguard-analyze-fn-htewgxesc3cba2b2.centralindia-01.azurewebsites.net";

// Cache: hostname → result
const domainCache = new Map();

// Cache TTL (10 minutes)
const CACHE_TTL_MS = 10 * 60 * 1000;

// Timeout for backend call (5 seconds)
const REQUEST_TIMEOUT_MS = 5000;

// -------------------------------
// Utility: fetch with timeout
// -------------------------------
function fetchWithTimeout(url, options, timeoutMs) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      reject(new Error("Request timeout"));
    }, timeoutMs);

    fetch(url, options)
      .then((response) => {
        clearTimeout(timer);
        resolve(response);
      })
      .catch((err) => {
        clearTimeout(timer);
        reject(err);
      });
  });
}

// -------------------------------
// Call backend with retry-once
// -------------------------------
async function callBackend(payload) {
  try {
    const response = await fetchWithTimeout(
      BACKEND_URL,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      },
      REQUEST_TIMEOUT_MS
    );

    if (!response.ok) {
      throw new Error("Backend returned non-200");
    }

    return await response.json();

  } catch (err) {
    // Retry ONCE
    const retryResponse = await fetchWithTimeout(
      BACKEND_URL,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      },
      REQUEST_TIMEOUT_MS
    );

    if (!retryResponse.ok) {
      throw new Error("Backend failed after retry");
    }

    return await retryResponse.json();
  }
}

// -------------------------------
// Message listener (CORE)
// -------------------------------
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  const { text, url, hostname } = message;

  if (!hostname) {
    sendResponse({ error: "Hostname missing" });
    return true;
  }

  const now = Date.now();

  // -------------------------------
  // CACHE HIT
  // -------------------------------
  if (domainCache.has(hostname)) {
    const cached = domainCache.get(hostname);

    if (now - cached.timestamp < CACHE_TTL_MS) {
      sendResponse(cached.data);
      return true;
    } else {
      domainCache.delete(hostname);
    }
  }

  // -------------------------------
  // CACHE MISS → BACKEND CALL
  // -------------------------------
  (async () => {
    try {
      const result = await callBackend({
        text,
        url,
        hostname,
      });

      domainCache.set(hostname, {
        data: result,
        timestamp: now,
      });

      sendResponse(result);

    } catch (err) {
      // FAIL-SAFE RESPONSE (never break UX)
      sendResponse({
        verdict: "unknown",
        risk_score: null,
        summary: "Unable to verify this website at the moment.",
        confidence: "low",
        error: "Backend unavailable",
      });
    }
  })();

  // IMPORTANT: keep message channel open
  return true;
});
