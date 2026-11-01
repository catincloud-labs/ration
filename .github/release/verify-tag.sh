#!/usr/bin/env bash
# Verify that refs/tags/<tag> is a release tag this repository will build:
# an annotated tag object, carrying an SSH signature, made by a key the
# allowed-signers file names, under its own name.
#
#   bash .github/release/verify-tag.sh <tag> <allowed-signers-file>
#
# One script, run by both halves of .github/workflows/release.yml: the
# `signature` job runs it on the pushed tag, and the `refusal` job runs it on
# tags built wrong on purpose and asserts each exit code below. A check run
# only on the tag would be a control observed only to pass.
#
# Each refusal has its own exit code, so an arm of the refusal job that expects
# one refusal cannot be satisfied by another:
#
#   0  verified
#   2  the allowed-signers file is missing or names no key, so nothing could
#      have verified; read as blind, never as "no signer matched"
#   3  refs/tags/<tag> is absent, or is not a tag object (a lightweight tag)
#   4  the tag object carries no SSH signature (unsigned, or signed by gpg)
#   5  git verify-tag refused the signature (a key the file does not name,
#      or a signature that does not cover the object)
#   6  the signed tag object names another tag: a signature moved to this ref
#
# Usage errors exit 64.

set -u

if [ "$#" -ne 2 ]; then
  echo "usage: verify-tag.sh <tag> <allowed-signers-file>" >&2
  exit 64
fi

TAG="$1"
REF="refs/tags/${TAG}"

# Absolute, because git resolves a relative gpg.ssh.allowedSignersFile against
# wherever it happens to run.
if [ ! -f "$2" ]; then
  echo "::error::Allowed-signers file $2 does not exist, so no tag could verify against it."
  exit 2
fi
SIGNERS="$(cd "$(dirname "$2")" && pwd)/$(basename "$2")"
if ! grep -q -v -E '^[[:space:]]*(#|$)' "$SIGNERS"; then
  echo "::error::Allowed-signers file $SIGNERS names no key, so no tag could verify against it."
  exit 2
fi

TYPE="$(git cat-file -t "$REF" 2>/dev/null || echo missing)"
case "$TYPE" in
  tag) ;;
  missing)
    echo "::error::${REF} is not in this clone, so there is nothing to verify."
    exit 3 ;;
  *)
    echo "::error::${REF} is a ${TYPE}, not a tag object, so there is no signature to read. A lightweight tag is cut again with git tag -s."
    exit 3 ;;
esac

# A classifier, not the gate: it names the unsigned case and keeps a gpg
# signature, which nothing here trusts, from reaching gpg's keyring. A message
# that merely contains this line still has to pass verify-tag below.
if ! git cat-file tag "$REF" | grep -q -x -e '-----BEGIN SSH SIGNATURE-----'; then
  echo "::error::${TAG} carries no SSH signature. Delete it and cut it again with git tag -s."
  exit 4
fi

if ! git -c gpg.ssh.allowedSignersFile="$SIGNERS" verify-tag "$REF"; then
  echo "::error::${TAG} is signed by a key ${SIGNERS} does not name, or its signature does not cover it."
  exit 5
fi

# verify-tag checks the signature over the tag object, and the object's name
# is written inside it. Nothing compares that name with the ref unless this
# does, so a signed tag for one version pushed under another would pass.
NAMED="$(git for-each-ref --format='%(tag)' "$REF")"
if [ "$NAMED" != "$TAG" ]; then
  echo "::error::The signed tag object at ${REF} names itself '${NAMED}': a signature made for another tag and moved here."
  exit 6
fi

echo "OK - ${TAG} is a tag object signed by a key ${SIGNERS} names."
