"""SQLAlchemy ORM models for the receipt/finance schema.

Design notes:
- `receipts` is the parent record for one purchase; `line_items` are its
  children.
- `categories` is a small reference table so category renames don't require
  touching every line item.
- `corrections` stores user edits to parsed data (FR-8/FR-9 in the SRS) so
  they can later be used as labeled training examples.
- `model_versions` tracks which trained model produced a given parse/
  classification, for reproducibility.
"""

from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)

    receipts: Mapped[list["Receipt"]] = relationship(back_populates="merchant")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    line_items: Mapped[list["LineItem"]] = relationship(back_populates="category")


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    component: Mapped[str] = mapped_column(String(50))  # "ocr_parser" | "classifier"
    version_tag: Mapped[str] = mapped_column(String(50))  # e.g. git SHA or semver
    trained_at: Mapped[dt.datetime] = mapped_column(default=dt.datetime.utcnow)
    metrics_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("merchants.id"), nullable=True)
    purchase_date: Mapped[dt.date | None] = mapped_column(nullable=True)
    subtotal: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    tax: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    total: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    image_path: Mapped[str] = mapped_column(String(500))
    raw_ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    parser_model_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("model_versions.id"), nullable=True)
    ingested_at: Mapped[dt.datetime] = mapped_column(default=dt.datetime.utcnow)

    merchant: Mapped[Merchant | None] = relationship(back_populates="receipts")
    line_items: Mapped[list["LineItem"]] = relationship(back_populates="receipt", cascade="all, delete-orphan")


class LineItem(Base):
    __tablename__ = "line_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    receipt_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("receipts.id"))
    description: Mapped[str] = mapped_column(String(300))
    quantity: Mapped[float] = mapped_column(Numeric(10, 2), default=1)
    unit_price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    line_total: Mapped[float] = mapped_column(Numeric(10, 2))
    category_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    classifier_model_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("model_versions.id"), nullable=True)
    classifier_confidence: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)

    receipt: Mapped[Receipt] = relationship(back_populates="line_items")
    category: Mapped[Category | None] = relationship(back_populates="line_items")


class Correction(Base):
    """A user-made fix to a parsed/classified field — future training data."""

    __tablename__ = "corrections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    line_item_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("line_items.id"), nullable=True)
    receipt_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("receipts.id"), nullable=True)
    field_name: Mapped[str] = mapped_column(String(50))
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str] = mapped_column(Text)
    corrected_at: Mapped[dt.datetime] = mapped_column(default=dt.datetime.utcnow)
