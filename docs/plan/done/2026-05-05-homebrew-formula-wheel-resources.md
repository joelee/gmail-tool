## Goal

- Fix Homebrew formula generation so `gmail-tool` installs cleanly on macOS.
- Avoid source-build failures for native Python dependencies such as `cryptography`.

## Problem

- The formula helper currently emits PyPI sdists for every Python resource.
- Homebrew then installs native dependencies from source inside the formula virtualenv.
- On macOS with `python@3.14`, `cryptography` falls into a Rust/maturin build path and fails.

## Plan

1. Update the formula generator to prefer wheels over sdists.
2. Emit platform-specific wheel resources when a dependency is not pure-Python.
3. Regenerate the sibling Homebrew formula for the current release.
4. Update release docs to document the binary-wheel requirement and validation.
5. Verify the generated formula references wheel artifacts for native dependencies.
