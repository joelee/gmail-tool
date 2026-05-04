#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
REPO_ROOT="$(readlink -f "$SCRIPT_DIR/..")"
FORMULA_PATH_DEFAULT="${HOMEBREW_FORMULA_PATH:-$REPO_ROOT/../homebrew-oss/Formula/gmail-tool.rb}"

usage() {
  printf 'Usage: %s vX.Y.Z [formula-path]\n' "$0"
  printf 'Example: %s v0.2.2\n' "$0"
  printf 'Default formula path uses HOMEBREW_FORMULA_PATH or ../homebrew-oss/Formula/gmail-tool.rb\n'
}

fail() {
  printf 'Error: %s\n' "$1" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "required command not found: $1"
}

if [[ $# -lt 1 || $# -gt 2 ]]; then
  usage
  exit 1
fi

TAG="$1"
[[ "$TAG" == v* ]] || fail 'release tag must start with `v`, for example `v0.2.1`'
VERSION="${TAG#v}"
FORMULA_PATH="${2:-$FORMULA_PATH_DEFAULT}"

require_command uv
require_command python

[[ -f "$REPO_ROOT/uv.lock" ]] || fail "uv.lock not found in $REPO_ROOT"

METADATA_JSON="$(mktemp)"
trap 'rm -f "$METADATA_JSON"' EXIT

uv run --with requests python - <<'PY' "$VERSION" "$METADATA_JSON"
import json
import sys
from urllib.request import urlopen

version = sys.argv[1]
output_path = sys.argv[2]

with urlopen("https://pypi.org/pypi/gmail-tool/json") as response:
    data = json.load(response)

release = data["releases"].get(version)
if not release:
    raise SystemExit(f"PyPI release not found for gmail-tool {version}")

sdists = [item for item in release if item["packagetype"] == "sdist"]
if len(sdists) != 1:
    raise SystemExit(f"Expected exactly one sdist for gmail-tool {version}, found {len(sdists)}")

with open(output_path, "w", encoding="utf-8") as handle:
    json.dump(
        {
            "version": version,
            "url": sdists[0]["url"],
            "sha256": sdists[0]["digests"]["sha256"],
        },
        handle,
    )
PY

FORMULA_CONTENT="$(python - <<'PY' "$REPO_ROOT/uv.lock" "$METADATA_JSON"
import json
import sys
import tomllib
from pathlib import Path

lock_path = Path(sys.argv[1])
metadata_path = Path(sys.argv[2])

metadata = json.loads(metadata_path.read_text())
lock = tomllib.loads(lock_path.read_text())
packages = {package["name"]: package for package in lock["package"]}

runtime_resources = [
    "annotated-doc",
    "certifi",
    "cffi",
    "charset-normalizer",
    "click",
    "cryptography",
    "google-api-core",
    "google-api-python-client",
    "google-auth",
    "google-auth-httplib2",
    "google-auth-oauthlib",
    "googleapis-common-protos",
    "httplib2",
    "idna",
    "markdown-it-py",
    "mdurl",
    "oauthlib",
    "proto-plus",
    "protobuf",
    "pyasn1",
    "pyasn1-modules",
    "pycparser",
    "pygments",
    "pyparsing",
    "python-dotenv",
    "requests",
    "requests-oauthlib",
    "rich",
    "shellingham",
    "typer",
    "uritemplate",
    "urllib3",
]

resource_lines: list[str] = []
for name in runtime_resources:
    package = packages[name]
    sdist = package["sdist"]
    sha256 = sdist["hash"].split(":", 1)[1]
    resource_lines.extend(
        [
            f'  resource "{name}" do',
            f'    url "{sdist["url"]}"',
            f'    sha256 "{sha256}"',
            "  end",
            "",
        ]
    )

resource_block = "\n".join(resource_lines).rstrip()

print(
    f'''class GmailTool < Formula
  include Language::Python::Virtualenv

  desc "CLI for Gmail labels and message queries"
  homepage "https://github.com/joelee/gmail-tool"
  url "{metadata["url"]}"
  sha256 "{metadata["sha256"]}"
  license "MIT"

  depends_on "python@3.14"

{resource_block}

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match version.to_s, shell_output("#{{bin}}/gmail-tool --version")
    assert_match "backup", shell_output("#{{bin}}/gmail-tool search --list-actions")
  end
end'''
)
PY
)"

printf '%s\n' "$FORMULA_CONTENT" > "$FORMULA_PATH"

printf 'Updated %s for gmail-tool %s\n' "$FORMULA_PATH" "$VERSION"
