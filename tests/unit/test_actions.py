from gmail_tool.actions import build_action_registry
from gmail_tool.filters import MessageFilters
from gmail_tool.gmail import GmailLabel, GmailMessageHeader


class FakeGateway:
    def __init__(self) -> None:
        self.count_calls: list[tuple[str, str | None]] = []
        self.list_calls: list[tuple[str, str | None, int]] = []
        self.search_list_calls: list[tuple[str | None, int]] = []
        self.ensure_label_calls: list[str] = []
        self.modify_calls: list[tuple[str, tuple[str, ...], tuple[str, ...]]] = []

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

    def search_message_headers(self, query: str | None, limit: int) -> list[GmailMessageHeader]:
        self.search_list_calls.append((query, limit))
        return [
            GmailMessageHeader(
                message_id="search-1",
                recipient="to@example.com",
                sender="from@example.com",
                date="Mon, 01 Jan 2024 10:00:00 +0000",
                subject="Hello",
            )
        ]

    def list_message_ids(self, label: str | None, query: str | None) -> list[str]:
        if label is None:
            return ["search-1", "search-2"]
        return ["label-1", "label-2"]

    def ensure_label(self, label_name: str) -> str:
        self.ensure_label_calls.append(label_name)
        return f"id:{label_name}"

    def modify_message_labels(
        self,
        message_id: str,
        *,
        add_label_ids: list[str],
        remove_label_ids: list[str],
    ) -> None:
        self.modify_calls.append((message_id, tuple(add_label_ids), tuple(remove_label_ids)))

    def list_labels(self) -> list[GmailLabel]:
        return [GmailLabel(id="LBL_EXISTING", name="Existing")]


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


def test_search_list_action_uses_search_gateway_path() -> None:
    gateway = FakeGateway()
    registry = build_action_registry()

    result = registry.run_for_search(
        "list",
        gateway,
        raw_query="from:bob@example.com",
        filters=MessageFilters(starred=True),
        limit=3,
    )

    assert result == [
        GmailMessageHeader(
            message_id="search-1",
            recipient="to@example.com",
            sender="from@example.com",
            date="Mon, 01 Jan 2024 10:00:00 +0000",
            subject="Hello",
        )
    ]
    assert gateway.search_list_calls == [("from:bob@example.com is:starred", 3)]


def test_add_label_action_adds_label_to_matching_search_messages() -> None:
    gateway = FakeGateway()
    registry = build_action_registry()

    result = registry.run_for_search(
        "add-label:FollowUp",
        gateway,
        raw_query="from:bob@example.com",
        filters=MessageFilters(),
        limit=10,
    )

    assert result == ["2 messages updated"]
    assert gateway.ensure_label_calls == ["FollowUp"]
    assert gateway.modify_calls == [
        ("search-1", ("id:FollowUp",), ()),
        ("search-2", ("id:FollowUp",), ()),
    ]


def test_remove_label_action_removes_label_from_matching_label_messages() -> None:
    gateway = FakeGateway()
    registry = build_action_registry()

    result = registry.run(
        "remove-label:Existing",
        gateway,
        "INBOX",
        MessageFilters(starred=False),
        limit=10,
    )

    assert result == ["2 messages updated"]
    assert gateway.modify_calls == [
        ("label-1", (), ("LBL_EXISTING",)),
        ("label-2", (), ("LBL_EXISTING",)),
    ]
