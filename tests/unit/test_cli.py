import csv
import io
import json

from typer.testing import CliRunner

from gmail_tool.cli import app
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


class FakeApplication:
    def __init__(self) -> None:
        self.last_call = None

    def list_labels(self) -> list[GmailLabel]:
        return [GmailLabel(id="1", name="INBOX"), GmailLabel(id="2", name="IMPORTANT")]

    def auth_check(self) -> dict[str, str | int]:
        return {
            "auth_mode": "oauth",
            "gmail_user_id": "me",
            "label_count": 2,
        }

    def read_message(self, message_id: str) -> GmailMessage:
        self.last_call = {"message_id": message_id}
        return GmailMessage(
            message_id=message_id,
            recipient="to@example.com",
            sender="from@example.com",
            date="Mon, 01 Jan 2024 10:00:00 +0000",
            subject="Hello",
            body="Message body",
        )

    def run_label_action(
        self,
        *,
        label: str,
        action: str,
        limit: int | None,
        from_date,
        to_date,
        starred,
    ):
        self.last_call = {
            "label": label,
            "action": action,
            "limit": limit,
            "from_date": from_date,
            "to_date": to_date,
            "starred": starred,
        }
        if action == "list":
            return [
                GmailMessageHeader(
                    message_id="abc123",
                    recipient="to@example.com",
                    sender="from@example.com",
                    date="Mon, 01 Jan 2024 10:00:00 +0000",
                    subject="Hello",
                ),
                GmailMessageHeader(
                    message_id="def456",
                    recipient="to2@example.com",
                    sender="from2@example.com",
                    date="Tue, 02 Jan 2024 11:00:00 +0000",
                    subject="World",
                ),
            ]
        return ["line-1", "line-2"]


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


def test_labels_command_outputs_label_names(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(app, ["labels"])

    assert result.exit_code == 0
    assert "INBOX" in result.stdout
    assert "IMPORTANT" in result.stdout


def test_labels_command_outputs_json(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(app, ["labels", "--format", "json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == [
        {"id": "1", "name": "INBOX"},
        {"id": "2", "name": "IMPORTANT"},
    ]


def test_labels_command_outputs_csv(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(app, ["labels", "--format", "csv"])

    assert result.exit_code == 0
    rows = list(csv.DictReader(io.StringIO(result.stdout)))
    assert rows == [
        {"id": "1", "name": "INBOX"},
        {"id": "2", "name": "IMPORTANT"},
    ]


def test_label_action_command_passes_filters(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(
        app,
        [
            "label",
            "INBOX",
            "count",
            "--from-date",
            "2024-01-01",
            "--to-date",
            "2024-01-02",
            "--starred",
            "false",
            "--limit",
            "10",
        ],
    )

    assert result.exit_code == 0
    assert fake_app.last_call == {
        "label": "INBOX",
        "action": "count",
        "limit": 10,
        "from_date": "2024-01-01",
        "to_date": "2024-01-02",
        "starred": False,
    }


def test_auth_check_command_outputs_status(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(app, ["auth-check"])

    assert result.exit_code == 0
    assert "auth_mode=oauth" in result.stdout
    assert "gmail_user_id=me" in result.stdout
    assert "label_count=2" in result.stdout


def test_read_command_outputs_full_message(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(app, ["read", "abc123"])

    assert result.exit_code == 0
    assert "message_id=abc123" in result.stdout
    assert "recipient=to@example.com" in result.stdout
    assert "sender=from@example.com" in result.stdout
    assert "date=Mon, 01 Jan 2024 10:00:00 +0000" in result.stdout
    assert "subject=Hello" in result.stdout
    assert "Message body" in result.stdout


def test_label_list_actions_outputs_supported_actions(monkeypatch) -> None:
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())

    result = CliRunner().invoke(app, ["label", "--list-actions"])

    assert result.exit_code == 0
    assert result.stdout.splitlines() == ["count", "list"]


def test_label_list_action_outputs_json(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(app, ["label", "INBOX", "list", "--format", "json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == [
        {
            "message_id": "abc123",
            "recipient": "to@example.com",
            "sender": "from@example.com",
            "date": "Mon, 01 Jan 2024 10:00:00 +0000",
            "subject": "Hello",
        },
        {
            "message_id": "def456",
            "recipient": "to2@example.com",
            "sender": "from2@example.com",
            "date": "Tue, 02 Jan 2024 11:00:00 +0000",
            "subject": "World",
        },
    ]


def test_label_list_action_outputs_csv(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(app, ["label", "INBOX", "list", "--format", "csv"])

    assert result.exit_code == 0
    rows = list(csv.DictReader(io.StringIO(result.stdout)))
    assert rows == [
        {
            "message_id": "abc123",
            "recipient": "to@example.com",
            "sender": "from@example.com",
            "date": "Mon, 01 Jan 2024 10:00:00 +0000",
            "subject": "Hello",
        },
        {
            "message_id": "def456",
            "recipient": "to2@example.com",
            "sender": "from2@example.com",
            "date": "Tue, 02 Jan 2024 11:00:00 +0000",
            "subject": "World",
        },
    ]


def test_label_list_action_outputs_message_identifier_in_text(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(app, ["label", "INBOX", "list"])

    assert result.exit_code == 0
    assert "message_id=abc123" in result.stdout
    assert "message_id=def456" in result.stdout


def test_label_count_action_rejects_structured_format(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(app, ["label", "INBOX", "count", "--format", "json"])

    assert result.exit_code != 0
    assert "--format is only supported for the list action" in result.stderr
