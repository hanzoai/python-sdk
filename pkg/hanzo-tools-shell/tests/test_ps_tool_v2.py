
import pytest
import psutil
import os
import signal
from hanzo_tools.shell.ps_tool import ps_tool, PsTool

@pytest.mark.asyncio
async def test_ps_list():
    """Test listing processes."""
    # List by CPU
    result = await ps_tool.call(None, action="list", sort_by="cpu", limit=10)
    assert "PID" in result
    assert "COMMAND" in result
    assert len(result.splitlines()) > 2  # Header + separator + at least one process

    # List by Memory
    result_mem = await ps_tool.call(None, action="list", sort_by="memory", limit=10)
    assert "PID" in result_mem

@pytest.mark.asyncio
async def test_ps_get_self():
    """Test getting info for the current process."""
    my_pid = os.getpid()
    result = await ps_tool.call(None, action="get", pid=my_pid)
    assert f"PID: {my_pid}" in result
    assert "Status: running" in result or "Status: sleeping" in result

@pytest.mark.asyncio
async def test_ps_get_invalid():
    """Test getting info for non-existent process."""
    # Max PID is usually 32768 or 4194304, so 99999999 is likely safe
    result = await ps_tool.call(None, action="get", pid=99999999)
    assert "not found" in result

@pytest.mark.asyncio
async def test_ps_kill_error():
    """Test killing a non-existent process."""
    result = await ps_tool.call(None, action="kill", pid=99999999)
    assert "not found" in result

# Note: We don't test successful kill to avoid killing random processes or the test runner itself.
