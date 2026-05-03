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
class SearchSettings:
    saved_queries: dict[str, str]


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
class BackupSettings:
    path: Path | None


@dataclass(frozen=True)
class Settings:
    app: AppSettings
    search: SearchSettings
    auth: AuthSettings
    backup: BackupSettings
    gmail: GmailSettings


def load_settings(config_path: Path | None = None) -> Settings:
    resolved_path = discover_config_path(config_path)
    load_dotenv()
    data = tomllib.loads(resolved_path.read_text(encoding="utf-8"))

    app_data = data["app"]
    search_data = data.get("search", {})
    auth_data = data["auth"]
    backup_data = data.get("backup", {})
    gmail_data = data["gmail"]

    oauth_data = auth_data["oauth"]
    service_account_data = auth_data["service_account"]

    return Settings(
        app=AppSettings(default_limit=int(app_data["default_limit"])),
        search=SearchSettings(saved_queries=dict(search_data.get("saved_queries", {}))),
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
        backup=BackupSettings(path=_resolve_backup_path(backup_data.get("path"), resolved_path)),
        gmail=GmailSettings(user_id=_read_env(gmail_data["user_id_env"])),
    )


def discover_config_path(
    config_path: Path | None = None,
    *,
    project_dir: Path | None = None,
    etc_path: Path | None = None,
) -> Path:
    if config_path is not None:
        return Path(config_path)

    candidate_paths: list[Path] = []

    env_config = os.getenv("GMAIL_TOOL_CONFIG")
    if env_config:
        candidate_paths.append(Path(env_config))

    xdg_config_home = os.getenv("XDG_CONFIG_HOME")
    if xdg_config_home:
        candidate_paths.append(Path(xdg_config_home) / "gmail-tool" / "config.toml")

    home = os.getenv("HOME")
    if home:
        candidate_paths.append(Path(home) / ".config" / "gmail-tool" / "config.toml")

    candidate_paths.append(etc_path or Path("/etc/gmail-tool.toml"))
    candidate_paths.append((project_dir or Path.cwd()) / "config.toml")

    for candidate in candidate_paths:
        if candidate.is_file():
            return candidate

    raise FileNotFoundError("No config.toml found in configured search locations")


def _read_env(name: str, *, required: bool = True) -> str | None:
    value = os.getenv(name)
    if value:
        return value
    if required:
        raise ValueError(f"Missing required environment variable: {name}")
    return None


def _resolve_backup_path(path_value: str | None, config_path: Path) -> Path | None:
    if path_value is None:
        return None

    path = Path(path_value)
    if path.is_absolute():
        return path
    return (config_path.parent / path).resolve()
