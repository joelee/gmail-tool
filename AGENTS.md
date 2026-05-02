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
- Move completed and implemented feature plans to `docs/plan/done/{timestamp}-{feature_name}.md`.
- Maintain `CHANGELOG.md` for user-visible changes.
- Keep test coverage above 60%.

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
