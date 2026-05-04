from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from email.header import decode_header, make_header
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Protocol

from gmail_tool.filters import MessageFilters
from gmail_tool.gmail import GmailGateway, GmailMessageHeader


@dataclass(frozen=True)
class ActionScope:
    label: str | None
    raw_query: str | None

    def combined_query(self, filters: MessageFilters) -> str | None:
        filter_query = filters.to_gmail_query()
        parts = [part for part in [self.raw_query, filter_query] if part]
        if not parts:
            return None
        return " ".join(parts)


class LabelAction(Protocol):
    name: str

    def run(
        self,
        gateway: GmailGateway,
        scope: ActionScope,
        filters: MessageFilters,
        *,
        limit: int,
        label_name: str | None = None,
        backup_path: Path | None = None,
        delete_after_backup: bool = False,
        progress_callback: Callable[[str | None], None] | None = None,
    ) -> list[str] | list[GmailMessageHeader]: ...


@dataclass
class CountAction:
    name: str = "count"
    description: str = "Print the number of matching messages."

    def run(
        self,
        gateway: GmailGateway,
        scope: ActionScope,
        filters: MessageFilters,
        *,
        limit: int,
        label_name: str | None = None,
        backup_path: Path | None = None,
        delete_after_backup: bool = False,
        progress_callback: Callable[[str | None], None] | None = None,
    ) -> list[str]:
        del limit
        del label_name
        del backup_path
        del delete_after_backup
        del progress_callback
        if scope.label is None:
            return [str(len(gateway.list_message_ids(None, scope.combined_query(filters))))]
        return [str(gateway.count_messages(scope.label, scope.combined_query(filters)))]


@dataclass
class ListAction:
    name: str = "list"
    description: str = "List matching message headers."

    def run(
        self,
        gateway: GmailGateway,
        scope: ActionScope,
        filters: MessageFilters,
        *,
        limit: int,
        label_name: str | None = None,
        backup_path: Path | None = None,
        delete_after_backup: bool = False,
        progress_callback: Callable[[str | None], None] | None = None,
    ) -> list[GmailMessageHeader]:
        del label_name
        del backup_path
        del delete_after_backup
        del progress_callback
        if scope.label is None:
            return gateway.search_message_headers(scope.combined_query(filters), limit)
        return gateway.list_message_headers(scope.label, scope.combined_query(filters), limit)


@dataclass
class BackupAction:
    default_backup_path: Path | None
    name: str = "backup"
    description: str = "Back up matching messages as .eml files."

    def run(
        self,
        gateway: GmailGateway,
        scope: ActionScope,
        filters: MessageFilters,
        *,
        limit: int,
        label_name: str | None = None,
        backup_path: Path | None = None,
        delete_after_backup: bool = False,
        progress_callback: Callable[[str | None], None] | None = None,
    ) -> list[str]:
        del label_name
        root = _resolve_backup_root(backup_path or self.default_backup_path)
        root.mkdir(parents=True, exist_ok=True)
        existing_ids = _existing_backup_ids(root)
        message_ids = gateway.list_message_ids(scope.label, scope.combined_query(filters))[:limit]
        total = len(message_ids)

        written = 0
        skipped = 0
        trashed = 0
        for index, message_id in enumerate(message_ids, start=1):
            if message_id in existing_ids:
                if progress_callback is not None:
                    progress_callback(
                        f"Skipping {index}/{total}: message_id={message_id} already backed up"
                    )
                skipped += 1
                continue

            raw_message = gateway.get_raw_message(message_id)
            timestamp = _message_timestamp(raw_message)
            if progress_callback is not None:
                progress_callback(
                    _format_batch_progress_message(
                        verb="Backing up",
                        index=index,
                        total=total,
                        raw_message=raw_message,
                    )
                )
            output_path = (
                root
                / timestamp.strftime("%Y")
                / timestamp.strftime("%m-%d")
                / f"{timestamp.strftime('%Y%m%d-%H%M%S')}-{message_id}.eml"
            )
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(raw_message.raw_bytes)
            existing_ids.add(message_id)
            written += 1
            if delete_after_backup:
                gateway.trash_message(message_id)
                trashed += 1

        if progress_callback is not None and total > 0:
            progress_callback(None)

        if delete_after_backup:
            return [
                f"{written} messages written to {root} ({skipped} skipped, {trashed} moved to Bin)"
            ]
        return [f"{written} messages written to {root} ({skipped} skipped)"]


