# Search Cheat Sheet Plan

## Goals

- Add `gmail-tool search --cheat-sheet` to print a Gmail search operator cheat sheet.
- Save the same cheat sheet content in `docs/search-cheat-sheet.md`.
- Keep the feature static and local so it does not depend on network access.

## Design Plan

1. Add a single source of truth for the cheat sheet text in the CLI module.
2. Add `--cheat-sheet` to the `search` command and make it return before Gmail access.
3. Mirror the cheat sheet content into `docs/search-cheat-sheet.md`.
4. Link the new doc from the README and usage docs.

## TDD Strategy

- Add a CLI test first that verifies key operator examples appear in `search --cheat-sheet` output.
- Implement the minimal CLI branch and static text needed to satisfy the test.

## Integration Test Coverage Plan

- This feature is static documentation output, so unit-level CLI coverage is sufficient.

## Risks

- The CLI output and doc file can drift if they are maintained separately.
