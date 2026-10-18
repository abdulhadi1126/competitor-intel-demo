"""SCOUT agent: profiles a competitor from its website (multiple pages) + public mentions."""
import requests
from bs4 import BeautifulSoup
from google import genai

MODEL = "gemini-3.8-flash"  # if Google retires this one day, change the name here

# Pages worth reading on most business sites, in priority order
CANDIDATE_PATHS = ["", "/pricing", "/about", "/features", "/plans", "/product"]


def _get_text(url: str, max_chars: int = 8000) -> str:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; CompetitorIntel/0.1)"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    lines = [line.strip() for line in soup.get_text(separator="\n").splitlines() if line.strip()]
    return "\n".join(lines)[:max_chars]


def fetch_website_text(url: str, max_chars: int = 12000) -> str:
    """Single-page fetch (kept for compatibility)."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return _get_text(url, max_chars)


def fetch_site_pages(url: str) -> str:
    """Fetch homepage + likely sub-pages (pricing, about, features...). Labeled, merged."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    base = url.rstrip("/")
    parts, seen = [], set()
    for path in CANDIDATE_PATHS:
        page_url = base + path
        try:
            text = _get_text(page_url)
            if text and len(text) > 80 and text not in seen:
                seen.add(text)
                label = path.strip("/") or "homepage"
                parts.append(f"--- PAGE: {label} ({page_url}) ---\n{text}")
        except Exception:
            continue  # page doesn't exist or blocked — skip quietly
        if sum(len(p) for p in parts) > 20000:
            break
    return "\n\n".join(parts)[:22000]


def search_mentions(company_name: str, max_results: int = 6) -> str:
    """Free web search (DuckDuckGo, no API key) for reviews / pricing talk / news."""
    try:
        q = requests.utils.quote(f"{company_name} reviews pricing")
        resp = requests.get(
            f"https://lite.duckduckgo.com/lite/?q={q}",
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            timeout=20,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        out = []
        for r in soup.select(".result-snippet")[:max_results]:
            t = r.get_text(" ", strip=True)
            if t:
                out.append("- " + t)
        return "\n".join(out)
    except Exception:
        return ""


def summarize_competitor(api_key: str, company_name: str, website_text: str,
                         mentions: str = "") -> str:
    """Turn raw website text + public mentions into a sharp, specific profile."""
    client = genai.Client(api_key=api_key)
    prompt = (
        f'You are a senior market research analyst. Profile "{company_name}" using ONLY the '
        "material below. Be ruthless about specificity.\n\n"
        "STRICT RULES:\n"
        "- Quote EXACT prices, plan names, feature names, and numbers whenever they appear.\n"
        "- NEVER write generic filler like 'strong online presence', 'user-friendly interface', "
        "or 'innovative solutions' — unless the site uses those exact words, and then quote them.\n"
        "- Every strength and weakness must point to something concrete you observed.\n"
        '- If pricing is absent, write "Pricing not listed" and note any signal (free trial, '
        '"contact sales", etc.).\n\n'
        "Write these sections:\n"
        "1. What they sell — concrete product/service list\n"
        "2. Pricing — exact figures, plan names, or 'not listed'\n"
        "3. Target customer — who specifically, based on site language\n"
        "4. Strengths — 3, each with the evidence you saw\n"
        "5. Weaknesses / gaps — 3, each with the evidence you saw\n"
        "6. Notable claims — striking quotes or promises from the site\n\n"
        f"WEBSITE MATERIAL:\n{website_text}\n\n"
        f"PUBLIC MENTIONS (reviews/news snippets):\n{mentions or 'none found'}"
    )
    return client.models.generate_content(model=MODEL, contents=prompt).text
