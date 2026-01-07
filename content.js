// Prevent multiple injections
if (!window.__SCAM_GUARD_LOADED__) {
  window.__SCAM_GUARD_LOADED__ = true;
  console.log("ScamGuard content script injected");


  // =============================
  // Extract page data (PURE)
  // =============================

  function extractPageData() {
    const text = document.body?.innerText || "";

    return {
      text: text.slice(0, 4000),
      url: window.location.href,
      hostname: window.location.hostname
    };
  }


  // =============================
  // Core execution
  // =============================

  function runScamGuard() {
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
      console.log("ScamGuard message received:", message);
    
      const { text, url, hostname } = message;
    
      sendResponse({ debug: "background reached" });
    
      return true;
    });
    
  }


  // Ensure DOM is ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", runScamGuard);
  } else {
    runScamGuard();
  }


  // =============================
  // UI Injection
  // =============================

  function injectWarningOverlay(result) {
    if (document.getElementById("scam-guard-overlay")) return;

    const color =
      result.verdict === "dangerous" ? "#dc2626" : "#facc15";

    const overlay = document.createElement("div");
    overlay.id = "scam-guard-overlay";

    overlay.innerHTML = `
      <div style="
        position:fixed;
        inset:0;
        background:rgba(0,0,0,0.85);
        z-index:999999;
        display:flex;
        justify-content:center;
        align-items:center;
        font-family:system-ui;
      ">
        <div style="
          background:#0f172a;
          color:white;
          padding:24px;
          max-width:480px;
          border-radius:14px;
        ">
          <h2 style="color:${color};font-size:22px;">
            ⚠ ${result.verdict.toUpperCase()} WEBSITE
          </h2>

          <p style="margin-top:8px;">
            ${result.summary}
          </p>

          <p style="margin-top:8px;">
            Risk score: <b>${result.risk_score}/100</b>
          </p>

          <button id="scam-guard-leave"
            style="
              margin-top:16px;
              width:100%;
              background:#16a34a;
              color:white;
              padding:10px;
              border-radius:8px;
              border:none;
              cursor:pointer;
            ">
            Leave site (recommended)
          </button>

          <button id="scam-guard-continue"
            ${result.verdict === "dangerous" ? "disabled" : ""}
            style="
              margin-top:10px;
              width:100%;
              background:transparent;
              border:1px solid ${color};
              color:${color};
              padding:10px;
              border-radius:8px;
              cursor:pointer;
            ">
            Continue anyway
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(overlay);

    document.getElementById("scam-guard-leave").onclick = () => {
      window.location.href = "about:blank";
    };

    const continueBtn = document.getElementById("scam-guard-continue");

    if (continueBtn && continueBtn.disabled) {
      setTimeout(() => {
        continueBtn.disabled = false;
      }, 4000);
    }

    if (continueBtn) {
      continueBtn.onclick = () => overlay.remove();
    }
  }
}