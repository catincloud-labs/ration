#!/usr/bin/env bash
# Check that <tag> is named for the version its own commit's pyproject.toml
# carries: exactly "v" followed by [project].version, read with a TOML parser
# from the tagged commit, never from the working tree.
#
#   bash .github/release/check-version.sh <tag>
#
# One script, run by both halves of .github/workflows/release.yml, the same way
# verify-tag.sh is: the `signature` job's gate is a single call to it on the
# pushed tag, and the `refusal` job runs it on tags and commits built wrong on
# purpose and asserts each exit code below. It is also the check to run by
# hand, before pushing a tag or after fetching one.
#
# Each refusal has its own exit code, so an arm of the refusal job that expects
# one refusal cannot be satisfied by another:
#
#   0  the tag is v<version>
#   3  refs/tags/<tag> is absent, or names nothing that peels to a commit
#   4  the tagged commit has no pyproject.toml, or one that names no
#      [project].version, so there is no version to compare; read as blind,
#      never as a match or a mismatch
#   5  the tag's name is not v<version>
#
# Usage errors, and a machine with no Python to parse with, exit 64.

set -u

if [ "$#" -ne 1 ]; then
  echo "usage: check-version.sh <tag>" >&2
  exit 64
fi

TAG="$1"
REF="refs/tags/${TAG}"

COMMIT="$(git rev-parse --verify --quiet "${REF}^{commit}")"
if [ -z "$COMMIT" ]; then
  echo "::error::${REF} is not in this clone, or names no commit, so there is no version to read."
  exit 3
fi

# python3 on the runner; python where only that name exists. The program comes
# from -c and only the file arrives on standard input.
PY="$(command -v python3 || command -v python)"
if [ -z "$PY" ]; then
  echo "::error::No python3 or python on PATH, so pyproject.toml cannot be parsed." >&2
  exit 64
fi

# A rev:path argument, so path conversion is off for this one command.
VERSION="$(MSYS_NO_PATHCONV=1 git show "${COMMIT}:pyproject.toml" 2>/dev/null \
  | "$PY" -c '
import sys, tomllib
try:
    version = tomllib.loads(sys.stdin.buffer.read().decode("utf-8"))["project"]["version"]
except (tomllib.TOMLDecodeError, KeyError, TypeError, UnicodeDecodeError):
    sys.exit(1)
if not isinstance(version, str) or not version:
    sys.exit(1)
print(version)
')"
if [ -z "$VERSION" ]; then
  echo "::error::The commit ${COMMIT} that ${TAG} names has no pyproject.toml carrying [project].version, so there is nothing to compare its name with."
  exit 4
fi

if [ "$TAG" != "v${VERSION}" ]; then
  echo "::error::${TAG} names the commit ${COMMIT}, whose pyproject.toml says version ${VERSION}: the tag for it is v${VERSION}. Delete the tag, then cut v${VERSION} or bump pyproject.toml first."
  exit 5
fi

echo "OK - ${TAG} is v followed by the version pyproject.toml carries at ${COMMIT}."
