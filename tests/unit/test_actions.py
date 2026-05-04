from pathlib import Path

from gmail_tool.actions import build_action_registry
from gmail_tool.filters import MessageFilters
from gmail_tool.gmail import GmailLabel, GmailMessageHeader, GmailRawMessage


class FakeGateway:
    def __init__(self) -> None:
        self.count_calls: list[tuple[str, str | None]] = []
        self.list_calls: list[tuple[str, str | None, int]] = []
        self.search_list_calls: list[tuple[str | None, int]] = []
        self.ensure_label_calls: list[str] = []
        self.modify_calls: list[tuple[str, tuple[str, ...], tuple[str, ...]]] = []
        self.trash_calls: list[str] = []
        self.raw_message_calls: list[str] = []
        self.raw_messages: dict[str, GmailRawMessage] = {}

    def count_messages(self, label: str, query: str | None) -> int:
        self.count_calls.append((label, query))
        return 3

    def list_message_headers(
        self,
        label: str,
        query: str | None,
        limit: int,
    ) -> list[GmailMessageHeader]:
        self.list_calls.append((label, query, limit))
        return [
            GmailMessageHeader(
                message_id="abc123",
                recipient="to@example.com",
                sender="from@example.com",
                date="Mon, 01 Jan 2024 10:00:00 +0000",
                subject="Hello",
            )
        ]

    def search_message_headers(self, query: str | None, limit: int) -> list[GmailMessageHeader]:
        self.search_list_calls.append((query, limit))
        return [
            GmailMessageHeader(
                message_id="search-1",
                recipient="to@example.com",
                sender="from@example.com",
                date="Mon, 01 Jan 2024 10:00:00 +0000",
                subject="Hello",
            )
        ]

    def list_message_ids(self, label: str | None, query: str | None) -> list[str]:
        if label is None:
            return ["search-1", "search-2"]
        return ["label-1", "label-2"]

    def ensure_label(self, label_name: str) -> str:
        self.ensure_label_calls.append(label_name)
        return f"id:{label_name}"

    def modify_message_labels(
        self,
        message_id: str,
        *,
        add_label_ids: list[str],
        remove_label_ids: list[str],
    ) -> None:
        self.modify_calls.append((message_id, tuple(add_label_ids), tuple(remove_label_ids)))

    def list_labels(self) -> list[GmailLabel]:
        return [GmailLabel(id="LBL_EXISTING", name="Existing")]

    def get_raw_message(self, message_id: str) -> GmailRawMessage:
        self.raw_message_calls.append(message_id)
        return self.raw_messages[message_id]

    def trash_message(self, message_id: str) -> None:
        self.trash_calls.append(message_id)


def build_raw_message(
    message_id: str,
    *,
    date_header: str | None,
    internal_date: int,
) -> GmailRawMessage:
    header_lines = [
        "From: Sender Example <from@example.com>",
        "To: to@example.com",
        "Subject: Subject",
    ]
    if date_header is not None:
        header_lines.append(f"Date: {date_header}")
    raw_bytes = ("\r\n".join(header_lines) + "\r\n\r\nBody").encode("utf-8")
    return GmailRawMessage(
        message_id=message_id,
        raw_bytes=raw_bytes,
        internal_date=internal_date,
    )


def test_count_action_uses_gateway_query() -> None:
    gateway = FakeGateway()
    registry = build_action_registry()

    result = registry.run("count", gateway, "INBOX", MessageFilters(starred=True), limit=5)

    assert result == ["3"]
    assert gateway.count_calls == [("INBOX", "is:starred")]


def test_list_action_formats_headers() -> None:
    gateway = FakeGateway()
    registry = build_action_registry()

    result = registry.run("list", gateway, "IMPORTANT", MessageFilters(), limit=2)

    assert result == [
        GmailMessageHeader(
            message_id="abc123",
            recipient="to@example.com",
            sender="from@example.com",
            date="Mon, 01 Jan 2024 10:00:00 +0000",
            subject="Hello",
        )
    ]
    assert gateway.list_calls == [("IMPORTANT", None, 2)]


def test_search_list_action_uses_search_gateway_path() -> None:
    gateway = FakeGateway()
    registry = build_action_registry()

    result = registry.run_for_search(
        "list",
        gateway,
        raw_query="from:bob@example.com",
        filters=MessageFilters(starred=True),
        limit=3,
    )

    assert result == [
        GmailMessageHeader(
            message_id="search-1",
            recipient="to@example.com",
            sender="from@example.com",
            date="Mon, 01 Jan 2024 10:00:00 +0000",
            subject="Hello",
        )
    ]
    assert gateway.search_list_calls == [("from:bob@example.com is:starred", 3)]


