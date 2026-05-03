# Label Action Rename Plan

## Goals

- Rename `add-label:<label_name>` to `label-add:<label_name>`.
- Rename `remove-label:<label_name>` to `label-remove:<label_name>`.
- Keep action behavior unchanged aside from the public names.

## Design Plan

1. Update dynamic action prefixes in the action registry.
2. Update tests to use the new action names.
3. Update docs and changelog references.

## TDD Strategy

- Update unit and integration tests first to reflect the renamed actions.
- Apply the minimal registry and doc changes needed to satisfy the tests.

## Integration Test Coverage Plan

- Existing action and application tests already cover mutation behavior, so rename coverage belongs there.

## Risks

- The rename is user-facing and should be reflected consistently in action listings, docs, and changelog entries.
