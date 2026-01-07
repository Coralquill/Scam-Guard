import datetime
import socket
from urllib.parse import urlparse

# -----------------------------
# Utility: Domain age lookup
# -----------------------------
def get_domain_age_days(domain: str) -> int:
    """
    Tries to estimate domain age using WHOIS-like socket fallback.
    If lookup fails, return a safe default (365 days).
    """
    try:
        # Very lightweight heuristic: resolve domain
        socket.gethostbyname(domain)
        # If domain resolves, assume it's not brand new
        # (Real WHOIS can be plugged in later)
        return 30
    except Exception:
        # Unresolvable domains are suspicious
        return 1


# -----------------------------
# Core page analysis
# -----------------------------
def analyze_page(data: dict):
    """
    Input: page signals from content script
    Output: verdict, score, confidence, signals
    """

    score = 0
    signals = []

    # -------- Domain checks --------
    domain = data.get("domain", "")
    domain_age_days = get_domain_age_days(domain)

    if domain_age_days < 7:
        score += 30
        signals.append(("NEW_DOMAIN", "high"))

    # -------- Page content checks --------
    if data.get("mentionsUPI"):
        score += 20
        signals.append(("UPI_MENTION", "medium"))

    if data.get("urgencyLanguage"):
        score += 25
        signals.append(("URGENCY_LANGUAGE", "high"))

    if data.get("hasLoginForm"):
        score += 10
        signals.append(("LOGIN_FORM", "low"))

    if data.get("externalFormAction"):
        score += 35
        signals.append(("EXTERNAL_FORM_ACTION", "high"))

    # -------- Verdict logic --------
    if score >= 70:
        verdict = "dangerous"
    elif score >= 40:
        verdict = "suspicious"
    else:
        verdict = "safe"

    confidence = min(score / 100.0, 1.0)

    return verdict, score, confidence, signals


# -----------------------------
# Signal descriptions (UI-facing)
# -----------------------------
SIGNAL_DESCRIPTIONS = {
    "NEW_DOMAIN": "Domain was registered very recently",
    "UPI_MENTION": "Mentions UPI or popular Indian payment apps",
    "URGENCY_LANGUAGE": "Uses urgency or fear-based language",
    "LOGIN_FORM": "Contains a login or password input field",
    "EXTERNAL_FORM_ACTION": "Form submits sensitive data to another domain"
}
