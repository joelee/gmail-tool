# Auth Diagnostics Command Plan

## Goals

- Add a small CLI command to validate Gmail authentication and basic API reachability.
- Keep the command read-only and safe for repeated local use.
- Reuse existing config and application wiring so diagnostics follow the same code path as normal commands.

## Design Plan

1. Add a command such as `auth-check` to the CLI.
2. Load settings from the standard config path or `--config` override.
3. Build the application and issue a lightweight Gmail API read call.
4. Print a short success summary including auth mode and basic mailbox reachability details.
5. Add unit tests for the CLI output and dispatch behavior.

## TDD Strategy

- Add CLI tests first for a successful diagnostics run.
- Implement the minimal application method and CLI command to satisfy the tests.

## Integration Test Coverage Plan

- Existing live Gmail integration tests will indirectly validate the shared auth and Gmail access path.

## Risks

- Diagnostics should avoid exposing secrets or token contents in output.
- The command should not add extra API complexity beyond a single lightweight read operation.
