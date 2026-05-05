# AGENTS

## Purpose

This repository contains a `uv` managed Python CLI for Gmail label exploration and message queries.

## Working Agreements

- Follow TDD for feature work: write or update tests before implementation changes where practical.
- Keep architecture extensible for new actions and filters.
- Keep configuration in `config.toml` and secrets in `.env`.
- Document feature planning in `docs/plan/*.md` before or alongside implementation.
- Maintain future tasks in `docs/plan/backlog.md`.
- Create new feature plans as timestamped files in `docs/plan/{timestamp}-{feature_name}.md`.
- Move completed and implemented feature plans to `docs/plan/done/{timestamp}-{feature_name}.md` immediately after the work is finished.
- Do not leave completed plan files in `docs/plan/`; only active work and `backlog.md` should remain there.
- When the repository is under git, use `git mv` to move completed plan files into `docs/plan/done/`.
- Record every new user-visible change under the `CHANGELOG.md` `Unreleased` section.
- Keep test coverage above 60%.
- Ensure every update is Ruff formatted before considering the work complete.
- When adding new packages, check whether they are compatible with the project's non-GIL Python support target and prefer dependencies with working free-threaded wheels or a validated source-build path.

## Release Workflow

- When asked to prepare a release, bump the package version in `pyproject.toml`.
- Roll the current `CHANGELOG.md` `Unreleased` entries into a versioned release section.
- Create release notes in `docs/release/vX.Y.Z.md`.
- Keep release notes focused on shipped changes, upgrade notes, and verification.
- If a `docs/release/` directory does not exist yet, create it as part of release preparation.

## Project Layout

- `src/gmail_tool/`: application package
- `tests/unit/`: fast unit tests
- `tests/integration/`: integration-style tests using fakes/mocks unless real credentials are explicitly configured
- `docs/plan/`: active plans, backlog, and delivery notes
- `docs/plan/done/`: completed feature plans
- `docs/`: project documentation including architecture and configuration docs

## Implementation Notes

- Prefer small, composable interfaces for Gmail auth, message actions, and query filters.
- Avoid baking transport details into CLI handlers.
- New actions should register through a central action registry.
- New filters should compile into Gmail search query fragments.
