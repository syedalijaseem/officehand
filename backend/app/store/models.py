"""Database tables (see docs/DATA_MODEL.md §3).

Conventions:
- IDs are random UUIDv7.
- Every business table carries `workspace_id` (via `WorkspaceScoped`) and is accessed only through
  `ScopedRepository`.
- Columns ending in `_enc` hold ciphertext (workspace DEK, or KEK for tokens). Plaintext columns
  are limited to IDs, statuses, enums, timestamps, hashes and metrics.
"""

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, Column, Index, UniqueConstraint, text
from sqlmodel import Field, SQLModel

from app.store.ids import uuid7


def utcnow() -> datetime:
    return datetime.now(UTC)


def _json_column() -> Any:
    return Field(default=None, sa_column=Column(JSON))


class Role(StrEnum):
    OWNER = "owner"
    OFFICE_MANAGER = "office_manager"
    MEMBER = "member"


class ConnectionKind(StrEnum):
    MAIL = "mail"
    DRIVE = "drive"


class ConnectionStatus(StrEnum):
    ACTIVE = "active"
    NEEDS_REAUTH = "needs_reauth"
    DISABLED = "disabled"
    REVOKED = "revoked"


class EmailStatus(StrEnum):
    NEW = "new"
    QUEUED = "queued"
    EXTRACTING = "extracting"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    EXECUTING = "executing"
    DONE = "done"
    REJECTED = "rejected"
    FAILED = "failed"
    ERROR = "error"


class Decision(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"


class ActionType(StrEnum):
    SHEET_APPEND = "sheet_append"
    LINE_ITEMS_APPEND = "line_items_append"
    GMAIL_DRAFT = "gmail_draft"


class ActionStatus(StrEnum):
    PENDING = "pending"
    DONE = "done"
    FAILED = "failed"


class WorkspaceScoped(SQLModel):
    workspace_id: uuid.UUID | None = Field(
        default=None, foreign_key="workspaces.id", index=True, nullable=False
    )


# --- Tenancy & identity -------------------------------------------------------------------------


class Workspace(SQLModel, table=True):
    __tablename__ = "workspaces"
    id: uuid.UUID = Field(default_factory=uuid7, primary_key=True)
    name: str = Field(max_length=200)
    settings: dict[str, Any] | None = _json_column()
    created_at: datetime = Field(default_factory=utcnow)


class DataKey(SQLModel, table=True):
    __tablename__ = "data_keys"
    workspace_id: uuid.UUID = Field(foreign_key="workspaces.id", primary_key=True)
    dek_wrapped: str
    kek_version: int = 1
    created_at: datetime = Field(default_factory=utcnow)


class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("google_iss", "google_sub"),)
    id: uuid.UUID = Field(default_factory=uuid7, primary_key=True)
    google_iss: str
    google_sub: str
    email: str = Field(max_length=320)
    name: str | None = Field(default=None, max_length=200)
    created_at: datetime = Field(default_factory=utcnow)


