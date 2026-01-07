from azure.data.tables import TableServiceClient
import os
import json
import datetime
import requests
import azure.functions as func
from urllib.parse import urlparse
from openai import AzureOpenAI


# =============================
# AZURE TABLE STORAGE CONFIG
# =============================

TABLE_CONN_STR = os.getenv("AZURE_TABLE_CONN_STR")
BRAND_TABLE_NAME = "BrandRegistry"

if not TABLE_CONN_STR:
    raise RuntimeError("AZURE_TABLE_CONN_STR environment variable not set")

table_service = TableServiceClient.from_connection_string(TABLE_CONN_STR)
brand_table = table_service.get_table_client(BRAND_TABLE_NAME)

# =============================
# BRAND REGISTRY UTILITIES
# =============================

def fetch_official_domains_for_brand(brand: str) -> list[str]:
    """
    Fetch official domains for a brand from Azure Table Storage.
    """
    domains = []

    try:
        entities = brand_table.query_entities(
            query_filter=f"PartitionKey eq '{brand.lower()}' and active eq true"
        )
        for e in entities:
            domains.append(e["domain"].lower())
    except Exception:
        pass

    return domains


def verify_domain_with_brand_registry(hostname: str, brand: str) -> dict:
    official_domains = fetch_official_domains_for_brand(brand)

    if not official_domains:
        return {
            "verified": False,
            "reason": "Brand not found in registry"
        }

    hostname = hostname.lower()

    for d in official_domains:
        if hostname == d or hostname.endswith("." + d):
            return {
                "verified": True,
                "reason": "Domain matches official brand registry"
            }

    return {
        "verified": False,
        "reason": "Domain is not registered with the brand"
    }

# =============================
# AZURE OPENAI CONFIG
# =============================

client = AzureOpenAI(
    api_key="<YOUR_AZURE_OPENAI_KEY>",
    api_version="2024-02-15-preview",
    azure_endpoint="<YOUR_AZURE_OPENAI_ENDPOINT>"
)

AZURE_OPENAI_DEPLOYMENT = "<YOUR_MODEL_DEPLOYMENT_NAME>"


# =============================
# DOMAIN TRUST CONFIG
# =============================

RISKY_TLDS = {
    "xyz", "top", "tk", "ml", "ga", "cf", "gq",
    "click", "work", "support", "zip", "mov"
}

RDAP_BASE_URL = "https://rdap.org/domain/"


# =============================
# DOMAIN UTILITIES
# =============================

def extract_domain(hostname: str) -> str:
    parts = hostname.lower().split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else hostname


def extract_tld(hostname: str) -> str:
    return hostname.lower().split(".")[-1]


def fetch_rdap_data(domain: str) -> dict:
    try:
        r = requests.get(f"{RDAP_BASE_URL}{domain}", timeout=5)
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}


def parse_creation_date(rdap: dict):
    for event in rdap.get("events", []):
        if event.get("eventAction") == "registration":
            try:
                return datetime.datetime.fromisoformat(
                    event["eventDate"].replace("Z", "")
                )
            except Exception:
                return None
    return None


def analyze_domain_trust(hostname: str) -> dict:
    domain = extract_domain(hostname)
    tld = extract_tld(hostname)

    rdap = fetch_rdap_data(domain)
    created = parse_creation_date(rdap)

    age_days = (
        (datetime.datetime.utcnow() - created).days
        if created else None
    )

    risky_tld = tld in RISKY_TLDS
    privacy_protected = "entities" not in rdap

    trust_score = 100
    signals = []

    if risky_tld:
        trust_score -= 25
        signals.append(("RISKY_TLD", "medium"))

    if age_days is None:
        trust_score -= 15
        signals.append(("UNKNOWN_DOMAIN_AGE", "medium"))
    elif age_days < 30:
        trust_score -= 40
        signals.append(("NEW_DOMAIN", "high"))
    elif age_days < 180:
        trust_score -= 20
        signals.append(("RECENT_DOMAIN", "medium"))

    if privacy_protected:
        trust_score -= 10
        signals.append(("PRIVACY_PROTECTED", "low"))

    trust_score = max(trust_score, 0)

    return {
        "domain": domain,
        "hostname": hostname,
        "tld": tld,
        "domain_age_days": age_days,
        "risky_tld": risky_tld,
        "privacy_protected": privacy_protected,
        "trust_score": trust_score,
        "signals": signals
    }

