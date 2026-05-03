from __future__ import annotations

import csv
import json
from dataclasses import asdict, is_dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Annotated

import typer

from gmail_tool.actions import build_action_registry
from gmail_tool.app import build_application
from gmail_tool.config import Settings, discover_config_path, load_settings
from gmail_tool.gmail import GmailLabel, GmailMessage, GmailMessageHeader

app = typer.Typer(
    no_args_is_help=True,
    context_settings={"help_option_names": ["--help", "-h"]},
)

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
    config_path = discover_config_path(config)
    _debug(f"Using config: {config_path}")
    return load_settings(config)


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
    application = build_application(_load_settings_with_debug(config))
    labels = application.list_labels()
    _emit_rows(labels, output_format=output_format, default_text=_format_labels_text)


@app.command("auth-check")
def auth_check(
    config: Annotated[
        Path | None,
        typer.Option("--config", "-c", dir_okay=False),
    ] = None,
) -> None:
    application = build_application(_load_settings_with_debug(config))
    result = application.auth_check()
    for key, value in result.items():
        typer.echo(f"{key}={value}")


@app.command("read")
def read_message(
    message_id: str,
    config: Annotated[
        Path | None,
        typer.Option("--config", "-c", dir_okay=False),
    ] = None,
) -> None:
    application = build_application(_load_settings_with_debug(config))
    message = application.read_message(message_id)
    for line in _format_full_message_text(message):
        typer.echo(line)


@app.command("search")
def search_messages(
    query_parts: Annotated[list[str] | None, typer.Argument()] = None,
    config: Annotated[
        Path | None,
        typer.Option("--config", "-c", dir_okay=False),
    ] = None,
    action: Annotated[str, typer.Option("--action", "-a")] = "list",
    saved_query: Annotated[str | None, typer.Option("--saved-query")] = None,
    list_query_examples: Annotated[bool, typer.Option("--list-query-examples")] = False,
    cheat_sheet: Annotated[bool, typer.Option("--cheat-sheet")] = False,
    output_format: Annotated[str | None, typer.Option("--format", "-f")] = None,
    limit: Annotated[int | None, typer.Option("--limit", "-l", min=1)] = None,
    from_date: Annotated[str | None, typer.Option("--from-date")] = None,
    to_date: Annotated[str | None, typer.Option("--to-date")] = None,
    starred: Annotated[str | None, typer.Option("--starred")] = None,
) -> None:
    settings = _load_settings_with_debug(config)

    if cheat_sheet:
        typer.echo(SEARCH_CHEAT_SHEET)
        return

    if list_query_examples:
        for example in SEARCH_QUERY_EXAMPLES:
            typer.echo(example)
        return

    if output_format is not None and action != "list":
        raise typer.BadParameter("--format is only supported for the list action")

    query = _build_search_query(settings, saved_query=saved_query, query_parts=query_parts)

    application = build_application(settings)
    rows = application.search_messages(
        action=action,
        query=query,
        limit=limit,
        from_date=from_date,
        to_date=to_date,
        starred=_parse_starred(starred),
    )
    _emit_rows(rows, output_format=output_format, default_text=_format_message_headers_text)


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
    limit: Annotated[int | None, typer.Option("--limit", "-l", min=1)] = None,
    from_date: Annotated[str | None, typer.Option("--from-date")] = None,
    to_date: Annotated[str | None, typer.Option("--to-date")] = None,
    starred: Annotated[str | None, typer.Option("--starred")] = None,
) -> None:
    if list_actions:
        for action_name in build_action_registry().list_names():
            typer.echo(action_name)
        return

    if label is None:
        raise typer.BadParameter("label is required unless --list-actions is used")

    if output_format is not None and action != "list":
        raise typer.BadParameter("--format is only supported for the list action")

    application = build_application(_load_settings_with_debug(config))
    try:
        rows = application.run_label_action(
            label=label,
            action=action,
            limit=limit,
            from_date=from_date,
            to_date=to_date,
            starred=_parse_starred(starred),
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    _emit_rows(rows, output_format=output_format, default_text=_format_message_headers_text)


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
