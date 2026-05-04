import csv
import io
import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

from gmail_tool.auth import OAuthCredentialsProvider, ServiceAccountCredentialsProvider
from gmail_tool.cli import _build_backup_progress_reporter, app
from gmail_tool.config import (
    AppSettings,
    AuthMode,
    AuthSettings,
    BackupSettings,
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

    def count_search_backup_deletions(
        self,
        *,
        query: str,
        limit,
        from_date,
        to_date,
        starred,
        backup_path=None,
    ) -> int:
        del query, limit, from_date, to_date, starred, backup_path
        return 1

    def count_label_backup_deletions(
        self,
        *,
        label: str,
        limit,
        from_date,
        to_date,
        starred,
        backup_path=None,
    ) -> int:
        del label, limit, from_date, to_date, starred, backup_path
        return 1

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

    def delete_message(self, message_id: str) -> None:
        self.last_call = {"message_id": message_id, "delete": True}

    def search_messages(
        self,
        *,
        action: str,
        label_name: str | None = None,
        query: str,
        limit: int | None,
        from_date,
        to_date,
        starred,
        backup_path=None,
        delete_after_backup: bool = False,
        progress_callback=None,
    ):
        self.last_call = {
            "action": action,
            "query": query,
            "limit": limit,
            "from_date": from_date,
            "to_date": to_date,
            "starred": starred,
        }
        if label_name is not None:
            self.last_call["label_name"] = label_name
        if backup_path is not None:
            self.last_call["backup_path"] = backup_path
        if delete_after_backup:
            self.last_call["delete_after_backup"] = delete_after_backup
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
        if action == "backup":
            if progress_callback is not None:
                progress_callback(
                    "Backing up 1/1: 2024-01-01 10:00:00 | "
                    "search-1 | from@example.com | Search Result"
                )
                progress_callback(None)
            return ["1 messages written to /tmp/backups (0 skipped)"]
        if action in {"label-add", "label-remove"}:
            if progress_callback is not None:
                progress_callback(
                    f"Applying {action} 1/1: 2024-01-01 10:00:00 | "
                    "search-1 | from@example.com | Search Result"
                )
                progress_callback(None)
        return ["2 messages updated"]

    def run_label_action(
        self,
        *,
        label: str,
        action: str,
        label_name: str | None = None,
        limit: int | None,
        from_date,
        to_date,
        starred,
        backup_path=None,
        delete_after_backup: bool = False,
        progress_callback=None,
    ):
        self.last_call = {
            "label": label,
            "action": action,
            "limit": limit,
            "from_date": from_date,
            "to_date": to_date,
            "starred": starred,
        }
        if label_name is not None:
            self.last_call["label_name"] = label_name
        if backup_path is not None:
            self.last_call["backup_path"] = backup_path
        if delete_after_backup:
            self.last_call["delete_after_backup"] = delete_after_backup
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
        if action == "backup":
            if progress_callback is not None:
                progress_callback(
                    "Backing up 1/1: 2024-01-01 10:00:00 | abc123 | from@example.com | Hello"
                )
                progress_callback(None)
            return ["1 messages written to /tmp/backups (0 skipped)"]
        if action in {"label-add", "label-remove"}:
            if progress_callback is not None:
                progress_callback(
                    f"Applying {action} 1/1: 2024-01-01 10:00:00 | "
                    "abc123 | from@example.com | Hello"
                )
                progress_callback(None)
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
        backup=BackupSettings(path=None),
        gmail=GmailSettings(user_id="me"),
    )


def _mock_missing_oauth_setup(monkeypatch) -> None:
    monkeypatch.setattr(
        "gmail_tool.cli.build_application",
        lambda settings: (_ for _ in ()).throw(
            ValueError("Missing required environment variable: GOOGLE_OAUTH_CLIENT_SECRET_FILE")
        ),
    )
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr(
        "gmail_tool.cli.discover_config_path", lambda path=None, required=False: None
    )
    monkeypatch.setattr("gmail_tool.cli.xdg_config_home", lambda: Path("/tmp/config"))
    monkeypatch.setattr("gmail_tool.cli.xdg_state_home", lambda: Path("/tmp/state"))


