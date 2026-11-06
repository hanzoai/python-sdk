"""Regression tests for background-process lifecycle tracking.

Previously, once an auto-backgrounded process exited, its tracking record
was deleted. Every later ``exec`` lookup for that process - ``wait``,
``logs``, ``ps`` (by proc_id) and ``kill`` - raised ``NotFoundError`` even
though the process had completed normally and its captured output existed
in the log file.
"""

import os
import types
import asyncio

import pytest
from hanzo_tools.shell.exec_tool import ExecTool
from hanzo_tools.shell.base_process import ProcessManager, AutoBackgroundExecutor


def _fake_process(pid: int = 4242, returncode=None):
    return types.SimpleNamespace(pid=pid, returncode=returncode)


@pytest.fixture
def manager():
    """The singleton ProcessManager with isolated class-level state."""
    pm = ProcessManager()
    pm._processes.clear()
    pm._logs.clear()
    pm._completed.clear()
    yield pm
    pm._processes.clear()
    pm._logs.clear()
    pm._completed.clear()


@pytest.fixture
def no_fast_tests(monkeypatch):
    """The fast test path bypasses process tracking entirely."""
    monkeypatch.delenv("HANZO_MCP_FAST_TESTS", raising=False)


def test_mark_completed_retains_record(manager):
    manager.add_process("p1", _fake_process(returncode=0), "/tmp/p1.log")
    manager.mark_completed("p1", 0)

    info = manager.get_process_info("p1")
    assert info is not None
    assert info["running"] is False
    assert info["return_code"] == 0
    assert info["log_file"] == "/tmp/p1.log"


def test_list_processes_keeps_completed_queryable(manager):
    manager.add_process("p2", _fake_process(returncode=3), "/tmp/p2.log")

    listed = manager.list_processes()
    assert listed["p2"]["running"] is False
    assert listed["p2"]["return_code"] == 3

    # Still queryable after the listing reported it once.
    info = manager.get_process_info("p2")
    assert info is not None
    assert info["return_code"] == 3
    assert info["log_file"] == "/tmp/p2.log"


def test_completed_registry_is_bounded(manager):
    for i in range(ProcessManager.MAX_COMPLETED_RECORDS + 10):
        pid = f"old-{i}"
        manager.add_process(pid, _fake_process(pid=i, returncode=0), None)
        manager.mark_completed(pid, 0)

    assert len(manager._completed) == ProcessManager.MAX_COMPLETED_RECORDS
    assert manager.get_process_info("old-0") is None  # evicted
    assert manager.get_process_info("old-109") is not None


def test_unknown_process_returns_none(manager):
    assert manager.get_process_info("never-tracked") is None


@pytest.mark.asyncio
async def test_background_process_queryable_after_exit(manager, no_fast_tests):
    executor = AutoBackgroundExecutor(manager)
    output, was_bg, proc_id = await executor.execute_with_auto_background(
        ["sh", "-c", "echo hello; sleep 1"],
        tool_name="exec",
        timeout=0.05,
    )
    assert was_bg and proc_id

    await asyncio.sleep(2.0)  # let the background reader observe the exit

    info = manager.get_process_info(proc_id)
    assert info is not None, "completed background process vanished"
    assert info["running"] is False
    assert info["return_code"] == 0

    log_file = info["log_file"]
    assert log_file and os.path.exists(log_file)
    with open(log_file) as f:
        contents = f.read()
    assert "hello" in contents
    assert "exit code 0" in contents


@pytest.mark.asyncio
async def test_exec_wait_logs_ps_after_completion(manager, no_fast_tests):
    """The exec tool keeps answering for a completed background process."""
    tool = ExecTool()
    executor = AutoBackgroundExecutor(tool.process_manager)
    _, was_bg, proc_id = await executor.execute_with_auto_background(
        ["sh", "-c", "echo done-output; sleep 1"],
        tool_name="exec",
        timeout=0.05,
    )
    assert was_bg and proc_id

    await asyncio.sleep(2.0)

    # wait: returns the completed result instead of NOT_FOUND
    waited = await tool.call(None, action="wait", proc_id=proc_id, timeout_ms=5000)
    assert waited["ok"] is True, waited
    assert waited["data"]["status"] == "completed"
    assert waited["data"]["exit_code"] == 0
    assert "done-output" in waited["data"]["output"]

    # logs: captured output stays reachable
    logs = await tool.call(None, action="logs", proc_id=proc_id)
    assert logs["ok"] is True, logs
    assert "done-output" in logs["data"]["output"]
    assert logs["data"]["exit_code"] == 0
    assert logs["data"]["running"] is False

    # ps by proc_id: still listed with its exit code
    ps = await tool.call(None, action="ps", proc_id=proc_id)
    assert ps["ok"] is True, ps
    assert ps["data"]["total"] == 1
    assert ps["data"]["processes"][0]["exit_code"] == 0
    assert ps["data"]["processes"][0]["running"] is False

    # kill: reports already-terminated instead of NOT_FOUND
    killed = await tool.call(None, action="kill", proc_id=proc_id)
    assert killed["ok"] is True, killed
    assert killed["data"]["killed"] is False
    assert killed["data"]["exit_code"] == 0

    # genuinely unknown IDs still raise NOT_FOUND
    missing = await tool.call(None, action="wait", proc_id="nope", timeout_ms=1000)
    assert missing["ok"] is False
    assert missing["error"]["code"] == "NOT_FOUND"
