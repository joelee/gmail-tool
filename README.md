# gmail-tool

[![PyPI version](https://img.shields.io/pypi/v/gmail-tool.svg)](https://pypi.org/project/gmail-tool/)
[![CI](https://github.com/joelee/gmail-tool/actions/workflows/ci.yml/badge.svg)](https://github.com/joelee/gmail-tool/actions/workflows/ci.yml)
[![Publish](https://github.com/joelee/gmail-tool/actions/workflows/publish.yml/badge.svg)](https://github.com/joelee/gmail-tool/actions/workflows/publish.yml)
[![Coverage](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/joelee/gmail-tool/main/.github/badges/coverage.json)](https://github.com/joelee/gmail-tool/actions/workflows/ci.yml)
[![PyPI Downloads](https://img.shields.io/pypi/dm/gmail-tool.svg)](https://pypi.org/project/gmail-tool/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://pypi.org/project/gmail-tool/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Search, inspect, label, and back up Gmail from the terminal with guided OAuth setup, shell-friendly output, and reusable Gmail queries.

`gmail-tool` is built for fast mailbox exploration and repeatable command-line workflows. It works well for personal Gmail usage, local automation, and Google Workspace environments that need service account access.

## Features

- List Gmail labels
- Read full messages by Gmail message ID
- Search Gmail with raw Gmail search operators
- Reuse saved queries from `config.toml`
- Run actions against either labels or search results: `list`, `count`, `delete`, `backup`, `label-add --name <label_name>`, and `label-remove --name <label_name>`
- Export labels and message lists as `json` or `csv`
- Filter message results with `--from-date`, `--to-date`, and `--starred true|false`
- Back up matching messages as resumable `.eml` files
- Optionally move successfully backed-up messages to Gmail Bin with `--delete` and `--force`
- Use guided auth helpers including `gmail-tool auth login`, `gmail-tool auth check`, `gmail-tool auth paths`, `gmail-tool auth logout`, and `gmail-tool auth login --no-browser`
- Use OAuth desktop flow without requiring `config.toml`
- Use service account auth for Google Workspace domain-wide delegation

## Installation

`gmail-tool` requires Python 3.12+.

### pip

```bash
python -m pip install gmail-tool
```

Verify the install:

```bash
gmail-tool --version
```

### Homebrew

```bash
brew install joelee/oss/gmail-tool
```

Verify the install:

```bash
gmail-tool --version
```

## Quick Start

For normal OAuth usage, `config.toml` is optional.

1. In Google Cloud Console, create a Desktop OAuth client and enable the Gmail API.
2. Save the downloaded client JSON to `~/.config/gmail-tool/client_secret.json`.
3. Authenticate and verify access:

```bash
gmail-tool auth login
gmail-tool auth check
gmail-tool labels
```

If you are on a remote shell or headless machine, use `gmail-tool auth login --no-browser`.

4. Run a real query:

```bash
gmail-tool search from:bob@example.com has:attachment
```

Full credential setup steps are in [Google Credentials](docs/google-credentials.md).

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

Default OAuth file locations when no overrides are set:

- client secret: `${XDG_CONFIG_HOME:-~/.config}/gmail-tool/client_secret.json`
- token: `${XDG_STATE_HOME:-~/.local/state}/gmail-tool/oauth-token.json`

Credential setup instructions are in [Google Credentials](docs/google-credentials.md).

## Common Commands

Show the CLI version:

```bash
gmail-tool --version
```

Enable debug output to stderr:

```bash
gmail-tool --verbose labels
```

List labels as JSON:

```bash
gmail-tool labels -f json
```

Auth diagnostics:

```bash
gmail-tool auth check
```

Read a full message by identifier:

```bash
gmail-tool message read <MESSAGE_ID>
```

Move a message to Bin:

```bash
gmail-tool message delete <MESSAGE_ID>
gmail-tool message delete <MESSAGE_ID> --force
```

Search with a raw Gmail query:

```bash
gmail-tool search from:bob@example.com has:attachment
```

Count search matches:

```bash
gmail-tool search -a count from:bob@example.com
```

Add a label to all search matches:

```bash
gmail-tool search -a label-add --name FollowUp from:bob@example.com
```

List built-in search examples:

```bash
gmail-tool search --list-query-examples
```

Print a Gmail search operator cheat sheet:

```bash
gmail-tool search --cheat-sheet
```

Run a saved query from `config.toml`:

```bash
gmail-tool search --saved-query recent_attachments
```

Back up matching messages as `.eml` files:

```bash
gmail-tool search -a backup from:bob@example.com
gmail-tool search -a backup --backup-path /tmp/gmail-backups from:bob@example.com
gmail-tool search -a backup --backup-path /tmp/gmail-backups --delete from:bob@example.com
gmail-tool search -a backup --backup-path /tmp/gmail-backups --delete --force from:bob@example.com
```

Count messages in a label:

```bash
gmail-tool label INBOX -a count
```

`gmail-tool label <LABEL>` accepts either an exact Gmail label name such as `@Later` or an exact label ID such as `Label_66`.

List messages in a label:

```bash
gmail-tool label IMPORTANT -l 10 --starred true
```

Or export them as CSV:

```bash
gmail-tool label IMPORTANT -l 10 -f csv
```

Plain-text list output includes `message_id` values that can be passed to `message read`.

The `search` command returns the same message list structure as `label ... list`.

Both `label` and `search` default to the `list` action. Use `--action` or `-a` to switch to `count`, `delete`, `backup`, `label-add --name <name>`, or `label-remove --name <name>`.

List supported actions:

```bash
gmail-tool label --list-actions
gmail-tool search --list-actions
gmail-tool search --help-action backup
gmail-tool label --help-action label-add
```

## Configuration

See `config.toml`, `.env.sample`, and [Configuration](docs/configuration.md).

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

Release packaging steps are documented in [Release Packaging](docs/release/packaging.md).

Homebrew packaging steps are documented in [Homebrew Packaging](docs/release/homebrew.md).

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