def _line_index_containing(output: str, text: str) -> int:
    for index, line in enumerate(output.splitlines()):
        if text in line:
            return index
    raise AssertionError(f"Could not find {text!r} in output:\n{output}")


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
        lambda path=None, required=False: Path("/tmp/test-config.toml"),
    )
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(app, ["--verbose", "labels"])

    assert result.exit_code == 0
    assert "Using config: /tmp/test-config.toml" in result.stderr


def test_help_lists_command_descriptions() -> None:
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "labels" in result.stdout
    assert "List Gmail labels." in result.stdout
    assert "message" in result.stdout
    assert "Read or delete a Gmail message by message ID." in result.stdout
    assert "search" in result.stdout
    assert "Search Gmail messages and run actions on matches." in result.stdout
    assert "label" in result.stdout
    assert "Run an action against a Gmail label." in result.stdout
    assert "auth" in result.stdout
    assert "Authentication helpers." in result.stdout


def test_top_level_help_sorts_options_and_commands_alphabetically() -> None:
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0

    option_lines = [
        _line_index_containing(result.stdout, "--help"),
        _line_index_containing(result.stdout, "--install-completion"),
        _line_index_containing(result.stdout, "--show-completion"),
        _line_index_containing(result.stdout, "--verbose"),
        _line_index_containing(result.stdout, "--version"),
    ]
    assert option_lines == sorted(option_lines)

    command_lines = [
        _line_index_containing(result.stdout, "Authentication helpers."),
        _line_index_containing(result.stdout, "Run an action against a Gmail label."),
        _line_index_containing(result.stdout, "List Gmail labels."),
        _line_index_containing(result.stdout, "Read or delete a Gmail message by message ID."),
        _line_index_containing(result.stdout, "Search Gmail messages and run actions on matches."),
    ]
    assert command_lines == sorted(command_lines)


def test_message_help_lists_read_and_delete_commands_alphabetically() -> None:
    result = CliRunner().invoke(app, ["message", "--help"])

    assert result.exit_code == 0

    command_lines = [
        _line_index_containing(result.stdout, "Move a Gmail message to Bin by Gmail message ID."),
        _line_index_containing(result.stdout, "Read a full Gmail message by Gmail message ID."),
    ]
    assert command_lines == sorted(command_lines)


def test_auth_help_sorts_commands_alphabetically() -> None:
    result = CliRunner().invoke(app, ["auth", "--help"])

    assert result.exit_code == 0

    command_lines = [
        _line_index_containing(result.stdout, "Check authentication and Gmail access."),
        _line_index_containing(result.stdout, "Authenticate with Gmail using OAuth."),
        _line_index_containing(result.stdout, "Remove the stored OAuth token file."),
        _line_index_containing(result.stdout, "Show resolved authentication file paths."),
    ]
    assert command_lines == sorted(command_lines)


def test_search_help_shows_argument_and_option_descriptions() -> None:
    result = CliRunner().invoke(app, ["search", "--help"])

    assert result.exit_code == 0
    assert "Raw Gmail search terms to combine into" in result.stdout
    assert "a single query." in result.stdout
    assert "Use a specific" in result.stdout
    assert "config.toml file." in result.stdout
    assert "Action to run: list," in result.stdout
    assert "count, backup, or label" in result.stdout
    assert "mutation." in result.stdout
    assert "Label name for" in result.stdout
    assert "label-add or" in result.stdout
    assert "label-remove actions." in result.stdout
    assert "Saved query name from" in result.stdout
    assert "config.toml to prepend." in result.stdout
    assert "List supported actions" in result.stdout
    assert "and exit." in result.stdout
    assert "Print built-in Gmail" in result.stdout
    assert "query examples and" in result.stdout
    assert "Print a Gmail search" in result.stdout
    assert "operator cheat sheet" in result.stdout
    assert "Output format for list" in result.stdout
    assert "action: json or csv." in result.stdout
    assert "Directory where backup" in result.stdout
    assert ".eml files will be" in result.stdout
    assert "written." in result.stdout
    assert "Maximum number of" in result.stdout
    assert "matching messages to" in result.stdout
    assert "process." in result.stdout
    assert "Only include messages" in result.stdout
    assert "on or after YYYY-MM-DD." in result.stdout
    assert "before YYYY-MM-DD." in result.stdout
    assert "Filter by starred" in result.stdout
    assert "state: true or false." in result.stdout


