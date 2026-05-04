# Changelog

## Unreleased

## v0.3.0 - 2026-05-04

- Improved `README.md` onboarding with clearer product positioning, current feature coverage, pip and Homebrew install instructions, and a more direct quick-start flow.
- Added command descriptions to CLI help output so `gmail-tool --help` and `gmail-tool auth --help` are more informative for first-time users.
- Removed the legacy `auth-check` alias in favor of `gmail-tool auth check`.
- Sorted CLI help options and commands alphabetically to make `gmail-tool --help` easier to scan.
- Added `backup --delete` with confirmation and `--force`, moving successfully written messages to the Gmail Bin after backup.
- Added help text for `search` and `label` arguments and options to improve subcommand `--help` output.
- Added `--help-action <action_name>` for `search` and `label` to print action-specific help and supported sub-options.
- Changed label mutation actions to use `--action label-add --name <label_name>` and `--action label-remove --name <label_name>` instead of `label-add:<label_name>` and `label-remove:<label_name>`.
- Refactored `gmail-tool read <message-id>` to `gmail-tool message read <message-id>` and added `gmail-tool message delete <message-id>` with confirmation and `--force`.
- Updated user-facing documentation examples to use `gmail-tool` instead of `uv run gmail-tool`.
- Added single-line progress output for long-running batch actions such as `backup`, `label-add`, and `label-remove`, while keeping `count` and `list` quiet.

## v0.2.2 - 2026-05-03

- Added GitHub Actions coverage JSON/XML artifacts and a generated coverage badge for README reporting.
- Added a GitHub Actions workflow that refreshes the checked-in coverage badge after successful `main` branch CI runs.
- Added README badges for PyPI version, CI status, coverage, Python support, and license.
- Added README badges for publish workflow status and PyPI download counts.
- Added configless OAuth defaults with XDG-based client secret and token paths for first-run installs.
- Added `gmail-tool auth login` and `gmail-tool auth check` for guided authentication setup and verification.
- Added `gmail-tool auth paths`, `gmail-tool auth logout`, and `gmail-tool auth login --no-browser` to improve local auth management and headless setup.
- Improved auth errors to print actionable OAuth setup instructions instead of raw missing-config failures.
- Tightened OAuth client secret and token file permissions during local auth setup.
- Improved unit coverage for `gmail.py` and `auth.py` with focused request/response and OAuth flow tests.
- Added a `scripts/update-homebrew-formula.sh` helper to regenerate the `gmail-tool` Homebrew formula from the published PyPI release and locked runtime dependencies.
- Documented the Homebrew packaging flow and formula refresh steps.

## v0.2.1 - 2026-05-03

- Added PyPI packaging metadata and a tag-driven GitHub Actions publish workflow using Trusted Publishing.
- Documented the release packaging flow for PyPI publication and Homebrew follow-up updates.

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
- Added message identifiers to label list output and a `gmail-tool message read <message-id>` command.
- Added `gmail-tool search <search arguments>` for raw Gmail query listing.
- Added `search --list-query-examples` and config-backed saved queries in `config.toml`.
- Added `search --cheat-sheet` and `docs/search-cheat-sheet.md`.
- Added config discovery priority for `config.toml` across all CLI commands.
- Changed `gmail-tool label` to use `--action/-a` with default action `list`.
- Added `search --action/-a` and label mutation actions `label-add` / `label-remove`.
- Added global `--version/-V` and `--verbose/-v` options plus `-c`, `-f`, `-l`, and `-h` short aliases.
- Added exact label-name resolution for `gmail-tool label <LABEL>`, while still accepting exact label IDs.