def test_label_add_action_adds_label_to_matching_search_messages() -> None:
    gateway = FakeGateway()
    registry = build_action_registry()

    result = registry.run_for_search(
        "label-add",
        gateway,
        raw_query="from:bob@example.com",
        filters=MessageFilters(),
        limit=10,
        label_name="FollowUp",
    )

    assert result == ["2 messages updated"]
    assert gateway.ensure_label_calls == ["FollowUp"]
    assert gateway.modify_calls == [
        ("search-1", ("id:FollowUp",), ()),
        ("search-2", ("id:FollowUp",), ()),
    ]


def test_label_add_action_reports_progress_for_each_message() -> None:
    gateway = FakeGateway()
    gateway.raw_messages = {
        "search-1": build_raw_message(
            "search-1",
            date_header="Tue, 02 Jan 2024 10:00:00 +0000",
            internal_date=1704189600000,
        ),
        "search-2": build_raw_message(
            "search-2",
            date_header="Wed, 03 Jan 2024 11:00:00 +0000",
            internal_date=1704279600000,
        ),
    }
    registry = build_action_registry()
    progress_messages: list[str | None] = []

    registry.run_for_search(
        "label-add",
        gateway,
        raw_query="from:bob@example.com",
        filters=MessageFilters(),
        limit=10,
        label_name="FollowUp",
        progress_callback=progress_messages.append,
    )

    assert progress_messages == [
        "Applying label-add 1/2: 2024-01-02 10:00:00 | search-1 | from@example.com | Subject",
        "Applying label-add 2/2: 2024-01-03 11:00:00 | search-2 | from@example.com | Subject",
        None,
    ]


def test_label_remove_action_removes_label_from_matching_label_messages() -> None:
    gateway = FakeGateway()
    registry = build_action_registry()

    result = registry.run(
        "label-remove",
        gateway,
        "INBOX",
        MessageFilters(starred=False),
        limit=10,
        label_name="Existing",
    )

    assert result == ["2 messages updated"]
    assert gateway.modify_calls == [
        ("label-1", (), ("LBL_EXISTING",)),
        ("label-2", (), ("LBL_EXISTING",)),
    ]


def test_label_remove_action_reports_progress_for_each_message() -> None:
    gateway = FakeGateway()
    gateway.raw_messages = {
        "label-1": build_raw_message(
            "label-1",
            date_header="Tue, 02 Jan 2024 10:00:00 +0000",
            internal_date=1704189600000,
        ),
        "label-2": build_raw_message(
            "label-2",
            date_header="Wed, 03 Jan 2024 11:00:00 +0000",
            internal_date=1704279600000,
        ),
    }
    registry = build_action_registry()
    progress_messages: list[str | None] = []

    registry.run(
        "label-remove",
        gateway,
        "INBOX",
        MessageFilters(starred=False),
        limit=10,
        label_name="Existing",
        progress_callback=progress_messages.append,
    )

    assert progress_messages == [
        "Applying label-remove 1/2: 2024-01-02 10:00:00 | label-1 | from@example.com | Subject",
        "Applying label-remove 2/2: 2024-01-03 11:00:00 | label-2 | from@example.com | Subject",
        None,
    ]


def test_action_registry_lists_names_with_descriptions() -> None:
    registry = build_action_registry()

    assert registry.list_actions() == [
        ("backup", "Back up matching messages as .eml files."),
        ("count", "Print the number of matching messages."),
        ("label-add", "Add a label to all matching messages."),
        ("label-remove", "Remove a label from all matching messages."),
        ("list", "List matching message headers."),
    ]


def test_action_registry_returns_help_for_backup_action() -> None:
    registry = build_action_registry()

    help_text = registry.help_for_action("backup")

    assert "Action: backup" in help_text
    assert "Back up matching messages as .eml files." in help_text
    assert "--backup-path <DIR>" in help_text
    assert "--delete" in help_text
    assert "--force" in help_text


def test_action_registry_returns_help_for_label_add_action() -> None:
    registry = build_action_registry()

    help_text = registry.help_for_action("label-add")

    assert "Action: label-add" in help_text
    assert "Add a label to all matching messages." in help_text
    assert "--name <LABEL_NAME>" in help_text


def test_label_add_action_requires_label_name() -> None:
    gateway = FakeGateway()
    registry = build_action_registry()

    try:
        registry.run_for_search(
            "label-add",
            gateway,
            raw_query="from:bob@example.com",
            filters=MessageFilters(),
            limit=10,
        )
    except ValueError as exc:
        assert str(exc) == "Action label-add requires --name"
    else:
        raise AssertionError("Expected ValueError when label-add is missing label name")


def test_action_registry_rejects_unknown_action_help() -> None:
    registry = build_action_registry()

    try:
        registry.help_for_action("missing")
    except ValueError as exc:
        assert str(exc) == "Unsupported action: missing"
    else:
        raise AssertionError("Expected ValueError for unsupported action help")


