# Search Action And Label Mutations Plan

## Goals

- Add the same `--action` option to `gmail-tool search` with default action `list`.
- Add action support for:
  - `add-label:<label_name>`
  - `remove-label:<label_name>`
- Keep action execution centralized so `label` and `search` share the same implementation.

## Design Plan

1. Extend the Gmail gateway with message listing and label mutation primitives.
2. Refactor the action registry so actions can run against either a label-constrained query or a raw search query.
3. Implement mutation actions that locate or create target labels as needed and apply changes across matching messages.
4. Add `--action` to `search` with default `list`.
5. Update docs and examples.

## TDD Strategy

- Add unit tests for action parsing and mutation behavior first.
- Add CLI tests for `search --action` defaulting and mutation action invocation.
- Implement the minimal shared action context needed to satisfy the tests.

## Integration Test Coverage Plan

- Application-level tests will verify search actions run with combined filters.
- Action tests will verify add/remove label behavior against a fake gateway.

## Risks

- Mutation actions must be idempotent when labels are already present or absent.
- Action naming with `:` should still list clearly in help and docs.
