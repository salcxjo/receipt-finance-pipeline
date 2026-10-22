# Software Requirements Specification
## Project: Receipt & Personal Finance Pipeline

**Version:** 0.1 (draft)
**Author:** Salar Mirikhoozani
**Status:** Draft — for review before Phase 1 kickoff

---

## 1. Introduction

### 1.1 Purpose
This document specifies the functional and non-functional requirements for a
personal-finance data platform that captures paper/digital receipts, extracts
structured data from them via OCR and ML, stores the result in a normalized
relational database, and exposes it through a desktop GUI, a REST API, and a
natural-language (LLM) query interface.

### 1.2 Scope
The system will:
- Accept receipt photos taken on an Android phone, uploaded over HTTP from a mobile web page (any image file can also be uploaded)
- Extract merchant, date, line items, and totals via OCR + a trained parsing model
- Classify line items into spending categories via a trained classifier
- Store all data in PostgreSQL with a versioned schema
- Provide a desktop GUI for browsing, correcting, and analyzing spending
- Provide a REST API for programmatic access
- Provide an LLM-backed natural-language query interface scoped to the schema

Out of scope for v1: bank account integration (Plaid/Yodlee-style), multi-user
accounts/auth beyond a single local user, mobile app.

### 1.3 Definitions
- **Receipt**: a single purchase record (one physical or digital receipt)
- **Line item**: one product/service entry within a receipt
- **Capture client**: the phone browser used to photograph and upload receipts
- **Category**: a spending classification (groceries, dining, transport, etc.)

---

## 2. System Overview

```
[Android phone: camera + mobile web page]
        |  HTTPS/HTTP over LAN or Tailscale, X-API-Key
        v
[Upload API: auth, size/format validation] -> [OCR + Parsing] -> [Ingestion]
                                                                     |
                                                                     v
                                                            [PostgreSQL DB]
                                                             /      |      \
                                                     [REST API] [GUI app] [LLM query layer]
```

---

## 3. Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1 | System shall accept a receipt photo taken on a phone via a mobile web page that opens the camera directly | Must |
| FR-2 | System shall accept JPEG/PNG/WebP files through an authenticated upload endpoint, rejecting non-images and oversized files | Must |
| FR-3 | System shall run OCR on a captured receipt image and extract raw text | Must |
| FR-4 | System shall parse OCR output into structured fields: merchant, date, line items (name, qty, unit price, total), tax, grand total | Must |
| FR-5 | System shall classify each line item into one of a configurable set of spending categories | Must |
| FR-6 | System shall persist parsed receipts and line items to the database with a link to the source image | Must |
| FR-7 | System shall allow a user to view a receipt's parsed data alongside its source image in the GUI | Must |
| FR-8 | System shall allow a user to correct a mis-parsed field or mis-classified category in the GUI | Must |
| FR-9 | Corrections made in FR-8 shall be stored as labeled training examples for future model retraining | Should |
| FR-10 | System shall provide spending summaries (by category, by merchant, by time period) in the GUI | Must |
| FR-11 | System shall expose all receipt/line-item/category data via a documented REST API | Must |
| FR-12 | System shall accept a natural-language question about the user's spending and return a correct, schema-grounded answer | Must |
| FR-13 | The LLM query layer shall never execute a write/DDL query against the database — read-only enforcement | Must |
| FR-14 | System shall log every ingestion event (success/failure/reason) for audit and debugging | Should |
| FR-15 | System shall support re-running OCR/classification on a stored receipt image if a model is updated | Could |

## 4. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-1 | Receipt OCR + parsing on the server shall complete in under 10 seconds per phone-resolution receipt |
| NFR-2 | The API server shall run headless (no monitor), on a laptop or a Raspberry Pi |
| NFR-3 | All database schema changes shall be applied via versioned migrations (no manual DDL) |
| NFR-4 | Line-item categorization accuracy shall reach at least 85% on a held-out test set before GUI integration |
| NFR-5 | The LLM query layer shall validate generated SQL against an allow-list of tables/columns before execution |
| NFR-6 | Test coverage on non-GUI source code shall be at least 75% |
| NFR-7 | The system shall be runnable fully locally with no cloud dependency except (optionally) the LLM API call |
| NFR-8 | GUI shall remain responsive (<200ms interaction latency) with up to 10,000 stored receipts |
| NFR-9 | The upload endpoint shall require an API key and be reachable only over a private network (LAN or Tailscale) |

## 5. Constraints
- Hardware: only an Android phone and a development machine are required; the Pi 4 and
  Pico 2W are not used in v1 (a Pi may optionally host the API server later)
- Primary development OS: Windows/Linux
- Must hand-code core logic (OCR post-processing, parsing, classification
  training loop, ingestion service, API, GUI) rather than relying on
  no-code/low-code tooling. Third-party libraries are fine for OCR engines,
  ORM, GUI framework, and web framework — hand-coding effort goes into the
  logic that connects them, not reimplementing libraries.

## 6. Requirements Traceability (initial)

| Requirement | Component | Test Type |
|-------------|-----------|-----------|
| FR-1, FR-2 | Upload endpoint + mobile page (`src/api`) | Unit, integration |
| FR-3, FR-4 | OCR/Parsing (`src/ml/inference`) | Unit |
| FR-5 | Classifier (`src/ml/inference`) | Unit |
| FR-6, FR-14 | Ingestion API (`src/ingestion`) | Unit, integration |
| FR-7, FR-8, FR-10 | GUI (`src/gui`) | Unit (pytest-qt) |
| FR-9 | Training pipeline (`src/ml/training`) | Unit |
| FR-11 | REST API (`src/api`) | Integration |
| FR-12, FR-13 | LLM query layer (`src/llm`) | Unit, integration |

## 7. Milestones
1. Schema + migrations (DB) — Postgres schema live, Alembic migrations working
2. Ingestion service + REST API skeleton, with tests
3. OCR + parsing pipeline (offline first, then Pi 4)
4. Classifier training pipeline + first trained model
5. GUI (browse, correct, summarize)
6. LLM query layer with SQL guardrails
7. End-to-end test: phone photo -> upload -> OCR -> DB -> GUI, on real receipts

## 8. Open Questions
- Which OCR engine: Tesseract (fully local, weaker on receipts) vs PaddleOCR
  (better accuracy, heavier) vs a cloud OCR API (fastest to a working demo,
  less "hand-coded") — recommend starting with Tesseract + a hand-written
  post-processing/layout parser, revisit if accuracy is too low
- Category taxonomy: fixed list vs user-editable — recommend fixed list of
  ~15 categories for v1, editable in v2
- Image preprocessing (resize, grayscale, deskew, threshold with OpenCV): raw phone photos
  OCR poorly, so this is likely the first accuracy win before touching the parser
