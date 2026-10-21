"""Build the fictional sample data files from their readable sources.

    uv run --project backend python scripts/build_sample_data.py

- sample_data/emails.yaml        -> sample_data/emails/E{n}.eml
- sample_data/docs/D2-*.md        -> sample_data/docs/D2-hendricks-specifications.pdf (real pages)
- attachments of kind scanned_pdf -> an image-only PDF with no text layer

Output is deterministic (fixed PDF dates, fixed Message-IDs) so re-running produces no diff.
"""

from __future__ import annotations

import re
import sys
from datetime import UTC, datetime
from email.message import EmailMessage
from email.policy import SMTP
from pathlib import Path
from typing import Any

import yaml
from fpdf import FPDF

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "sample_data"
FIXED_PDF_DATE = datetime(2026, 2, 12, tzinfo=UTC)
PAGE_BREAK = "=== PAGE ==="


class _SpecPDF(FPDF):
    footer_text = ""

    def footer(self) -> None:
        if not self.footer_text:
            return
        self.set_y(-15)
        self.set_font("Helvetica", "", 8)
        self.cell(0, 5, f"{self.footer_text} - Page {self.page_no()}", align="C")


def _new_pdf(footer_text: str = "") -> FPDF:
    pdf = _SpecPDF(format="Letter")
    pdf.footer_text = footer_text
    pdf.set_creation_date(FIXED_PDF_DATE)
    pdf.set_producer("OfficeHand sample data")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(22, 22, 22)
    return pdf


def render_spec_pdf(markdown_path: Path, out_path: Path) -> None:
    source = re.sub(r"<!--.*?-->", "", markdown_path.read_text(encoding="utf-8"), flags=re.S)
    pdf = _new_pdf(footer_text="Hendricks Residence - Specifications")
    for page_text in source.split(PAGE_BREAK):
        pdf.add_page()
        for block in (b.strip() for b in page_text.strip().split("\n\n")):
            if not block:
                continue
            if block.startswith("# "):
                pdf.set_font("Helvetica", "B", 16)
                pdf.multi_cell(0, 8, block[2:], new_x="LMARGIN", new_y="NEXT")
            elif block.startswith("## "):
                pdf.ln(2)
                pdf.set_font("Helvetica", "B", 12)
                pdf.multi_cell(0, 7, block[3:], new_x="LMARGIN", new_y="NEXT")
            else:
                pdf.set_font("Helvetica", "", 10.5)
                pdf.multi_cell(0, 5.5, " ".join(block.split("\n")), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2.5)
    pdf.output(str(out_path))


def scanned_pdf_bytes() -> bytes:
    """An image-only 'scan' of a statement: ruled lines and boxes, no extractable text."""
    pdf = _new_pdf()
    pdf.add_page()
    pdf.set_fill_color(235, 235, 230)
    pdf.rect(0, 0, 216, 279, style="F")
    pdf.set_draw_color(90, 90, 90)
    pdf.set_line_width(0.6)
    pdf.rect(22, 22, 70, 18)
    for row in range(14):
        y = 60 + row * 12
        pdf.line(22, y, 194, y)
    for x in (22, 60, 140, 194):
        pdf.line(x, 60, x, 216)
    return bytes(pdf.output())


def build_email(entry: dict[str, Any], defaults: dict[str, Any]) -> bytes:
    msg = EmailMessage(policy=SMTP)
    msg["From"] = entry["from"]
    msg["To"] = entry.get("to", defaults["to"])
    msg["Date"] = entry["date"]
    msg["Subject"] = entry["subject"]
    msg["Message-ID"] = f"<{entry['id'].lower()}@sample.officehand.example>"
    msg["Authentication-Results"] = entry.get("auth_results", defaults["auth_results"])
    if "reply_to" in entry:
        msg["Reply-To"] = entry["reply_to"]
    if "list_unsubscribe" in entry:
        msg["List-Unsubscribe"] = entry["list_unsubscribe"]

    msg.set_content(entry["text"])
    if "html" in entry:
        msg.add_alternative(entry["html"], subtype="html")
    for attachment in entry.get("attachments", []):
        if attachment["kind"] != "scanned_pdf":
            raise ValueError(f"Unknown attachment kind: {attachment['kind']}")
        msg.add_attachment(
            scanned_pdf_bytes(), maintype="application", subtype="pdf", filename=attachment["filename"]
        )
    # Fixed MIME boundaries keep the output byte-for-byte reproducible.
    for index, part in enumerate(msg.walk()):
        if part.is_multipart():
            part.set_boundary(f"==officehand-{entry['id'].lower()}-{index}==")
    return msg.as_bytes()


def main() -> int:
    source = yaml.safe_load((SAMPLE / "emails.yaml").read_text(encoding="utf-8"))
    out_dir = SAMPLE / "emails"
    out_dir.mkdir(exist_ok=True)
    for entry in source["emails"]:
        (out_dir / f"{entry['id']}.eml").write_bytes(build_email(entry, source["defaults"]))

    render_spec_pdf(
        SAMPLE / "docs" / "D2-hendricks-specifications.md",
        SAMPLE / "docs" / "D2-hendricks-specifications.pdf",
    )
    print(f"Built {len(source['emails'])} emails and the D2 specifications PDF.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
