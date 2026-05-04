# Action Help Option Plan

## Goals

- Add `--help-action <action_name>` to `gmail-tool search` and `gmail-tool label`.
- Print action-specific help text without contacting Gmail.
- Include supported sub-options for the selected action.

## Approach

1. Extend the action registry with action help metadata for built-in and dynamic actions.
2. Add CLI handling that prints the selected action help and exits early.
3. Keep `--help-action` local and credential-free, similar to `--list-actions`.
4. Add tests for valid actions, dynamic actions, and unknown action names.
5. Update docs and changelog after implementation.
