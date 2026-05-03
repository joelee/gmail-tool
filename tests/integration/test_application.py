from gmail_tool.actions import build_action_registry
from gmail_tool.app import Application
from gmail_tool.config import (
    AppSettings,
    AuthMode,
    AuthSettings,
    GmailSettings,
    OAuthSettings,
    SearchSettings,
    ServiceAccountSettings,
    Settings,
)
from gmail_tool.gmail import GmailLabel, GmailMessage, GmailMessageHeader


class FakeGateway:
    def list_labels(self):
        return [
            GmailLabel(id="INBOX", name="INBOX"),
            GmailLabel(id="Label_66", name="@Later"),
            GmailLabel(id="LBL_EXISTING", name="Existing"),
        ]

    def __init__(self) -> None:
        self.count_calls: list[tuple[str, str | None]] = []
        self.list_calls: list[tuple[str, str | None, int]] = []
        self.search_calls: list[tuple[str, int]] = []
        self.modify_calls: list[tuple[str, tuple[str, ...], tuple[str, ...]]] = []

    def count_messages(self, label: str, query: str | None) -> int:
        self.count_calls.append((label, query))
        return 7

    def list_message_headers(self, label: str, query: str | None, limit: int):
        self.list_calls.append((label, query, limit))
        return [
            GmailMessageHeader(
                message_id="msg-1",
                recipient="to@example.com",
                sender="from@example.com",
                date="Tue, 02 Jan 2024 10:00:00 +0000",
                subject="Subject",
            )
        ]

    def get_message(self, message_id: str):
        assert message_id == "msg-1"
        return GmailMessage(
            message_id="msg-1",
            recipient="to@example.com",
            sender="from@example.com",
            date="Tue, 02 Jan 2024 10:00:00 +0000",
            subject="Subject",
            body="Hello world",
        )

    def search_message_headers(self, query: str | None, limit: int):
        self.search_calls.append((query or "", limit))
        return [
            GmailMessageHeader(
                message_id="search-1",
                recipient="to@example.com",
                sender="from@example.com",
                date="Wed, 03 Jan 2024 10:00:00 +0000",
                subject="Search Result",
            )
        ]

    def list_message_ids(self, label: str | None, query: str | None) -> list[str]:
        if label is None:
            assert query == "from:bob@example.com"
            return ["search-1", "search-2"]
        assert label == "INBOX"
        assert query == "-is:starred"
        return ["label-1", "label-2"]

    def ensure_label(self, label_name: str) -> str:
        return f"id:{label_name}"

    def modify_message_labels(
        self,
        message_id: str,
        *,
        add_label_ids: list[str],
        remove_label_ids: list[str],
    ) -> None:
        self.modify_calls.append((message_id, tuple(add_label_ids), tuple(remove_label_ids)))


def build_settings() -> Settings:
    return Settings(
        app=AppSettings(default_limit=100),
        search=SearchSettings(saved_queries={}),
        auth=AuthSettings(
            mode=AuthMode.OAUTH,
            scopes=["scope-a"],
            oauth=OAuthSettings(client_secret_file="secret.json", token_file="token.json"),
            service_account=ServiceAccountSettings(
                service_account_file="svc.json",
                subject="user@example.com",
            ),
        ),
        gmail=GmailSettings(user_id="me"),
    )


def test_application_lists_labels() -> None:
    app = Application(
        settings=build_settings(),
        gateway=FakeGateway(),
        action_registry=build_action_registry(),
    )

    labels = app.list_labels()

    assert [label.name for label in labels] == ["INBOX", "@Later", "Existing"]


def test_application_runs_count_action() -> None:
    gateway = FakeGateway()
    app = Application(
        settings=build_settings(),
        gateway=gateway,
        action_registry=build_action_registry(),
    )

    lines = app.run_label_action(
        label="INBOX",
        action="count",
        limit=None,
        from_date="2024-01-01",
        to_date=None,
        starred=True,
    )

    assert lines == ["7"]
    assert gateway.count_calls == [("INBOX", "after:2024/01/01 is:starred")]


