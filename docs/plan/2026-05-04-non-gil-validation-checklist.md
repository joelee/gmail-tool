# Non-GIL 3.13t And 3.14t Validation Checklist

## Goal

Validate `gmail-tool` against free-threaded CPython builds for the next unreleased target, focusing on Python `3.13t` and `3.14t`.

## Current Assessment

- The project code is low-risk for free-threaded CPython because it is mostly pure Python and uses a synchronous CLI flow.
- The largest risk is dependency installation and runtime behavior under `cp313t` and `cp314t`, not the application logic itself.
- Current CI and publish workflows only install Python `3.12`, so free-threaded support is not yet tested or claimed.

## Validation Checklist

### 1. Install interpreters

Use `uv` managed Python installs for both free-threaded targets.

```bash
uv python install 3.13t
uv python install 3.14t
```

Confirm the interpreter build is free-threaded:

```bash
uv run --python 3.13t python -c "import sys, sysconfig; print(sys.version); print(sysconfig.get_config_var('Py_GIL_DISABLED')); print(sysconfig.get_config_var('SOABI'))"
uv run --python 3.14t python -c "import sys, sysconfig; print(sys.version); print(sysconfig.get_config_var('Py_GIL_DISABLED')); print(sysconfig.get_config_var('SOABI'))"
```

Expected:

- `Py_GIL_DISABLED` prints `1`
- `SOABI` includes `t`

### 2. Verify dependency resolution and installation

Check that the environment can resolve and install the project cleanly on both interpreters.

```bash
uv sync --dev --python 3.13t
uv sync --dev --python 3.14t
```

If installation fails, capture which package failed and whether it failed due to:

- missing `cp313t` / `cp314t` wheels
- source build failure
- unsupported metadata markers

### 3. Import smoke tests

Run a direct import check for the main runtime stack:

```bash
uv run --python 3.13t python -c "import gmail_tool, googleapiclient, google.auth, google_auth_oauthlib, typer, click"
uv run --python 3.14t python -c "import gmail_tool, googleapiclient, google.auth, google_auth_oauthlib, typer, click"
```

Run a native-risk import check as well:

```bash
uv run --python 3.13t python -c "import cryptography, cffi, google.protobuf"
uv run --python 3.14t python -c "import cryptography, cffi, google.protobuf"
```

### 4. Run test suite

Run focused tests first:

```bash
uv run --python 3.13t pytest tests/unit/test_actions.py tests/unit/test_cli.py tests/unit/test_gmail.py tests/integration/test_application.py
uv run --python 3.14t pytest tests/unit/test_actions.py tests/unit/test_cli.py tests/unit/test_gmail.py tests/integration/test_application.py
```

Then run the full non-live suite:

```bash
uv run --python 3.13t pytest
uv run --python 3.14t pytest
```

Run pre-commit checks under at least one free-threaded interpreter:

```bash
uv run --python 3.14t pre-commit run --all-files
```

### 5. Run CLI smoke tests

These should work without Gmail credentials:

```bash
uv run --python 3.13t gmail-tool --version
uv run --python 3.13t gmail-tool --help
uv run --python 3.13t gmail-tool auth --help
uv run --python 3.13t gmail-tool message --help
uv run --python 3.13t gmail-tool search --list-actions
uv run --python 3.13t gmail-tool search --help-action backup

uv run --python 3.14t gmail-tool --version
uv run --python 3.14t gmail-tool --help
uv run --python 3.14t gmail-tool auth --help
uv run --python 3.14t gmail-tool message --help
uv run --python 3.14t gmail-tool search --list-actions
uv run --python 3.14t gmail-tool search --help-action backup
```

### 6. Run optional credentialed smoke tests

Only if local Gmail credentials are intentionally configured:

```bash
uv run --python 3.13t gmail-tool auth paths
uv run --python 3.13t gmail-tool auth check

uv run --python 3.14t gmail-tool auth paths
uv run --python 3.14t gmail-tool auth check
```

If OAuth is configured with mutation scopes, also verify one safe mutating path on test mail only.

