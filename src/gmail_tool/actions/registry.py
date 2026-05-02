from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from gmail_tool.filters import MessageFilters
from gmail_tool.gmail import GmailGateway, GmailMessageHeader


class LabelAction(Protocol):
    name: str

    def run(
        self,
        gateway: GmailGateway,
        label: str,
        filters: MessageFilters,
        *,
        limit: int,
    ) -> list[str] | list[GmailMessageHeader]: ...


@dataclass
class CountAction:
    name: str = "count"

    def run(
        self,
        gateway: GmailGateway,
        label: str,
        filters: MessageFilters,
        *,
        limit: int,
    ) -> list[str]:
        del limit
        return [str(gateway.count_messages(label, filters.to_gmail_query()))]


@dataclass
class ListAction:
    name: str = "list"

    def run(
        self,
        gateway: GmailGateway,
        label: str,
        filters: MessageFilters,
        *,
        limit: int,
    ) -> list[GmailMessageHeader]:
        return gateway.list_message_headers(label, filters.to_gmail_query(), limit)


class ActionRegistry:
    def __init__(self, actions: list[LabelAction]) -> None:
        self._actions = {action.name: action for action in actions}

    def list_names(self) -> list[str]:
        return sorted(self._actions)

    def run(
        self,
        action_name: str,
        gateway: GmailGateway,
        label: str,
        filters: MessageFilters,
        *,
        limit: int,
    ) -> list[str] | list[GmailMessageHeader]:
        try:
            action = self._actions[action_name]
        except KeyError as exc:
            raise ValueError(f"Unsupported action: {action_name}") from exc
        return action.run(gateway, label, filters, limit=limit)


def build_action_registry() -> ActionRegistry:
    return ActionRegistry(actions=[CountAction(), ListAction()])
