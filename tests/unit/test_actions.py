from gmail_tool.actions import build_action_registry
from gmail_tool.filters import MessageFilters
from gmail_tool.gmail import GmailMessageHeader


class FakeGateway:
    def __init__(self) -> None:
        self.count_calls: list[tuple[str, str | None]] = []
        self.list_calls: list[tuple[str, str | None, int]] = []

    def count_messages(self, label: str, query: str | None) -> int:
        self.count_calls.append((label, query))
        return 3

    def list_message_headers(
        self,
        label: str,
        query: str | None,
        limit: int,
    ) -> list[GmailMessageHeader]:
        self.list_calls.append((label, query, limit))
        return [
            GmailMessageHeader(
                message_id="abc123",
                recipient="to@example.com",
                sender="from@example.com",
                date="Mon, 01 Jan 2024 10:00:00 +0000",
                subject="Hello",
            )
        ]


def test_count_action_uses_gateway_query() -> None:
    gateway = FakeGateway()
    registry = build_action_registry()

    result = registry.run("count", gateway, "INBOX", MessageFilters(starred=True), limit=5)

    assert result == ["3"]
    assert gateway.count_calls == [("INBOX", "is:starred")]


def test_list_action_formats_headers() -> None:
    gateway = FakeGateway()
    registry = build_action_registry()

    result = registry.run("list", gateway, "IMPORTANT", MessageFilters(), limit=2)

    assert result == [
        GmailMessageHeader(
            message_id="abc123",
            recipient="to@example.com",
            sender="from@example.com",
            date="Mon, 01 Jan 2024 10:00:00 +0000",
            subject="Hello",
        )
    ]
    assert gateway.list_calls == [("IMPORTANT", None, 2)]
