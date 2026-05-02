from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta


@dataclass(frozen=True)
class MessageFilters:
    from_date: date | None = None
    to_date: date | None = None
    starred: bool | None = None

    def to_gmail_query(self) -> str | None:
        parts: list[str] = []

        if self.from_date is not None:
            parts.append(f"after:{self.from_date.strftime('%Y/%m/%d')}")

        if self.to_date is not None:
            exclusive_end = self.to_date + timedelta(days=1)
            parts.append(f"before:{exclusive_end.strftime('%Y/%m/%d')}")

        if self.starred is True:
            parts.append("is:starred")
        elif self.starred is False:
            parts.append("-is:starred")

        if not parts:
            return None
        return " ".join(parts)


def parse_date(value: str | None) -> date | None:
    if value is None:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()
