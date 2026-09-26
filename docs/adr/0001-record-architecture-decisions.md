# 1. Record architecture decisions

## Status
Accepted

## Context
We need a lightweight, permanent record of significant technical decisions
and their rationale, so future-us (or a recruiter/interviewer) can see why a
choice was made, not just what it was.

## Decision
We will use Architecture Decision Records (ADRs), one Markdown file per
decision, numbered sequentially, stored in `docs/adr/`. Each ADR has:
Status, Context, Decision, Consequences.

## Consequences
Every non-trivial technical choice (database, GUI framework, OCR engine,
LLM guardrail design, etc.) gets an ADR before or shortly after
implementation. Small/reversible choices don't need one.
