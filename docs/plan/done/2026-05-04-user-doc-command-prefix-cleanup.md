# User Doc Command Prefix Cleanup

## Goal

Update user-facing documentation so executable examples use `gmail-tool` instead of `uv run gmail-tool`.

## Scope

- Update markdown documentation examples intended for end users.
- Keep development and verification commands such as `uv run pytest` unchanged.
- Record the documentation cleanup in the changelog.

## Verification

- Grep markdown docs for `uv run gmail-tool` and confirm remaining matches are not user-facing examples.
