import base64

from gmail_tool.gmail import (
    GmailApiGateway,
    GmailLabel,
    GmailMessage,
    GmailMessageHeader,
    GmailRawMessage,
)


class _ExecutableRequest:
    def __init__(self, response):
        self._response = response

    def execute(self):
        return self._response


class _LabelsResource:
    def __init__(self, responses, calls):
        self._responses = responses
        self._calls = calls

    def list(self, **kwargs):
        self._calls.append(("labels.list", kwargs))
        return _ExecutableRequest(self._responses["labels.list"].pop(0))

    def create(self, **kwargs):
        self._calls.append(("labels.create", kwargs))
        return _ExecutableRequest(self._responses["labels.create"].pop(0))


class _MessagesResource:
    def __init__(self, responses, calls):
        self._responses = responses
        self._calls = calls

    def list(self, **kwargs):
        self._calls.append(("messages.list", kwargs))
        return _ExecutableRequest(self._responses["messages.list"].pop(0))

    def get(self, **kwargs):
        self._calls.append(("messages.get", kwargs))
        return _ExecutableRequest(self._responses["messages.get"].pop(0))

    def modify(self, **kwargs):
        self._calls.append(("messages.modify", kwargs))
        return _ExecutableRequest(self._responses["messages.modify"].pop(0))


class _UsersResource:
    def __init__(self, responses, calls):
        self._responses = responses
        self._calls = calls

    def labels(self):
        return _LabelsResource(self._responses, self._calls)

    def messages(self):
        return _MessagesResource(self._responses, self._calls)


class _FakeService:
    def __init__(self, responses):
        self.calls = []
        self._responses = responses

    def users(self):
        return _UsersResource(self._responses, self.calls)


def _header(name: str, value: str) -> dict[str, str]:
    return {"name": name, "value": value}


def test_list_labels_returns_label_models() -> None:
    service = _FakeService({"labels.list": [{"labels": [{"id": "INBOX", "name": "INBOX"}]}]})

    gateway = GmailApiGateway(service=service, user_id="me")

    assert gateway.list_labels() == [GmailLabel(id="INBOX", name="INBOX")]
    assert service.calls == [("labels.list", {"userId": "me"})]


def test_list_message_ids_pages_until_next_token_is_missing() -> None:
    service = _FakeService(
        {
            "messages.list": [
                {"messages": [{"id": "m1"}], "nextPageToken": "next-token"},
                {"messages": [{"id": "m2"}]},
            ]
        }
    )

    gateway = GmailApiGateway(service=service, user_id="me")

    assert gateway.list_message_ids(None, "from:bob@example.com") == ["m1", "m2"]
    assert service.calls == [
        ("messages.list", {"userId": "me", "q": "from:bob@example.com", "pageToken": None}),
        (
            "messages.list",
            {"userId": "me", "q": "from:bob@example.com", "pageToken": "next-token"},
        ),
    ]


def test_list_message_ids_passes_label_filter_when_present() -> None:
    service = _FakeService(
        {"messages.list": [{"messages": [{"id": "unused"}]}, {"messages": [{"id": "m1"}]}]}
    )

    gateway = GmailApiGateway(service=service, user_id="me")

    assert gateway.list_message_ids("LBL", None) == ["m1"]
    assert service.calls == [
        ("messages.list", {"userId": "me", "q": None, "pageToken": None}),
        ("messages.list", {"userId": "me", "labelIds": ["LBL"], "q": None, "pageToken": None}),
    ]


def test_list_message_headers_fetches_metadata_headers() -> None:
    service = _FakeService(
        {
            "messages.list": [{"messages": [{"id": "m1"}]}],
            "messages.get": [
                {
                    "payload": {
                        "headers": [
                            _header("To", "to@example.com"),
                            _header("From", "from@example.com"),
                            _header("Date", "Mon, 01 Jan 2024 10:00:00 +0000"),
                            _header("Subject", "Hello"),
                        ]
                    }
                }
            ],
        }
    )

    gateway = GmailApiGateway(service=service, user_id="me")

    assert gateway.list_message_headers("INBOX", "is:starred", 5) == [
        GmailMessageHeader(
            message_id="m1",
            recipient="to@example.com",
            sender="from@example.com",
            date="Mon, 01 Jan 2024 10:00:00 +0000",
            subject="Hello",
        )
    ]