def test_application_runs_list_action_with_default_limit() -> None:
    gateway = FakeGateway()
    app = Application(
        settings=build_settings(),
        gateway=gateway,
        action_registry=build_action_registry(),
    )

    lines = app.run_label_action(
        label="INBOX",
        action="list",
        limit=None,
        from_date=None,
        to_date=None,
        starred=False,
    )

    assert lines == [
        GmailMessageHeader(
            message_id="msg-1",
            recipient="to@example.com",
            sender="from@example.com",
            date="Tue, 02 Jan 2024 10:00:00 +0000",
            subject="Subject",
        )
    ]
    assert gateway.list_calls == [("INBOX", "-is:starred", 100)]


def test_application_resolves_exact_label_name_to_id() -> None:
    gateway = FakeGateway()
    app = Application(
        settings=build_settings(),
        gateway=gateway,
        action_registry=build_action_registry(),
    )

    lines = app.run_label_action(
        label="@Later",
        action="list",
        limit=None,
        from_date=None,
        to_date=None,
        starred=None,
    )

    assert lines == [
        GmailMessageHeader(
            message_id="msg-1",
            recipient="to@example.com",
            sender="from@example.com",
            date="Tue, 02 Jan 2024 10:00:00 +0000",
            subject="Subject",
        )
    ]
    assert gateway.list_calls == [("Label_66", None, 100)]


def test_application_accepts_exact_label_id_unchanged() -> None:
    gateway = FakeGateway()
    app = Application(
        settings=build_settings(),
        gateway=gateway,
        action_registry=build_action_registry(),
    )

    lines = app.run_label_action(
        label="Label_66",
        action="count",
        limit=None,
        from_date=None,
        to_date=None,
        starred=None,
    )

    assert lines == ["7"]
    assert gateway.count_calls == [("Label_66", None)]


def test_application_rejects_unknown_label() -> None:
    app = Application(
        settings=build_settings(),
        gateway=FakeGateway(),
        action_registry=build_action_registry(),
    )

    try:
        app.run_label_action(
            label="MissingLabel",
            action="list",
            limit=None,
            from_date=None,
            to_date=None,
            starred=None,
        )
    except ValueError as exc:
        assert str(exc) == "Unknown label: MissingLabel"
    else:
        raise AssertionError("Expected ValueError for unknown label")


def test_application_reads_message() -> None:
    app = Application(
        settings=build_settings(),
        gateway=FakeGateway(),
        action_registry=build_action_registry(),
    )

    message = app.read_message("msg-1")

    assert message == GmailMessage(
        message_id="msg-1",
        recipient="to@example.com",
        sender="from@example.com",
        date="Tue, 02 Jan 2024 10:00:00 +0000",
        subject="Subject",
        body="Hello world",
    )


def test_application_searches_messages_with_filters() -> None:
    gateway = FakeGateway()
    app = Application(
        settings=build_settings(),
        gateway=gateway,
        action_registry=build_action_registry(),
    )

    lines = app.search_messages(
        action="list",
        query="from:bob@example.com has:attachment",
        limit=None,
        from_date="2024-01-01",
        to_date=None,
        starred=True,
    )

    assert gateway.search_calls == [
        ("from:bob@example.com has:attachment after:2024/01/01 is:starred", 100)
    ]
    assert lines == [
        GmailMessageHeader(
            message_id="search-1",
            recipient="to@example.com",
            sender="from@example.com",
            date="Wed, 03 Jan 2024 10:00:00 +0000",
            subject="Search Result",
        )
    ]


def test_application_searches_with_count_action() -> None:
    gateway = FakeGateway()
    app = Application(
        settings=build_settings(),
        gateway=gateway,
        action_registry=build_action_registry(),
    )

    lines = app.search_messages(
        query="from:bob@example.com",
        action="count",
        limit=None,
        from_date=None,
        to_date=None,
        starred=None,
    )

    assert lines == ["2"]


def test_application_searches_with_add_label_action() -> None:
    gateway = FakeGateway()
    app = Application(
        settings=build_settings(),
        gateway=gateway,
        action_registry=build_action_registry(),
    )

    lines = app.search_messages(
        query="from:bob@example.com",
        action="add-label:FollowUp",
        limit=None,
        from_date=None,
        to_date=None,
        starred=None,
    )

    assert lines == ["2 messages updated"]
    assert gateway.modify_calls == [
        ("search-1", ("id:FollowUp",), ()),
        ("search-2", ("id:FollowUp",), ()),
    ]
