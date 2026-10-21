"""Loads the fictional sample data used by demo mode and the evals (docs/SAMPLE_DATA.md)."""

import io
from dataclasses import dataclass
from datetime import datetime
from email import message_from_bytes, policy
from email.message import EmailMessage
from email.utils import parseaddr, parsedate_to_datetime
from functools import cached_property
from pathlib import Path
from typing import Any

import yaml
from pypdf import PdfReader


@dataclass(frozen=True, slots=True)
class Project:
    id: str
    name: str
    client: str
    address: str
    aliases: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Organization:
    name: str
    role: str
    domains: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SampleAttachment:
    filename: str
    content_type: str
    data: bytes

    def as_stream(self) -> io.BytesIO:
        return io.BytesIO(self.data)


@dataclass(frozen=True, slots=True)
class SampleEmail:
    id: str
    message_id: str
    from_name: str
    from_addr: str
    reply_to: str | None
    subject: str
    received_at: datetime
    auth_results: str
    text: str
    html: str | None
    attachments: tuple[SampleAttachment, ...]
    raw: bytes


@dataclass(frozen=True, slots=True)
class SampleDocument:
    id: str
    title: str
    project_id: str
    doc_type: str
    drive_format: str
    path: Path


@dataclass(frozen=True)
class SampleData:
    projects: tuple[Project, ...]
    organizations: tuple[Organization, ...]
    internal_domain: str
    emails: tuple[SampleEmail, ...]
    documents: tuple[SampleDocument, ...]

    def project(self, project_id: str) -> Project:
        return next(p for p in self.projects if p.id == project_id)

    def email(self, email_id: str) -> SampleEmail:
        return next(e for e in self.emails if e.id == email_id)

    def document(self, document_id: str) -> SampleDocument:
        return next(d for d in self.documents if d.id == document_id)

    def document_text(self, document_id: str) -> str:
        document = self.document(document_id)
        if document.path.suffix == ".pdf":
            return "\n".join(page.extract_text() for page in PdfReader(document.path).pages)
        return document.path.read_text(encoding="utf-8")

    @cached_property
    def known_domains(self) -> frozenset[str]:
        domains = {d for org in self.organizations for d in org.domains}
        return frozenset({*domains, self.internal_domain})


def _read_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _attachment_bytes(part: EmailMessage) -> bytes:
    payload = part.get_payload(decode=True)
    return payload if isinstance(payload, bytes) else b""


def _parse_email(email_id: str, raw: bytes) -> SampleEmail:
    message = message_from_bytes(raw, policy=policy.default)
    if not isinstance(message, EmailMessage):
        raise TypeError(f"{email_id} did not parse as an email message")
    from_name, from_addr = parseaddr(str(message["From"]))
    reply_to = parseaddr(str(message["Reply-To"]))[1] if message["Reply-To"] else None

    plain = message.get_body(preferencelist=("plain",))
    html = message.get_body(preferencelist=("html",))
    attachments = tuple(
        SampleAttachment(
            filename=part.get_filename() or "attachment",
            content_type=part.get_content_type(),
            data=_attachment_bytes(part),
        )
        for part in message.iter_attachments()
        if isinstance(part, EmailMessage)
    )
    return SampleEmail(
        id=email_id,
        message_id=str(message["Message-ID"]),
        from_name=from_name,
        from_addr=from_addr.lower(),
        reply_to=reply_to.lower() if reply_to else None,
        subject=str(message["Subject"]),
        received_at=parsedate_to_datetime(str(message["Date"])),
        auth_results=str(message["Authentication-Results"] or ""),
        text=plain.get_content() if isinstance(plain, EmailMessage) else "",
        html=html.get_content() if isinstance(html, EmailMessage) else None,
        attachments=attachments,
        raw=raw,
    )


def load_sample_data(base: Path) -> SampleData:
    projects_doc = _read_yaml(base / "projects.yaml")
    contacts = _read_yaml(base / "contacts.yaml")
    manifest = _read_yaml(base / "docs" / "manifest.yaml")

    projects = tuple(
        Project(p["id"], p["name"], p["client"], p["address"], tuple(p.get("aliases", [])))
        for p in projects_doc["projects"]
    )
    organizations = tuple(
        Organization(o["name"], o["role"], tuple(o["domains"])) for o in contacts["organizations"]
    )
    email_paths = sorted((base / "emails").glob("E*.eml"), key=lambda p: int(p.stem[1:]))
    emails = tuple(_parse_email(path.stem, path.read_bytes()) for path in email_paths)
    documents = tuple(
        SampleDocument(
            id=d["id"],
            title=d["title"],
            project_id=d["project_id"],
            doc_type=d["doc_type"],
            drive_format=d["drive_format"],
            path=base / "docs" / d["file"],
        )
        for d in manifest["documents"]
    )
    return SampleData(
        projects=projects,
        organizations=organizations,
        internal_domain=contacts["internal"]["domain"],
        emails=emails,
        documents=documents,
    )
