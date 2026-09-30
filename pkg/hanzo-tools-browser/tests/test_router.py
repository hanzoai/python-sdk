"""The seat on a real router, each node in its own process and the runtime
directory the test's own, so the router of whoever runs the tests is never
touched."""

import os
import subprocess
import sys
import textwrap

import pytest

zapd = pytest.importorskip("zapd")

SEAT = textwrap.dedent(
    """
    import sys, time
    from hanzo_tools.browser.zapd_consumer import get_consumer
    me = get_consumer()
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        found = me.resolve_browser("chrome", None)
        if found:
            break
        time.sleep(0.05)
    print(me.id)
    print(found)
    """
)

BROWSER = textwrap.dedent(
    """
    import sys, zapd
    zapd.embed()
    me = zapd.Node("browser/chrome-test")
    sys.stdin.read()
    """
)


def test_the_seat_is_an_mcp_node_that_finds_the_browser(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    if len(str(run / "zap" / "zapd.sock")) > 100:
        pytest.skip("the runtime path is too long for a unix socket here")
    env = dict(os.environ, XDG_RUNTIME_DIR=str(run), XDG_STATE_HOME=str(tmp_path / "state"), ZAP_LOG="zapd=warn")
    browser = subprocess.Popen([sys.executable, "-c", BROWSER], stdin=subprocess.PIPE, env=env)
    try:
        out = subprocess.run(
            [sys.executable, "-c", SEAT], env=env, capture_output=True, text=True, timeout=30
        ).stdout.split()
    finally:
        browser.stdin.close()
        browser.kill()
        browser.wait()
    host = zapd.host()
    assert out[0].startswith(f"mcp/{host}/hanzo-")
    assert out[1] == f"browser/{host}/chrome-test"
