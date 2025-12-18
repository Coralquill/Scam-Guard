chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (!message || !message.text) {
      sendResponse({ error: "No text provided" });
      return true;
    }
  
    fetch("https://scamguard-analyze-fn-htewgxesc3cba2b2.centralindia-01.azurewebsites.net/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: message.text })
    })
      .then(res => res.json())
      .then(data => sendResponse(data))
      .catch(err => sendResponse({ error: err.toString() }));
  
    return true;
  });
  