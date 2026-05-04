# Coverage Reporting And Badges Plan

## Goals

- Make test coverage easy to inspect in CI artifacts.
- Generate badge-friendly coverage data from the repository itself.
- Add README badges for version, CI status, and coverage.

## Approach

1. Produce machine-readable coverage output from the CI workflow.
2. Generate a small JSON badge file in the repository for coverage percentage.
3. Publish coverage artifacts from GitHub Actions.
4. Add README badges that point at GitHub Actions and the checked-in coverage badge JSON.

## Notes

- Prefer a GitHub-native path over a third-party coverage SaaS.
- Keep the implementation small and easy to update locally.
