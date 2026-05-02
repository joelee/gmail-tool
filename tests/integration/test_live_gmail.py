from __future__ import annotations

from pathlib import Path

import pytest

from gmail_tool.actions import build_action_registry
from gmail_tool.app import Application, build_application
from gmail_tool.config import load_settings
from gmail_tool.gmail import GmailApiGateway


@pytest.mark.live_gmail
def test_live_gmail_application_builds_real_gateway(live_gmail_guard) -> None:
    del live_gmail_guard
    settings = load_settings(Path("config.toml"))

    application = build_application(settings)

    assert isinstance(application, Application)
    assert isinstance(application.gateway, GmailApiGateway)


@pytest.mark.live_gmail
def test_live_gmail_can_list_labels(live_gmail_guard) -> None:
    del live_gmail_guard
    settings = load_settings(Path("config.toml"))
    application = build_application(settings)

    labels = application.list_labels()

    assert labels
    assert any(label.name == "INBOX" for label in labels)


@pytest.mark.live_gmail
def test_live_gmail_can_count_inbox_messages(live_gmail_guard) -> None:
    del live_gmail_guard
    settings = load_settings(Path("config.toml"))
    application = Application(
        settings=settings,
        gateway=build_application(settings).gateway,
        action_registry=build_action_registry(),
    )

    lines = application.run_label_action(
        label="INBOX",
        action="count",
        limit=1,
        from_date=None,
        to_date=None,
        starred=None,
    )

    assert len(lines) == 1
    assert int(lines[0]) >= 0
