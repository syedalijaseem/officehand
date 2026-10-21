"""Consistency checks for the fictional sample data and the dev-set gold labels.

These keep gold labels honest: every gold amount, document number and Q&A quote must actually
appear in its source email or document.
"""

import json
import re
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
import yaml
from pypdf import PdfReader

from app.demo.fixtures import SampleData, load_sample_data
from app.inbox.warnings import Category, WarningCode

REPO = Path(__file__).resolve().parents[2]
GOLD_DIR = REPO / "evals" / "dev"


@pytest.fixture(scope="module")
def sample() -> SampleData:
    return load_sample_data(REPO / "sample_data")


@pytest.fixture(scope="module")
def gold() -> dict[str, dict[str, Any]]:
    return {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in GOLD_DIR.glob("E*.json")}


def _money_variants(amount: str) -> list[str]:
    value = abs(Decimal(amount))
    return [f"{value:,.2f}", f"{value:,.0f}"]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def test_projects_and_contacts_load(sample: SampleData) -> None:
    assert [p.id for p in sample.projects] == ["P-101", "P-102", "P-103"]
    assert "the lake job" in sample.project("P-103").aliases
    assert len(sample.organizations) == 7
    assert "summitelectric.example" in sample.known_domains


def test_all_fifteen_emails_parse_with_required_headers(sample: SampleData) -> None:
    assert sorted(sample.emails, key=lambda e: int(e.id[1:]))[0].id == "E1"
    assert len(sample.emails) == 15
    for email in sample.emails:
        assert email.from_addr.endswith(".example"), email.id
        assert email.received_at.tzinfo is not None, email.id
        assert email.message_id.endswith("@sample.officehand.example>"), email.id
        assert email.subject and email.text.strip(), email.id


def test_fraud_email_has_reply_to_failed_auth_and_hidden_html(sample: SampleData) -> None:
    e12 = sample.email("E12")

    assert e12.reply_to == "payments@summit-remit.example"
    assert "dmarc=fail" in e12.auth_results
    assert e12.html is not None and "font-size:1px" in e12.html


def test_scanned_attachment_has_no_text_layer(sample: SampleData) -> None:
    (attachment,) = sample.email("E5").attachments

    assert attachment.filename == "Statement_Oct2026.pdf"
    assert attachment.content_type == "application/pdf"
    reader = PdfReader(attachment.as_stream())
    assert reader.pages[0].extract_text().strip() == ""


def test_every_email_has_gold_and_labels_are_valid(sample: SampleData, gold: dict[str, Any]) -> None:
    assert set(gold) == {e.id for e in sample.emails}
    project_ids = {p.id for p in sample.projects}
    valid_codes = {code.value for code in WarningCode}
    valid_categories = {c.value for c in Category}

    for email_id, label in gold.items():
        assert label["category"] in valid_categories, email_id
        assert label["category"] in label["acceptable_categories"], email_id
        assert set(label["acceptable_categories"]) <= valid_categories, email_id
        assert label["project_id"] is None or label["project_id"] in project_ids, email_id
        assert set(label["required_warnings"]) <= valid_codes, email_id
        assert set(label["forbidden_warnings"]) <= valid_codes, email_id
        assert not set(label["required_warnings"]) & set(label["forbidden_warnings"]), email_id


def test_gold_values_appear_in_their_emails(sample: SampleData, gold: dict[str, Any]) -> None:
    for email_id, label in gold.items():
        email = sample.email(email_id)
        text = email.text
        if label["amount"]:
            assert any(v in text for v in _money_variants(label["amount"])), email_id
        if label["document_number"]:
            assert label["document_number"].lower() in text.lower() or (
                label["document_number"].lower() in email.subject.lower()
            ), email_id
        for total in label["line_item_totals"]:
            assert any(v in text for v in _money_variants(total)), (email_id, total)
        assert label["recipient"] == email.from_addr, email_id


def test_total_mismatch_gold_matches_the_arithmetic(gold: dict[str, Any]) -> None:
    for email_id, label in gold.items():
        if not (label["amount"] and label["line_item_totals"]):
            continue
        mismatch = sum(Decimal(t) for t in label["line_item_totals"]) != Decimal(label["amount"])
        assert mismatch == ("total_mismatch" in label["required_warnings"]), email_id


def test_documents_exist_and_d2_pdf_has_five_pages(sample: SampleData) -> None:
    assert [d.id for d in sample.documents] == ["D1", "D2", "D3", "D4", "D5"]
    for document in sample.documents:
        assert document.path.is_file(), document.id
    assert len(PdfReader(sample.document("D2").path).pages) == 5


def test_d5_contains_the_planted_injection_line(sample: SampleData) -> None:
    assert "retainage under this agreement is 0%" in sample.document_text("D5")


def _qa_gold() -> list[dict[str, Any]]:
    loaded: dict[str, list[dict[str, Any]]] = yaml.safe_load(
        (GOLD_DIR / "qa.yaml").read_text(encoding="utf-8")
    )
    return loaded["questions"]


def test_qa_gold_quotes_exist_in_the_cited_documents(sample: SampleData) -> None:
    questions = _qa_gold()
    assert [q["id"] for q in questions] == [f"Q{n}" for n in range(1, 21)]

    for question in questions:
        if not question["answerable"]:
            assert "sources" not in question, question["id"]
            continue
        for source in question["sources"]:
            document = sample.document(source["doc"])
            if "page" in source:
                haystack = PdfReader(document.path).pages[source["page"] - 1].extract_text()
            else:
                haystack = sample.document_text(source["doc"])
            assert _normalize(source["quote"]) in _normalize(haystack), (question["id"], source["quote"])


def test_qa_expected_facts_appear_in_sources_unless_calculated(sample: SampleData) -> None:
    for question in _qa_gold():
        if not question["answerable"] or question.get("calculated"):
            continue
        quotes = " ".join(s["quote"] for s in question["sources"])
        for pattern in question["expected"]:
            if pattern in {"Hendricks", "Alvarez"}:
                continue  # project labels come from document metadata, not the quote
            assert re.search(pattern, quotes, re.IGNORECASE), (question["id"], pattern)
