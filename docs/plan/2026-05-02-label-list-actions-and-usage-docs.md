# Label Action Listing And Usage Docs Plan

## Goals

- Add a CLI path to list currently supported label actions.
- Keep the implementation aligned with the central action registry so future actions appear automatically.
- Add a dedicated usage guide with practical command examples.

## Design Plan

1. Add a registry method that exposes supported action names.
2. Extend the `label` CLI command with a `--list-actions` option.
3. Allow `label --list-actions` to print actions without requiring label execution.
4. Add unit tests for the new CLI behavior.
5. Create `docs/usage.md` with command reference and examples.

## TDD Strategy

- Add CLI tests first to define output and argument handling.
- Implement the minimal registry and CLI changes needed to satisfy the tests.

## Integration Test Coverage Plan

- Existing live Gmail tests continue to validate real Gmail access.
- This feature is primarily CLI and registry logic, so unit tests are the main coverage.

## Risks

- The new option should not make normal `label <LABEL> <ACTION>` usage ambiguous.
- The action list should come from the registry, not a duplicated constant in the CLI.
