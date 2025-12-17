const text = document.body.innerText.toLowerCase();

const scamWords = ["urgent", "verify", "account suspended", "reward"];

let found = false;
for (let word of scamWords) {
  if (text.includes(word)) {
    found = true;
    break;
  }
}

if (found) {
  alert("⚠️ ScamGuard Warning: This site looks suspicious.");
}
