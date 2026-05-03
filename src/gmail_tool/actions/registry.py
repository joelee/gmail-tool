from __future__ import annotations

from dataclasses import dataclass
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
    ) -> list[str] | list[GmailMessageHeader]: ...


@dataclass
class CountAction:
    name: str = "count"

    def run(
        self,
        gateway: GmailGateway,
        scope: ActionScope,
        filters: MessageFilters,
        *,
        limit: int,
    ) -> list[str]:
        del limit
        if scope.label is None:
            return [str(len(gateway.list_message_ids(None, scope.combined_query(filters))))]
        return [str(gateway.count_messages(scope.label, scope.combined_query(filters)))]


@dataclass
class ListAction:
    name: str = "list"

    def run(
        self,
        gateway: GmailGateway,
        scope: ActionScope,
        filters: MessageFilters,
        *,
        limit: int,
    ) -> list[GmailMessageHeader]:
        if scope.label is None:
            return gateway.search_message_headers(scope.combined_query(filters), limit)
        return gateway.list_message_headers(scope.label, scope.combined_query(filters), limit)


class LabelMutationAction:
    def __init__(self, prefix: str, *, remove: bool) -> None:
        self.name = prefix
        self._remove = remove

    def matches(self, action_name: str) -> bool:
        return action_name.startswith(f"{self.name}:") and len(action_name) > len(self.name) + 1

    def run(
        self,
        action_name: str,
        gateway: GmailGateway,
        scope: ActionScope,
        filters: MessageFilters,
        *,
        limit: int,
    ) -> list[str]:
        del limit
        label_name = action_name.split(":", 1)[1]
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
        for message_id in message_ids:
            gateway.modify_message_labels(
                message_id,
                add_label_ids=[] if self._remove else [label_id],
                remove_label_ids=[label_id] if self._remove else [],
            )
        return [f"{len(message_ids)} messages updated"]


class ActionRegistry:
    def __init__(self, actions: list[LabelAction]) -> None:
        self._actions = {action.name: action for action in actions}
        self._dynamic_actions = [
            LabelMutationAction("add-label", remove=False),
            LabelMutationAction("remove-label", remove=True),
        ]

    def list_names(self) -> list[str]:
        return sorted([*self._actions, "add-label:<label_name>", "remove-label:<label_name>"])

    def run(
        self,
        action_name: str,
        gateway: GmailGateway,
        label: str,
        filters: MessageFilters,
        *,
        limit: int,
    ) -> list[str] | list[GmailMessageHeader]:
        scope = ActionScope(label=label, raw_query=None)
        return self._run(action_name, gateway, scope, filters, limit=limit)

    def run_for_search(
        self,
        action_name: str,
        gateway: GmailGateway,
        *,
        raw_query: str,
        filters: MessageFilters,
        limit: int,
    ) -> list[str] | list[GmailMessageHeader]:
        scope = ActionScope(label=None, raw_query=raw_query)
        return self._run(action_name, gateway, scope, filters, limit=limit)

    def _run(
        self,
        action_name: str,
        gateway: GmailGateway,
        scope: ActionScope,
        filters: MessageFilters,
        *,
        limit: int,
    ) -> list[str] | list[GmailMessageHeader]:
        try:
            action = self._actions[action_name]
            return action.run(gateway, scope, filters, limit=limit)
        except KeyError as exc:
            for dynamic_action in self._dynamic_actions:
                if dynamic_action.matches(action_name):
                    return dynamic_action.run(action_name, gateway, scope, filters, limit=limit)
            raise ValueError(f"Unsupported action: {action_name}") from exc


def build_action_registry() -> ActionRegistry:
    return ActionRegistry(actions=[CountAction(), ListAction()])
