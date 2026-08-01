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
# hanzoai/openapi is PRIVATE, so raw.githubusercontent.com 404s it and a clone
# needs credentials: SPEC_TOKEN, else GH_TOKEN, else GITHUB_TOKEN, else ssh.
# Point OPENAPI at a checkout you already have to skip the clone entirely.
#
# Requires: python3 (+pyyaml), java 11+, git.
set -euo pipefail
cd "$(dirname "$0")/.."

OPENAPI="${OPENAPI:-}"
SPEC_REPO="${SPEC_REPO:-hanzoai/openapi}"
SPEC_REF="${SPEC_REF:-main}"

if [ -z "$OPENAPI" ]; then
  OPENAPI="$(mktemp -d "${TMPDIR:-/tmp}/hanzo-openapi.XXXXXX")"
  trap 'rm -rf "$OPENAPI"' EXIT
  TOKEN="${SPEC_TOKEN:-${GH_TOKEN:-${GITHUB_TOKEN:-}}}"
  if [ -n "$TOKEN" ]; then
    echo "cloning private ${SPEC_REPO}@${SPEC_REF} with a token (raw.githubusercontent.com 404s private paths)"
    git clone --depth 1 --branch "$SPEC_REF" \
      "https://x-access-token:${TOKEN}@github.com/${SPEC_REPO}.git" "$OPENAPI" >/dev/null 2>&1
  else
    echo "cloning ${SPEC_REPO}@${SPEC_REF} over ssh; set SPEC_TOKEN/GH_TOKEN/GITHUB_TOKEN or OPENAPI to override"
    git clone --depth 1 --branch "$SPEC_REF" "git@github.com:${SPEC_REPO}.git" "$OPENAPI" >/dev/null
  fi
fi

# THE DOCUMENT AS AN ARGUMENT. hanzoai/ci's client: lane fetches openapi.yaml at
# the sha hanzoai/cloud just deployed and exports SPEC; the driver projects THAT
# rather than the checkout's own hanzo.yaml. With SPEC unset nothing changes —
# a maintainer regenerating by hand still gets the checkout's document.
if [ -n "${SPEC:-}" ]; then set -- --spec "$SPEC" "$@"; fi

exec python3 "$OPENAPI/generate.py" python --repo "$PWD" "$@"
