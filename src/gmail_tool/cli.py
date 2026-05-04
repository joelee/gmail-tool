from __future__ import annotations

import csv
import json
import shutil
from dataclasses import asdict, is_dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Annotated

import typer

from gmail_tool.actions import build_action_registry
from gmail_tool.app import build_application
from gmail_tool.auth import AuthSetupError, OAuthCredentialsProvider, build_credentials_provider
from gmail_tool.config import (
    Settings,
    discover_config_path,
    load_settings,
    xdg_config_home,
    xdg_state_home,
)
from gmail_tool.gmail import GmailLabel, GmailMessage, GmailMessageHeader

app = typer.Typer(
    no_args_is_help=True,
    context_settings={"help_option_names": ["--help", "-h"]},
)
auth_app = typer.Typer(help="Authentication helpers.")
app.add_typer(auth_app, name="auth")

_verbose = False

SEARCH_QUERY_EXAMPLES = [
    "from:bob@example.com has:attachment",
    "newer_than:7d",
    "subject:invoice",
    "label:INBOX is:unread",
]

SEARCH_CHEAT_SHEET = """# Gmail Search Operators Cheat Sheet

## Core Operators

- `from:` sender address or name
  Example: `from:bob@example.com`
- `to:` recipient address or name
  Example: `to:alice@example.com`
- `subject:` match subject text
  Example: `subject:invoice`
- quoted text for exact phrase matching
  Example: `"monthly report"`

## Status And Flags

- `is:starred` starred messages
- `is:unread` unread messages
- `is:read` read messages
- `has:attachment` messages with attachments
- `is:important` important messages

## Date And Time

- `after:` messages after a date
  Example: `after:2026/05/01`
- `before:` messages before a date
  Example: `before:2026/06/01`
- `older_than:` relative age filter
  Example: `older_than:30d`
- `newer_than:` relative age filter
  Example: `newer_than:7d`

## Labels And Folders

- `label:` specific label
  Example: `label:INBOX`
- `in:` system location
  Example: `in:sent`

## Size

- `larger:` size in bytes
  Example: `larger:1000000`
- `smaller:` size in bytes
  Example: `smaller:500000`

## Boolean Operators

- space means AND
  Example: `from:bob@example.com has:attachment`
- `OR` matches either side
  Example: `from:bob@example.com OR from:alice@example.com`
- `-` negates a term
  Example: `-label:spam`
"""


def _render_json(rows: list[object]) -> str:
    return json.dumps([_to_row_dict(row) for row in rows], indent=2)


