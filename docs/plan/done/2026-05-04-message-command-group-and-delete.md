# Message Command Group And Delete

## Goal

Move `gmail-tool read <message_id>` under a new `gmail-tool message` command group and add `gmail-tool message delete <message_id>` to move a message to Gmail Bin.

## Scope

- Replace the top-level `read` command with `message read`.
- Add `message delete` with confirmation and `--force`.
- Reuse the existing Gmail trash API path through the application layer.
- Update CLI help, tests, and user documentation.

## Verification

- Run focused CLI, application, and Gmail gateway tests.
