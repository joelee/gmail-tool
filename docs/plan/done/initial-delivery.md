# Initial Delivery Plan

## Goals

- Build a `uv` managed Python CLI for Gmail label queries.
- Support label listing, per-label `count`, and per-label `list` actions.
- Make auth, actions, and filters extensible.
- Keep configuration driven through `config.toml` and secrets in `.env`.
- Establish a repeatable planning workflow with backlog tracking and archival of completed plans.

## Design Plan

1. Define project skeleton, packaging, and repository standards.
2. Create a configuration loader that merges `config.toml` with environment variables.
3. Implement an auth strategy interface with OAuth desktop and service-account providers.
4. Implement a Gmail gateway wrapper around the Google Gmail API.
5. Implement filter compilation into Gmail query syntax.
6. Implement an action registry for label actions.
7. Build CLI commands for label listing and label actions.
8. Add unit tests for config, filters, registry, and CLI behavior.
9. Add integration-style tests around the Gmail service boundary using fakes.
10. Add CI, pre-commit, and Docker packaging.

## TDD Strategy

- Start with tests for filter query generation and action dispatch.
- Add tests for config validation and auth provider selection.
- Add CLI tests using Typer's test runner.
- Add integration-style tests using mocked Gmail service responses.

## Integration Test Coverage Plan

- Verify label listing through a fake Gmail client.
- Verify `count` action calls the message listing path with compiled filters.
- Verify `list` action transforms message payload headers into CLI output rows.
- Verify auth provider construction from configuration.

## Risks

- Service account auth only works for Workspace with delegation.
- Gmail query semantics are server-defined; tests should validate generated query strings, not undocumented API behavior.

## Plan Lifecycle

- Store backlog items in `docs/plan/backlog.md`.
- Create new feature plans as timestamped files in `docs/plan/`.
- Move completed feature plans into `docs/plan/done/`.
