"""The contract plane agrees with the other two languages, byte for byte.

The catalogue is one generated artifact (hanzoai/openapi `tools.py`) copied into
each language's package. These assertions are the same three in the TypeScript
and Rust suites, against the same digest, so "the three MCP lines agree" is a
test that fails rather than a claim someone repeats.
"""

import hashlib
import json

from hanzo_mcp import catalogue as cat

# The one catalogue's digest. Identical in @hanzo/mcp (schema/catalogue.json)
# and hanzo-mcp-core (catalogue.json). Bump ONLY by regenerating all three from
# the one generator — an edit here that is not a regeneration is the drift this
# file exists to catch.
DIGEST = "d6d49a17085a062bbbb2691bdc7edb3915048196b80fd1ac45408663c9d7b346"
COUNT = 2279


def test_digest():
    got = hashlib.sha256(cat.CATALOGUE.read_bytes()).hexdigest()
    assert got == DIGEST, (
        f"catalogue.json is not the generated artifact ({got}). "
        f"Regenerate every language: scripts/tools.sh"
    )


def test_count():
    assert len(cat.catalogue()) == COUNT
    assert json.loads(cat.CATALOGUE.read_text())["count"] == COUNT


def test_names_are_operation_ids():
    # Sorted, unique, and non-empty — a tool is addressed by this string.
    ns = cat.names()
    assert ns == sorted(ns)
    assert len(ns) == len(set(ns))
    assert all(n and not n.isspace() for n in ns)


def test_every_tool_is_callable_shaped():
    for t in cat.catalogue():
        assert t["name"]
        assert isinstance(t["description"], str)
        s = t["inputSchema"]
        assert s["type"] == "object"
        assert isinstance(s["properties"], dict)


def test_find():
    ns = cat.names()
    assert cat.find(ns[0])["name"] == ns[0]
    assert cat.find("nothing_serves_this_zzq9") is None
