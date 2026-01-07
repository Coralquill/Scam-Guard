export function showScamWarning(result) {
    const overlay = document.createElement("div");
    overlay.id = "scam-guard-overlay";
  
    const color =
      result.verdict === "dangerous" ? "#dc2626" : "#facc15";
  
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
            ⚠ ${result.verdict.toUpperCase()} SITE DETECTED
          </h2>
  
          <p>Risk score: <b>${result.risk_score}/100</b></p>
  
          <ul>
            ${result.signals.map(s =>
              `<li>${s.description}</li>`
            ).join("")}
          </ul>
  
          <button id="leave-site"
            style="margin-top:16px;background:#16a34a;color:white;padding:10px;border-radius:8px;">
            Leave Site (Recommended)
          </button>
  
          <button id="continue-site"
            disabled
            style="margin-top:10px;border:1px solid ${color};color:${color};padding:10px;border-radius:8px;">
            Continue Anyway
          </button>
        </div>
      </div>
    `;
  
    document.body.appendChild(overlay);
  
    document.getElementById("leave-site").onclick = () => {
      window.location.href = "about:blank";
    };
  
    const continueBtn = document.getElementById("continue-site");
    setTimeout(() => continueBtn.disabled = false, 4000);
    continueBtn.onclick = () => overlay.remove();
  }
  