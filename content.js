// Get visible text from the current webpage (limit size to avoid overload)
const pageText = document.body.innerText.slice(0, 2000);

// Send page text to background script for backend analysis
chrome.runtime.sendMessage(
  { text: pageText },
  (response) => {
    // Safety check: response may be undefined if something failed
    if (!response) {
      console.error("ScamGuard: No response from background script");
      return;
    }

    // If backend returned an error
    if (response.error) {
      console.error("ScamGuard backend error:", response.error);
      return;
    }

    // If scam score crosses threshold, warn the user
    if (response.scam_score >= 2) {
      alert("⚠️ ScamGuard Warning: This site may be a scam.");
    }
  }
);