def _render_csv(rows: list[object]) -> str:
    if not rows:
        return ""

    fieldnames = list(_to_row_dict(rows[0]))
    lines: list[str] = []
    writer = csv.DictWriter(_ListWriter(lines), fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(_to_row_dict(row))
    return "".join(lines)


def _to_row_dict(row: object) -> dict[str, object]:
    if is_dataclass(row):
        return asdict(row)
    raise TypeError(f"Unsupported row type for structured output: {type(row)!r}")


class _ListWriter:
    def __init__(self, lines: list[str]) -> None:
        self._lines = lines

    def write(self, value: str) -> int:
        self._lines.append(value)
        return len(value)


def _parse_starred(value: str | None) -> bool | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise typer.BadParameter("starred must be true or false")


def _get_version() -> str:
    try:
        return version("gmail-tool")
    except PackageNotFoundError:
        return "0.0.0"


def _debug(message: str) -> None:
    if _verbose:
        typer.echo(message, err=True)


def _load_settings_with_debug(config: Path | None) -> Settings:
    config_path = discover_config_path(config, required=False)
    if config_path is not None:
        _debug(f"Using config: {config_path}")
    else:
        _debug("Using built-in defaults (no config.toml found)")
    return load_settings(config)


def _exit_with_error(message: str) -> None:
    typer.echo(message, err=True)
    raise typer.Exit(code=2)


def _run_with_setup_help(operation, *, config: Path | None = None):
    try:
        return operation()
    except FileNotFoundError as exc:
        _exit_with_error(f"{exc}\n\n{_oauth_setup_instructions(config)}")
    except AuthSetupError as exc:
        _exit_with_error(f"{exc}\n\n{_oauth_setup_instructions(config)}")
    except ValueError as exc:
        message = str(exc)
        if message.startswith("Missing required environment variable:"):
            _exit_with_error(f"{message}\n\n{_oauth_setup_instructions(config)}")
        raise


def _oauth_setup_instructions(config: Path | None) -> str:
    config_path = discover_config_path(config, required=False)
    client_secret_path = xdg_config_home() / "gmail-tool" / "client_secret.json"
    token_path = xdg_state_home() / "gmail-tool" / "oauth-token.json"

    lines = [
        "Gmail authentication is not configured yet.",
        "",
        "Quick start:",
        "1. In Google Cloud Console, create a Desktop OAuth client and enable Gmail API.",
        f"2. Save the downloaded JSON file to: {client_secret_path}",
        "3. Run: gmail-tool auth login",
        "",
        f"The OAuth token will be stored at: {token_path}",
        "",
        "Optional overrides:",
        "  GOOGLE_OAUTH_CLIENT_SECRET_FILE",
        "  GOOGLE_OAUTH_TOKEN_FILE",
        "  GMAIL_USER_ID",
        "",
        "Docs:",
        "  https://github.com/joelee/gmail-tool/blob/main/docs/google-credentials.md",
    ]

    if config_path is not None:
        lines.extend(["", f"Resolved config file: {config_path}"])

    return "\n".join(lines)


def _run_auth_check(config: Path | None) -> None:
    application = build_application(_load_settings_with_debug(config))
    result = application.auth_check()
    for key, value in result.items():
        typer.echo(f"{key}={value}")


def _run_auth_paths(config: Path | None) -> None:
    settings = _load_settings_with_debug(config)
    typer.echo(f"auth_mode={settings.auth.mode.value}")
    typer.echo(f"oauth_client_secret_file={settings.auth.oauth.client_secret_file}")
    typer.echo(f"oauth_token_file={settings.auth.oauth.token_file}")
    typer.echo(f"service_account_file={settings.auth.service_account.service_account_file}")
    typer.echo(f"gmail_user_id={settings.gmail.user_id}")


def _run_auth_logout(config: Path | None) -> None:
    settings = _load_settings_with_debug(config)
    if settings.auth.mode.value != "oauth":
        _exit_with_error("auth logout is only supported when auth mode is oauth")

    token_path = Path(settings.auth.oauth.token_file)
    if token_path.exists():
        token_path.unlink()
        typer.echo(f"removed_token_file={token_path}")
        return

    typer.echo(f"token_file_not_found={token_path}")


def _emit_action_list() -> None:
    actions = build_action_registry().list_actions()
    width = max(len(action_name) for action_name, _ in actions)
    for action_name, description in actions:
        typer.echo(f"{action_name.ljust(width)}  {description}")


def _build_backup_progress_reporter():
    previous_width = 0

    def report(message: str | None) -> None:
        nonlocal previous_width
        if message is None:
            if previous_width > 0:
                typer.echo("", err=True)
                previous_width = 0
            return

        columns = max(shutil.get_terminal_size(fallback=(80, 24)).columns - 1, 20)
        visible_message = message[:columns]
        previous_width = max(previous_width, len(visible_message))
        typer.echo(f"\r{visible_message.ljust(previous_width)}", err=True, nl=False)

    return report


def _validate_backup_path(action: str, backup_path: Path | None) -> None:
    if backup_path is not None and action != "backup":
        _exit_with_error("--backup-path is only supported for the backup action")


@app.callback(invoke_without_command=True)
def main_callback(
    version_option: Annotated[
        bool,
        typer.Option("--version", "-V", help="Show the version and exit."),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Print debug output to stderr."),
    ] = False,
) -> None:
    global _verbose
    _verbose = verbose

    if version_option:
        typer.echo(_get_version())
        raise typer.Exit()


@app.command("labels")
def labels(
    config: Annotated[
        Path | None,
        typer.Option("--config", "-c", dir_okay=False),
    ] = None,
    output_format: Annotated[str | None, typer.Option("--format", "-f")] = None,
) -> None:
    def operation() -> None:
        application = build_application(_load_settings_with_debug(config))
        labels = application.list_labels()
        _emit_rows(labels, output_format=output_format, default_text=_format_labels_text)

    _run_with_setup_help(operation, config=config)


@app.command("auth-check")
def auth_check(
    config: Annotated[
        Path | None,
        typer.Option("--config", "-c", dir_okay=False),
    ] = None,
) -> None:
    _run_with_setup_help(lambda: _run_auth_check(config), config=config)


@auth_app.command("check")
def auth_check_command(
    config: Annotated[
        Path | None,
        typer.Option("--config", "-c", dir_okay=False),
    ] = None,
) -> None:
    _run_with_setup_help(lambda: _run_auth_check(config), config=config)


@auth_app.command("login")
def auth_login(
    config: Annotated[
        Path | None,
        typer.Option("--config", "-c", dir_okay=False),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("--force", help="Ignore an existing token and force browser login."),
    ] = False,
    no_browser: Annotated[
        bool,
        typer.Option(
            "--no-browser", help="Print a console OAuth flow instead of opening a browser."
        ),
    ] = False,
) -> None:
    def operation() -> None:
        settings = _load_settings_with_debug(config)
        provider = build_credentials_provider(settings)

        if not isinstance(provider, OAuthCredentialsProvider):
            _exit_with_error("auth login is only supported when auth mode is oauth")

        credentials = provider.get_credentials(force_reauth=force, open_browser=not no_browser)
        typer.echo(f"auth_mode={settings.auth.mode.value}")
        typer.echo(f"gmail_user_id={settings.gmail.user_id}")
        typer.echo(f"token_file={settings.auth.oauth.token_file}")
        typer.echo(f"scopes={' '.join(credentials.scopes or settings.auth.scopes)}")
        typer.echo("status=authenticated")

    _run_with_setup_help(operation, config=config)


@auth_app.command("paths")
def auth_paths(
    config: Annotated[
        Path | None,
        typer.Option("--config", "-c", dir_okay=False),
    ] = None,
) -> None:
    _run_with_setup_help(lambda: _run_auth_paths(config), config=config)


@auth_app.command("logout")
def auth_logout(
    config: Annotated[
        Path | None,
        typer.Option("--config", "-c", dir_okay=False),
    ] = None,
) -> None:
    _run_with_setup_help(lambda: _run_auth_logout(config), config=config)


@app.command("read")
def read_message(
    message_id: str,
    config: Annotated[
        Path | None,
        typer.Option("--config", "-c", dir_okay=False),
    ] = None,
) -> None:
    def operation() -> None:
        application = build_application(_load_settings_with_debug(config))
        message = application.read_message(message_id)
        for line in _format_full_message_text(message):
            typer.echo(line)

    _run_with_setup_help(operation, config=config)


@app.command("search")
def search_messages(
    query_parts: Annotated[list[str] | None, typer.Argument()] = None,
    config: Annotated[
        Path | None,
        typer.Option("--config", "-c", dir_okay=False),
    ] = None,
    action: Annotated[str, typer.Option("--action", "-a")] = "list",
    saved_query: Annotated[str | None, typer.Option("--saved-query")] = None,
    list_actions: Annotated[bool, typer.Option("--list-actions")] = False,
    list_query_examples: Annotated[bool, typer.Option("--list-query-examples")] = False,
    cheat_sheet: Annotated[bool, typer.Option("--cheat-sheet")] = False,
    output_format: Annotated[str | None, typer.Option("--format", "-f")] = None,
    backup_path: Annotated[
        Path | None,
        typer.Option("--backup-path", dir_okay=True, file_okay=False),
    ] = None,
    limit: Annotated[int | None, typer.Option("--limit", "-l", min=1)] = None,
    from_date: Annotated[str | None, typer.Option("--from-date")] = None,
    to_date: Annotated[str | None, typer.Option("--to-date")] = None,
    starred: Annotated[str | None, typer.Option("--starred")] = None,
) -> None:
    if list_actions:
        _emit_action_list()
        return

    if cheat_sheet:
        typer.echo(SEARCH_CHEAT_SHEET)
        return

    if list_query_examples:
        for example in SEARCH_QUERY_EXAMPLES:
            typer.echo(example)
        return

    if output_format is not None and action != "list":
        _exit_with_error("--format is only supported for the list action")

    _validate_backup_path(action, backup_path)

    def operation() -> None:
        settings = _load_settings_with_debug(config)
        query = _build_search_query(settings, saved_query=saved_query, query_parts=query_parts)

        application = build_application(settings)
        progress_callback = _build_backup_progress_reporter() if action == "backup" else None
        rows = application.search_messages(
            action=action,
            query=query,
            limit=limit,
            from_date=from_date,
            to_date=to_date,
            starred=_parse_starred(starred),
            backup_path=backup_path,
            progress_callback=progress_callback,
        )
        _emit_rows(rows, output_format=output_format, default_text=_format_message_headers_text)

    _run_with_setup_help(operation, config=config)


def _build_search_query(
    settings: Settings,
    *,
    saved_query: str | None,
    query_parts: list[str] | None,
) -> str:
    parts: list[str] = []

    if saved_query is not None:
        try:
            parts.append(settings.search.saved_queries[saved_query])
        except KeyError as exc:
            raise typer.BadParameter(f"Unknown saved query: {saved_query}") from exc

    if query_parts:
        parts.append(" ".join(query_parts))

    if not parts:
        raise typer.BadParameter("at least one search argument is required")

    return " ".join(parts)


@app.command("label")
def label_action(
    label: Annotated[str | None, typer.Argument()] = None,
    config: Annotated[
        Path | None,
        typer.Option("--config", "-c", dir_okay=False),
    ] = None,
    action: Annotated[str, typer.Option("--action", "-a")] = "list",
    list_actions: Annotated[bool, typer.Option("--list-actions")] = False,
    output_format: Annotated[str | None, typer.Option("--format", "-f")] = None,
    backup_path: Annotated[
        Path | None,
        typer.Option("--backup-path", dir_okay=True, file_okay=False),
    ] = None,
    limit: Annotated[int | None, typer.Option("--limit", "-l", min=1)] = None,
    from_date: Annotated[str | None, typer.Option("--from-date")] = None,
    to_date: Annotated[str | None, typer.Option("--to-date")] = None,
    starred: Annotated[str | None, typer.Option("--starred")] = None,
) -> None:
    if list_actions:
        _emit_action_list()
        return

    if label is None:
        raise typer.BadParameter("label is required unless --list-actions is used")

    if output_format is not None and action != "list":
        _exit_with_error("--format is only supported for the list action")

    _validate_backup_path(action, backup_path)

    def operation() -> None:
        application = build_application(_load_settings_with_debug(config))
        progress_callback = _build_backup_progress_reporter() if action == "backup" else None
        try:
            rows = application.run_label_action(
                label=label,
                action=action,
                limit=limit,
                from_date=from_date,
                to_date=to_date,
                starred=_parse_starred(starred),
                backup_path=backup_path,
                progress_callback=progress_callback,
            )
        except ValueError as exc:
            raise typer.BadParameter(str(exc)) from exc
        _emit_rows(rows, output_format=output_format, default_text=_format_message_headers_text)

    _run_with_setup_help(operation, config=config)


def _emit_rows(
    rows: list[str] | list[GmailLabel] | list[GmailMessageHeader],
    *,
    output_format: str | None,
    default_text,
) -> None:
    if output_format is None:
        for line in default_text(rows):
            typer.echo(line)
        return

    normalized = output_format.strip().lower()
    if normalized == "json":
        typer.echo(_render_json(rows))
        return
    if normalized == "csv":
        typer.echo(_render_csv(rows), nl=False)
        return
    raise typer.BadParameter("--format must be json or csv")


def _format_labels_text(rows: list[GmailLabel] | list[str] | list[GmailMessageHeader]) -> list[str]:
    return [label.name for label in rows]


def _format_message_headers_text(
    rows: list[GmailLabel] | list[str] | list[GmailMessageHeader],
) -> list[str]:
    if rows and isinstance(rows[0], str):
        return rows
    return [
        (
            f"message_id={header.message_id} | recipient={header.recipient} | "
            f"sender={header.sender} | "
            f"date={header.date} | subject={header.subject}"
        )
        for header in rows
    ]


def _format_full_message_text(message: GmailMessage) -> list[str]:
    return [
        f"message_id={message.message_id}",
        f"recipient={message.recipient}",
        f"sender={message.sender}",
        f"date={message.date}",
        f"subject={message.subject}",
        "",
        message.body,
    ]


def main() -> None:
    app()
