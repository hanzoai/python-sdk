"""Blue-Red agent coordination protocol via shared memory.

The blue-red protocol is a structured review cycle:
1. Blue agent analyzes code/system and stores a report
2. Red agent reads Blue's report, finds issues, stores findings
3. Blue reads Red's findings, implements fixes, stores response
4. Red re-reviews Blue's fixes, stores verification result

All messages are stored in the "blue-red" namespace with typed keys,
enabling deterministic retrieval without semantic search.
"""

import json
import time
from typing import Any, Dict, List, Optional


class BlueRedChannel:
    """Shared memory channel for blue-red agent coordination."""

    NAMESPACE = "blue-red"

    def __init__(self, memory_service):
        """Initialize with a PluginMemoryService instance."""
        self.memory = memory_service

    async def blue_report(self, report: dict, scope: str = "") -> str:
        """Blue stores its report for Red to read."""
        key = f"blue-report-{int(time.time())}"
        await self.memory.store_memory(
            content=json.dumps(report),
            metadata={
                "agent": "blue",
                "type": "report",
                "scope": scope,
            },
            namespace=self.NAMESPACE,
            key=key,
            tags=["blue", "report"],
        )
        return key

    async def red_report(self, findings: dict, scope: str = "") -> str:
        """Red stores findings for Blue to read."""
        key = f"red-report-{int(time.time())}"
        await self.memory.store_memory(
            content=json.dumps(findings),
            metadata={
                "agent": "red",
                "type": "findings",
                "scope": scope,
            },
            namespace=self.NAMESPACE,
            key=key,
            tags=["red", "findings"],
        )
        return key

    async def blue_response(self, fixes: dict) -> str:
        """Blue stores fix response for Red re-review."""
        key = f"blue-response-{int(time.time())}"
        await self.memory.store_memory(
            content=json.dumps(fixes),
            metadata={
                "agent": "blue",
                "type": "response",
            },
            namespace=self.NAMESPACE,
            key=key,
            tags=["blue", "response", "fixes"],
        )
        return key

    async def red_rereview(self, verification: dict) -> str:
        """Red stores re-review results."""
        key = f"red-rereview-{int(time.time())}"
        await self.memory.store_memory(
            content=json.dumps(verification),
            metadata={
                "agent": "red",
                "type": "rereview",
            },
            namespace=self.NAMESPACE,
            key=key,
            tags=["red", "rereview"],
        )
        return key

    async def get_latest_blue_report(self) -> Optional[Dict[str, Any]]:
        """Red reads Blue's latest report."""
        results = await self.memory.search_memory(
            query="",
            metadata_filter={
                "namespace": self.NAMESPACE,
                "agent": "blue",
                "type": "report",
            },
        )
        return results[0] if results else None

    async def get_latest_red_findings(self) -> Optional[Dict[str, Any]]:
        """Blue reads Red's latest findings."""
        results = await self.memory.search_memory(
            query="",
            metadata_filter={
                "namespace": self.NAMESPACE,
                "agent": "red",
                "type": "findings",
            },
        )
        return results[0] if results else None

    async def get_full_cycle(self) -> List[Dict[str, Any]]:
        """Get all messages in the blue-red cycle, ordered by creation time."""
        results = await self.memory.list_memories(namespace=self.NAMESPACE)
        return sorted(results, key=lambda r: r.get("created_at", ""))
