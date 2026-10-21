"""Email categories and warning codes (docs/DATA_MODEL.md §1).

Warnings are computed by deterministic code, never by the model. The model's self-reports can
only *add* a warning, never clear one.
"""

from enum import StrEnum


class Category(StrEnum):
    CHANGE_ORDER = "change_order"
    INVOICE = "invoice"
    QUOTE_REQUEST = "quote_request"
    SUBCONTRACTOR_UPDATE = "subcontractor_update"
    OTHER = "other"


class Severity(StrEnum):
    INFO = "info"
    WARN = "warn"
    BLOCK = "block"  # Approve stays disabled until the user acknowledges it


class WarningCode(StrEnum):
    UNGROUNDED_FIELD = "ungrounded_field"
    TOTAL_MISMATCH = "total_mismatch"
    MISSING_AMOUNT = "missing_amount"
    MISSING_REQUIRED_FIELD = "missing_required_field"
    UNMATCHED_PROJECT = "unmatched_project"
    AMBIGUOUS_RELATIVE_DATE = "ambiguous_relative_date"
    DATE_IN_PAST = "date_in_past"
    DUPLICATE_DOCUMENT_NUMBER = "duplicate_document_number"
    MULTIPLE_REQUESTS = "multiple_requests"
    SCANNED_ATTACHMENT = "scanned_attachment"
    LOW_CONFIDENCE = "low_confidence"
    UNKNOWN_SENDER_DOMAIN = "unknown_sender_domain"
    LOOKALIKE_SENDER_DOMAIN = "lookalike_sender_domain"
    DISPLAY_NAME_SPOOF = "display_name_spoof"
    REPLY_TO_MISMATCH = "reply_to_mismatch"
    SENDER_AUTH_FAILED = "sender_auth_failed"
    PAYMENT_DETAILS_CHANGE = "payment_details_change"
    POSSIBLE_INJECTION = "possible_injection"
    DRAFT_MENTIONS_OTHER_CLIENT = "draft_mentions_other_client"
    DRAFT_UNEXPECTED_FIGURE = "draft_unexpected_figure"
    DRAFT_COMMITMENT = "draft_commitment"


# Default severities. Some rules lower a severity by context (e.g. missing_amount is only info
# for a client's change-order request that still needs pricing); see inbox/validate.py.
DEFAULT_SEVERITY: dict[WarningCode, Severity] = {
    WarningCode.UNGROUNDED_FIELD: Severity.WARN,
    WarningCode.TOTAL_MISMATCH: Severity.WARN,
    WarningCode.MISSING_AMOUNT: Severity.WARN,
    WarningCode.MISSING_REQUIRED_FIELD: Severity.WARN,
    WarningCode.UNMATCHED_PROJECT: Severity.WARN,
    WarningCode.AMBIGUOUS_RELATIVE_DATE: Severity.INFO,
    WarningCode.DATE_IN_PAST: Severity.INFO,
    WarningCode.DUPLICATE_DOCUMENT_NUMBER: Severity.WARN,
    WarningCode.MULTIPLE_REQUESTS: Severity.INFO,
    WarningCode.SCANNED_ATTACHMENT: Severity.WARN,
    WarningCode.LOW_CONFIDENCE: Severity.INFO,
    WarningCode.UNKNOWN_SENDER_DOMAIN: Severity.INFO,
    WarningCode.LOOKALIKE_SENDER_DOMAIN: Severity.BLOCK,
    WarningCode.DISPLAY_NAME_SPOOF: Severity.BLOCK,
    WarningCode.REPLY_TO_MISMATCH: Severity.WARN,
    WarningCode.SENDER_AUTH_FAILED: Severity.WARN,
    WarningCode.PAYMENT_DETAILS_CHANGE: Severity.BLOCK,
    WarningCode.POSSIBLE_INJECTION: Severity.BLOCK,
    WarningCode.DRAFT_MENTIONS_OTHER_CLIENT: Severity.BLOCK,
    WarningCode.DRAFT_UNEXPECTED_FIGURE: Severity.WARN,
    WarningCode.DRAFT_COMMITMENT: Severity.WARN,
}
