from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow

from gmail_tool.config import AuthMode, Settings


class CredentialsProvider(Protocol):
    def get_credentials(self) -> Any: ...


class OAuthCredentialsProvider:
    def __init__(self, client_secret_file: str, token_file: str, scopes: list[str]) -> None:
        self._client_secret_file = client_secret_file
        self._token_file = Path(token_file)
        self._scopes = scopes

    def get_credentials(self) -> Credentials:
        credentials: Credentials | None = None
        if self._token_file.exists():
            credentials = Credentials.from_authorized_user_file(str(self._token_file), self._scopes)

        if credentials and credentials.valid:
            return credentials

        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(self._client_secret_file, self._scopes)
            credentials = flow.run_local_server(port=0)

        self._token_file.parent.mkdir(parents=True, exist_ok=True)
        self._token_file.write_text(credentials.to_json(), encoding="utf-8")
        return credentials


class ServiceAccountCredentialsProvider:
    def __init__(self, service_account_file: str, scopes: list[str], subject: str | None) -> None:
        self._service_account_file = service_account_file
        self._scopes = scopes
        self._subject = subject

    def get_credentials(self) -> ServiceAccountCredentials:
        credentials = ServiceAccountCredentials.from_service_account_file(
            self._service_account_file,
            scopes=self._scopes,
        )
        if self._subject:
            credentials = credentials.with_subject(self._subject)
        return credentials


def build_credentials_provider(settings: Settings) -> CredentialsProvider:
    if settings.auth.mode is AuthMode.OAUTH:
        return OAuthCredentialsProvider(
            client_secret_file=settings.auth.oauth.client_secret_file,
            token_file=settings.auth.oauth.token_file,
            scopes=settings.auth.scopes,
        )

    return ServiceAccountCredentialsProvider(
        service_account_file=settings.auth.service_account.service_account_file,
        scopes=settings.auth.scopes,
        subject=settings.auth.service_account.subject,
    )
