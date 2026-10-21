# OfficeHand

**An AI assistant for small-business offices that works inside Google Workspace. You approve every action.**

OfficeHand reads the office inbox and logs what matters into a Google Sheet. It drafts replies for you to approve, and it answers plain-English questions about project documents with citations to the exact source. The first version is built for the office manager of a custom residential construction company. The core is designed to be reused for other small businesses, such as equipment and car dealers.

> Status: **early development** (foundation in place; workflows in progress). All data in this repo is fictional.

---

## Who it's for

The office manager of a small company who:

- lives in Gmail, Google Sheets and Google Drive
- re-types invoices, change orders and quote requests into a spreadsheet by hand
- gets asked "what's the countertop allowance on the Hendricks job?" and has to dig through a contract to answer
- is not technical and has no time to learn a new tool

## The two workflows

### 1. Inbox → Tracker

1. Click **Sync inbox**. OfficeHand reads new emails: change orders, invoices, quote requests and subcontractor updates.
2. Each email is classified. Key details are pulled out: client, project, amount, dates, line items and the action needed. Every field is validated, and anything odd is flagged (for example, line items that don't add up to the total, or a request to change bank details).
3. A draft reply is prepared.
4. You review the result, edit anything, and click **Approve**. Only then does OfficeHand add the row to the Google Sheet and save the reply to your **Gmail Drafts**. You still press Send in Gmail.

### 2. Project document Q&A

Ask a question in plain English, for example _"What's the change-order markup on the Alvarez job?"_ The answer comes with numbered citations, and each one shows the document, the section and the exact quoted text. If the answer isn't in the documents, OfficeHand says so instead of guessing.

## Screenshots

| Inbox queue   | Review & approve | Document Q&A  |
| ------------- | ---------------- | ------------- |
| _placeholder_ | _placeholder_    | _placeholder_ |

## Principles

- **Human in the loop.** Nothing is sent, written or changed without an explicit Approve.
- **Reliable over clever.** Outputs are structured, every field is validated with Pydantic, errors show clearly, and every LLM call is traced.
- **Verifiably grounded.** Extracted amounts, document numbers and dates must quote the email. Every answer sentence must quote its source document, and code checks each quote and number before you see it.
- **Safe by design.** The model has no tools and never sees credentials. Email and document text is treated as untrusted data, never as instructions. Google OAuth uses the fewest scopes that work.
- **Swappable model.** v1 uses Google Gemini behind a small provider interface.

## Stack

FastAPI (Python 3.12) · Angular (latest stable, ≥ v21: standalone, signals, zoneless) + Tailwind · Google Gemini (chat + embeddings) · LlamaIndex (parsing/chunking) · Chroma (embedded vector store) · SQLite · Docker · Fly.io

## Quickstart

```bash
git clone https://github.com/syedalijaseem/officehand && cd officehand
cp .env.example .env            # then: make secrets, and paste the values into .env
docker compose up --build
open http://localhost:8000
```

`DEMO_MODE=true` runs against the bundled fictional sample data, so you don't need a Google account. `LLM_PROVIDER=fake` runs without an API key; set `LLM_PROVIDER=gemini` and `GEMINI_API_KEY` for real model calls.

For local development without Docker, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Contributing & security

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup and workflow. Please report vulnerabilities privately as described in [SECURITY.md](SECURITY.md).

## License

MIT