class LabelMutationAction:
    def __init__(self, name: str, *, remove: bool) -> None:
        self.name = name
        self._remove = remove

    @property
    def description(self) -> str:
        if self._remove:
            return "Remove a label from all matching messages."
        return "Add a label to all matching messages."

    def run(
        self,
        gateway: GmailGateway,
        scope: ActionScope,
        filters: MessageFilters,
        *,
        limit: int,
        label_name: str | None = None,
        backup_path: Path | None = None,
        delete_after_backup: bool = False,
        progress_callback: Callable[[str | None], None] | None = None,
    ) -> list[str]:
        del limit
        del backup_path
        del delete_after_backup
        if label_name is None:
            raise ValueError(f"Action {self.name} requires --name")
        label_id = None
        if self._remove:
            for label in gateway.list_labels():
                if label.name == label_name:
                    label_id = label.id
                    break
            if label_id is None:
                return ["0 messages updated"]
        else:
            label_id = gateway.ensure_label(label_name)
        message_ids = gateway.list_message_ids(scope.label, scope.combined_query(filters))
        total = len(message_ids)
        for index, message_id in enumerate(message_ids, start=1):
            if progress_callback is not None:
                raw_message = gateway.get_raw_message(message_id)
                progress_callback(
                    _format_batch_progress_message(
                        verb=f"Applying {self.name}",
                        index=index,
                        total=total,
                        raw_message=raw_message,
                    )
                )
            gateway.modify_message_labels(
                message_id,
                add_label_ids=[] if self._remove else [label_id],
                remove_label_ids=[label_id] if self._remove else [],
            )
        if progress_callback is not None and total > 0:
            progress_callback(None)
        return [f"{len(message_ids)} messages updated"]


class ActionRegistry:
    def __init__(
        self,
        actions: list[LabelAction],
        *,
        default_backup_path: Path | None = None,
    ) -> None:
        self._actions = {action.name: action for action in actions}
        self._backup_action = BackupAction(default_backup_path=default_backup_path)
        self._actions["backup"] = self._backup_action
        self._label_mutation_actions = {
            action.name: action
            for action in [
                LabelMutationAction("label-add", remove=False),
                LabelMutationAction("label-remove", remove=True),
            ]
        }

    def list_actions(self) -> list[tuple[str, str]]:
        actions = [(action.name, action.description) for action in self._actions.values()]
        actions.extend(
            (action.name, action.description) for action in self._label_mutation_actions.values()
        )
        return sorted(actions)

    def help_for_action(self, action_name: str) -> str:
        if action_name in self._actions:
            return self._format_action_help(
                action_name=action_name,
                description=self._actions[action_name].description,
                sub_options=self._sub_options_for_action(action_name),
            )

        if action_name in self._label_mutation_actions:
            action = self._label_mutation_actions[action_name]
            return self._format_action_help(
                action_name=action.name,
                description=action.description,
                sub_options=self._sub_options_for_action(action.name),
            )

        raise ValueError(f"Unsupported action: {action_name}")

    def run(
        self,
        action_name: str,
        gateway: GmailGateway,
        label: str,
        filters: MessageFilters,
        *,
        limit: int,
        label_name: str | None = None,
        backup_path: Path | None = None,
        delete_after_backup: bool = False,
        progress_callback: Callable[[str | None], None] | None = None,
    ) -> list[str] | list[GmailMessageHeader]:
        scope = ActionScope(label=label, raw_query=None)
        return self._run(
            action_name,
            gateway,
            scope,
            filters,
            limit=limit,
            label_name=label_name,
            backup_path=backup_path,
            delete_after_backup=delete_after_backup,
            progress_callback=progress_callback,
        )

    def run_for_search(
        self,
        action_name: str,
        gateway: GmailGateway,
        *,
        raw_query: str,
        filters: MessageFilters,
        limit: int,
        label_name: str | None = None,
        backup_path: Path | None = None,
        delete_after_backup: bool = False,
        progress_callback: Callable[[str | None], None] | None = None,
    ) -> list[str] | list[GmailMessageHeader]:
        scope = ActionScope(label=None, raw_query=raw_query)
        return self._run(
            action_name,
            gateway,
            scope,
            filters,
            limit=limit,
            label_name=label_name,
            backup_path=backup_path,
            delete_after_backup=delete_after_backup,
            progress_callback=progress_callback,
        )

    def count_backup_deletions(
        self,
        gateway: GmailGateway,
        *,
        label: str | None,
        raw_query: str | None,
        filters: MessageFilters,
        limit: int,
        backup_path: Path | None = None,
    ) -> int:
        root = _resolve_backup_root(backup_path or self._backup_action.default_backup_path)
        existing_ids = _existing_backup_ids(root) if root.exists() else set()
        scope = ActionScope(label=label, raw_query=raw_query)
        message_ids = gateway.list_message_ids(scope.label, scope.combined_query(filters))[:limit]
        return sum(1 for message_id in message_ids if message_id not in existing_ids)

    def _run(
        self,
        action_name: str,
        gateway: GmailGateway,
        scope: ActionScope,
        filters: MessageFilters,
        *,
        limit: int,
        label_name: str | None = None,
        backup_path: Path | None = None,
        delete_after_backup: bool = False,
        progress_callback: Callable[[str | None], None] | None = None,
    ) -> list[str] | list[GmailMessageHeader]:
        try:
            action = self._actions[action_name]
            return action.run(
                gateway,
                scope,
                filters,
                limit=limit,
                label_name=label_name,
                backup_path=backup_path,
                delete_after_backup=delete_after_backup,
                progress_callback=progress_callback,
            )
        except KeyError as exc:
            dynamic_action = self._label_mutation_actions.get(action_name)
            if dynamic_action is not None:
                return dynamic_action.run(
                    gateway,
                    scope,
                    filters,
                    limit=limit,
                    label_name=label_name,
                    backup_path=backup_path,
                    delete_after_backup=delete_after_backup,
                    progress_callback=progress_callback,
                )
            raise ValueError(f"Unsupported action: {action_name}") from exc

    def _sub_options_for_action(self, action_name: str) -> list[str]:
        if action_name == "backup":
            return [
                "--backup-path <DIR>  Write backup .eml files under this directory.",
                "--delete             Move successfully written messages to Bin after backup.",
                "--force              Skip the delete confirmation prompt when used with --delete.",
            ]
        if action_name in self._label_mutation_actions:
            return ["--name <LABEL_NAME>  Label name to add or remove."]
        return []

    def _format_action_help(
        self,
        *,
        action_name: str,
        description: str,
        sub_options: list[str],
    ) -> str:
        lines = [
            f"Action: {action_name}",
            f"Description: {description}",
            "",
            "Sub-options:",
        ]
        if sub_options:
            lines.extend(sub_options)
        else:
            lines.append("No action-specific sub-options.")
        return "\n".join(lines)


