# Live Gmail Integration Tests Plan

## Goals

- Add integration tests that verify the application can authenticate against Gmail and read basic mailbox metadata.
- Keep live Gmail tests safe and opt-in so default CI and local test runs remain stable.
- Reuse the existing configuration and auth stack instead of adding one-off test wiring.

## Design Plan

1. Add a small live-test helper that loads the standard project settings from `config.toml` and `.env`.
2. Gate live tests behind an explicit environment variable such as `ENABLE_LIVE_GMAIL_TESTS=true`.
3. Require credential files to exist before running live tests.
4. Verify at least label listing against the real Gmail API.
5. Verify read-only message access with a lightweight label count query.
6. Document how to run the live tests and what prerequisites are required.

## TDD Strategy

- Add integration tests first with skip guards for missing credentials or disabled live mode.
- Implement any missing test helper functions after the tests define the desired behavior.

## Integration Test Coverage Plan

- Verify auth provider creation from real local settings.
- Verify Gmail label listing succeeds against the real API.
- Verify counting messages for a known system label such as `INBOX` returns a non-negative integer.

## Risks

- OAuth may require an interactive browser flow the first time if no refresh token file exists.
- Mailbox contents vary across accounts, so assertions should validate types and access, not exact counts.
- These tests must never run by default in CI without explicitly provisioned credentials.