def test_label_help_shows_argument_and_option_descriptions() -> None:
    result = CliRunner().invoke(app, ["label", "--help"])

    assert result.exit_code == 0
    assert "Exact Gmail label name or exact Gmail label ID." in result.stdout
    assert "Use a specific config.toml" in result.stdout
    assert "file." in result.stdout
    assert "Action to run: list, count," in result.stdout
    assert "backup, or label mutation." in result.stdout
    assert "Label name for label-add or" in result.stdout
    assert "label-remove actions." in result.stdout
    assert "List supported actions and" in result.stdout
    assert "exit." in result.stdout
    assert "Output format for list action:" in result.stdout
    assert "json or csv." in result.stdout
    assert "Directory where backup .eml" in result.stdout
    assert "files will be written." in result.stdout
    assert "Maximum number of matching" in result.stdout
    assert "messages to process." in result.stdout
    assert "Only include messages on or" in result.stdout
    assert "after YYYY-MM-DD." in result.stdout
    assert "Only include messages before" in result.stdout
    assert "YYYY-MM-DD." in result.stdout
    assert "Filter by starred state: true" in result.stdout
    assert "or false." in result.stdout


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
        lambda path=None, required=False: Path(path) if path else Path("/tmp/test-config.toml"),
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


def test_auth_subcommand_check_outputs_status(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(app, ["auth", "check"])

    assert result.exit_code == 0
    assert "auth_mode=oauth" in result.stdout
    assert "gmail_user_id=me" in result.stdout
    assert "label_count=2" in result.stdout


def test_auth_login_runs_oauth_flow(monkeypatch) -> None:
    settings = build_settings()

    class FakeProvider(OAuthCredentialsProvider):
        def __init__(self) -> None:
            self.force_reauth = None
            self.open_browser = None

        def get_credentials(self, *, force_reauth: bool = False, open_browser: bool = True):
            self.force_reauth = force_reauth
            self.open_browser = open_browser
            return type("Creds", (), {"scopes": ["scope-a"]})()

    fake_provider = FakeProvider()

    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: settings)
    monkeypatch.setattr("gmail_tool.cli.build_credentials_provider", lambda settings: fake_provider)

    result = CliRunner().invoke(app, ["auth", "login", "--force"])

    assert result.exit_code == 0
    assert fake_provider.force_reauth is True
    assert fake_provider.open_browser is True
    assert "status=authenticated" in result.stdout
    assert f"token_file={settings.auth.oauth.token_file}" in result.stdout


def test_auth_login_supports_no_browser(monkeypatch) -> None:
    settings = build_settings()

    class FakeProvider(OAuthCredentialsProvider):
        def __init__(self) -> None:
            self.open_browser = None

        def get_credentials(self, *, force_reauth: bool = False, open_browser: bool = True):
            del force_reauth
            self.open_browser = open_browser
            return type("Creds", (), {"scopes": ["scope-a"]})()

    fake_provider = FakeProvider()

    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: settings)
    monkeypatch.setattr("gmail_tool.cli.build_credentials_provider", lambda settings: fake_provider)

    result = CliRunner().invoke(app, ["auth", "login", "--no-browser"])

    assert result.exit_code == 0
    assert fake_provider.open_browser is False


def test_auth_paths_outputs_resolved_locations(monkeypatch) -> None:
    settings = build_settings()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: settings)

    result = CliRunner().invoke(app, ["auth", "paths"])

    assert result.exit_code == 0
    assert f"auth_mode={settings.auth.mode.value}" in result.stdout
    assert f"oauth_client_secret_file={settings.auth.oauth.client_secret_file}" in result.stdout
    assert f"oauth_token_file={settings.auth.oauth.token_file}" in result.stdout
    assert f"gmail_user_id={settings.gmail.user_id}" in result.stdout


def test_auth_logout_removes_existing_oauth_token(monkeypatch, tmp_path: Path) -> None:
    token_file = tmp_path / "oauth-token.json"
    token_file.write_text("{}", encoding="utf-8")

    settings = Settings(
        app=build_settings().app,
        search=build_settings().search,
        auth=AuthSettings(
            mode=AuthMode.OAUTH,
            scopes=["scope-a"],
            oauth=OAuthSettings(client_secret_file="secret.json", token_file=str(token_file)),
            service_account=ServiceAccountSettings(
                service_account_file="service.json",
                subject="user@example.com",
            ),
        ),
        backup=build_settings().backup,
        gmail=build_settings().gmail,
    )

    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: settings)

    result = CliRunner().invoke(app, ["auth", "logout"])

    assert result.exit_code == 0
    assert not token_file.exists()
    assert f"removed_token_file={token_file}" in result.stdout


