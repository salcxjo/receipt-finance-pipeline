import pytest

from src.llm.query_engine import UnsafeQueryError, validate_sql


def test_allows_plain_select_on_allowed_tables() -> None:
    sql = "SELECT description, line_total FROM line_items WHERE line_total > 10"
    assert validate_sql(sql) == sql


def test_allows_join_across_allowed_tables() -> None:
    sql = (
        "SELECT c.name, SUM(li.line_total) FROM line_items li "
        "JOIN categories c ON c.id = li.category_id GROUP BY c.name"
    )
    validate_sql(sql)  # should not raise


def test_rejects_delete() -> None:
    with pytest.raises(UnsafeQueryError):
        validate_sql("DELETE FROM receipts WHERE id = '123'")


def test_rejects_drop_table() -> None:
    with pytest.raises(UnsafeQueryError):
        validate_sql("DROP TABLE receipts")


def test_rejects_disallowed_table() -> None:
    with pytest.raises(UnsafeQueryError):
        validate_sql("SELECT * FROM pg_shadow")


def test_rejects_sql_comment_injection_attempt() -> None:
    with pytest.raises(UnsafeQueryError):
        validate_sql("SELECT * FROM receipts -- ; DROP TABLE receipts")


def test_rejects_update_disguised_in_cte() -> None:
    with pytest.raises(UnsafeQueryError):
        validate_sql(
            "WITH x AS (UPDATE receipts SET total = 0 RETURNING id) SELECT * FROM x"
        )
