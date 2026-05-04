# Batch Action Progress Reporting

## Goal

Show single-line progress output for long-running batch actions such as `label-add` and `label-remove`, similar to the existing `backup` action.

## Scope

- Reuse the existing progress callback pattern.
- Keep `count` and `list` free of progress output.
- Emit per-message progress details for label mutation actions.
- Keep the implementation extensible for future message-processing actions.

## Verification

- Run focused unit tests for action registry and CLI progress output.