def test_search_message_headers_fetches_metadata_headers() -> None:
    service = _FakeService(
        {
            "messages.list": [{"messages": [{"id": "m1"}]}],
            "messages.get": [{"payload": {"headers": [_header("Subject", "Search")]}}],
        }
    )

    gateway = GmailApiGateway(service=service, user_id="me")

    assert gateway.search_message_headers("from:bob@example.com", 3) == [
        GmailMessageHeader(
            message_id="m1",
            recipient="",
            sender="",
            date="",
            subject="Search",
        )
    ]


def test_ensure_label_reuses_existing_label() -> None:
    service = _FakeService({"labels.list": [{"labels": [{"id": "LBL", "name": "FollowUp"}]}]})

    gateway = GmailApiGateway(service=service, user_id="me")

    assert gateway.ensure_label("FollowUp") == "LBL"


def test_ensure_label_creates_label_when_missing() -> None:
    service = _FakeService(
        {
            "labels.list": [{"labels": [{"id": "LBL", "name": "Existing"}]}],
            "labels.create": [{"id": "NEW_LABEL"}],
        }
    )

    gateway = GmailApiGateway(service=service, user_id="me")

    assert gateway.ensure_label("FollowUp") == "NEW_LABEL"
    assert service.calls[-1] == (
        "labels.create",
        {
            "userId": "me",
            "body": {
                "name": "FollowUp",
                "labelListVisibility": "labelShow",
                "messageListVisibility": "show",
            },
        },
    )


def test_modify_message_labels_calls_gmail_modify() -> None:
    service = _FakeService({"messages.modify": [{}]})

    gateway = GmailApiGateway(service=service, user_id="me")
    gateway.modify_message_labels("m1", add_label_ids=["A"], remove_label_ids=["B"])

    assert service.calls == [
        (
            "messages.modify",
            {
                "userId": "me",
                "id": "m1",
                "body": {"addLabelIds": ["A"], "removeLabelIds": ["B"]},
            },
        )
    ]


def test_get_message_prefers_text_plain_body() -> None:
    plain_body = base64.urlsafe_b64encode(b"Plain body").decode().rstrip("=")
    html_body = base64.urlsafe_b64encode(b"<p>HTML</p>").decode().rstrip("=")
    service = _FakeService(
        {
            "messages.get": [
                {
                    "payload": {
                        "headers": [
                            _header("To", "to@example.com"),
                            _header("From", "from@example.com"),
                            _header("Date", "Mon"),
                            _header("Subject", "Hello"),
                        ],
                        "parts": [
                            {"mimeType": "text/html", "body": {"data": html_body}},
                            {"mimeType": "text/plain", "body": {"data": plain_body}},
                        ],
                    }
                }
            ]
        }
    )

    gateway = GmailApiGateway(service=service, user_id="me")

    assert gateway.get_message("m1") == GmailMessage(
        message_id="m1",
        recipient="to@example.com",
        sender="from@example.com",
        date="Mon",
        subject="Hello",
        body="Plain body",
    )


def test_get_message_falls_back_to_html_then_payload_body() -> None:
    html_body = base64.urlsafe_b64encode(b"<p>HTML</p>").decode().rstrip("=")
    payload_body = base64.urlsafe_b64encode(b"Payload body").decode().rstrip("=")
    service = _FakeService(
        {
            "messages.get": [
                {"payload": {"parts": [{"mimeType": "text/html", "body": {"data": html_body}}]}},
                {"payload": {"body": {"data": payload_body}}},
            ]
        }
    )

    gateway = GmailApiGateway(service=service, user_id="me")

    assert gateway.get_message("html").body == "<p>HTML</p>"
    assert gateway.get_message("payload").body == "Payload body"


def test_get_raw_message_decodes_base64url_payload() -> None:
    raw_bytes = b"From: from@example.com\r\n\r\nBody"
    encoded = base64.urlsafe_b64encode(raw_bytes).decode().rstrip("=")
    service = _FakeService({"messages.get": [{"raw": encoded, "internalDate": "1704276000000"}]})

    gateway = GmailApiGateway(service=service, user_id="me")

    assert gateway.get_raw_message("m1") == GmailRawMessage(
        message_id="m1",
        raw_bytes=raw_bytes,
        internal_date=1704276000000,
    )


def test_extract_body_returns_empty_string_when_missing() -> None:
    gateway = GmailApiGateway(service=_FakeService({}), user_id="me")

    assert gateway._extract_body({}) == ""
