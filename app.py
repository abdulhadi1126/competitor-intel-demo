"""Competitor Intel — ONE COPY PER CLIENT.

The client opens this app, enters their company + competitors, picks analyses,
and gets a dashboard report + downloadable PDF. Deploy a separate copy for each
paying client (see README.md).
"""
import os
import streamlit as st

from scout import fetch_website_text, summarize_competitor
from analyst import compare
from reporter import markdown_to_pdf


st.set_page_config(page_title="Competitor Intel", layout="wide")

# --- Optional client password: set CLIENT_PASSWORD in the host's Secrets.
# Keeps each client's copy private even on free (public-URL) hosting. ---
_required_pw = os.getenv("CLIENT_PASSWORD", "")
if _required_pw and not st.session_state.get("authed", False):
    st.title("Competitor Intelligence Dashboard")
    _pw = st.text_input("Enter your access password", type="password")
    if st.button("Unlock"):
        if _pw == _required_pw:
            st.session_state["authed"] = True
            st.rerun()
        else:
            st.error("Wrong password — try again.")
    st.stop()

st.title("Competitor Intelligence Dashboard")
st.caption("Run your own competitor analysis, anytime. Your data never leaves this session.")

# --- API key: client pastes their own FREE Gemini key (sidebar, session-only) ---
api_key = st.sidebar.text_input(
    "Gemini API key",
    type="password",
    help="Free key: https://aistudio.google.com/apikey — paste it here. It is not stored.",
)
if not api_key:
    api_key = os.getenv("GEMINI_API_KEY", "")

client_company = st.text_input("Your company name")

st.subheader("Competitors (up to 3)")
competitors = []
for i in range(1, 4):
    c1, c2 = st.columns(2)
    name = c1.text_input(f"Competitor {i} name", key=f"name{i}")
    url = c2.text_input(f"Competitor {i} website", key=f"url{i}", placeholder="https://…")
    if name.strip() and url.strip():
        competitors.append((name.strip(), url.strip()))

analyses = st.multiselect(
    "Analyses to run",
    ["Pricing comparison", "Positioning", "Strengths & weaknesses", "Opportunities & threats"],
    default=["Pricing comparison", "Strengths & weaknesses", "Opportunities & threats"],
)

if st.button("Run analysis", type="primary"):
    if not api_key:
        st.error("Add your free Gemini API key in the sidebar first.")
        st.stop()
    if not client_company.strip():
        st.error("Enter your company name.")
        st.stop()
    if not competitors:
        st.error("Enter at least one competitor (name + website).")
        st.stop()

    profiles = {}
    prog = st.progress(0, text="Scouting competitors…")
    for idx, (name, url) in enumerate(competitors):
        with st.spinner(f"Scouting {name}…"):
            try:
                text = fetch_website_text(url)
                profiles[name] = summarize_competitor(api_key, name, text)
            except Exception as e:  # noqa: BLE001 — show friendly error per competitor
                st.warning(f"Could not scout {name}: {e}")
        prog.progress((idx + 1) / (len(competitors) + 1), text="Scouting competitors…")

    if not profiles:
        st.error("No competitor data collected. Check the website URLs and try again.")
        st.stop()

    with st.spinner("Analyzing…"):
        report_md = compare(api_key, client_company.strip(), profiles, analyses)
    prog.progress(1.0, text="Done")

    st.subheader("Report")
    st.markdown(report_md)
    pdf_bytes = markdown_to_pdf(f"Competitor Analysis — {client_company.strip()}", report_md)
    st.download_button(
        "Download PDF report",
        pdf_bytes,
        file_name="competitor-analysis.pdf",
        mime="application/pdf",
    )
