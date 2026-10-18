"""REPORTER agent: turns the analysis markdown into a downloadable PDF."""
import re
from fpdf import FPDF
from fpdf.enums import XPos, YPos


def _safe(text: str) -> str:
    # fpdf's built-in fonts are latin-1; strip anything outside it
    return text.encode("latin-1", errors="replace").decode("latin-1")


def markdown_to_pdf(title: str, markdown_text: str) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    def mc(h: float, text: str) -> None:
        # fpdf2 >= 2.7.6 defaults multi_cell cursor to the right; reset it each line
        pdf.multi_cell(0, h, _safe(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "B", 18)
    mc(10, title)
    pdf.ln(4)
    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()
        if not line:
            pdf.ln(3)
            continue
        if line.startswith("### "):
            pdf.set_font("Helvetica", "B", 13)
            mc(8, line[4:])
            pdf.ln(1)
        elif line.startswith("## "):
            pdf.set_font("Helvetica", "B", 15)
            mc(9, line[3:])
            pdf.ln(1)
        elif line.startswith("# "):
            pdf.set_font("Helvetica", "B", 16)
            mc(9, line[2:])
            pdf.ln(1)
        elif line.startswith(("- ", "* ")):
            pdf.set_font("Helvetica", "", 11)
            mc(6, "- " + line[2:])
        elif line.startswith("|"):
            pdf.set_font("Courier", "", 8)
            mc(5, line)
        else:
            clean = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
            pdf.set_font("Helvetica", "", 11)
            mc(6, clean)
    out = pdf.output()
    return bytes(out)
