# PyPI And Homebrew Release Packaging Plan

## Goals

- Publish `gmail-tool` releases to PyPI.
- Publish a Homebrew formula for `gmail-tool` in `../homebrew-oss/`.
- Keep the release flow repeatable and low-friction for future versions.

## PyPI Plan

1. Confirm the package name `gmail-tool` remains available on PyPI.
2. Add packaging metadata improvements to `pyproject.toml`:
   - `homepage`
   - `repository`
   - `documentation`
   - `keywords`
   - `classifiers`
3. Add a GitHub Actions publish workflow that:
   - builds sdist and wheel
   - optionally publishes on version tags such as `vX.Y.Z`
4. Prefer PyPI Trusted Publishing from GitHub Actions over long-lived API tokens.
5. Document the release steps in repo docs.

## Homebrew Plan

1. Package `gmail-tool` in `../homebrew-oss/Formula/gmail-tool.rb`.
2. Prefer installing from the PyPI sdist tarball, not from the GitHub source archive, so the formula matches the published Python package.
3. Use Homebrew `virtualenv_install_with_resources` for dependency installation.
4. Generate resource blocks from the pinned published package dependencies.
5. Add a formula test that exercises `gmail-tool --version` or `gmail-tool --help` without requiring Gmail credentials.
6. Update the tap README and any release guidance docs for the new formula.

## Release Flow Recommendation

1. Prepare the upstream release in `gmail-tool`:
   - bump version
   - roll changelog
   - write release notes
2. Tag and push the release.
3. Publish to PyPI from GitHub Actions.
4. After PyPI artifacts are live, update `homebrew-oss`:
   - add or update `Formula/gmail-tool.rb`
   - point `url` and `sha256` at the published PyPI sdist
   - refresh Python resources
5. Validate on macOS:
   - `brew install --build-from-source joelee/oss/gmail-tool`
   - `brew test joelee/oss/gmail-tool`
   - `brew audit --strict joelee/oss/gmail-tool`

## Risks

- Homebrew Python formulas require explicit resource management for dependencies.
- Publishing from GitHub tags is simplest, but only if tag discipline is reliable.
- Gmail credentials should never be required for formula install or formula test.

## Notes

- The sibling tap `../homebrew-oss/` already has a working formula workflow that can be adapted for `gmail-tool`.
- Upstream packaging metadata, Trusted Publishing workflow, and release documentation were added in `v0.2.1` preparation.
- The Homebrew formula should be updated after the PyPI sdist is live so the formula can use the published artifact URL and checksum.
