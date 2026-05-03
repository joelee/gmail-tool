import csv
import io
import json
from pathlib import Path

from typer.testing import CliRunner

from gmail_tool.cli import app
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

    def search_messages(
        self,
        *,
        action: str,
        query: str,
        limit: int | None,
        from_date,
        to_date,
        starred,
    ):
        self.last_call = {
            "action": action,
            "query": query,
            "limit": limit,
            "from_date": from_date,
            "to_date": to_date,
            "starred": starred,
        }
        if action == "list":
            return [
                GmailMessageHeader(
                    message_id="search-1",
                    recipient="to@example.com",
                    sender="from@example.com",
                    date="Mon, 01 Jan 2024 10:00:00 +0000",
                    subject="Search Result",
                )
            ]
        return ["2 messages updated"]

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
        app=AppSettings(default_limit=100),
        search=SearchSettings(
            saved_queries={
                "recent_attachments": "has:attachment newer_than:30d",
                "ring": "from:no-reply@rs.ring.com newer_than:7d",
            }
        ),
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


def test_global_version_option_outputs_version(monkeypatch) -> None:
    monkeypatch.setattr("gmail_tool.cli._get_version", lambda: "9.9.9")

    result = CliRunner().invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == "9.9.9"


def test_global_short_version_option_outputs_version(monkeypatch) -> None:
    monkeypatch.setattr("gmail_tool.cli._get_version", lambda: "9.9.9")

    result = CliRunner().invoke(app, ["-V"])

    assert result.exit_code == 0
    assert result.stdout.strip() == "9.9.9"


