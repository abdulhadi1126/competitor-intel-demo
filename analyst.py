"""ANALYST agent: compares scouted competitors against the client's company."""
from google import genai

MODEL = "gemini-3.8-flash"  # if Google retires this one day, change the name here


def compare(api_key: str, client_company: str, profiles: dict, analyses: list) -> str:
    """profiles: {competitor_name: profile_text}. Returns a markdown report."""
    client = genai.Client(api_key=api_key)
    joined = "\n\n---\n\n".join(f"## {name}\n{prof}" for name, prof in profiles.items())
    wants = ", ".join(analyses) if analyses else "general comparison"
    prompt = (
        f'You are a market research analyst writing for "{client_company}".\n\n'
        f"Competitor profiles:\n{joined}\n\n"
        f"Write a comparison covering: {wants}.\n"
        "Include:\n"
        "- A markdown comparison table (Company | What they sell | Pricing | Key strength | Key weakness)\n"
        f"- 3 concrete opportunities for {client_company} (gaps competitors leave open)\n"
        "- 3 threats to watch\n"
        "Keep it practical and specific. Never invent facts not present in the profiles."
    )
    return client.models.generate_content(model=MODEL, contents=prompt).text
