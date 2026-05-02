# Architecture Overview

## Layers

- `cli.py`: command-line entrypoints and argument parsing
- `config.py`: application settings and environment/config file loading
- `auth.py`: auth provider interface and implementations
- `gmail.py`: Gmail API client wrapper
- `filters.py`: filter model and query compilation
- `actions/`: extensible action implementations and registry

## Extensibility

- Add new actions by implementing the action protocol and registering it in the action registry.
- Add new filters by extending the filter model and query compiler.
- Add new auth methods by implementing the auth provider interface.

## Test Strategy

- Unit tests cover pure logic and CLI dispatch.
- Integration-style tests cover service orchestration with fake Gmail API responses.
