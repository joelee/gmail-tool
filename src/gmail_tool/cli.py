from __future__ import annotations

import csv
import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Annotated

import typer

from gmail_tool.actions import build_action_registry
from gmail_tool.app import build_application
from gmail_tool.config import load_settings
from gmail_tool.gmail import GmailLabel, GmailMessage, GmailMessageHeader

app = typer.Typer(no_args_is_help=True)


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


@app.command("labels")
def labels(
    config: Annotated[
        Path,
        typer.Option("--config", exists=True, dir_okay=False),
    ] = Path("config.toml"),
    output_format: Annotated[str | None, typer.Option("--format")] = None,
) -> None:
    application = build_application(load_settings(config))
    labels = application.list_labels()
    _emit_rows(labels, output_format=output_format, default_text=_format_labels_text)


@app.command("auth-check")
def auth_check(
    config: Annotated[
        Path,
        typer.Option("--config", exists=True, dir_okay=False),
    ] = Path("config.toml"),
) -> None:
    application = build_application(load_settings(config))
    result = application.auth_check()
    for key, value in result.items():
        typer.echo(f"{key}={value}")


@app.command("read")
def read_message(
    message_id: str,
    config: Annotated[
        Path,
        typer.Option("--config", exists=True, dir_okay=False),
    ] = Path("config.toml"),
) -> None:
    application = build_application(load_settings(config))
    message = application.read_message(message_id)
    for line in _format_full_message_text(message):
        typer.echo(line)


@app.command("label")
def label_action(
    label: Annotated[str | None, typer.Argument()] = None,
    action: Annotated[str | None, typer.Argument()] = None,
    config: Annotated[
        Path,
        typer.Option("--config", exists=True, dir_okay=False),
    ] = Path("config.toml"),
    list_actions: Annotated[bool, typer.Option("--list-actions")] = False,
    output_format: Annotated[str | None, typer.Option("--format")] = None,
    limit: Annotated[int | None, typer.Option("--limit", min=1)] = None,
    from_date: Annotated[str | None, typer.Option("--from-date")] = None,
    to_date: Annotated[str | None, typer.Option("--to-date")] = None,
    starred: Annotated[str | None, typer.Option("--starred")] = None,
) -> None:
    if list_actions:
        for action_name in build_action_registry().list_names():
            typer.echo(action_name)
        return

    if label is None or action is None:
        raise typer.BadParameter("label and action are required unless --list-actions is used")

    if output_format is not None and action != "list":
        raise typer.BadParameter("--format is only supported for the list action")

    application = build_application(load_settings(config))
    rows = application.run_label_action(
        label=label,
        action=action,
        limit=limit,
        from_date=from_date,
        to_date=to_date,
        starred=_parse_starred(starred),
    )
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
