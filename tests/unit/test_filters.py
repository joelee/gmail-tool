from datetime import date

from gmail_tool.filters import MessageFilters


def test_compile_query_with_date_range_and_starred_true() -> None:
    filters = MessageFilters(from_date=date(2024, 1, 2), to_date=date(2024, 1, 31), starred=True)

    assert filters.to_gmail_query() == "after:2024/01/02 before:2024/02/01 is:starred"


def test_compile_query_with_starred_false_only() -> None:
    filters = MessageFilters(starred=False)

    assert filters.to_gmail_query() == "-is:starred"


def test_compile_query_with_no_filters() -> None:
    assert MessageFilters().to_gmail_query() is None