def test_auth_logout_reports_missing_oauth_token(monkeypatch, tmp_path: Path) -> None:
    token_file = tmp_path / "missing-token.json"
    settings = Settings(
        app=build_settings().app,
        search=build_settings().search,
        auth=AuthSettings(
            mode=AuthMode.OAUTH,
            scopes=["scope-a"],
            oauth=OAuthSettings(client_secret_file="secret.json", token_file=str(token_file)),
            service_account=ServiceAccountSettings(
                service_account_file="service.json",
                subject="user@example.com",
            ),
        ),
        backup=build_settings().backup,
        gmail=build_settings().gmail,
    )

    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: settings)

    result = CliRunner().invoke(app, ["auth", "logout"])

    assert result.exit_code == 0
    assert f"token_file_not_found={token_file}" in result.stdout


def test_auth_logout_rejects_service_account_mode(monkeypatch) -> None:
    settings = Settings(
        app=build_settings().app,
        search=build_settings().search,
        auth=AuthSettings(
            mode=AuthMode.SERVICE_ACCOUNT,
            scopes=["scope-a"],
            oauth=OAuthSettings(client_secret_file="secret.json", token_file="token.json"),
            service_account=ServiceAccountSettings(
                service_account_file="service.json",
                subject="user@example.com",
            ),
        ),
        backup=build_settings().backup,
        gmail=build_settings().gmail,
    )

    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: settings)

    result = CliRunner().invoke(app, ["auth", "logout"])

    assert result.exit_code == 2
    assert "auth logout is only supported when auth mode is oauth" in result.stderr


def test_auth_login_rejects_service_account_mode(monkeypatch) -> None:
    settings = Settings(
        app=build_settings().app,
        search=build_settings().search,
        auth=AuthSettings(
            mode=AuthMode.SERVICE_ACCOUNT,
            scopes=["scope-a"],
            oauth=OAuthSettings(client_secret_file="secret.json", token_file="token.json"),
            service_account=ServiceAccountSettings(
                service_account_file="service.json",
                subject="user@example.com",
            ),
        ),
        backup=build_settings().backup,
        gmail=build_settings().gmail,
    )

    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: settings)
    monkeypatch.setattr(
        "gmail_tool.cli.build_credentials_provider",
        lambda settings: ServiceAccountCredentialsProvider("service.json", ["scope-a"], None),
    )

    result = CliRunner().invoke(app, ["auth", "login"])

    assert result.exit_code == 2
    assert "auth login is only supported when auth mode is oauth" in result.stderr


def test_auth_check_prints_setup_help_when_oauth_secret_missing(monkeypatch) -> None:
    _mock_missing_oauth_setup(monkeypatch)

    result = CliRunner().invoke(app, ["auth", "check"])

    assert result.exit_code == 2
    assert "Gmail authentication is not configured yet." in result.stderr
    assert "/tmp/config/gmail-tool/client_secret.json" in result.stderr
    assert "/tmp/state/gmail-tool/oauth-token.json" in result.stderr


def test_labels_prints_setup_help_when_oauth_secret_missing(monkeypatch) -> None:
    _mock_missing_oauth_setup(monkeypatch)

    result = CliRunner().invoke(app, ["labels"])

    assert result.exit_code == 2
    assert "Gmail authentication is not configured yet." in result.stderr
    assert "/tmp/config/gmail-tool/client_secret.json" in result.stderr


def test_message_read_prints_setup_help_when_oauth_secret_missing(monkeypatch) -> None:
    _mock_missing_oauth_setup(monkeypatch)

    result = CliRunner().invoke(app, ["message", "read", "abc123"])

    assert result.exit_code == 2
    assert "Gmail authentication is not configured yet." in result.stderr
    assert "/tmp/state/gmail-tool/oauth-token.json" in result.stderr


