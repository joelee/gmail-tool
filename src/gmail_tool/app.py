from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from gmail_tool.actions import ActionRegistry, build_action_registry
from gmail_tool.auth import build_credentials_provider
from gmail_tool.config import Settings
from gmail_tool.filters import MessageFilters, parse_date
from gmail_tool.gmail import (
    GmailApiGateway,
    GmailGateway,
    GmailLabel,
    GmailMessage,
    GmailMessageHeader,
)


@dataclass
class Application:
    settings: Settings
    gateway: GmailGateway
    action_registry: ActionRegistry

    def list_labels(self) -> list[GmailLabel]:
        return self.gateway.list_labels()

    def auth_check(self) -> dict[str, str | int]:
        labels = self.gateway.list_labels()
        return {
            "auth_mode": self.settings.auth.mode.value,
            "gmail_user_id": self.settings.gmail.user_id,
            "label_count": len(labels),
        }

    def read_message(self, message_id: str) -> GmailMessage:
        return self.gateway.get_message(message_id)

    def search_messages(
        self,
        *,
        action: str,
        query: str,
        limit: int | None,
        from_date: str | None,
        to_date: str | None,
        starred: bool | None,
        backup_path: Path | None = None,
        progress_callback: Callable[[str | None], None] | None = None,
    ) -> list[str] | list[GmailMessageHeader]:
        filters = MessageFilters(
            from_date=parse_date(from_date),
            to_date=parse_date(to_date),
            starred=starred,
        )
        effective_limit = limit or self.settings.app.default_limit
        return self.action_registry.run_for_search(
            action,
            self.gateway,
            raw_query=query,
            filters=filters,
            limit=effective_limit,
            backup_path=backup_path,
            progress_callback=progress_callback,
        )

    def run_label_action(
        self,
        *,
        label: str,
        action: str,
        limit: int | None,
        from_date: str | None,
        to_date: str | None,
        starred: bool | None,
        backup_path: Path | None = None,
        progress_callback: Callable[[str | None], None] | None = None,
    ) -> list[str] | list[GmailMessageHeader]:
        filters = MessageFilters(
            from_date=parse_date(from_date),
            to_date=parse_date(to_date),
            starred=starred,
        )
        effective_limit = limit or self.settings.app.default_limit
        resolved_label = self._resolve_label_id(label)
        return self.action_registry.run(
            action,
            self.gateway,
            resolved_label,
            filters,
            limit=effective_limit,
            backup_path=backup_path,
            progress_callback=progress_callback,
        )

    def _resolve_label_id(self, label: str) -> str:
        labels = self.gateway.list_labels()

        for known_label in labels:
            if known_label.id == label:
                return known_label.id

        for known_label in labels:
            if known_label.name == label:
                return known_label.id

        raise ValueError(f"Unknown label: {label}")


def build_application(settings: Settings) -> Application:
    from googleapiclient.discovery import build

    credentials_provider = build_credentials_provider(settings)
    credentials = credentials_provider.get_credentials()
    service = build("gmail", "v1", credentials=credentials)
    gateway = GmailApiGateway(service=service, user_id=settings.gmail.user_id)
    return Application(
        settings=settings,
        gateway=gateway,
        action_registry=build_action_registry(default_backup_path=settings.backup.path),
    )