def test_backup_action_writes_eml_files_to_default_backup_path(tmp_path: Path) -> None:
    gateway = FakeGateway()
    gateway.raw_messages = {
        "search-1": build_raw_message(
            "search-1",
            date_header="Tue, 02 Jan 2024 10:00:00 +0000",
            internal_date=1704189600000,
        ),
        "search-2": build_raw_message(
            "search-2",
            date_header="Wed, 03 Jan 2024 11:00:00 +0000",
            internal_date=1704279600000,
        ),
    }
    backup_root = tmp_path / "backups"
    registry = build_action_registry(default_backup_path=backup_root)

    result = registry.run_for_search(
        "backup",
        gateway,
        raw_query="from:bob@example.com",
        filters=MessageFilters(),
        limit=1,
    )

    expected_root = backup_root.resolve()
    expected_file = expected_root / "2024" / "01-02" / "20240102-100000-search-1.eml"
    assert result == [f"1 messages written to {expected_root} (0 skipped)"]
    assert expected_file.read_bytes() == gateway.raw_messages["search-1"].raw_bytes
    assert gateway.raw_message_calls == ["search-1"]


def test_backup_action_uses_backup_path_override(tmp_path: Path) -> None:
    gateway = FakeGateway()
    gateway.raw_messages = {
        "search-1": build_raw_message(
            "search-1",
            date_header="Tue, 02 Jan 2024 10:00:00 +0000",
            internal_date=1704189600000,
        ),
        "search-2": build_raw_message(
            "search-2",
            date_header="Wed, 03 Jan 2024 11:00:00 +0000",
            internal_date=1704279600000,
        ),
    }
    registry = build_action_registry(default_backup_path=tmp_path / "default-backups")
    override_root = tmp_path / "override-backups"

    result = registry.run_for_search(
        "backup",
        gateway,
        raw_query="from:bob@example.com",
        filters=MessageFilters(),
        limit=1,
        backup_path=override_root,
    )

    expected_root = override_root.resolve()
    expected_file = expected_root / "2024" / "01-02" / "20240102-100000-search-1.eml"
    assert result == [f"1 messages written to {expected_root} (0 skipped)"]
    assert expected_file.exists()
    assert not (tmp_path / "default-backups").exists()


def test_backup_action_resumes_by_skipping_existing_message_ids(tmp_path: Path) -> None:
    gateway = FakeGateway()
    gateway.raw_messages = {
        "search-1": build_raw_message(
            "search-1",
            date_header="Tue, 02 Jan 2024 10:00:00 +0000",
            internal_date=1704189600000,
        ),
        "search-2": build_raw_message(
            "search-2",
            date_header="Wed, 03 Jan 2024 11:00:00 +0000",
            internal_date=1704279600000,
        ),
    }
    backup_root = tmp_path / "backups"
    existing_file = backup_root / "2024" / "01-02" / "20240102-100000-search-1.eml"
    existing_file.parent.mkdir(parents=True)
    existing_file.write_bytes(b"existing")
    registry = build_action_registry(default_backup_path=backup_root)

    result = registry.run_for_search(
        "backup",
        gateway,
        raw_query="from:bob@example.com",
        filters=MessageFilters(),
        limit=10,
    )

    expected_root = backup_root.resolve()
    expected_file = expected_root / "2024" / "01-03" / "20240103-110000-search-2.eml"
    assert result == [f"1 messages written to {expected_root} (1 skipped)"]
    assert existing_file.read_bytes() == b"existing"
    assert expected_file.exists()
    assert gateway.raw_message_calls == ["search-2"]


def test_backup_action_falls_back_to_internal_date_when_date_header_missing(tmp_path: Path) -> None:
    gateway = FakeGateway()
    gateway.raw_messages = {
        "search-1": build_raw_message(
            "search-1",
            date_header=None,
            internal_date=1704189600000,
        ),
        "search-2": build_raw_message(
            "search-2",
            date_header="Wed, 03 Jan 2024 11:00:00 +0000",
            internal_date=1704279600000,
        ),
    }
    backup_root = tmp_path / "backups"
    registry = build_action_registry(default_backup_path=backup_root)

    registry.run_for_search(
        "backup",
        gateway,
        raw_query="from:bob@example.com",
        filters=MessageFilters(),
        limit=1,
    )

    expected_file = backup_root.resolve() / "2024" / "01-02" / "20240102-100000-search-1.eml"
    assert expected_file.exists()


