import time
import requests
import json
from pydantic import BaseModel
from google import genai
from google.genai import types

# ==========================================
# 1. CONFIGURATION & ALL YOUR KEYS
# ==========================================
GEMINI_API_KEY = "AIzaSyCxnWNBt2vah9jEtmdhAqTIMbBoxmPFRrQ"
TELEGRAM_BOT_TOKEN = "8893291119:AAF34pPDYryCFGbTzD2vp9cKf3YoKzFaVsM"
TELEGRAM_CHAT_ID = "2138227333"

GODADDY_API_KEY = "hkoA5cyKaGYE_HqJE4ezrvgRZwwPALEzLs1"
GODADDY_API_SECRET = "6MrYr7pkK5U2sbPWeoe34Q"

client = genai.Client(api_key=GEMINI_API_KEY)

# ==========================================
# 2. SCHEMAS
# ==========================================
class DomainAnalysis(BaseModel):
    domain: str
    status: str
    score: int
    valuation_tier: str
    niche: str
    estimated_value: str
    target_buyers: list[str]
    actionable_recommendation: str

class DomainGenerationList(BaseModel):
    generated_domains: list[str]

# ==========================================
# 3. GODADDY REAL-TIME AVAILABILITY CHECK
# ==========================================
def check_godaddy_availability(domain: str) -> dict:
    url = f"https://api.godaddy.com/v1/domains/available?domain={domain}"
    headers = {
        "Authorization": f"sso-key {GODADDY_API_KEY}:{GODADDY_API_SECRET}",
        "accept": "application/json"
    }
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"GoDaddy Check Error for {domain}: {e}")
    return {"available": False}

# ==========================================
# 4. TELEGRAM ALERT SENDER
# ==========================================
def send_telegram_alert(analysis: DomainAnalysis):
    message = (
        f"🚨 **HIGH POTENTIAL DOMAIN FOUND!** 🚨\n\n"
        f"🌐 **Domain**: `{analysis.domain}`\n"
        f"✅ **Status**: {analysis.status}\n"
        f"🎯 **Niche**: {analysis.niche}\n"
        f"⭐ **Score**: {analysis.score}/100\n"
        f"💰 **Est. Resale Value**: {analysis.estimated_value}\n"
        f"💎 **Tier**: {analysis.valuation_tier}\n"
        f"🏢 **Buyers**: {', '.join(analysis.target_buyers)}\n"
        f"💡 **Action**: {analysis.actionable_recommendation}"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    
    try:
        requests.post(url, json=payload, timeout=5)
        print(f"Alert sent to Telegram for {analysis.domain}")
    except Exception as e:
        print(f"Telegram API Error: {e}")

# ==========================================
# 5. GEMINI AI GENERATOR & EVALUATOR
# ==========================================
def generate_candidate_domains(keyword: str, niche: str, tlds=[".com", ".io", ".ai"]) -> list[str]:
    prompt = f"""
    Generate 15 high-potential, extremely brandable domain ideas:
    - Base Keyword / Core Concept: {keyword}
    - Niche Focus: {niche}
    - TLD Extensions: {', '.join(tlds)}
    Target Resale Value: $10,000 to $100,000+
    Focus on short, memorable combinations likely to be unregistered or expiring.
    """
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=DomainGenerationList,
        ),
    )
    return DomainGenerationList.model_validate_json(response.text).generated_domains

def evaluate_domain(domain_name: str, status_info: dict) -> DomainAnalysis:
    prompt = f"Analyze domain potential: {domain_name}. Availability Info: {status_info}"
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction="""
            You are a master domain flipper specializing in high-ticket domains ($10k-$100k+).
            Analyze brandability, commercial intent, and market demand.
            """,
            response_mime_type="application/json",
            response_schema=DomainAnalysis,
        ),
    )
    return DomainAnalysis.model_validate_json(response.text)

# ==========================================
# 6. 24/7 AUTOMATED ENGINE PIPELINE
# ==========================================
def run_247_domain_hunter():
    keywords = ["ai", "pay", "cloud", "crypto", "agent", "saas"]
    niches = ["AI & Automation", "FinTech & Payments", "Crypto & Web3", "SaaS & Cloud"]
    
    print("🚀 24/7 Domain Hunter Pipeline Started...")
    
    while True:
        for kw in keywords:
            for niche in niches:
                print(f"\n🔍 Searching for Keyword: '{kw}' in Niche: '{niche}'...")
                candidates = generate_candidate_domains(kw, niche)
                
                for domain in candidates:
                    domain = domain.lower().strip()
                    godaddy_data = check_godaddy_availability(domain)
                    
                    if godaddy_data.get("available", False):
                        print(f"AVAILABLE DOMAIN: {domain} -> Running AI Valuation...")
                        analysis = evaluate_domain(domain, godaddy_data)
                        
                        if analysis.score >= 75 or "Tier 1" in analysis.valuation_tier or "Tier 2" in analysis.valuation_tier:
                            send_telegram_alert(analysis)
                    else:
                        print(f"TAKEN: {domain}")
                
                time.sleep(10)
                
        print("Completed one full cycle. Waiting 15 minutes before next scan...")
        time.sleep(900)

if __name__ == "__main__":
    run_247_domain_hunter()
