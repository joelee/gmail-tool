# Homebrew Packaging

`gmail-tool` is distributed to Homebrew from the sibling tap in `../homebrew-oss/`.

## Formula Source

- Formula path: `../homebrew-oss/Formula/gmail-tool.rb`
- Published artifact source: PyPI sdist for the matching `gmail-tool` release

## Update Flow

After a PyPI release is live:

1. Refresh the formula from the published package metadata:

```bash
scripts/update-homebrew-formula.sh vX.Y.Z
```

2. Review the generated formula in `../homebrew-oss/Formula/gmail-tool.rb`.
3. Validate on macOS:

```bash
brew install --build-from-source joelee/oss/gmail-tool
brew test joelee/oss/gmail-tool
brew audit --strict joelee/oss/gmail-tool
```

The helper script reads the published PyPI sdist URL and checksum and regenerates the Python resource blocks from `uv.lock`.

Set `HOMEBREW_FORMULA_PATH` to override the default output path. If it is unset, the script falls back to `../homebrew-oss/Formula/gmail-tool.rb`.
