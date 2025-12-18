import json
import azure.functions as func


def ai_verdict_stub(text: str) -> dict:
    """
    Temporary AI stub.
    Simulates an LLM response for borderline cases.
    """
    suspicious_phrases = ["verify", "click", "limited", "act now"]

    for phrase in suspicious_phrases:
        if phrase in text.lower():
            return {
                "verdict": "Likely Scam",
                "reason": "Language suggests urgency or manipulation"
            }

    return {
        "verdict": "Unclear",
        "reason": "Message lacks strong scam indicators"
    }


app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="analyze", methods=["POST"])
def analyze(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        text = body.get("text", "").lower()

        scam_words = ["urgent", "verify", "reward"]
        score = sum(1 for w in scam_words if w in text)

        # Hybrid decision logic
        if score >= 3:
            verdict = "Likely Scam"
            reason = "Multiple scam indicators detected"
        elif score == 0:
            verdict = "Likely Safe"
            reason = "No scam indicators detected"
        else:
            # Borderline case → AI stub
            ai_result = ai_verdict_stub(text)
            verdict = ai_result["verdict"]
            reason = ai_result["reason"]

        return func.HttpResponse(
            json.dumps({
                "scam_score": score,
                "verdict": verdict,
                "reason": reason
            }),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=400
        )
