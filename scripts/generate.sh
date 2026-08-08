#!/usr/bin/env bash
# Regenerate pkg/hanzoai/cloud/ from the Hanzo Cloud API document.
#
# A CALL SITE, not a generator invocation. The invocation is logic and lives
# once, in `generate.py`; every per-language knob — generator, library, package
# name — is data in `sdks.yaml` beside it. Nothing about how this client is
# produced is written down here, so there is nothing here that can drift.
#
#   ./scripts/generate.sh            # regenerate in place
#   ./scripts/generate.sh --check    # non-zero if the committed client drifted
#
# BOTH INPUTS ARRIVE AS VALUES. $SPEC is the document, already fetched at a
# pinned ref and digest-checked; $OPENAPI is the checkout holding the driver.
# hanzoai/ci's client lane sets both, because it holds the one credential that
# reads this forge. This script used to clone the driver itself, anonymously,
# from a private repo — so every CI regeneration died at the clone with
# `could not read Username`. Set OPENAPI by hand to run it by hand.
#
# Requires: python3 (+pyyaml), java 11+.
set -euo pipefail
cd "$(dirname "$0")/.."

: "${OPENAPI:?the generator lives in hanzoai/openapi; hanzoai/ci's client lane sets OPENAPI, or point it at a checkout}"

if [ -n "${SPEC:-}" ]; then set -- --spec "$SPEC" "$@"; fi

exec python3 "$OPENAPI/generate.py" python --repo "$PWD" "$@"
