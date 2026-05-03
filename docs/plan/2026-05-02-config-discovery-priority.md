# Config Discovery Priority Plan

## Goals

- Discover `config.toml` using the requested priority order.
- Allow all CLI commands to use the same discovery behavior.
- Keep explicit `--config` as the highest-priority override.

## Design Plan

1. Add a config discovery helper in `config.py`.
2. Implement the requested priority order in one place.
3. Update `load_settings` to resolve through discovery when no path is passed.
4. Change CLI `--config` options to be optional rather than requiring a local default path.
5. Add unit tests for discovery order and explicit overrides.

## TDD Strategy

- Add config discovery tests first for each priority level.
- Implement the helper and then update the CLI option defaults.

## Integration Test Coverage Plan

- Config-loading tests cover the resolution logic directly.
- Existing CLI tests continue to verify command behavior with explicit and implicit config loading.

## Risks

- The project-directory fallback should continue to work for existing workflows.
- Discovery should fail clearly if no config file exists anywhere in the search path.
