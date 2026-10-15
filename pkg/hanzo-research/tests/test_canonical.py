"""The canonical bytes and digests are the Rust crate's, read from tests/vectors/rust.json."""

from __future__ import annotations

import os
import json
import math

import pytest
from hanzo_research import Run, Measure, canonical

VECTORS = json.load(open(os.path.join(os.path.dirname(__file__), "vectors", "rust.json"), encoding="utf-8"))


@pytest.mark.parametrize("v", VECTORS["vectors"], ids=lambda v: v["name"])
def test_bytes_and_digest_equal_the_crates(v):
    assert canonical.canonicalize(v["value"]).decode() == v["canonical"]
    assert canonical.digest(v["value"]) == v["digest"]


def test_a_run_digests_as_the_crate_digests_it():
    rec = VECTORS["records"]["run"]
    run = Run.load(rec["value"])
    assert canonical.digest(run) == rec["digest"]
    assert canonical.digest(run.dump()) == rec["digest"]


def test_rfc8785_appendix_example():
    # RFC 8785 section 3.2.2's sample, built from code points so no escape is read twice
    bs, q = chr(92), chr(34)
    text = chr(0x20AC) + "$" + chr(15) + chr(10) + "A'B" + q + bs + bs + q + "/"
    value = {"numbers": [333333333.33333329, 1e30, 4.50, 2e-3, 1e-27], "string": text, "literals": [None, True, False]}
    want = (
        '{"literals":[null,true,false],"numbers":[333333333.3333333,1e+30,4.5,0.002,1e-27],"string":"'
        + chr(0x20AC)
        + "$"
        + bs
        + "u000f"
        + bs
        + "nA'B"
        + bs
        + q
        + bs * 4
        + bs
        + q
        + '/"}'
    )
    assert canonical.canonicalize(value).decode() == want


def test_numbers_past_the_crates_range_are_ecmascripts():
    # the crate writes these with Rust's Display (recorded in rust.json "apart"); RFC 8785 says:
    want = {
        1e21: "1e+21",
        1e-7: "1e-7",
        1.5e300: "1.5e+300",
        -0.0: "0",
        5e-324: "5e-324",
        9007199254740993: "9007199254740992",
        2**64 - 1: "18446744073709552000",
    }
    for x, s in want.items():
        assert canonical.number(x) == s
    crate = {str(a["value"]): a["canonical"] for a in VECTORS["apart"]}
    assert crate["1e+21"] == "1000000000000000000000"
    assert crate["-0.0"] == "-0"


def test_shortest_round_trip_digits():
    for x in (0.1, 0.8734610296764017, 123456.789, 1e-6, 1e20, 2.5e-5, 1 / 3, 100.0, -3.5):
        assert float(canonical.number(x)) == x


def test_what_has_no_json_form_is_refused():
    for bad in (math.nan, math.inf, -math.inf):
        with pytest.raises(ValueError):
            canonical.canonicalize({"x": bad})
    with pytest.raises(ValueError):
        canonical.canonicalize("\ud800")
    with pytest.raises(TypeError):
        canonical.canonicalize({1: "x"})
    with pytest.raises(TypeError):
        canonical.canonicalize({"x": object()})
    assert canonical.canonicalize([True, False, None]) == b"[true,false,null]"


def test_a_dataclass_reads_as_its_fields():
    m = Measure("all", "f1", 0.5, n=3)
    assert canonical.canonicalize(m) == canonical.canonicalize(m.dump())
    assert (
        canonical.canonicalize(m) == b'{"category":"all","hi":null,"lo":null,"metric":"f1","n":3,"of":null,"value":0.5}'
    )