def test_search_prints_setup_help_when_oauth_secret_missing(monkeypatch) -> None:
    _mock_missing_oauth_setup(monkeypatch)

    result = CliRunner().invoke(app, ["search", "from:bob@example.com"])

    assert result.exit_code == 2
    assert "Gmail authentication is not configured yet." in result.stderr
    assert "Run: gmail-tool auth login" in result.stderr


def test_label_prints_setup_help_when_oauth_secret_missing(monkeypatch) -> None:
    _mock_missing_oauth_setup(monkeypatch)

    result = CliRunner().invoke(app, ["label", "INBOX"])

    assert result.exit_code == 2
    assert "Gmail authentication is not configured yet." in result.stderr
    assert "Docs:" in result.stderr


def test_message_read_command_outputs_full_message(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(app, ["message", "read", "abc123"])

    assert result.exit_code == 0
    assert "message_id=abc123" in result.stdout
    assert "recipient=to@example.com" in result.stdout
    assert "sender=from@example.com" in result.stdout
    assert "date=Mon, 01 Jan 2024 10:00:00 +0000" in result.stdout
    assert "subject=Hello" in result.stdout
    assert "Message body" in result.stdout


def test_message_delete_requires_confirmation(monkeypatch) -> None:
    fake_app = FakeApplication()
    confirm_calls: list[str] = []

    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    def fake_confirm(message: str, **kwargs) -> bool:
        del kwargs
        confirm_calls.append(message)
        return True

    monkeypatch.setattr("gmail_tool.cli.typer.confirm", fake_confirm)

    result = CliRunner().invoke(app, ["message", "delete", "abc123"])

    assert result.exit_code == 0
    assert confirm_calls == ["Move message abc123 to Bin?"]
    assert fake_app.last_call == {"message_id": "abc123", "delete": True}
    assert result.stdout.strip() == "message_id=abc123 moved to Bin"


def test_message_delete_can_be_forced_without_confirmation(monkeypatch) -> None:
    fake_app = FakeApplication()

    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)
    monkeypatch.setattr(
        "gmail_tool.cli.typer.confirm",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("should not confirm")),
    )

    result = CliRunner().invoke(app, ["message", "delete", "abc123", "--force"])

    assert result.exit_code == 0
    assert fake_app.last_call == {"message_id": "abc123", "delete": True}
    assert result.stdout.strip() == "message_id=abc123 moved to Bin"


def test_message_delete_cancels_when_confirmation_is_rejected(monkeypatch) -> None:
    fake_app = FakeApplication()

    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)
    monkeypatch.setattr("gmail_tool.cli.typer.confirm", lambda *args, **kwargs: False)

    result = CliRunner().invoke(app, ["message", "delete", "abc123"])

    assert result.exit_code == 2
    assert fake_app.last_call is None
    assert "Cancelled." in result.stderr


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


def test_search_backup_action_passes_backup_path(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(
        app,
        [
            "search",
            "from:bob@example.com",
            "--action",
            "backup",
            "--backup-path",
            "/tmp/backups",
        ],
    )

    assert result.exit_code == 0
    assert fake_app.last_call == {
        "action": "backup",
        "query": "from:bob@example.com",
        "limit": None,
        "from_date": None,
        "to_date": None,
        "starred": None,
        "backup_path": Path("/tmp/backups"),
    }
    assert "\rBacking up 1/1: 2024-01-01 10:00:00 | search-1 | from@example.com |" in result.stderr


def test_search_backup_delete_requires_confirmation(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)
    monkeypatch.setattr("gmail_tool.cli.typer.confirm", lambda *args, **kwargs: True)

    result = CliRunner().invoke(
        app,
        [
            "search",
            "from:bob@example.com",
            "--action",
            "backup",
            "--backup-path",
            "/tmp/backups",
            "--delete",
        ],
    )

    assert result.exit_code == 0
    assert fake_app.last_call["delete_after_backup"] is True


def test_search_backup_delete_can_be_cancelled(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)
    monkeypatch.setattr("gmail_tool.cli.typer.confirm", lambda *args, **kwargs: False)

    result = CliRunner().invoke(
        app,
        [
            "search",
            "from:bob@example.com",
            "--action",
            "backup",
            "--backup-path",
            "/tmp/backups",
            "--delete",
        ],
    )

    assert result.exit_code == 2
    assert "Cancelled." in result.stderr


def test_search_backup_delete_force_skips_confirmation(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)
    monkeypatch.setattr(
        "gmail_tool.cli.typer.confirm",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("should not confirm")),
    )

    result = CliRunner().invoke(
        app,
        [
            "search",
            "from:bob@example.com",
            "--action",
            "backup",
            "--backup-path",
            "/tmp/backups",
            "--delete",
            "--force",
        ],
    )

    assert result.exit_code == 0
    assert fake_app.last_call["delete_after_backup"] is True


