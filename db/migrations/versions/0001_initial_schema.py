"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "merchants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
    )

    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
    )

    op.create_table(
        "model_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("component", sa.String(50), nullable=False),
        sa.Column("version_tag", sa.String(50), nullable=False),
        sa.Column("trained_at", sa.DateTime(), nullable=False),
        sa.Column("metrics_json", sa.Text(), nullable=True),
    )

    op.create_table(
        "receipts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("merchant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("merchants.id"), nullable=True),
        sa.Column("purchase_date", sa.Date(), nullable=True),
        sa.Column("subtotal", sa.Numeric(10, 2), nullable=True),
        sa.Column("tax", sa.Numeric(10, 2), nullable=True),
        sa.Column("total", sa.Numeric(10, 2), nullable=True),
        sa.Column("image_path", sa.String(500), nullable=False),
        sa.Column("raw_ocr_text", sa.Text(), nullable=True),
        sa.Column("parser_model_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("model_versions.id"), nullable=True),
        sa.Column("ingested_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "line_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("receipt_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("receipts.id"), nullable=False),
        sa.Column("description", sa.String(300), nullable=False),
        sa.Column("quantity", sa.Numeric(10, 2), nullable=False, server_default="1"),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("line_total", sa.Numeric(10, 2), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id"), nullable=True),
        sa.Column("classifier_model_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("model_versions.id"), nullable=True),
        sa.Column("classifier_confidence", sa.Numeric(4, 3), nullable=True),
    )

    op.create_table(
        "corrections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("line_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("line_items.id"), nullable=True),
        sa.Column("receipt_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("receipts.id"), nullable=True),
        sa.Column("field_name", sa.String(50), nullable=False),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=False),
        sa.Column("corrected_at", sa.DateTime(), nullable=False),
    )

    op.create_index("ix_receipts_purchase_date", "receipts", ["purchase_date"])
    op.create_index("ix_line_items_receipt_id", "line_items", ["receipt_id"])
    op.create_index("ix_line_items_category_id", "line_items", ["category_id"])


def downgrade() -> None:
    op.drop_table("corrections")
    op.drop_table("line_items")
    op.drop_table("receipts")
    op.drop_table("model_versions")
    op.drop_table("categories")
    op.drop_table("merchants")
