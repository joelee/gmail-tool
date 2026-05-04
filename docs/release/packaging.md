# Release Packaging

## PyPI

`gmail-tool` publishes Python packages from GitHub Actions using PyPI Trusted Publishing.

One-time PyPI setup:

1. Create the `gmail-tool` project on PyPI if it does not exist yet.
2. In PyPI project settings, add a trusted publisher for `joelee/gmail-tool`.
3. Use the `Publish` workflow and the `pypi` environment.

Release steps:

1. Bump the version in `pyproject.toml`.
2. Move `CHANGELOG.md` entries from `Unreleased` into a new `vX.Y.Z` section.
3. Add release notes at `docs/release/vX.Y.Z.md`.
4. Commit the release prep.
5. Tag the release as `vX.Y.Z`.
6. Push the branch and the tag.
7. Confirm the `Publish` workflow built and uploaded both the sdist and wheel to PyPI.

Manual verification:

```bash
uv build
```

## Homebrew

The Homebrew tap lives in `../homebrew-oss/` and should install `gmail-tool` from the published PyPI sdist, not from the GitHub source archive.

After the PyPI release is live:

1. Download the published sdist URL for `gmail-tool-X.Y.Z.tar.gz`.
2. Compute or copy its `sha256` from the published artifact.
3. Update `../homebrew-oss/Formula/gmail-tool.rb`.

```bash
scripts/update-homebrew-formula.sh vX.Y.Z
```

4. Refresh Python resource blocks so the formula matches the published package dependencies.
5. Validate on macOS:

```bash
brew install --build-from-source joelee/oss/gmail-tool
brew test joelee/oss/gmail-tool
brew audit --strict joelee/oss/gmail-tool
```

Homebrew formula tests must stay credential-free. Prefer `gmail-tool --version` or `gmail-tool --help` for formula verification.

`scripts/update-homebrew-formula.sh` writes to `HOMEBREW_FORMULA_PATH` when that environment variable is set. Otherwise it falls back to `../homebrew-oss/Formula/gmail-tool.rb`.