def extract_claimed_brand(page_text: str) -> str | None:
    """
    Extracts the brand the page claims to represent.
    Returns lowercase brand name or None.
    """

    prompt = f"""
Identify if the webpage claims to represent a company or brand.

Return ONLY the brand name in lowercase, or null.
No explanation.

Text:
\"\"\"
{page_text[:3000]}
\"\"\"
"""

    try:
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "Extract brand names only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=50
        )

        brand = response.choices[0].message.content.strip().lower()
        return brand if brand != "null" else None

    except Exception:
        return None

# =============================
# AI SEMANTIC ANALYSIS
# =============================

def ai_semantic_analysis(page_text: str, domain_info: dict) -> dict:
    prompt = f"""
You are a cybersecurity assistant.

Determine whether this webpage is attempting impersonation,
fraud, or user deception.

Domain context:
- Domain: {domain_info['domain']}
- Domain age (days): {domain_info['domain_age_days']}
- Risky TLD: {domain_info['risky_tld']}
- Privacy protected: {domain_info['privacy_protected']}

Webpage content:
\"\"\"
{page_text[:4000]}
\"\"\"

Respond ONLY in valid JSON:
{{
  "impersonation": true | false,
  "confidence": "low" | "medium" | "high",
  "summary": "<one clear sentence understandable by non-technical users>"
}}
"""

    try:
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are a cybersecurity analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=300
        )

        return json.loads(response.choices[0].message.content)

    except Exception:
        return {
            "impersonation": False,
            "confidence": "low",
            "summary": "No strong signs of impersonation were detected."
        }


# =============================
# FINAL SCORING + VERDICT
# =============================

def compute_final_verdict(domain_info: dict, ai_result: dict) -> dict:
    score = 100 - domain_info["trust_score"]

    if ai_result["impersonation"]:
        score += 40

    score = min(score, 100)

    if score >= 70:
        verdict = "dangerous"
    elif score >= 40:
        verdict = "suspicious"
    else:
        verdict = "safe"

    return {
        "verdict": verdict,
        "risk_score": score,
        "confidence": ai_result["confidence"],
        "summary": ai_result["summary"]
    }


# =============================
# AZURE FUNCTION APP
# =============================

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="analyze", methods=["POST"])
def analyze(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()

        page_text = body.get("text", "")
        url = body.get("url", "")
        hostname = body.get("hostname", "")

        if not hostname and url:
            hostname = urlparse(url).hostname or ""

        if not hostname:
            return func.HttpResponse(
                json.dumps({"error": "hostname missing"}),
                status_code=400,
                mimetype="application/json"
            )

        domain_info = analyze_domain_trust(hostname)

        claimed_brand = extract_claimed_brand(page_text)

        brand_verification = None
        brand_impersonation = False

        if claimed_brand:
            brand_verification = verify_domain_with_brand_registry(
                hostname,
                claimed_brand
            )

            if not brand_verification["verified"]:
                brand_impersonation = True

        ai_result = ai_semantic_analysis(page_text, domain_info)

        # -----------------------------
        # FINAL SCORING
        # -----------------------------

        score = 100 - domain_info["trust_score"]

        if brand_impersonation:
            score += 60  # strongest signal

        if ai_result["impersonation"]:
            score += 20  # supporting signal

        score = min(score, 100)

        if score >= 70:
            verdict = "dangerous"
        elif score >= 40:
            verdict = "suspicious"
        else:
            verdict = "safe"


        response = {
            "verdict": verdict,
            "risk_score": score,
            "summary": (
                f"This website claims to be {claimed_brand}, but the domain is not officially registered with that brand."
                if brand_impersonation
                else ai_result["summary"]
            ),
            "brand_verification": {
                "claimed_brand": claimed_brand,
                "verified": brand_verification["verified"] if brand_verification else None,
                "reason": brand_verification["reason"] if brand_verification else None
            },
            "domain_trust": domain_info,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }


        return func.HttpResponse(
            json.dumps(response),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
