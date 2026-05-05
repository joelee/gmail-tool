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

python_wheel_tags = [
    "cp314-cp314",
    "cp314-abi3",
    "cp313-abi3",
    "cp312-abi3",
    "cp311-abi3",
    "cp310-abi3",
    "cp39-abi3",
    "cp38-abi3",
]

platform_wheel_tokens = {
    "macos_arm": ["macosx_11_0_arm64", "macosx_10_15_universal2", "macosx_10_9_universal2"],
    "macos_intel": ["macosx_10_13_x86_64", "macosx_10_15_universal2", "macosx_10_9_universal2"],
    "linux_arm": ["manylinux2014_aarch64", "manylinux_2_17_aarch64", "manylinux_2_28_aarch64"],
    "linux_intel": ["manylinux2014_x86_64", "manylinux_2_17_x86_64", "manylinux_2_28_x86_64"],
}


def filename_for(artifact: dict[str, str]) -> str:
    return artifact["url"].rsplit("/", 1)[1]


def _python_tag_rank(filename: str) -> int:
    for index, tag in enumerate(python_wheel_tags):
        if tag in filename:
            return index
    return len(python_wheel_tags)


def _render_resource(name: str, artifact: dict[str, str], *, indent: int) -> list[str]:
    prefix = "  " * indent
    inner_prefix = "  " * (indent + 1)
    sha256 = artifact["hash"].split(":", 1)[1]
    return [
        f'{prefix}resource "{name}" do',
        f'{inner_prefix}url "{artifact["url"]}"',
        f'{inner_prefix}sha256 "{sha256}"',
        f"{prefix}end",
        "",
    ]


def _select_pure_wheel(package: dict[str, object]) -> dict[str, str] | None:
    wheels = package.get("wheels", [])
    for suffix in ("-py3-none-any.whl", "-py2.py3-none-any.whl"):
        for wheel in wheels:
            if filename_for(wheel).endswith(suffix):
                return wheel
    return None


def _select_platform_wheel(package: dict[str, object], *, target: str) -> dict[str, str] | None:
    best: dict[str, str] | None = None
    best_key: tuple[int, int, str] | None = None
    for wheel in package.get("wheels", []):
        filename = filename_for(wheel)
        if "cp314t" in filename:
            continue
        for token_index, token in enumerate(platform_wheel_tokens[target]):
            if token in filename:
                candidate_key = (token_index, _python_tag_rank(filename), filename)
                if best_key is None or candidate_key < best_key:
                    best = wheel
                    best_key = candidate_key
                break
    return best


top_level_resources: list[tuple[str, dict[str, str]]] = []
macos_shared_resources: list[tuple[str, dict[str, str]]] = []
macos_arm_resources: list[tuple[str, dict[str, str]]] = []
macos_intel_resources: list[tuple[str, dict[str, str]]] = []
linux_shared_resources: list[tuple[str, dict[str, str]]] = []
linux_arm_resources: list[tuple[str, dict[str, str]]] = []
linux_intel_resources: list[tuple[str, dict[str, str]]] = []

for name in runtime_resources:
    package = packages[name]
    pure_wheel = _select_pure_wheel(package)
    if pure_wheel is not None:
        top_level_resources.append((name, pure_wheel))
        continue

    macos_arm = _select_platform_wheel(package, target="macos_arm")
    macos_intel = _select_platform_wheel(package, target="macos_intel")
    linux_arm = _select_platform_wheel(package, target="linux_arm")
    linux_intel = _select_platform_wheel(package, target="linux_intel")

    if any(artifact is None for artifact in [macos_arm, macos_intel, linux_arm, linux_intel]):
        raise SystemExit(f"Could not resolve Homebrew wheel resources for {name}")

    if macos_arm["url"] == macos_intel["url"]:
        macos_shared_resources.append((name, macos_arm))
    else:
        macos_arm_resources.append((name, macos_arm))
        macos_intel_resources.append((name, macos_intel))

    if linux_arm["url"] == linux_intel["url"]:
        linux_shared_resources.append((name, linux_arm))
    else:
        linux_arm_resources.append((name, linux_arm))
        linux_intel_resources.append((name, linux_intel))

resource_lines: list[str] = []
for name, artifact in top_level_resources:
    resource_lines.extend(_render_resource(name, artifact, indent=1))

if any([macos_shared_resources, macos_arm_resources, macos_intel_resources]):
    resource_lines.append("  on_macos do")
    for name, artifact in macos_shared_resources:
        resource_lines.extend(_render_resource(name, artifact, indent=2))
    if macos_arm_resources:
        resource_lines.append("    on_arm do")
        for name, artifact in macos_arm_resources:
            resource_lines.extend(_render_resource(name, artifact, indent=3))
        resource_lines.append("    end")
        resource_lines.append("")
    if macos_intel_resources:
        resource_lines.append("    on_intel do")
        for name, artifact in macos_intel_resources:
            resource_lines.extend(_render_resource(name, artifact, indent=3))
        resource_lines.append("    end")
        resource_lines.append("")
    resource_lines.append("  end")
    resource_lines.append("")

if any([linux_shared_resources, linux_arm_resources, linux_intel_resources]):
    resource_lines.append("  on_linux do")
    for name, artifact in linux_shared_resources:
        resource_lines.extend(_render_resource(name, artifact, indent=2))
    if linux_arm_resources:
        resource_lines.append("    on_arm do")
        for name, artifact in linux_arm_resources:
            resource_lines.extend(_render_resource(name, artifact, indent=3))
        resource_lines.append("    end")
        resource_lines.append("")
    if linux_intel_resources:
        resource_lines.append("    on_intel do")
        for name, artifact in linux_intel_resources:
            resource_lines.extend(_render_resource(name, artifact, indent=3))
        resource_lines.append("    end")
        resource_lines.append("")
    resource_lines.append("  end")
    resource_lines.append("")

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
