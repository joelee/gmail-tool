# gmail-tool

[![PyPI version](https://img.shields.io/pypi/v/gmail-tool.svg)](https://pypi.org/project/gmail-tool/)
[![CI](https://github.com/joelee/gmail-tool/actions/workflows/ci.yml/badge.svg)](https://github.com/joelee/gmail-tool/actions/workflows/ci.yml)
[![Publish](https://github.com/joelee/gmail-tool/actions/workflows/publish.yml/badge.svg)](https://github.com/joelee/gmail-tool/actions/workflows/publish.yml)
[![Coverage](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/joelee/gmail-tool/main/.github/badges/coverage.json)](https://github.com/joelee/gmail-tool/actions/workflows/ci.yml)
[![PyPI Downloads](https://img.shields.io/pypi/dm/gmail-tool.svg)](https://pypi.org/project/gmail-tool/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://pypi.org/project/gmail-tool/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

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

For the normal OAuth desktop flow, `config.toml` is optional.

Quick start:

1. Place your Desktop OAuth client JSON at `~/.config/gmail-tool/client_secret.json`
2. Run `gmail-tool auth login`
3. Run `gmail-tool auth check`

Useful helpers:

- `gmail-tool auth paths`
- `gmail-tool auth logout`
- `gmail-tool auth login --no-browser`

Credential setup instructions are in `docs/google-credentials.md`.

## Quick Start

1. Install `uv`.
2. For OAuth, place your Desktop OAuth client JSON at `~/.config/gmail-tool/client_secret.json`.
3. Install dependencies:
```bash
uv sync --dev
```

4. Log in:

```bash
uv run gmail-tool auth login
uv run gmail-tool auth check
uv run gmail-tool auth paths
```

5. List labels:

```bash
uv run gmail-tool labels
```

Show the CLI version:

```bash
uv run gmail-tool --version
```

Enable debug output to stderr:

```bash
uv run gmail-tool --verbose labels
```

Or as JSON:

```bash
uv run gmail-tool labels -f json
```

Auth diagnostics:

```bash
uv run gmail-tool auth-check
uv run gmail-tool auth check
```

Read a full message by identifier:

```bash
uv run gmail-tool read <MESSAGE_ID>
```

Search with a raw Gmail query:

```bash
uv run gmail-tool search from:bob@example.com has:attachment
```

Count search matches:

```bash
uv run gmail-tool search -a count from:bob@example.com
```

Add a label to all search matches:

```bash
uv run gmail-tool search -a label-add:FollowUp from:bob@example.com
```

List built-in search examples:

```bash
uv run gmail-tool search --list-query-examples
```

Print a Gmail search operator cheat sheet:

```bash
uv run gmail-tool search --cheat-sheet
```

Run a saved query from `config.toml`:

```bash
uv run gmail-tool search --saved-query recent_attachments
```

Back up matching messages as `.eml` files:

```bash
uv run gmail-tool search -a backup from:bob@example.com
uv run gmail-tool search -a backup --backup-path /tmp/gmail-backups from:bob@example.com
```

6. Count messages in a label:

```bash
uv run gmail-tool label INBOX -a count
```

`gmail-tool label <LABEL>` accepts either an exact Gmail label name such as `@Later` or an exact label ID such as `Label_66`.

7. List messages in a label:

```bash
uv run gmail-tool label IMPORTANT -l 10 --starred true
```

Or export them as CSV:

```bash
uv run gmail-tool label IMPORTANT -l 10 -f csv
```

Plain-text list output includes `message_id` values that can be passed to `read`.

The `search` command returns the same message list structure as `label ... list`.

Both `label` and `search` default to the `list` action. Use `--action` or `-a` to switch to `count`, `backup`, `label-add:<name>`, or `label-remove:<name>`.

The `label` command defaults to the `list` action. Use `--action count` or `-a count` to switch actions.

8. List supported actions:

```bash
uv run gmail-tool label --list-actions
uv run gmail-tool search --list-actions
```

## Configuration

See `config.toml`, `.env.sample`, and `docs/configuration.md`.

All commands accept `--config <path>` or `-c <path>`. If omitted, config discovery falls back through environment, XDG, home config, `/etc`, and the project directory. If no config file is found, built-in OAuth defaults are used.

## Development

```bash
uv sync --dev
uv run pytest --cov=src/gmail_tool --cov-report=term-missing --cov-report=xml --cov-report=json
./scripts/update-coverage-badge.sh coverage.json
uv run pre-commit run --all-files
```

Coverage artifacts produced by CI:

- `coverage.json`
- `coverage.xml`
- `.github/badges/coverage.json`

## Releases

PyPI publishing is handled by the GitHub Actions `Publish` workflow on version tags such as `v0.2.2`.

Release packaging steps are documented in `docs/release/packaging.md`.

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

- [Architecture](docs/architecture.md)
- [Configuration](docs/configuration.md)
- [Google Credentials](docs/google-credentials.md)
- [GMail Search Cheat Sheet](docs/search-cheat-sheet.md)
- [Homebrew Packaging](docs/release/homebrew.md)
- [Release Packaging](docs/release/packaging.md)
- [Usage](docs/usage.md)
