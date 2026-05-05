## Goal

- Add a first-class `delete` action for `gmail-tool search` and `gmail-tool label`.
- Move matching messages to Gmail Bin.
- Require confirmation by default and allow bypass with `--force`.

## Scope

- Extend the action registry with a `delete` action.
- Reuse existing batch progress output for message mutations.
- Keep existing `backup --delete` behavior working.
- Keep `--list-actions` and `--help-action delete` credential-free.

## Plan

1. Add unit and integration coverage for the new action and CLI validation rules.
2. Implement action-registry delete execution with progress reporting.
3. Update CLI validation and confirmation flow so `--force` also supports `--action delete`.
4. Update changelog and usage docs.
5. Run Ruff formatting and tests.

## Notes

- Prefer the smallest change that fits the current action registry and confirmation helpers.
- Keep delete confirmation messaging explicit about moving messages to Bin.
