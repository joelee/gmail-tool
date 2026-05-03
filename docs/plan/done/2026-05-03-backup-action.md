# Backup Action Plan

## Goals

- Add a `backup` action for both `gmail-tool label` and `gmail-tool search`.
- Use `config.toml` backup path by default and allow `--backup-path` to override it.
- Write each message as a `.eml` file under `YYYY/MM-DD/YYYYMMDD-HHmmss-<message_id>.eml`.
- Make backup runs resumable and efficient after interruption.

## Design Plan

1. Add `[backup].path` configuration support with relative paths resolved from the config file location.
2. Extend the Gmail gateway with raw message retrieval.
3. Add a `backup` action to the action registry.
4. Write `.eml` files from Gmail raw message bytes and use the message `Date` header, falling back to Gmail `internalDate` when needed.
5. Pre-scan existing `.eml` files under the backup root, extract backed-up `message_id` values, and skip them before fetching raw message data.
6. Support `--backup-path` on `label` and `search` only for the `backup` action.

## TDD Strategy

- Add config, action, application, and CLI tests first.
- Implement the minimal settings, gateway, registry, and CLI changes needed to satisfy those tests.

## Integration Test Coverage Plan

- Cover backup file layout and resume behavior in action and application tests using temporary directories.
- Cover CLI option parsing and validation in CLI unit tests.

## Risks

- Backup runs should be resumable without re-fetching already written messages.
- Relative config backup paths should resolve predictably.
- Backup output should remain idempotent across reruns.
