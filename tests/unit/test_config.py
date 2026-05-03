from pathlib import Path

import pytest

from gmail_tool.config import AuthMode, discover_config_path, load_settings


def test_load_settings_reads_config_and_env(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        """
[app]
default_limit = 9

[search.saved_queries]
recent_attachments = "has:attachment newer_than:30d"
ring = "from:no-reply@rs.ring.com newer_than:7d"

[auth]
mode = "service_account"
scopes = ["scope-a"]

[auth.oauth]
client_secret_env = "OAUTH_SECRET"
token_file_env = "OAUTH_TOKEN"

[auth.service_account]
service_account_file_env = "SERVICE_ACCOUNT_FILE"
subject_env = "SERVICE_ACCOUNT_SUBJECT"

[gmail]
user_id_env = "GMAIL_USER"
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setenv("OAUTH_SECRET", "/tmp/oauth-secret.json")
    monkeypatch.setenv("OAUTH_TOKEN", "/tmp/oauth-token.json")
    monkeypatch.setenv("SERVICE_ACCOUNT_FILE", "/tmp/service-account.json")
    monkeypatch.setenv("SERVICE_ACCOUNT_SUBJECT", "user@example.com")
    monkeypatch.setenv("GMAIL_USER", "me")

    settings = load_settings(config_path)

    assert settings.app.default_limit == 9
    assert settings.auth.mode is AuthMode.SERVICE_ACCOUNT
    assert settings.auth.oauth.client_secret_file == "/tmp/oauth-secret.json"
    assert settings.auth.service_account.subject == "user@example.com"
    assert settings.gmail.user_id == "me"
    assert settings.search.saved_queries == {
        "recent_attachments": "has:attachment newer_than:30d",
        "ring": "from:no-reply@rs.ring.com newer_than:7d",
    }


def test_discover_config_path_prefers_explicit_argument(monkeypatch, tmp_path: Path) -> None:
    explicit = tmp_path / "explicit.toml"
    explicit.write_text("[app]\ndefault_limit = 1\n", encoding="utf-8")

    monkeypatch.setenv("GMAIL_TOOL_CONFIG", str(tmp_path / "env.toml"))

    discovered = discover_config_path(explicit)

    assert discovered == explicit


def test_discover_config_path_uses_environment_variable(monkeypatch, tmp_path: Path) -> None:
    env_path = tmp_path / "env.toml"
    env_path.write_text("[app]\ndefault_limit = 1\n", encoding="utf-8")
    monkeypatch.setenv("GMAIL_TOOL_CONFIG", str(env_path))
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))

    discovered = discover_config_path()

    assert discovered == env_path


def test_discover_config_path_uses_xdg_config_home(monkeypatch, tmp_path: Path) -> None:
    xdg_root = tmp_path / "xdg"
    xdg_path = xdg_root / "gmail-tool" / "config.toml"
    xdg_path.parent.mkdir(parents=True)
    xdg_path.write_text("[app]\ndefault_limit = 1\n", encoding="utf-8")

    monkeypatch.delenv("GMAIL_TOOL_CONFIG", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg_root))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))

    discovered = discover_config_path()

    assert discovered == xdg_path


def test_discover_config_path_uses_home_config(monkeypatch, tmp_path: Path) -> None:
    home_root = tmp_path / "home"
    home_path = home_root / ".config" / "gmail-tool" / "config.toml"
    home_path.parent.mkdir(parents=True)
    home_path.write_text("[app]\ndefault_limit = 1\n", encoding="utf-8")

    monkeypatch.delenv("GMAIL_TOOL_CONFIG", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setenv("HOME", str(home_root))

    discovered = discover_config_path()

    assert discovered == home_path


def test_discover_config_path_uses_etc_before_project_dir(monkeypatch, tmp_path: Path) -> None:
    etc_path = tmp_path / "etc" / "gmail-tool.toml"
    etc_path.parent.mkdir(parents=True)
    etc_path.write_text("[app]\ndefault_limit = 1\n", encoding="utf-8")

    project_path = tmp_path / "project" / "config.toml"
    project_path.parent.mkdir(parents=True)
    project_path.write_text("[app]\ndefault_limit = 2\n", encoding="utf-8")

    monkeypatch.delenv("GMAIL_TOOL_CONFIG", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))

    discovered = discover_config_path(
        None,
        project_dir=project_path.parent,
        etc_path=etc_path,
    )

    assert discovered == etc_path


def test_discover_config_path_falls_back_to_project_dir(monkeypatch, tmp_path: Path) -> None:
    project_path = tmp_path / "project" / "config.toml"
    project_path.parent.mkdir(parents=True)
    project_path.write_text("[app]\ndefault_limit = 2\n", encoding="utf-8")

    monkeypatch.delenv("GMAIL_TOOL_CONFIG", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))

    discovered = discover_config_path(
        None,
        project_dir=project_path.parent,
        etc_path=tmp_path / "missing-etc.toml",
    )

    assert discovered == project_path


def test_discover_config_path_raises_when_no_file_exists(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("GMAIL_TOOL_CONFIG", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))

    with pytest.raises(FileNotFoundError):
        discover_config_path(
            None,
            project_dir=tmp_path / "project",
            etc_path=tmp_path / "missing-etc.toml",
        )
