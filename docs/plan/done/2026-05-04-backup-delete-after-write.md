# Backup Delete-After-Write Plan

## Goals

- Add `--delete` support to the `backup` action for both `search` and `label` commands.
- After a message is successfully written as `.eml`, move it to the Gmail Bin.
- Ask for confirmation before deleting messages, showing how many messages will be moved to Bin.
- Allow bypassing the confirmation prompt with `--force`.

## Approach

1. Extend backup action plumbing so backup runs can optionally delete successfully written messages.
2. Add a Gmail gateway operation that moves a message to Bin using the Gmail API.
3. Add a preview/count path for backup writes so the CLI can show an accurate delete confirmation count.
4. Add CLI validation so `--delete` and `--force` are only valid for the `backup` action.
5. Update tests first for the action layer, application layer, and CLI confirmation UX.
6. Update user-facing docs and changelog after the behavior is implemented.
