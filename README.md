# gmail-tool

CLI application for exploring Gmail labels and querying messages by label with configurable auth, actions, and filters.

## Initial Features

- List Gmail labels
- Run actions against a label
- Actions:
  - `count`: print the number of messages in the label
  - `list`: print message headers (`recipient`, `sender`, `date`, `subject`) with `--limit`
- Global filters:
  - date range via `--from-date` and `--to-date`
  - `--starred true|false`
- Config-driven behavior via `config.toml`
- Secrets loaded from `.env`
- Docker packaging, pre-commit hooks, and GitHub Actions

## Authentication

Supported auth modes:

- OAuth desktop flow
- Service account flow for Google Workspace domain-wide delegation

Choose auth mode in `config.toml`.

Credential setup instructions are in `docs/google-credentials.md`.

## Quick Start

1. Install `uv`.
2. Copy `.env.sample` to `.env` and fill required values.
3. Review `config.toml` and adjust auth settings.
4. Install dependencies:

```bash
uv sync --dev
```

5. List labels:

```bash
uv run gmail-tool labels
```

Or as JSON:

```bash
uv run gmail-tool labels --format json
```

Auth diagnostics:

```bash
uv run gmail-tool auth-check
```

Read a full message by identifier:

```bash
uv run gmail-tool read <MESSAGE_ID>
```

6. Count messages in a label:

```bash
uv run gmail-tool label INBOX count
```

7. List messages in a label:

```bash
uv run gmail-tool label IMPORTANT list --limit 10 --starred true
```

Or export them as CSV:

```bash
uv run gmail-tool label IMPORTANT list --limit 10 --format csv
```

Plain-text list output includes `message_id` values that can be passed to `read`.

8. List supported actions:

```bash
uv run gmail-tool label --list-actions
```

## Configuration

See `config.toml`, `.env.sample`, and `docs/configuration.md`.

## Development

```bash
uv sync --dev
uv run pytest --cov=src/gmail_tool --cov-report=term-missing
uv run pre-commit run --all-files
```

### Live Gmail Integration Tests

Live Gmail tests are opt-in and use your local `.env` and `config.toml`.

Run them with an existing OAuth token:

```bash
ENABLE_LIVE_GMAIL_TESTS=true uv run pytest -m live_gmail
```

If this is your first OAuth run and no token exists yet, allow browser authentication explicitly:

```bash
ENABLE_LIVE_GMAIL_TESTS=true ALLOW_GMAIL_OAUTH_BROWSER=true uv run pytest -m live_gmail -s
```

These tests verify Gmail API access against your real mailbox and are skipped unless explicitly enabled.

## Documentation

- `docs/plan/initial-delivery.md`
- `docs/plan/2026-05-02-auth-diagnostics-command.md`
- `docs/plan/backlog.md`
- `docs/plan/done/2026-05-02-live-gmail-integration-tests.md`
- `docs/architecture.md`
- `docs/configuration.md`
- `docs/google-credentials.md`
- `docs/usage.md`
