# Global List Actions With Descriptions Plan

## Goals

- Allow both `gmail-tool label --list-actions` and `gmail-tool search --list-actions`.
- Print each supported action with a short one-line description.
- Keep action listing local so it does not require Gmail authentication.

## Design Plan

1. Extend the action registry to expose action metadata instead of just names.
2. Add a small CLI formatter for action listings.
3. Support `--list-actions` on `search` and reuse the same output path for `label`.
4. Keep normal action execution unchanged.
5. Update docs and changelog.

## TDD Strategy

- Add tests first for registry metadata and CLI output from both commands.
- Implement the minimal registry and CLI changes needed to satisfy those tests.

## Integration Test Coverage Plan

- This is local CLI behavior and registry metadata, so unit tests are sufficient.

## Risks

- `search --list-actions` must bypass the normal requirement for a search query.
- The description format should stay stable and easy to read.