def test_backup_action_reports_progress_for_written_and_skipped_messages(tmp_path: Path) -> None:
    gateway = FakeGateway()
    gateway.raw_messages = {
        "search-1": build_raw_message(
            "search-1",
            date_header="Tue, 02 Jan 2024 10:00:00 +0000",
            internal_date=1704189600000,
        ),
        "search-2": build_raw_message(
            "search-2",
            date_header="Wed, 03 Jan 2024 11:00:00 +0000",
            internal_date=1704279600000,
        ),
    }
    backup_root = tmp_path / "backups"
    existing_file = backup_root / "2024" / "01-02" / "20240102-100000-search-1.eml"
    existing_file.parent.mkdir(parents=True)
    existing_file.write_bytes(b"existing")
    registry = build_action_registry(default_backup_path=backup_root)
    progress_messages: list[str | None] = []

    registry.run_for_search(
        "backup",
        gateway,
        raw_query="from:bob@example.com",
        filters=MessageFilters(),
        limit=10,
        progress_callback=progress_messages.append,
    )

    assert progress_messages == [
        "Skipping 1/2: message_id=search-1 already backed up",
        "Backing up 2/2: 2024-01-03 11:00:00 | search-2 | from@example.com | Subject",
        None,
    ]


def test_backup_action_decodes_subject_for_progress(tmp_path: Path) -> None:
    gateway = FakeGateway()
    gateway.raw_messages = {
        "search-1": GmailRawMessage(
            message_id="search-1",
            raw_bytes=(
                b"From: Sender Example <from@example.com>\r\n"
                b"To: to@example.com\r\n"
                b"Subject: =?utf-8?Q?Weekly=20Update=3A=20Alpha=204.7.2=20&=20Roadmap?=\r\n"
                b"Date: Tue, 02 Jan 2024 10:00:00 +0000\r\n\r\n"
                b"Body"
            ),
            internal_date=1704189600000,
        ),
        "search-2": build_raw_message(
            "search-2",
            date_header="Wed, 03 Jan 2024 11:00:00 +0000",
            internal_date=1704279600000,
        ),
    }
    backup_root = tmp_path / "backups"
    registry = build_action_registry(default_backup_path=backup_root)
    progress_messages: list[str | None] = []

    registry.run_for_search(
        "backup",
        gateway,
        raw_query="from:bob@example.com",
        filters=MessageFilters(),
        limit=1,
        progress_callback=progress_messages.append,
    )

    assert progress_messages == [
        (
            "Backing up 1/1: 2024-01-02 10:00:00 | search-1 | from@example.com | "
            "Weekly Update: Alpha 4.7.2 & Roadmap"
        ),
        None,
    ]


def test_backup_action_moves_written_messages_to_bin_when_delete_enabled(tmp_path: Path) -> None:
    gateway = FakeGateway()
    gateway.raw_messages = {
        "search-1": build_raw_message(
            "search-1",
            date_header="Tue, 02 Jan 2024 10:00:00 +0000",
            internal_date=1704189600000,
        ),
        "search-2": build_raw_message(
            "search-2",
            date_header="Wed, 03 Jan 2024 11:00:00 +0000",
            internal_date=1704279600000,
        ),
    }
    backup_root = tmp_path / "backups"
    registry = build_action_registry(default_backup_path=backup_root)

    result = registry.run_for_search(
        "backup",
        gateway,
        raw_query="from:bob@example.com",
        filters=MessageFilters(),
        limit=1,
        delete_after_backup=True,
    )

    expected_root = backup_root.resolve()
    expected_file = expected_root / "2024" / "01-02" / "20240102-100000-search-1.eml"
    assert result == [f"1 messages written to {expected_root} (0 skipped, 1 moved to Bin)"]
    assert expected_file.exists()
    assert gateway.trash_calls == ["search-1"]


def test_backup_action_does_not_move_skipped_messages_to_bin(tmp_path: Path) -> None:
    gateway = FakeGateway()
    gateway.raw_messages = {
        "search-1": build_raw_message(
            "search-1",
            date_header="Tue, 02 Jan 2024 10:00:00 +0000",
            internal_date=1704189600000,
        ),
        "search-2": build_raw_message(
            "search-2",
            date_header="Wed, 03 Jan 2024 11:00:00 +0000",
            internal_date=1704279600000,
        ),
    }
    backup_root = tmp_path / "backups"
    existing_file = backup_root / "2024" / "01-02" / "20240102-100000-search-1.eml"
    existing_file.parent.mkdir(parents=True)
    existing_file.write_bytes(b"existing")
    registry = build_action_registry(default_backup_path=backup_root)

    result = registry.run_for_search(
        "backup",
        gateway,
        raw_query="from:bob@example.com",
        filters=MessageFilters(),
        limit=10,
        delete_after_backup=True,
    )

    expected_root = backup_root.resolve()
    assert result == [f"1 messages written to {expected_root} (1 skipped, 1 moved to Bin)"]
    assert gateway.trash_calls == ["search-2"]
