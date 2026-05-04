# Label Mutation Name Option

## Goal

Replace label mutation action syntax from `label-add:<label_name>` and `label-remove:<label_name>` with `label-add --name <label_name>` and `label-remove --name <label_name>`.

## Scope

- Update CLI parsing for `search` and `label`.
- Require `--name` for `label-add` and `label-remove`.
- Reject `--name` for non-label-mutation actions.
- Update action registry listing and help text.
- Update tests and usage documentation.

## Verification

- Run focused unit tests for CLI and action registry behavior.
- Run focused integration tests for application-level label mutation behavior.
