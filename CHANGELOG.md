# Changelog

## Unreleased

## v0.2.0 - 2026-05-03

- Added a resumable `backup` action with config-backed and CLI override backup paths, writing `.eml` files by message timestamp.
- Added shared `--list-actions` support for both `gmail-tool label` and `gmail-tool search`, with one-line action descriptions.
- Aligned `--list-actions` descriptions for clearer CLI output.
- Fixed CLI non-list `--format` validation so CI and local runs report the expected error message consistently.
- Renamed label mutation actions from `add-label` / `remove-label` to `label-add` / `label-remove`.

## v0.1.1 - 2026-05-03

- Scaffolded `uv` managed Gmail CLI project.
- Added extensible auth, action, and filter architecture.
- Added tests, Docker packaging, pre-commit hooks, and CI.
- Documented Google credential setup and plan lifecycle workflow.
- Added opt-in live Gmail integration tests for real credential verification.
- Added `auth-check` CLI command for auth and Gmail reachability diagnostics.
- Added `gmail-tool label --list-actions` and a dedicated `docs/usage.md` guide.
- Changed the default label action limit to `100` when `--limit` is omitted.
- Added `--format json|csv` for `labels` and `label <LABEL> list`.
- Added message identifiers to label list output and a `gmail-tool read <message-id>` command.
- Added `gmail-tool search <search arguments>` for raw Gmail query listing.
- Added `search --list-query-examples` and config-backed saved queries in `config.toml`.
- Added `search --cheat-sheet` and `docs/search-cheat-sheet.md`.
- Added config discovery priority for `config.toml` across all CLI commands.
- Changed `gmail-tool label` to use `--action/-a` with default action `list`.
- Added `search --action/-a` and label mutation actions `label-add:<name>` / `label-remove:<name>`.
- Added global `--version/-V` and `--verbose/-v` options plus `-c`, `-f`, `-l`, and `-h` short aliases.
- Added exact label-name resolution for `gmail-tool label <LABEL>`, while still accepting exact label IDs.
