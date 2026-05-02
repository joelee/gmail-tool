from __future__ import annotations

import os
from pathlib import Path

import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "live_gmail: marks tests that access the real Gmail API and require local credentials",
    )


def is_live_gmail_enabled() -> bool:
    return os.getenv("ENABLE_LIVE_GMAIL_TESTS", "").strip().lower() == "true"


def should_allow_oauth_browser() -> bool:
    return os.getenv("ALLOW_GMAIL_OAUTH_BROWSER", "").strip().lower() == "true"


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def token_file_exists() -> bool:
    from gmail_tool.config import load_settings

    settings = load_settings(project_root() / "config.toml")
    return Path(settings.auth.oauth.token_file).exists()


@pytest.fixture(scope="session")
def live_gmail_guard() -> None:
    if not is_live_gmail_enabled():
        pytest.skip("Set ENABLE_LIVE_GMAIL_TESTS=true to run live Gmail integration tests")

    if token_file_exists() or should_allow_oauth_browser():
        return

    pytest.skip(
        "Live Gmail tests require an existing OAuth token file or ALLOW_GMAIL_OAUTH_BROWSER=true"
    )