class Member(WorkspaceScoped, table=True):
    __tablename__ = "members"
    __table_args__ = (UniqueConstraint("workspace_id", "user_id"),)
    id: uuid.UUID = Field(default_factory=uuid7, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    role: Role
    project_scope: list[str] | None = _json_column()  # None = all projects
    created_at: datetime = Field(default_factory=utcnow)
    removed_at: datetime | None = None


class Invitation(WorkspaceScoped, table=True):
    __tablename__ = "invitations"
    id: uuid.UUID = Field(default_factory=uuid7, primary_key=True)
    email_lower: str = Field(max_length=320, index=True)
    role: Role
    invited_by: uuid.UUID = Field(foreign_key="users.id")
    token_hash: str
    expires_at: datetime
    accepted_at: datetime | None = None


class UserSession(SQLModel, table=True):
    __tablename__ = "sessions"
    id_hash: str = Field(primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspaces.id", index=True)
    auth_time: datetime
    ip_hash: str | None = None
    ua_hash: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    last_seen_at: datetime = Field(default_factory=utcnow)
    expires_at: datetime
    revoked_at: datetime | None = None


class Connection(WorkspaceScoped, table=True):
    __tablename__ = "connections"
    id: uuid.UUID = Field(default_factory=uuid7, primary_key=True)
    owner_user_id: uuid.UUID = Field(foreign_key="users.id")
    kind: ConnectionKind
    scopes: str
    refresh_token_enc: str
    status: ConnectionStatus = ConnectionStatus.ACTIVE
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


# --- Inbox workflow -----------------------------------------------------------------------------


class Email(WorkspaceScoped, table=True):
    __tablename__ = "emails"
    __table_args__ = (UniqueConstraint("workspace_id", "gmail_message_id"),)
    id: uuid.UUID = Field(default_factory=uuid7, primary_key=True)
    connection_id: uuid.UUID | None = Field(default=None, foreign_key="connections.id")
    gmail_message_id: str
    thread_id: str
    rfc822_message_id: str | None = None
    from_addr_enc: str
    reply_to_enc: str | None = None
    auth_results: dict[str, Any] | None = _json_column()
    subject_enc: str | None = None
    received_at: datetime
    body_raw_enc: str | None = None
    body_text_enc: str | None = None
    attachments_text_enc: str | None = None
    attachments_meta: list[dict[str, Any]] | None = _json_column()
    status: EmailStatus = Field(default=EmailStatus.NEW, index=True)
    attempts: int = 0
    locked_at: datetime | None = None
    error_code: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class Extraction(WorkspaceScoped, table=True):
    __tablename__ = "extractions"
    __table_args__ = (UniqueConstraint("email_id", "version"),)
    id: uuid.UUID = Field(default_factory=uuid7, primary_key=True)
    email_id: uuid.UUID = Field(foreign_key="emails.id", index=True)
    version: int = 1
    raw_llm_json_enc: str | None = None
    validated_json_enc: str | None = None
    warning_codes: list[str] | None = _json_column()
    draft_reply_enc: str | None = None
    model: str
    prompt_version: str
    created_at: datetime = Field(default_factory=utcnow)


class Approval(WorkspaceScoped, table=True):
    __tablename__ = "approvals"
    __table_args__ = (
        Index(
            "uq_approvals_one_approved_per_email",
            "email_id",
            unique=True,
            sqlite_where=text("decision = 'approved'"),
        ),
    )
    id: uuid.UUID = Field(default_factory=uuid7, primary_key=True)
    email_id: uuid.UUID = Field(foreign_key="emails.id", index=True)
    extraction_id: uuid.UUID = Field(foreign_key="extractions.id")
    approved_by: uuid.UUID = Field(foreign_key="users.id")
    approver_role: Role
    approved_at: datetime = Field(default_factory=utcnow)
    decision: Decision
    final_payload_enc: str | None = None
    payload_sha256: str | None = None
    recipient_enc: str | None = None
    edited_fields: dict[str, Any] | None = _json_column()
    draft_text_final_enc: str | None = None
    blocks_acknowledged: list[str] | None = _json_column()
    second_approved_by: uuid.UUID | None = Field(default=None, foreign_key="users.id")
    second_approved_at: datetime | None = None


class Action(WorkspaceScoped, table=True):
    __tablename__ = "actions"
    id: uuid.UUID = Field(default_factory=uuid7, primary_key=True)
    approval_id: uuid.UUID = Field(foreign_key="approvals.id", index=True)
    type: ActionType
    status: ActionStatus = ActionStatus.PENDING
    external_ref: str | None = None
    attempts: int = 0
    last_error_code: str | None = None
    updated_at: datetime = Field(default_factory=utcnow)


class TrackerSeq(SQLModel, table=True):
    __tablename__ = "tracker_seq"
    workspace_id: uuid.UUID = Field(foreign_key="workspaces.id", primary_key=True)
    year: int = Field(primary_key=True)
    next_value: int = 1


class Lock(SQLModel, table=True):
    __tablename__ = "locks"
    workspace_id: uuid.UUID = Field(foreign_key="workspaces.id", primary_key=True)
    name: str = Field(primary_key=True)
    holder: str
    expires_at: datetime


# --- LLM, Q&A, documents, audit -----------------------------------------------------------------


class LlmCall(WorkspaceScoped, table=True):
    __tablename__ = "llm_calls"
    id: uuid.UUID = Field(default_factory=uuid7, primary_key=True)
    user_id: uuid.UUID | None = Field(default=None, foreign_key="users.id")
    purpose: str = Field(index=True)  # extract | draft | answer | embed | judge
    model: str
    prompt_version: str | None = None
    latency_ms: int
    input_tokens: int = 0
    output_tokens: int = 0
    cost_micro_usd: int = 0
    ok: bool
    error_type: str | None = None
    finish_reason: str | None = None
    email_id: uuid.UUID | None = Field(default=None, foreign_key="emails.id")
    question_id: uuid.UUID | None = Field(default=None, foreign_key="questions.id")
    langfuse_trace_id: str | None = None
    created_at: datetime = Field(default_factory=utcnow, index=True)


class Question(WorkspaceScoped, table=True):
    __tablename__ = "questions"
    id: uuid.UUID = Field(default_factory=uuid7, primary_key=True)
    user_id: uuid.UUID | None = Field(default=None, foreign_key="users.id")
    text_enc: str
    project_filter: str | None = None
    answer_enc: str | None = None
    answerable: bool | None = None
    dropped_claims: int = 0
    feedback: str | None = None  # up | down
    created_at: datetime = Field(default_factory=utcnow)


class Document(WorkspaceScoped, table=True):
    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("workspace_id", "drive_file_id"),)
    id: uuid.UUID = Field(default_factory=uuid7, primary_key=True)
    drive_file_id: str
    title_enc: str
    mime_type: str
    project_id: str = Field(index=True)  # "P-101" or "company"
    drive_url: str | None = None
    modified_time: datetime | None = None
    checksum: str | None = None
    chunk_count: int = 0
    suspicious_chunks: int = 0
    last_indexed_at: datetime | None = None


class AuditLog(SQLModel, table=True):
    """Append-only. Holds metadata only, never content. workspace_id may be null for the final
    entry written after a workspace wipe."""

    __tablename__ = "audit_log"
    id: uuid.UUID = Field(default_factory=uuid7, primary_key=True)
    at: datetime = Field(default_factory=utcnow, index=True)
    workspace_id: uuid.UUID | None = Field(default=None, index=True)
    actor_user_id: uuid.UUID | None = None
    event: str = Field(index=True)
    object_type: str | None = None
    object_id: str | None = None
    outcome: str  # success | denied | failed
    ip_hash: str | None = None
    ua_hash: str | None = None
    detail: dict[str, Any] | None = _json_column()
