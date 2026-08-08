#!/usr/bin/env bash
# Pull the tool catalogue from the ONE generator. No flags, no logic: the
# projection lives once, in hanzoai/openapi, and this file only says where this
# repo keeps its copy. A second generator here is the drift it exists to end.
set -euo pipefail
OPENAPI="${OPENAPI_DIR:-$(dirname "$0")/../../../../openapi}"
exec python3 "$OPENAPI/tools.py" --out "$(dirname "$0")/../hanzo_mcp/catalogue.json" "$@"
