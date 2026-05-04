# Coverage Improvements And Badge Automation Plan

## Goals

- Increase meaningful unit coverage in `gmail.py` and `auth.py`.
- Automatically refresh the checked-in coverage badge on `main`.
- Extend the README badge set for release and package visibility.

## Approach

1. Add focused unit tests for Gmail gateway request/response handling.
2. Add focused auth tests for refresh, token writes, and no-browser OAuth flow.
3. Keep production code changes minimal and only where tests expose rough edges.
4. Add a GitHub Actions workflow that updates `.github/badges/coverage.json` on `main`.
5. Add useful public badges to the README without cluttering the top of the page.
