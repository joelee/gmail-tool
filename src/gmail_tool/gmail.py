from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class GmailLabel:
    id: str
    name: str


@dataclass(frozen=True)
class GmailMessageHeader:
    message_id: str
    recipient: str
    sender: str
    date: str
    subject: str


@dataclass(frozen=True)
class GmailMessage:
    message_id: str
    recipient: str
    sender: str
    date: str
    subject: str
    body: str


@dataclass(frozen=True)
class GmailRawMessage:
    message_id: str
    raw_bytes: bytes
    internal_date: int


class GmailGateway(Protocol):
    def list_labels(self) -> list[GmailLabel]: ...

    def count_messages(self, label: str, query: str | None) -> int: ...

    def list_message_ids(self, label: str | None, query: str | None) -> list[str]: ...

    def list_message_headers(
        self,
        label: str,
        query: str | None,
        limit: int,
    ) -> list[GmailMessageHeader]: ...

    def search_message_headers(self, query: str | None, limit: int) -> list[GmailMessageHeader]: ...

    def ensure_label(self, label_name: str) -> str: ...

    def modify_message_labels(
        self,
        message_id: str,
        *,
        add_label_ids: list[str],
        remove_label_ids: list[str],
    ) -> None: ...

    def get_message(self, message_id: str) -> GmailMessage: ...

    def get_raw_message(self, message_id: str) -> GmailRawMessage: ...


class GmailApiGateway:
    def __init__(self, service: Any, user_id: str) -> None:
        self._service = service
        self._user_id = user_id

    def list_labels(self) -> list[GmailLabel]:
        response = self._service.users().labels().list(userId=self._user_id).execute()
        return [GmailLabel(id=item["id"], name=item["name"]) for item in response.get("labels", [])]

    def count_messages(self, label: str, query: str | None) -> int:
        return len(self.list_message_ids(label, query))

    def list_message_ids(self, label: str | None, query: str | None) -> list[str]:
        message_ids: list[str] = []
        page_token: str | None = None
        while True:
            request = (
                self._service.users()
                .messages()
                .list(
                    userId=self._user_id,
                    q=query,
                    pageToken=page_token,
                )
            )
            if label is not None:
                request = (
                    self._service.users()
                    .messages()
                    .list(
                        userId=self._user_id,
                        labelIds=[label],
                        q=query,
                        pageToken=page_token,
                    )
                )
            response = request.execute()
            message_ids.extend(item["id"] for item in response.get("messages", []))
            page_token = response.get("nextPageToken")
            if page_token is None:
                return message_ids

    def list_message_headers(
        self,
        label: str,
        query: str | None,
        limit: int,
    ) -> list[GmailMessageHeader]:
        response = (
            self._service.users()
            .messages()
            .list(
                userId=self._user_id,
                labelIds=[label],
                q=query,
                maxResults=limit,
            )
            .execute()
        )
        messages = response.get("messages", [])
        return [self._fetch_header(item["id"]) for item in messages]

    def search_message_headers(self, query: str | None, limit: int) -> list[GmailMessageHeader]:
        response = (
            self._service.users()
            .messages()
            .list(
                userId=self._user_id,
                q=query,
                maxResults=limit,
            )
            .execute()
        )
        messages = response.get("messages", [])
        return [self._fetch_header(item["id"]) for item in messages]

    def ensure_label(self, label_name: str) -> str:
        for label in self.list_labels():
            if label.name == label_name:
                return label.id

        response = (
            self._service.users()
            .labels()
            .create(
                userId=self._user_id,
                body={
                    "name": label_name,
                    "labelListVisibility": "labelShow",
                    "messageListVisibility": "show",
                },
            )
            .execute()
        )
        return response["id"]

    def modify_message_labels(
        self,
        message_id: str,
        *,
        add_label_ids: list[str],
        remove_label_ids: list[str],
    ) -> None:
        (
            self._service.users()
            .messages()
            .modify(
                userId=self._user_id,
                id=message_id,
                body={"addLabelIds": add_label_ids, "removeLabelIds": remove_label_ids},
            )
            .execute()
        )

    def get_message(self, message_id: str) -> GmailMessage:
        response = (
            self._service.users()
            .messages()
            .get(
                userId=self._user_id,
                id=message_id,
                format="full",
            )
            .execute()
        )
        header_map = self._header_map(response)
        body = self._extract_body(response.get("payload", {}))
        return GmailMessage(
            message_id=message_id,
            recipient=header_map.get("to", ""),
            sender=header_map.get("from", ""),
            date=header_map.get("date", ""),
            subject=header_map.get("subject", ""),
            body=body,
        )

    def get_raw_message(self, message_id: str) -> GmailRawMessage:
        response = (
            self._service.users()
            .messages()
            .get(
                userId=self._user_id,
                id=message_id,
                format="raw",
            )
            .execute()
        )
        raw_data = response["raw"]
        padding = "=" * (-len(raw_data) % 4)
        return GmailRawMessage(
            message_id=message_id,
            raw_bytes=base64.urlsafe_b64decode(raw_data + padding),
            internal_date=int(response["internalDate"]),
        )

    def _fetch_header(self, message_id: str) -> GmailMessageHeader:
        response = (
            self._service.users()
            .messages()
            .get(
                userId=self._user_id,
                id=message_id,
                format="metadata",
                metadataHeaders=["To", "From", "Date", "Subject"],
            )
            .execute()
        )
        header_map = self._header_map(response)
        return GmailMessageHeader(
            message_id=message_id,
            recipient=header_map.get("to", ""),
            sender=header_map.get("from", ""),
            date=header_map.get("date", ""),
            subject=header_map.get("subject", ""),
        )

    def _header_map(self, response: dict[str, Any]) -> dict[str, str]:
        return {
            header["name"].lower(): header["value"]
            for header in response.get("payload", {}).get("headers", [])
        }

    def _extract_body(self, payload: dict[str, Any]) -> str:
        body = self._extract_preferred_body(payload, mime_type="text/plain")
        if body is not None:
            return body

        body = self._extract_preferred_body(payload, mime_type="text/html")
        if body is not None:
            return body

        data = payload.get("body", {}).get("data")
        if data:
            return self._decode_body_data(data)
        return ""

    def _extract_preferred_body(self, payload: dict[str, Any], *, mime_type: str) -> str | None:
        if payload.get("mimeType") == mime_type:
            data = payload.get("body", {}).get("data")
            if data:
                return self._decode_body_data(data)

        for part in payload.get("parts", []):
            body = self._extract_preferred_body(part, mime_type=mime_type)
            if body is not None:
                return body
        return None

    def _decode_body_data(self, data: str) -> str:
        padding = "=" * (-len(data) % 4)
        return base64.urlsafe_b64decode(data + padding).decode("utf-8", errors="replace")
