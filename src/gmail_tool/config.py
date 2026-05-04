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
    load_dotenv()
    resolved_path = discover_config_path(config_path, required=False)
    data = _default_config_data()
    if resolved_path is not None:
        _merge_config_data(data, tomllib.loads(resolved_path.read_text(encoding="utf-8")))

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
                client_secret_file=_read_path_env(
                    oauth_data["client_secret_env"],
                    default=_default_oauth_client_secret_path(),
                ),
                token_file=_read_path_env(
                    oauth_data["token_file_env"],
                    default=_default_oauth_token_path(),
                ),
            ),
            service_account=ServiceAccountSettings(
                service_account_file=_read_env(
                    service_account_data["service_account_file_env"], required=False
                ),
                subject=_read_env(service_account_data["subject_env"], required=False),
            ),
        ),
        backup=BackupSettings(path=_resolve_backup_path(backup_data.get("path"), resolved_path)),
        gmail=GmailSettings(user_id=_read_env(gmail_data["user_id_env"], default="me") or "me"),
    )


def discover_config_path(
    config_path: Path | None = None,
    *,
    project_dir: Path | None = None,
    etc_path: Path | None = None,
    required: bool = True,
) -> Path | None:
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

    if not required:
        return None

    raise FileNotFoundError("No config.toml found in configured search locations")


def _read_env(name: str, *, required: bool = True, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value:
        return value
    if default is not None:
        return default
    if required:
        raise ValueError(f"Missing required environment variable: {name}")
    return None


def _read_path_env(name: str, *, default: Path) -> str:
    value = os.getenv(name)
    if value:
        return value
    return str(default)


def _resolve_backup_path(path_value: str | None, config_path: Path | None) -> Path | None:
    if path_value is None:
        return None

    path = Path(path_value)
    if path.is_absolute():
        return path
    if config_path is None:
        return path.resolve()
    return (config_path.parent / path).resolve()


def _default_config_data() -> dict[str, object]:
    return {
        "app": {"default_limit": 100},
        "search": {"saved_queries": {}},
        "auth": {
            "mode": "oauth",
            "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
            "oauth": {
                "client_secret_env": "GOOGLE_OAUTH_CLIENT_SECRET_FILE",
                "token_file_env": "GOOGLE_OAUTH_TOKEN_FILE",
            },
            "service_account": {
                "service_account_file_env": "GOOGLE_SERVICE_ACCOUNT_FILE",
                "subject_env": "GOOGLE_SERVICE_ACCOUNT_SUBJECT",
            },
        },
        "gmail": {"user_id_env": "GMAIL_USER_ID"},
    }


def _merge_config_data(base: dict[str, object], override: dict[str, object]) -> None:
    for key, value in override.items():
        current = base.get(key)
        if isinstance(current, dict) and isinstance(value, dict):
            _merge_config_data(current, value)
            continue
        base[key] = value


def _default_oauth_client_secret_path() -> Path:
    return xdg_config_home() / "gmail-tool" / "client_secret.json"


def _default_oauth_token_path() -> Path:
    return xdg_state_home() / "gmail-tool" / "oauth-token.json"


def xdg_config_home() -> Path:
    configured = os.getenv("XDG_CONFIG_HOME")
    if configured:
        return Path(configured)
    return home_dir() / ".config"


def xdg_state_home() -> Path:
    configured = os.getenv("XDG_STATE_HOME")
    if configured:
        return Path(configured)
    return home_dir() / ".local" / "state"


def home_dir() -> Path:
    home = os.getenv("HOME")
    if home:
        return Path(home)
    return Path.home()
