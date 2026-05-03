# Search Command Plan

## Goals

- Add `gmail-tool search <search arguments>` using raw Gmail query syntax.
- Reuse the same message header output model as `gmail-tool label <LABEL> list`.
- Support plain text, JSON, and CSV output for search results.

## Design Plan

1. Add a Gmail gateway method for message-header search without label filtering.
2. Add an application method that combines raw Gmail query text with existing global filters.
3. Add a `search` CLI command that accepts trailing raw query tokens.
4. Reuse existing list formatting and `--limit` behavior.
5. Update usage docs with examples.

## TDD Strategy

- Add CLI tests first for text, JSON, and CSV output.
- Add an application test to verify the raw query and global filters are combined correctly.
- Implement the minimal gateway and CLI changes needed to satisfy the tests.

## Integration Test Coverage Plan

- Application-level tests will verify the combined query string and default limit handling.
- Live Gmail tests can continue to validate the Gmail transport independently.

## Risks

- Raw query tokens must preserve spaces when forwarded to Gmail.
- Combining raw query text with global filters should be deterministic and avoid extra whitespace.
