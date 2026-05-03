# Label Action Option Plan

## Goals

- Change `gmail-tool label` so action selection uses `--action` and `-a`.
- Default the label action to `list` when no action is specified.
- Keep `--list-actions` unchanged.

## Design Plan

1. Update the `label` CLI signature so `label` remains positional and `action` becomes an option.
2. Default the action option to `list`.
3. Update tests to cover `--action`, `-a`, and implicit default behavior.
4. Refresh usage docs and examples.

## TDD Strategy

- Update CLI tests first to define the new invocation patterns.
- Apply the minimal CLI change needed to satisfy the tests.

## Integration Test Coverage Plan

- Existing application-level tests already cover action dispatch behavior.
- This change is primarily CLI parsing and defaults, so CLI unit tests are the main coverage.

## Risks

- The new option should not interfere with `--list-actions`.
- Docs and examples must be updated to avoid stale positional-action usage.
