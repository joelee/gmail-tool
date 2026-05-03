# Label Name Or ID Resolution Plan

## Goals

- Allow `gmail-tool label <LABEL>` to accept either an exact Gmail label name or an exact Gmail label ID.
- Keep downstream Gmail calls using label IDs.
- Reject unknown labels with a clear error.

## Design Plan

1. Resolve the label reference in `Application.run_label_action()` before calling the action registry.
2. Match exact label IDs first, then exact label names.
3. Raise a small application-level error for unknown labels.
4. Convert that error into a CLI `BadParameter` so the user gets a clean message.
5. Update docs and changelog.

## TDD Strategy

- Add application tests first for exact name resolution, exact ID passthrough, and unknown labels.
- Add a CLI test for the user-facing error message.
- Implement the minimal application and CLI changes needed to satisfy those tests.

## Integration Test Coverage Plan

- Cover resolution in `tests/integration/test_application.py` because the behavior lives at the application boundary.
- Cover the CLI error surface in `tests/unit/test_cli.py`.

## Risks

- Resolution must stay exact-only and avoid fuzzy or case-insensitive matches.
- Search-based flows should remain unchanged.
- Label mutation actions should keep their current name-based semantics for target labels.
