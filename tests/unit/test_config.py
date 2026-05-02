from pathlib import Path

from gmail_tool.config import AuthMode, load_settings


def test_load_settings_reads_config_and_env(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        """
[app]
default_limit = 9

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