def test_search_delete_requires_backup_action(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(
        app,
        ["search", "from:bob@example.com", "--action", "count", "--delete"],
    )

    assert result.exit_code != 0
    assert "--delete is only supported for the backup action" in result.stderr


def test_search_force_requires_backup_delete(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(
        app,
        ["search", "from:bob@example.com", "--action", "backup", "--force"],
    )

    assert result.exit_code != 0
    assert "--force is only supported together with --delete for the backup action" in result.stderr


def test_search_backup_path_rejects_non_backup_action(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(
        app,
        [
            "search",
            "from:bob@example.com",
            "--action",
            "count",
            "--backup-path",
            "/tmp/backups",
        ],
    )

    assert result.exit_code != 0
    assert "--backup-path is only supported for the backup action" in result.stderr


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
        ["search", "from:bob@example.com", "--action", "label-add", "--name", "FollowUp"],
    )

    assert result.exit_code == 0
    assert "2 messages updated" in result.stdout
    assert fake_app.last_call["label_name"] == "FollowUp"
    assert (
        "\rApplying label-add 1/1: 2024-01-01 10:00:00 | search-1 | from@example.com |"
        in result.stderr
    )


def test_search_label_add_requires_name(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(app, ["search", "from:bob@example.com", "--action", "label-add"])

    assert result.exit_code == 2
    assert "--name is required for the label-add action" in result.stderr


def test_search_name_rejected_for_non_label_action(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(
        app,
        ["search", "from:bob@example.com", "--action", "count", "--name", "FollowUp"],
    )

    assert result.exit_code == 2
    assert "--name is only supported for the label-add and label-remove actions" in result.stderr


def test_search_command_rejects_unknown_saved_query(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(app, ["search", "--saved-query", "missing"])

    assert result.exit_code != 0
    assert "Unknown saved query: missing" in result.stderr


def test_search_list_actions_outputs_supported_actions(monkeypatch) -> None:
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())

    result = CliRunner().invoke(app, ["search", "--list-actions"])

    assert result.exit_code == 0
    assert result.stdout.splitlines() == [
        "backup        Back up matching messages as .eml files.",
        "count         Print the number of matching messages.",
        "label-add     Add a label to all matching messages.",
        "label-remove  Remove a label from all matching messages.",
        "list          List matching message headers.",
    ]


def test_search_list_actions_does_not_load_settings(monkeypatch) -> None:
    def fail_load_settings(path=None):
        del path
        raise AssertionError("search --list-actions should not load settings")

    monkeypatch.setattr("gmail_tool.cli.load_settings", fail_load_settings)

    result = CliRunner().invoke(app, ["search", "--list-actions"])

    assert result.exit_code == 0
    assert "backup" in result.stdout


def test_search_help_action_outputs_action_help_without_loading_settings(monkeypatch) -> None:
    def fail_load_settings(path=None):
        del path
        raise AssertionError("search --help-action should not load settings")

    monkeypatch.setattr("gmail_tool.cli.load_settings", fail_load_settings)

    result = CliRunner().invoke(app, ["search", "--help-action", "backup"])

    assert result.exit_code == 0
    assert "Action: backup" in result.stdout
    assert "--backup-path <DIR>" in result.stdout
    assert "--delete" in result.stdout


def test_search_help_action_reports_unknown_action(monkeypatch) -> None:
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())

    result = CliRunner().invoke(app, ["search", "--help-action", "missing"])

    assert result.exit_code == 2
    assert "Unsupported action: missing" in result.stderr


def test_label_list_actions_outputs_supported_actions(monkeypatch) -> None:
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())

    result = CliRunner().invoke(app, ["label", "--list-actions"])

    assert result.exit_code == 0
    assert result.stdout.splitlines() == [
        "backup        Back up matching messages as .eml files.",
        "count         Print the number of matching messages.",
        "label-add     Add a label to all matching messages.",
        "label-remove  Remove a label from all matching messages.",
        "list          List matching message headers.",
    ]


def test_label_help_action_outputs_label_action_help_without_loading_settings(monkeypatch) -> None:
    def fail_load_settings(path=None):
        del path
        raise AssertionError("label --help-action should not load settings")

    monkeypatch.setattr("gmail_tool.cli.load_settings", fail_load_settings)

    result = CliRunner().invoke(app, ["label", "--help-action", "label-add"])

    assert result.exit_code == 0
    assert "Action: label-add" in result.stdout
    assert "--name <LABEL_NAME>" in result.stdout


def test_label_add_requires_name(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(app, ["label", "INBOX", "--action", "label-add"])

    assert result.exit_code == 2
    assert "--name is required for the label-add action" in result.stderr


def test_label_remove_passes_name(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(
        app,
        ["label", "INBOX", "--action", "label-remove", "--name", "Existing"],
    )

    assert result.exit_code == 0
    assert fake_app.last_call["action"] == "label-remove"
    assert fake_app.last_call["label_name"] == "Existing"
    assert (
        "\rApplying label-remove 1/1: 2024-01-01 10:00:00 | abc123 | from@example.com |"
        in result.stderr
    )


def test_label_backup_action_passes_backup_path(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(
        app,
        [
            "label",
            "INBOX",
            "--action",
            "backup",
            "--backup-path",
            "/tmp/backups",
        ],
    )

    assert result.exit_code == 0
    assert fake_app.last_call == {
        "label": "INBOX",
        "action": "backup",
        "limit": None,
        "from_date": None,
        "to_date": None,
        "starred": None,
        "backup_path": Path("/tmp/backups"),
    }
    assert "\rBacking up 1/1: 2024-01-01 10:00:00 | abc123 | from@example.com | Hello" in (
        result.stderr
    )


def test_label_backup_delete_requires_confirmation(monkeypatch) -> None:
    fake_app = FakeApplication()
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)
    monkeypatch.setattr("gmail_tool.cli.typer.confirm", lambda *args, **kwargs: True)

    result = CliRunner().invoke(
        app,
        [
            "label",
            "INBOX",
            "--action",
            "backup",
            "--backup-path",
            "/tmp/backups",
            "--delete",
        ],
    )

    assert result.exit_code == 0
    assert fake_app.last_call["delete_after_backup"] is True


def test_backup_progress_truncates_to_terminal_width(monkeypatch) -> None:
    reporter = _build_backup_progress_reporter()
    messages: list[tuple[str, bool, bool]] = []

    monkeypatch.setattr(
        "gmail_tool.cli.typer.echo",
        lambda text, err=False, nl=True: messages.append((text, err, nl)),
    )
    monkeypatch.setattr(
        "gmail_tool.cli.shutil.get_terminal_size",
        lambda fallback=(80, 24): shutil.os.terminal_size((20, 24)),
    )

    reporter("Backing up 1/1: message_id=search-1 | subject=A very long subject")
    reporter(None)

    assert messages == [
        ("\rBacking up 1/1: mess", True, False),
        ("", True, True),
    ]


def test_label_backup_path_rejects_non_backup_action(monkeypatch) -> None:
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
            "--backup-path",
            "/tmp/backups",
        ],
    )

    assert result.exit_code != 0
    assert "--backup-path is only supported for the backup action" in result.stderr


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

    def raise_unknown_label(
        *,
        label: str,
        action: str,
        label_name: str | None = None,
        limit,
        from_date,
        to_date,
        starred,
        backup_path=None,
        delete_after_backup: bool = False,
        progress_callback=None,
    ):
        del (
            action,
            label_name,
            limit,
            from_date,
            to_date,
            starred,
            backup_path,
            delete_after_backup,
            progress_callback,
        )
        raise ValueError(f"Unknown label: {label}")

    fake_app.run_label_action = raise_unknown_label
    monkeypatch.setattr("gmail_tool.cli.load_settings", lambda path=None: build_settings())
    monkeypatch.setattr("gmail_tool.cli.build_application", lambda settings: fake_app)

    result = CliRunner().invoke(app, ["label", "@Later"])

    assert result.exit_code != 0
    assert "Unknown label: @Later" in result.stderr
