# Search Examples And Saved Queries Plan

## Goals

- Add `search --list-query-examples` to show useful raw Gmail query examples.
- Add saved-query support through `config.toml`.
- Keep the feature small and aligned with the existing raw-query search design.

## Design Plan

1. Extend `Settings` with a search configuration section containing saved queries.
2. Add `[search.saved_queries]` examples to `config.toml`.
3. Add `--list-query-examples` to print built-in query examples without Gmail access.
4. Add `--saved-query <name>` so users can run configured queries by name.
5. Keep raw query arguments and saved queries composable in one command.

## TDD Strategy

- Add config-loading tests for saved queries first.
- Add CLI tests for example listing and saved-query lookup.
- Implement the smallest config and CLI changes needed to satisfy those tests.

## Integration Test Coverage Plan

- Application search tests continue to cover the search execution path.
- New coverage focuses on config loading and CLI argument behavior.

## Risks

- The command should fail clearly if a saved query name is unknown.
- Query combination order should remain deterministic.
