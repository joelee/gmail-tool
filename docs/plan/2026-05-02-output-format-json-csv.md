# Output Format Json Csv Plan

## Goals

- Add `--format json|csv` to `labels`.
- Add `--format json|csv` to `label <LABEL> list`.
- Keep `count`, `auth-check`, and non-list label actions on their current plain-text output path.

## Design Plan

1. Add CLI-level format parsing for supported commands.
2. Return structured message header rows for the `list` action so formatting does not depend on parsing display strings.
3. Render plain text by default, and JSON or CSV when explicitly requested.
4. Reject `--format` for unsupported label actions such as `count`.
5. Update docs and examples.

## TDD Strategy

- Add CLI tests first for JSON and CSV output on `labels` and `label ... list`.
- Add a CLI test that verifies `label ... count --format ...` is rejected.
- Implement the minimal formatting layer and action output changes needed to satisfy the tests.

## Integration Test Coverage Plan

- Existing integration tests continue to validate Gmail access and the list action path.
- The new formatting behavior is primarily CLI output logic, so unit tests provide most coverage.

## Risks

- Formatting support should not alter the default human-readable output.
- CSV output must remain stable and include headers.
