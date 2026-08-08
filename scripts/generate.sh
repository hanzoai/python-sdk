#!/usr/bin/env bash
# Regenerate pkg/hanzoai/cloud/ from the Hanzo OpenAPI document.
#
# This is a CALL SITE, not a generator invocation. The invocation is logic and
# lives once, in hanzoai/openapi `generate.py`; every per-language knob —
# generator, library, package name — is data in `sdks.yaml` beside it. Nothing
# about how this client is produced is written down in this repo, so there is
# nothing here that can drift on its own. It is the same eight lines java-sdk
# and kotlin-sdk already run, and deliberately not a second driver: the old
# scripts/generate.sh here WAS one, it did `rm -rf pkg/hanzoai`, and it was
# deleted for that reason. This one cannot — `generate.py` owns exactly the one
# `take` path sdks.yaml names, `hanzoai/cloud -> pkg/hanzoai/cloud`.
#
#   ./scripts/generate.sh            # regenerate in place
#   ./scripts/generate.sh --check    # non-zero if the committed client drifted
#
# THE GENERATOR IS A TOOL; THE DOCUMENT IS AN ARGUMENT. They had one name here
# and it broke the lane. `SPEC_REF` is the ref of the DOCUMENT — hanzoai/ci's
# client lane exports a hanzoai/cloud sha or v-tag — and it was also handed to
# `git clone --branch` on hanzoai/openapi, which is a different repository and
# has never had a ref by that name. So every CI regeneration died at the clone,
# and by hand it worked only because SPEC_REF defaulted to `main` and both repos
# happen to have one. The generator is cloned at its own default branch now, and
# the document reaches the driver as a value.
#
# Point OPENAPI at a checkout you already have to skip the clone entirely.
#
# Requires: python3 (+pyyaml), java 11+, git.
set -euo pipefail
cd "$(dirname "$0")/.."

OPENAPI="${OPENAPI:-}"

if [ -z "$OPENAPI" ]; then
  OPENAPI="$(mktemp -d "${TMPDIR:-/tmp}/hanzo-openapi.XXXXXX")"
  trap 'rm -rf "$OPENAPI"' EXIT
  git clone --depth 1 -q https://git.hanzo.ai/hanzoai/openapi "$OPENAPI"
fi

# hanzoai/ci's client lane fetches the release document and exports SPEC, so it
# arrives by value, already digest-checked. Without it the driver reads this
# tree's own .spec-lock and fetches the same bytes from git.hanzo.ai, so a hand
# run and a CI run project the same document rather than whatever main is today.
if [ -n "${SPEC:-}" ]; then set -- --spec "$SPEC" "$@"; fi

exec python3 "$OPENAPI/generate.py" python --repo "$PWD" "$@"
