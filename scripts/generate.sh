#!/usr/bin/env bash
# Regenerate the Hanzo Python client (`hanzoai`) from the unified OpenAPI spec.
#
# The ONE way: hanzoai/openapi `hanzo.yaml` is the single source of truth. The
# `hanzoai` package under pkg/ is generated from it with openapi-generator — no
# Stainless. Other pkg/hanzo-* packages are hand-written and untouched here.
#
#   ./scripts/generate.sh                 # pulls spec from hanzoai/openapi@main
#   SPEC=/path/to/hanzo.yaml ./scripts/generate.sh   # local spec override
#
# Requires: java 17+, curl.
set -euo pipefail
cd "$(dirname "$0")/.."

GENERATOR_VERSION="${GENERATOR_VERSION:-7.14.0}"
# hanzoai/openapi is private — fetch hanzo.yaml through the GitHub API with a
# token (SPEC_TOKEN). raw.githubusercontent.com only serves public repos (it
# 404s on a private repo). Local override still honored: SPEC=/path/to/hanzo.yaml.
SPEC_REPO="${SPEC_REPO:-hanzoai/openapi}"
SPEC_REF="${SPEC_REF:-main}"
SPEC="${SPEC:-}"
JAR="${JAR:-/tmp/openapi-generator-cli-${GENERATOR_VERSION}.jar}"

if [ -z "$SPEC" ]; then
  : "${SPEC_TOKEN:?SPEC_TOKEN required to read private $SPEC_REPO}"
  SPEC="$(mktemp)"
  curl -fsSL -H "Authorization: Bearer $SPEC_TOKEN" -H "Accept: application/vnd.github.raw" \
    "https://api.github.com/repos/$SPEC_REPO/contents/hanzo.yaml?ref=$SPEC_REF" -o "$SPEC"
fi
if [ ! -f "$JAR" ]; then
  curl -fsSL -o "$JAR" \
    "https://repo1.maven.org/maven2/org/openapitools/openapi-generator-cli/${GENERATOR_VERSION}/openapi-generator-cli-${GENERATOR_VERSION}.jar"
fi

OUT="$(mktemp -d)"
java -jar "$JAR" generate \
  -i "$SPEC" -g python \
  --additional-properties=packageName=hanzoai,projectName=hanzoai,library=urllib3 \
  --global-property=apiTests=false,modelTests=false,apiDocs=false,modelDocs=false \
  --git-user-id=hanzoai --git-repo-id=python-sdk \
  -o "$OUT"

# Only the package itself lives in this monorepo (pkg/hanzoai). The generated
# pyproject/setup/README/etc. are discarded — the repo root owns build config.
rm -rf pkg/hanzoai
cp -r "$OUT/hanzoai" pkg/hanzoai
echo "generated $(find pkg/hanzoai -name '*.py' | wc -l) python files into pkg/hanzoai"
