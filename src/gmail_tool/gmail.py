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


class GmailGateway(Protocol):
    def list_labels(self) -> list[GmailLabel]: ...

    def count_messages(self, label: str, query: str | None) -> int: ...

    def list_message_headers(
        self,
        label: str,
        query: str | None,
        limit: int,
    ) -> list[GmailMessageHeader]: ...

    def get_message(self, message_id: str) -> GmailMessage: ...


class GmailApiGateway:
    def __init__(self, service: Any, user_id: str) -> None:
        self._service = service
        self._user_id = user_id

    def list_labels(self) -> list[GmailLabel]:
        response = self._service.users().labels().list(userId=self._user_id).execute()
        return [GmailLabel(id=item["id"], name=item["name"]) for item in response.get("labels", [])]

    def count_messages(self, label: str, query: str | None) -> int:
        total = 0
        page_token: str | None = None
        while True:
            response = (
                self._service.users()
                .messages()
                .list(
                    userId=self._user_id,
                    labelIds=[label],
                    q=query,
                    pageToken=page_token,
                )
                .execute()
            )
            total += len(response.get("messages", []))
            page_token = response.get("nextPageToken")
            if page_token is None:
                return total

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