def build_action_registry(*, default_backup_path: Path | None = None) -> ActionRegistry:
    return ActionRegistry(
        actions=[CountAction(), ListAction()],
        default_backup_path=default_backup_path,
    )


def _existing_backup_ids(root: Path) -> set[str]:
    message_ids: set[str] = set()
    for eml_file in root.glob("**/*.eml"):
        stem = eml_file.stem
        parts = stem.split("-", 2)
        if len(parts) == 3:
            message_ids.add(parts[2])
    return message_ids


def _format_batch_progress_message(
    *,
    verb: str,
    index: int,
    total: int,
    raw_message,
) -> str:
    timestamp = _message_timestamp(raw_message)
    sender_email = _message_sender_email(raw_message)
    subject = _message_subject(raw_message)
    return (
        f"{verb} {index}/{total}: {timestamp.strftime('%Y-%m-%d %H:%M:%S')} | "
        f"{raw_message.message_id} | {sender_email} | {subject}"
    )


def _resolve_backup_root(target_root: Path | None) -> Path:
    if target_root is None:
        raise ValueError("backup path is required via config or --backup-path")
    return target_root.resolve()


def _message_timestamp(raw_message) -> datetime:
    header_block = raw_message.raw_bytes.split(b"\r\n\r\n", 1)[0].decode("utf-8", errors="replace")
    for line in header_block.split("\r\n"):
        if line.lower().startswith("date:"):
            try:
                timestamp = parsedate_to_datetime(line.split(":", 1)[1].strip())
                if timestamp.tzinfo is None:
                    return timestamp.replace(tzinfo=UTC)
                return timestamp.astimezone(UTC)
            except (TypeError, ValueError, IndexError):
                break
    return datetime.fromtimestamp(raw_message.internal_date / 1000, tz=UTC)


def _message_subject(raw_message) -> str:
    header_block = raw_message.raw_bytes.split(b"\r\n\r\n", 1)[0].decode("utf-8", errors="replace")
    for line in header_block.split("\r\n"):
        if line.lower().startswith("subject:"):
            raw_subject = line.split(":", 1)[1].strip()
            try:
                return str(make_header(decode_header(raw_subject)))
            except (TypeError, ValueError):
                return raw_subject
    return ""


def _message_sender_email(raw_message) -> str:
    header_block = raw_message.raw_bytes.split(b"\r\n\r\n", 1)[0].decode("utf-8", errors="replace")
    for line in header_block.split("\r\n"):
        if line.lower().startswith("from:"):
            sender = line.split(":", 1)[1].strip()
            if "<" in sender and ">" in sender:
                return sender.split("<", 1)[1].split(">", 1)[0].strip()
            return sender
    return ""
