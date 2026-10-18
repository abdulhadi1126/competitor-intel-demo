"""SCOUT agent: fetches a competitor's website and profiles it with Gemini (free tier)."""
import requests
from bs4 import BeautifulSoup
from google import genai

MODEL = "gemini-3.8-flash"  # if Google retires this one day, change the name here


def fetch_website_text(url: str, max_chars: int = 12000) -> str:
    """Download a page and return its readable text (no menus/scripts)."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    headers = {"User-Agent": "Mozilla/5.0 (compatible; CompetitorIntel/0.1)"}
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)[:max_chars]


def summarize_competitor(api_key: str, company_name: str, website_text: str) -> str:
    """Turn raw website text into a structured competitor profile."""
    client = genai.Client(api_key=api_key)
    prompt = (
        f'You are a market research analyst. Based ONLY on the website text below for "{company_name}", '
        "write a concise competitor profile with these sections:\n"
        "1. What they sell (products/services)\n"
        '2. Pricing (any prices, plans, or pricing signals — write "not listed" if absent)\n'
        "3. Positioning (who they target, key claims)\n"
        "4. Strengths visible from the site\n"
        "5. Weaknesses or gaps visible from the site\n\n"
        f"Website text:\n{website_text}\n\n"
        "Keep it factual. Never invent prices, features, or facts not present in the text."
    )
    return client.models.generate_content(model=MODEL, contents=prompt).text
