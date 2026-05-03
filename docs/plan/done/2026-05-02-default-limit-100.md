# Default Limit 100 Plan

## Goals

- Reduce the default message listing limit from `1000` to `100`.
- Keep the behavior config-driven through `config.toml`.
- Update tests and documentation to match the new default.

## Design Plan

1. Update tests and fixtures that currently assume `1000`.
2. Change `config.toml` and example config docs to `100`.
3. Update usage docs and changelog references to the new default.

## TDD Strategy

- Update application and CLI-related fixtures first.
- Apply the minimal config and doc changes needed after the tests define the new expectation.

## Integration Test Coverage Plan

- Existing application tests cover the default list and search limit paths.

## Risks

- Only implicit limit behavior should change; explicit `--limit` must remain unchanged.
