# Changelog

## Unreleased

- Scaffolded `uv` managed Gmail CLI project.
- Added extensible auth, action, and filter architecture.
- Added tests, Docker packaging, pre-commit hooks, and CI.
- Documented Google credential setup and plan lifecycle workflow.
- Added opt-in live Gmail integration tests for real credential verification.
- Added `auth-check` CLI command for auth and Gmail reachability diagnostics.
- Added `gmail-tool label --list-actions` and a dedicated `docs/usage.md` guide.
- Changed the default label action limit to `1000` when `--limit` is omitted.
- Added `--format json|csv` for `labels` and `label <LABEL> list`.
- Added message identifiers to label list output and a `gmail-tool read <message-id>` command.
