from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from dotenv import load_dotenv


class AuthMode(StrEnum):
    OAUTH = "oauth"
    SERVICE_ACCOUNT = "service_account"


@dataclass(frozen=True)
class AppSettings:
    default_limit: int


@dataclass(frozen=True)
class OAuthSettings:
    client_secret_file: str
    token_file: str


@dataclass(frozen=True)
class ServiceAccountSettings:
    service_account_file: str
    subject: str | None


@dataclass(frozen=True)
class AuthSettings:
    mode: AuthMode
    scopes: list[str]
    oauth: OAuthSettings
    service_account: ServiceAccountSettings


@dataclass(frozen=True)
class GmailSettings:
    user_id: str


@dataclass(frozen=True)
class Settings:
    app: AppSettings
    auth: AuthSettings
    gmail: GmailSettings


def load_settings(config_path: Path | None = None) -> Settings:
    resolved_path = config_path or Path("config.toml")
    load_dotenv()
    data = tomllib.loads(resolved_path.read_text(encoding="utf-8"))

    app_data = data["app"]
    auth_data = data["auth"]
    gmail_data = data["gmail"]

    oauth_data = auth_data["oauth"]
    service_account_data = auth_data["service_account"]

    return Settings(
        app=AppSettings(default_limit=int(app_data["default_limit"])),
        auth=AuthSettings(
            mode=AuthMode(auth_data["mode"]),
            scopes=list(auth_data["scopes"]),
            oauth=OAuthSettings(
                client_secret_file=_read_env(oauth_data["client_secret_env"]),
                token_file=_read_env(oauth_data["token_file_env"]),
            ),
            service_account=ServiceAccountSettings(
                service_account_file=_read_env(service_account_data["service_account_file_env"]),
                subject=_read_env(service_account_data["subject_env"], required=False),
            ),
        ),
        gmail=GmailSettings(user_id=_read_env(gmail_data["user_id_env"])),
    )


def _read_env(name: str, *, required: bool = True) -> str | None:
    value = os.getenv(name)
    if value:
        return value
    if required:
        raise ValueError(f"Missing required environment variable: {name}")
    return None