def test_global_verbose_outputs_debug_to_stderr(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr(
        "gmail_tool.cli.discover_config_path",
        lambda path=None: Path("/tmp/test-config.toml"),
    )
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(app, ["--verbose", "labels"])

    assert result.exit_code == 0
    assert "Using config: /tmp/test-config.toml" in result.stderr


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
            "--action",
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


def test_label_short_config_format_and_limit_options(monkeypatch) -> None:
    fake_app = FakeApplication()
    seen_config: list[object] = []

    monkeypatch.setattr(
        "gmail_tool.cli.discover_config_path",
        lambda path=None: Path(path) if path else Path("/tmp/test-config.toml"),
    )
    monkeypatch.setattr(
        "gmail_tool.cli.load_settings",
        lambda path=None: seen_config.append(path) or build_settings(),
    )
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(app, ["label", "INBOX", "-c", "alt.toml", "-f", "json", "-l", "2"])

    assert result.exit_code == 0
    assert seen_config == [Path("alt.toml")]
    assert fake_app.last_call == {
        "label": "INBOX",
        "action": "list",
        "limit": 2,
        "from_date": None,
        "to_date": None,
        "starred": None,
    }


def test_label_action_short_option_passes_action(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(app, ["label", "INBOX", "-a", "count"])

    assert result.exit_code == 0
    assert fake_app.last_call == {
        "label": "INBOX",
        "action": "count",
        "limit": None,
        "from_date": None,
        "to_date": None,
        "starred": None,
    }


def test_label_action_defaults_to_list(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(app, ["label", "INBOX"])

    assert result.exit_code == 0
    assert fake_app.last_call == {
        "label": "INBOX",
        "action": "list",
        "limit": None,
        "from_date": None,
        "to_date": None,
        "starred": None,
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


def test_search_command_passes_query_and_filters(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(
        app,
        [
            "search",
            "from:bob@example.com",
            "has:attachment",
            "--from-date",
            "2024-01-01",
            "--to-date",
            "2024-01-31",
            "--starred",
            "true",
            "--limit",
            "5",
        ],
    )

    assert result.exit_code == 0
    assert fake_app.last_call == {
        "action": "list",
        "query": "from:bob@example.com has:attachment",
        "limit": 5,
        "from_date": "2024-01-01",
        "to_date": "2024-01-31",
        "starred": True,
    }


def test_search_command_outputs_json(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(app, ["search", "from:bob@example.com", "--format", "json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == [
        {
            "message_id": "search-1",
            "recipient": "to@example.com",
            "sender": "from@example.com",
            "date": "Mon, 01 Jan 2024 10:00:00 +0000",
            "subject": "Search Result",
        }
    ]


def test_search_command_outputs_csv(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(app, ["search", "from:bob@example.com", "--format", "csv"])

    assert result.exit_code == 0
    rows = list(csv.DictReader(io.StringIO(result.stdout)))
    assert rows == [
        {
            "message_id": "search-1",
            "recipient": "to@example.com",
            "sender": "from@example.com",
            "date": "Mon, 01 Jan 2024 10:00:00 +0000",
            "subject": "Search Result",
        }
    ]


def test_search_command_outputs_text_with_message_identifier(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(app, ["search", "from:bob@example.com"])

    assert result.exit_code == 0
    assert "message_id=search-1" in result.stdout
    assert "subject=Search Result" in result.stdout


def test_search_command_lists_query_examples(monkeypatch) -> None:
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())

    result = CliRunner().invoke(app, ["search", "--list-query-examples"])

    assert result.exit_code == 0
    assert "from:bob@example.com has:attachment" in result.stdout
    assert "newer_than:7d" in result.stdout


def test_search_command_prints_cheat_sheet(monkeypatch) -> None:
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())

    result = CliRunner().invoke(app, ["search", "--cheat-sheet"])

    assert result.exit_code == 0
    assert "Gmail Search Operators Cheat Sheet" in result.stdout
    assert "from:" in result.stdout
    assert "has:attachment" in result.stdout
    assert "newer_than:" in result.stdout


def test_search_command_uses_saved_query(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(app, ["search", "--saved-query", "recent_attachments"])

    assert result.exit_code == 0
    assert fake_app.last_call == {
        "action": "list",
        "query": "has:attachment newer_than:30d",
        "limit": None,
        "from_date": None,
        "to_date": None,
        "starred": None,
    }


def test_search_command_combines_saved_query_and_raw_query(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(
        app,
        ["search", "has:drive", "--saved-query", "ring"],
    )

    assert result.exit_code == 0
    assert fake_app.last_call == {
        "action": "list",
        "query": "from:no-reply@rs.ring.com newer_than:7d has:drive",
        "limit": None,
        "from_date": None,
        "to_date": None,
        "starred": None,
    }


def test_search_action_option_passes_count_action(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(app, ["search", "from:bob@example.com", "--action", "count"])

    assert result.exit_code == 0
    assert fake_app.last_call == {
        "action": "count",
        "query": "from:bob@example.com",
        "limit": None,
        "from_date": None,
        "to_date": None,
        "starred": None,
    }


def test_search_action_rejects_structured_format_for_non_list(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(
        app,
        ["search", "from:bob@example.com", "--action", "count", "--format", "json"],
    )

    assert result.exit_code != 0
    assert "--format is only supported for the list action" in result.stderr


def test_search_action_defaults_to_list(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(app, ["search", "from:bob@example.com"])

    assert result.exit_code == 0
    assert fake_app.last_call["action"] == "list"


def test_search_add_label_action_outputs_update_count(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(
        app,
        ["search", "from:bob@example.com", "--action", "add-label:FollowUp"],
    )

    assert result.exit_code == 0
    assert "2 messages updated" in result.stdout


def test_search_command_rejects_unknown_saved_query(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(app, ["search", "--saved-query", "missing"])

    assert result.exit_code != 0
    assert "Unknown saved query: missing" in result.stderr


def test_label_list_actions_outputs_supported_actions(monkeypatch) -> None:
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())

    result = CliRunner().invoke(app, ["label", "--list-actions"])

    assert result.exit_code == 0
    assert result.stdout.splitlines() == [
        "add-label:<label_name>",
        "count",
        "list",
        "remove-label:<label_name>",
    ]


def test_label_list_action_outputs_json(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(app, ["label", "INBOX", "--format", "json"])

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

    result = CliRunner().invoke(app, ["label", "INBOX", "--format", "csv"])

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

    result = CliRunner().invoke(app, ["label", "INBOX"])

    assert result.exit_code == 0
    assert "message_id=abc123" in result.stdout
    assert "message_id=def456" in result.stdout


def test_label_count_action_rejects_structured_format(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(app, ["label", "INBOX", "--action", "count", "--format", "json"])

    assert result.exit_code != 0
    assert "--format is only supported for the list action" in result.stderr


def test_label_action_reports_unknown_label_cleanly(monkeypatch) -> None:
    fake_app = FakeApplication()

    def raise_unknown_label(*, label: str, action: str, limit, from_date, to_date, starred):
        raise ValueError(f"Unknown label: {label}")

    fake_app.run_label_action = raise_unknown_label
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(app, ["label", "@Later"])

    assert result.exit_code != 0
    assert "Unknown label: @Later" in result.stderr