### 7. Update project support metadata if green

If both interpreters pass installation and test validation:

- add CI jobs for `3.13t` and `3.14t`
- update README support text
- add Python classifiers if appropriate
- add a changelog entry for free-threaded validation/support
- keep the repository guidance aligned by requiring future dependency additions to check non-GIL compatibility first

## Dependency Wheel Review

Review based on the current resolved lockfile (`uv.lock`) and whether a package is pure Python or shows explicit free-threaded wheel tags.

### Runtime dependencies

- `google-api-python-client`: pure Python wheel (`py3-none-any`), low risk.
- `google-api-core`: pure Python wheel (`py3-none-any`), low risk.
- `google-auth`: pure Python wheel (`py3-none-any`), low risk.
- `google-auth-httplib2`: pure Python wheel (`py3-none-any`), low risk.
- `google-auth-oauthlib`: pure Python wheel (`py3-none-any`), low risk.
- `requests`: pure Python wheel (`py3-none-any`), low risk.
- `requests-oauthlib`: pure Python wheel (`py2.py3-none-any`), low risk.
- `oauthlib`: pure Python wheel (`py3-none-any`), low risk.
- `httplib2`: pure Python wheel (`py3-none-any`), low risk.
- `python-dotenv`: pure Python wheel (`py3-none-any`), low risk.
- `typer`: pure Python wheel (`py3-none-any`), low risk.
- `click`: pure Python wheel (`py3-none-any`), low risk.
- `rich`: pure Python wheel (`py3-none-any`), low risk.
- `protobuf`: currently resolved as `py3-none-any`, likely low install risk in this environment, but still verify import/runtime behavior.
- `googleapis-common-protos`: pure Python wheel (`py3-none-any`), low risk.
- `proto-plus`: pure Python wheel (`py3-none-any`), low risk.
- `uritemplate`: pure Python wheel (`py3-none-any`), low risk.
- `certifi`: pure Python wheel (`py3-none-any`), low risk.
- `charset-normalizer`: explicit `cp314t` wheels present in lockfile, good signal for `3.14t`; still validate `3.13t` install path during sync.
- `idna`: pure Python wheel (`py3-none-any`), low risk.
- `urllib3`: pure Python wheel (`py3-none-any`), low risk.

### Native-risk transitive runtime dependencies

- `cryptography`: explicit `cp314t` wheels present in lockfile, good signal for `3.14t`; `3.13t` should be validated directly during sync/import.
- `cffi`: explicit `cp314t` wheels present in lockfile, good signal for `3.14t`; `3.13t` should be validated directly during sync/import.
- `pycparser`: pure Python wheel (`py3-none-any`), low risk.

### Dev dependencies affecting CI validation

- `coverage`: explicit `cp313t` and `cp314t` wheels present in lockfile, strong signal for both targets.
- `pytest`, `pytest-cov`, `pluggy`, `iniconfig`, `packaging`: pure Python wheels, low risk.
- `pre-commit`, `virtualenv`, `identify`, `cfgv`, `nodeenv`, `platformdirs`, `distlib`, `filelock`, `python-discovery`: pure Python wheels, low risk.
- `pyyaml`: explicit `cp314t` wheels present in lockfile, good signal for `3.14t`; validate `3.13t` during sync.
- `ruff`: no wheel evidence was established from the current spot check, so this remains an explicit validation item for the free-threaded pre-commit path.

## Open Risks To Resolve

- `3.13t` wheel coverage was not confirmed from the current lockfile scan for every native package.
- `ruff` still needs an actual free-threaded install/run check.
- CI does not yet exercise free-threaded builds.
- The project does not yet declare free-threaded support in packaging metadata or docs.

## Exit Criteria

The project can be called "validated on non-GIL Python" when all of the following are true:

- `uv sync --dev --python 3.13t` passes
- `uv sync --dev --python 3.14t` passes
- focused tests pass on both
- full non-live `pytest` passes on both
- credential-free CLI smoke tests pass on both
- pre-commit passes on at least one free-threaded target
- CI is updated to run at least one free-threaded job
