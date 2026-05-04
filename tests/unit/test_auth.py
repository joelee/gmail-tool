import os
import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from gmail_tool.auth import (
    AuthSetupError,
    OAuthCredentialsProvider,
    ServiceAccountCredentialsProvider,
    build_credentials_provider,
)
from gmail_tool.config import (
    AppSettings,
    AuthMode,
    AuthSettings,
    BackupSettings,
    GmailSettings,
    OAuthSettings,
    SearchSettings,
    ServiceAccountSettings,
    Settings,
)


def test_build_credentials_provider_for_oauth() -> None:
    settings = Settings(
        app=AppSettings(default_limit=100),
        search=SearchSettings(saved_queries={}),
        auth=AuthSettings(
            mode=AuthMode.OAUTH,
            scopes=["scope-a"],
            oauth=OAuthSettings(client_secret_file="secret.json", token_file="token.json"),
            service_account=ServiceAccountSettings(
                service_account_file="service.json",
                subject="user@example.com",
            ),
        ),
        backup=BackupSettings(path=None),
        gmail=GmailSettings(user_id="me"),
    )

    provider = build_credentials_provider(settings)

    assert isinstance(provider, OAuthCredentialsProvider)


def test_build_credentials_provider_for_service_account() -> None:
    settings = Settings(
        app=AppSettings(default_limit=100),
        search=SearchSettings(saved_queries={}),
        auth=AuthSettings(
            mode=AuthMode.SERVICE_ACCOUNT,
            scopes=["scope-a"],
            oauth=OAuthSettings(client_secret_file="secret.json", token_file="token.json"),
            service_account=ServiceAccountSettings(
                service_account_file="service.json",
                subject="user@example.com",
            ),
        ),
        backup=BackupSettings(path=None),
        gmail=GmailSettings(user_id="me"),
    )

    provider = build_credentials_provider(settings)

    assert isinstance(provider, ServiceAccountCredentialsProvider)


def test_oauth_provider_requires_existing_client_secret_file(tmp_path: Path) -> None:
    provider = OAuthCredentialsProvider(
        client_secret_file=str(tmp_path / "missing.json"),
        token_file=str(tmp_path / "token.json"),
        scopes=["scope-a"],
    )

    with pytest.raises(AuthSetupError, match="OAuth client secret file not found"):
        provider._ensure_private_client_secret_file()


def test_oauth_provider_restricts_client_secret_permissions(tmp_path: Path) -> None:
    client_secret_file = tmp_path / "client_secret.json"
    client_secret_file.write_text("{}", encoding="utf-8")
    os.chmod(client_secret_file, 0o644)

    provider = OAuthCredentialsProvider(
        client_secret_file=str(client_secret_file),
        token_file=str(tmp_path / "token.json"),
        scopes=["scope-a"],
    )

    provider._ensure_private_client_secret_file()

    assert stat.S_IMODE(client_secret_file.stat().st_mode) == 0o600


def test_oauth_provider_returns_valid_existing_token(monkeypatch, tmp_path: Path) -> None:
    token_file = tmp_path / "token.json"
    token_file.write_text("{}", encoding="utf-8")
    provider = OAuthCredentialsProvider(
        client_secret_file=str(tmp_path / "client_secret.json"),
        token_file=str(token_file),
        scopes=["scope-a"],
    )

    credentials = SimpleNamespace(valid=True)
    monkeypatch.setattr(
        "gmail_tool.auth.Credentials.from_authorized_user_file",
        lambda path, scopes: credentials,
    )

    assert provider.get_credentials() is credentials


def test_oauth_provider_refreshes_expired_token(monkeypatch, tmp_path: Path) -> None:
    token_file = tmp_path / "token.json"
    token_file.write_text("{}", encoding="utf-8")
    provider = OAuthCredentialsProvider(
        client_secret_file=str(tmp_path / "client_secret.json"),
        token_file=str(token_file),
        scopes=["scope-a"],
    )

    refreshed = {"called": False}

    class FakeCredentials:
        valid = False
        expired = True
        refresh_token = "refresh-token"

        def refresh(self, request):
            del request
            refreshed["called"] = True

        def to_json(self):
            return '{"token": "updated"}'

    monkeypatch.setattr(
        "gmail_tool.auth.Credentials.from_authorized_user_file",
        lambda path, scopes: FakeCredentials(),
    )

    credentials = provider.get_credentials()

    assert isinstance(credentials, FakeCredentials)
    assert refreshed["called"] is True
    assert token_file.read_text(encoding="utf-8") == '{"token": "updated"}'
    assert stat.S_IMODE(token_file.stat().st_mode) == 0o600


def test_oauth_provider_runs_local_server_and_writes_token(monkeypatch, tmp_path: Path) -> None:
    client_secret_file = tmp_path / "client_secret.json"
    client_secret_file.write_text("{}", encoding="utf-8")
    provider = OAuthCredentialsProvider(
        client_secret_file=str(client_secret_file),
        token_file=str(tmp_path / "state" / "oauth-token.json"),
        scopes=["scope-a"],
    )

    class FakeCredentials:
        valid = True
        expired = False
        refresh_token = None

        def to_json(self):
            return '{"token": "created"}'

    credentials = FakeCredentials()

    class FakeFlow:
        def run_local_server(self, port=0):
            assert port == 0
            return credentials

    monkeypatch.setattr(
        "gmail_tool.auth.InstalledAppFlow.from_client_secrets_file",
        lambda path, scopes: FakeFlow(),
    )

    assert provider.get_credentials() is credentials
    assert provider._token_file.read_text(encoding="utf-8") == '{"token": "created"}'
    assert stat.S_IMODE(provider._token_file.parent.stat().st_mode) & 0o077 == 0


def test_oauth_provider_runs_console_when_browser_disabled(monkeypatch, tmp_path: Path) -> None:
    client_secret_file = tmp_path / "client_secret.json"
    client_secret_file.write_text("{}", encoding="utf-8")
    provider = OAuthCredentialsProvider(
        client_secret_file=str(client_secret_file),
        token_file=str(tmp_path / "token.json"),
        scopes=["scope-a"],
    )

    class FakeCredentials:
        valid = True
        expired = False
        refresh_token = None

        def to_json(self):
            return '{"token": "console"}'

    credentials = FakeCredentials()

    class FakeFlow:
        def run_console(self):
            return credentials

    monkeypatch.setattr(
        "gmail_tool.auth.InstalledAppFlow.from_client_secrets_file",
        lambda path, scopes: FakeFlow(),
    )

    assert provider.get_credentials(open_browser=False) is credentials
