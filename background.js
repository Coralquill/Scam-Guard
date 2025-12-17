chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    fetch("http://127.0.0.1:8000/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: message.text })
    })
    .then(res => res.json())
    .then(data => sendResponse(data))
    .catch(err => sendResponse({ error: err.toString() }));
  
    return true; // keep message channel open
  });
  