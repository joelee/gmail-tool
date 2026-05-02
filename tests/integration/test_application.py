from gmail_tool.actions import build_action_registry
from gmail_tool.app import Application
from gmail_tool.config import (
    AppSettings,
    AuthMode,
    AuthSettings,
    GmailSettings,
    OAuthSettings,
    ServiceAccountSettings,
    Settings,
)
from gmail_tool.gmail import GmailLabel, GmailMessage, GmailMessageHeader


class FakeGateway:
    def list_labels(self):
        return [GmailLabel(id="1", name="INBOX")]

    def count_messages(self, label: str, query: str | None) -> int:
        assert label == "INBOX"
        assert query == "after:2024/01/01 is:starred"
        return 7

    def list_message_headers(self, label: str, query: str | None, limit: int):
        assert label == "INBOX"
        assert query == "-is:starred"
        assert limit == 1000
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


def build_settings() -> Settings:
    return Settings(
        app=AppSettings(default_limit=1000),
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

    assert [label.name for label in labels] == ["INBOX"]


def test_application_runs_count_action() -> None:
    app = Application(
        settings=build_settings(),
        gateway=FakeGateway(),
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


def test_application_runs_list_action_with_default_limit() -> None:
    app = Application(
        settings=build_settings(),
        gateway=FakeGateway(),
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
