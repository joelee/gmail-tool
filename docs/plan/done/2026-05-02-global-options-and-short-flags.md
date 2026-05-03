# Global Options And Short Flags Plan

## Goals

- Add global `--version` / `-V`.
- Add global `--verbose` / `-v` for extra debug output.
- Add short aliases:
  - `-c` for `--config`
  - `-f` for `--format`
  - `-l` for `--limit`
  - `-h` for `--help`

## Design Plan

1. Add an app callback for global option handling.
2. Add a small debug-output helper that writes to stderr when verbose mode is enabled.
3. Add short aliases to the existing command options.
4. Configure Typer help to support `-h` in addition to `--help`.
5. Update docs and examples.

## TDD Strategy

- Add CLI tests first for version output, verbose output, and the new short aliases.
- Implement the minimal callback and option alias changes needed to satisfy the tests.

## Integration Test Coverage Plan

- This feature is CLI behavior only, so unit-level CLI tests are sufficient.

## Risks

- Global options should not alter normal command output when not enabled.
- Verbose output should go to stderr so structured stdout remains usable.
