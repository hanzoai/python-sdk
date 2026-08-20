"""The worker half: pull work, hold the lease while it runs, settle it.

The worker POLLS. It never accepts a push, so it needs no inbound address and
runs behind NAT — the reason the claim endpoint exists.

What this does NOT do is keep its own copy of the engine's rules. There is no
client-side reap timer, no retry ladder and no duplicate-claim guard here: the
engine reaps expired leases before every claim, serializes claims per
namespace, and derives the lease from the activity's own heartbeat timeout. A
second opinion on any of that would be a second opinion that can disagree.
"""

from __future__ import annotations

import asyncio
import inspect
import os
import socket
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from .client import Tasks
from .errors import TasksError, Terminal
from .types import Activity

Handler = Callable[[Activity], Any | Awaitable[Any]]

# A fraction of the lease, so a heartbeat is missed twice before the claim is
# reaped. Heartbeating exactly at the lease boundary races the reaper.
HEARTBEAT_FRACTION = 3


def default_identity() -> str:
    """Who this worker is: host and pid, enough to find it in a history."""
    return f"{socket.gethostname()}/{os.getpid()}"


class Worker:
    """Polls one task queue and runs the handler registered for each type.

    Handlers may be async or plain functions. A plain function is run in a
    worker thread rather than inline — a blocking call on the event loop would
    stall the heartbeat, the lease would expire mid-run, and the engine would
    hand the same activity to somebody else while this one was still working
    on it.
    """

    def __init__(
        self,
        tasks: Tasks,
        *,
        task_queue: str = "default",
        identity: str = "",
        lease_seconds: int = 60,
        poll_interval: float = 1.0,
        on_error: Callable[[BaseException, Activity | None], None] | None = None,
    ) -> None:
        self.tasks = tasks
        self.task_queue = task_queue
        self.identity = identity or tasks.identity or default_identity()
        self.lease_seconds = lease_seconds
        self.poll_interval = poll_interval
        self.on_error = on_error
        self._handlers: dict[str, Handler] = {}

    # ── registration ────────────────────────────────────────────────────

    def handler(self, type: str) -> Callable[[Handler], Handler]:
        """Register the handler for one activity type, as a decorator."""

        def register(fn: Handler) -> Handler:
            self.register(type, fn)
            return fn

        return register

    def register(self, type: str, fn: Handler) -> None:
        self._handlers[type] = fn

    # ── the loop ────────────────────────────────────────────────────────

    async def run(self, *, stop: asyncio.Event | None = None) -> None:
        """Poll until ``stop`` is set, running whatever is claimed.

        Sleeps ``poll_interval`` only when the queue was empty, so a backlog
        drains at full speed.
        """
        while stop is None or not stop.is_set():
            try:
                worked = await self.step()
            except asyncio.CancelledError:
                raise
            except BaseException as exc:  # a poll failure must not end the loop
                self._report(exc, None)
                worked = False
            if not worked:
                if stop is None:
                    await asyncio.sleep(self.poll_interval)
                else:
                    # Wake immediately when asked to stop, rather than serving
                    # out the poll interval first.
                    try:
                        await asyncio.wait_for(stop.wait(), self.poll_interval)
                    except TimeoutError:
                        pass

    async def step(self) -> bool:
        """Claim one activity and run it. False when the queue was empty."""
        activity = await self.tasks.claim(
            task_queue=self.task_queue,
            identity=self.identity,
            lease_seconds=self.lease_seconds,
        )
        if activity is None:
            return False
        await self._execute(activity)
        return True

    async def _execute(self, activity: Activity) -> None:
        handler = self._handlers.get(activity.type)
        if handler is None:
            # Fail it rather than drop it: an unhandled type left claimed just
            # waits out its lease and comes back to the same worker.
            await self._settle(
                activity, "fail", cause=f"no handler registered for {activity.type!r}"
            )
            return

        beat = asyncio.create_task(self._beat(activity))
        try:
            result = await self._call(handler, activity)
        except asyncio.CancelledError:
            beat.cancel()
            raise
        except BaseException as exc:
            self._report(exc, activity)
            await self._stop_beat(beat)
            await self._settle(activity, "fail", cause=f"{type(exc).__name__}: {exc}")
            return
        await self._stop_beat(beat)
        await self._settle(activity, "complete", result=result)

    async def _call(self, handler: Handler, activity: Activity) -> Any:
        if inspect.iscoroutinefunction(handler):
            return await handler(activity)
        # A plain function runs in a thread, never inline: a blocking call on
        # the event loop stalls the heartbeat, the lease expires mid-run, and
        # the engine hands the same activity to somebody else while this
        # worker is still doing it.
        outcome = await asyncio.to_thread(handler, activity)
        if inspect.isawaitable(outcome):
            return await outcome
        return outcome

    async def _settle(self, activity: Activity, verb: str, **body: Any) -> None:
        try:
            if verb == "complete":
                await self.tasks.complete(activity.id, activity.run_id, body["result"])
            else:
                await self.tasks.fail(activity.id, activity.run_id, body["cause"])
        except Terminal as exc:
            # The lease was lost and somebody else settled this run. Report it
            # and carry on — the work is done, just not by us.
            self._report(exc, activity)
        except TasksError as exc:
            self._report(exc, activity)

    # ── the lease ───────────────────────────────────────────────────────

    async def _beat(self, activity: Activity) -> None:
        """Heartbeat until cancelled, holding the claim while work runs."""
        interval = self._interval(activity)
        while True:
            await asyncio.sleep(interval)
            try:
                await self.tasks.heartbeat(activity.id, activity.run_id)
            except asyncio.CancelledError:
                raise
            except BaseException as exc:
                # A missed heartbeat is survivable — the lease has slack — so
                # report and keep beating rather than abandoning the run.
                self._report(exc, activity)

    def _interval(self, activity: Activity) -> float:
        """Beat at a fraction of the lease the SERVER granted.

        Read off ``leaseExpiry`` rather than recomputed from a timeout string,
        because the engine's own rule — heartbeat timeout, else the requested
        lease, else its default — is the one that decides when the reaper
        fires, and it already applied it.
        """
        window = float(self.lease_seconds or 60)
        if activity.lease_expiry:
            try:
                expiry = datetime.fromisoformat(activity.lease_expiry)
                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=UTC)
                granted = (expiry - datetime.now(UTC)).total_seconds()
                if granted > 0:
                    window = granted
            except ValueError:
                pass
        return max(1.0, window / HEARTBEAT_FRACTION)

    @staticmethod
    async def _stop_beat(beat: asyncio.Task[None]) -> None:
        beat.cancel()
        try:
            await beat
        except (asyncio.CancelledError, Exception):
            pass

    def _report(self, exc: BaseException, activity: Activity | None) -> None:
        if self.on_error is not None:
            self.on_error(exc, activity)
