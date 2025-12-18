// Get visible text from the current webpage (limit size to avoid overload)
const pageText = document.body.innerText.slice(0, 2000);

// Send page text to background script for backend analysis
chrome.runtime.sendMessage(
  { text: pageText },
  (response) => {
    if (!response) {
      console.error("ScamGuard: No response from background script");
      return;
    }

    if (response.error) {
      console.error("ScamGuard backend error:", response.error);
      return;
    }

    if (response.verdict === "Likely Scam") {
      alert(
        "⚠️ ScamGuard Warning\n\n" +
        "Verdict: " + response.verdict + "\n" +
        "Reason: " + response.reason
      );
    }
  }
);
