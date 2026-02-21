"""Hanzo Infrastructure SDK - Unified client for Hanzo OSS infrastructure.

Provides async clients for all Hanzo infrastructure services:
- Vector: Qdrant vector database
- KV: Redis/Valkey key-value store
- DocumentDB: MongoDB document database
- Storage: S3/MinIO object storage
- Search: Meilisearch full-text search
- PubSub: NATS messaging
- Tasks: Temporal workflows
- Queues: Distributed work queues
- Cron: Scheduled jobs
- Functions: Nuclio serverless functions

Example:
    ```python
    from hanzo.infra import HanzoInfra


    async def main():
        # Initialize from environment variables
        infra = await HanzoInfra.from_env()

        # Use individual clients
        await infra.kv.set("key", "value")
        await infra.vector.upsert("embeddings", points)

        # Or with context manager
        async with await HanzoInfra.from_env() as infra:
            results = await infra.search.search("products", "query")

        # Selective initialization
        infra = await HanzoInfra.from_env(services=["kv", "vector"])
    ```
"""

from __future__ import annotations

import os
from typing import Any, Optional, Sequence

from .kv import KVClient, KVConfig
from .cron import CronJob, CronClient, CronConfig, CronExecution
from .tasks import TasksClient, TasksConfig, WorkflowHandle, WorkflowExecution
from .pubsub import Message, PubSubClient, PubSubConfig, Subscription
from .queues import Job, JobStatus, QueueStats, QueuesClient, QueuesConfig
from .search import SearchHit, SearchClient, SearchConfig, SearchResult
from .vector import ScoredPoint, VectorPoint, VectorClient, VectorConfig
from .storage import (
    ObjectInfo,
    PresignedUrl,
    UploadResult,
    StorageClient,
    StorageConfig,
)
from .functions import (
    FunctionSpec,
    InvokeResult,
    FunctionStatus,
    FunctionsClient,
    FunctionsConfig,
)
from .documentdb import (
    Document,
    DeleteResult,
    UpdateResult,
    DocumentDBClient,
    DocumentDBConfig,
)

__all__ = [
    # Main class
    "HanzoInfra",
    # Vector (Qdrant)
    "VectorClient",
    "VectorConfig",
    "VectorPoint",
    "ScoredPoint",
    # KV (Redis/Valkey)
    "KVClient",
    "KVConfig",
    # DocumentDB (MongoDB)
    "DocumentDBClient",
    "DocumentDBConfig",
    "Document",
    "UpdateResult",
    "DeleteResult",
    # Storage (S3/MinIO)
    "StorageClient",
    "StorageConfig",
    "ObjectInfo",
    "UploadResult",
    "PresignedUrl",
    # Search (Meilisearch)
    "SearchClient",
    "SearchConfig",
    "SearchHit",
    "SearchResult",
    # PubSub (NATS)
    "PubSubClient",
    "PubSubConfig",
    "Message",
    "Subscription",
    # Tasks (Temporal)
    "TasksClient",
    "TasksConfig",
    "WorkflowHandle",
    "WorkflowExecution",
    # Queues
    "QueuesClient",
    "QueuesConfig",
    "Job",
    "JobStatus",
    "QueueStats",
    # Cron
    "CronClient",
    "CronConfig",
    "CronJob",
    "CronExecution",
    # Functions (Nuclio)
    "FunctionsClient",
    "FunctionsConfig",
    "FunctionSpec",
    "FunctionStatus",
    "InvokeResult",
]


ALL_SERVICES = [
    "vector",
    "kv",
    "documentdb",
    "storage",
    "search",
    "pubsub",
    "tasks",
    "queues",
    "cron",
    "functions",
]


class HanzoInfra:
    """Unified client for Hanzo infrastructure services.

    Provides a single entry point for all infrastructure services,
    with lazy initialization and configurable service selection.

    Attributes:
        vector: Qdrant vector database client.
        kv: Redis/Valkey key-value client.
        documentdb: MongoDB document database client.
        storage: S3/MinIO object storage client.
        search: Meilisearch full-text search client.
        pubsub: NATS messaging client.
        tasks: Temporal workflow client.
        queues: Distributed work queue client.
        cron: Scheduled jobs client.
        functions: Nuclio serverless functions client.
    """

    def __init__(
        self,
        vector: Optional[VectorClient] = None,
        kv: Optional[KVClient] = None,
        documentdb: Optional[DocumentDBClient] = None,
        storage: Optional[StorageClient] = None,
        search: Optional[SearchClient] = None,
        pubsub: Optional[PubSubClient] = None,
        tasks: Optional[TasksClient] = None,
        queues: Optional[QueuesClient] = None,
        cron: Optional[CronClient] = None,
        functions: Optional[FunctionsClient] = None,
    ) -> None:
        """Initialize HanzoInfra with individual clients.

        Args:
            vector: Qdrant vector client.
            kv: Redis/Valkey client.
            documentdb: MongoDB client.
            storage: S3/MinIO client.
            search: Meilisearch client.
            pubsub: NATS client.
            tasks: Temporal client.
            queues: Work queue client.
            cron: Cron scheduler client.
            functions: Nuclio functions client.
        """
        self._vector = vector
        self._kv = kv
        self._documentdb = documentdb
        self._storage = storage
        self._search = search
        self._pubsub = pubsub
        self._tasks = tasks
        self._queues = queues
        self._cron = cron
        self._functions = functions

    @property
    def vector(self) -> VectorClient:
        """Get vector client (Qdrant)."""
        if self._vector is None:
            raise RuntimeError(
                "Vector client not initialized. Initialize with services=['vector']"
            )
        return self._vector

    @property
    def kv(self) -> KVClient:
        """Get key-value client (Redis/Valkey)."""
        if self._kv is None:
            raise RuntimeError(
                "KV client not initialized. Initialize with services=['kv']"
            )
        return self._kv

    @property
    def documentdb(self) -> DocumentDBClient:
        """Get document database client (MongoDB)."""
        if self._documentdb is None:
            raise RuntimeError(
                "DocumentDB client not initialized. Initialize with services=['documentdb']"
            )
        return self._documentdb

    @property
    def storage(self) -> StorageClient:
        """Get object storage client (S3/MinIO)."""
        if self._storage is None:
            raise RuntimeError(
                "Storage client not initialized. Initialize with services=['storage']"
            )
        return self._storage

    @property
    def search(self) -> SearchClient:
        """Get search client (Meilisearch)."""
        if self._search is None:
            raise RuntimeError(
                "Search client not initialized. Initialize with services=['search']"
            )
        return self._search

    @property
    def pubsub(self) -> PubSubClient:
        """Get pub/sub client (NATS)."""
        if self._pubsub is None:
            raise RuntimeError(
                "PubSub client not initialized. Initialize with services=['pubsub']"
            )
        return self._pubsub

    @property
    def tasks(self) -> TasksClient:
        """Get tasks/workflow client (Temporal)."""
        if self._tasks is None:
            raise RuntimeError(
                "Tasks client not initialized. Initialize with services=['tasks']"
            )
        return self._tasks

    @property
    def queues(self) -> QueuesClient:
        """Get work queue client."""
        if self._queues is None:
            raise RuntimeError(
                "Queues client not initialized. Initialize with services=['queues']"
            )
        return self._queues

    @property
    def cron(self) -> CronClient:
        """Get cron scheduler client."""
        if self._cron is None:
            raise RuntimeError(
                "Cron client not initialized. Initialize with services=['cron']"
            )
        return self._cron

    @property
    def functions(self) -> FunctionsClient:
        """Get serverless functions client (Nuclio)."""
        if self._functions is None:
            raise RuntimeError(
                "Functions client not initialized. Initialize with services=['functions']"
            )
        return self._functions

    @classmethod
    async def from_env(
        cls,
        services: Optional[Sequence[str]] = None,
        connect: bool = True,
    ) -> HanzoInfra:
        """Create HanzoInfra from environment variables.

        Args:
            services: List of services to initialize. If None, initializes all.
                Valid values: vector, kv, documentdb, storage, search, pubsub,
                tasks, queues, cron, functions.
            connect: Automatically connect to services.

        Returns:
            Configured HanzoInfra instance.

        Example:
            ```python
            # Initialize all services
            infra = await HanzoInfra.from_env()

            # Initialize only specific services
            infra = await HanzoInfra.from_env(services=["kv", "vector"])
            ```
        """
        services_to_init = set(services) if services else set(ALL_SERVICES)

        # Validate service names
        invalid = services_to_init - set(ALL_SERVICES)
        if invalid:
            raise ValueError(f"Invalid services: {invalid}. Valid: {ALL_SERVICES}")

        clients: dict[str, Any] = {}

        # Initialize requested services
        if "vector" in services_to_init:
            clients["vector"] = VectorClient(VectorConfig.from_env())

        if "kv" in services_to_init:
            clients["kv"] = KVClient(KVConfig.from_env())

        if "documentdb" in services_to_init:
            clients["documentdb"] = DocumentDBClient(DocumentDBConfig.from_env())

        if "storage" in services_to_init:
            clients["storage"] = StorageClient(StorageConfig.from_env())

        if "search" in services_to_init:
            clients["search"] = SearchClient(SearchConfig.from_env())

        if "pubsub" in services_to_init:
            clients["pubsub"] = PubSubClient(PubSubConfig.from_env())

        if "tasks" in services_to_init:
            clients["tasks"] = TasksClient(TasksConfig.from_env())

        if "queues" in services_to_init:
            clients["queues"] = QueuesClient(QueuesConfig.from_env())

        if "cron" in services_to_init:
            clients["cron"] = CronClient(CronConfig.from_env())

        if "functions" in services_to_init:
            clients["functions"] = FunctionsClient(FunctionsConfig.from_env())

        infra = cls(**clients)

        if connect:
            await infra.connect()

        return infra

    async def connect(self) -> None:
        """Connect all initialized services."""
        if self._vector:
            await self._vector.connect()
        if self._kv:
            await self._kv.connect()
        if self._documentdb:
            await self._documentdb.connect()
        if self._storage:
            await self._storage.connect()
        if self._search:
            await self._search.connect()
        if self._pubsub:
            await self._pubsub.connect()
        if self._tasks:
            await self._tasks.connect()
        if self._queues:
            await self._queues.connect()
        if self._cron:
            await self._cron.connect()
        if self._functions:
            await self._functions.connect()

    async def close(self) -> None:
        """Close all service connections."""
        if self._vector:
            await self._vector.close()
        if self._kv:
            await self._kv.close()
        if self._documentdb:
            await self._documentdb.close()
        if self._storage:
            await self._storage.close()
        if self._search:
            await self._search.close()
        if self._pubsub:
            await self._pubsub.close()
        if self._tasks:
            await self._tasks.close()
        if self._queues:
            await self._queues.close()
        if self._cron:
            await self._cron.close()
        if self._functions:
            await self._functions.close()

    async def health_check(self) -> dict[str, bool]:
        """Check health of all initialized services.

        Returns:
            Dict mapping service name to health status.
        """
        results = {}

        if self._vector:
            results["vector"] = await self._vector.health_check()
        if self._kv:
            results["kv"] = await self._kv.health_check()
        if self._documentdb:
            results["documentdb"] = await self._documentdb.health_check()
        if self._storage:
            results["storage"] = await self._storage.health_check()
        if self._search:
            results["search"] = await self._search.health_check()
        if self._pubsub:
            results["pubsub"] = await self._pubsub.health_check()
        if self._tasks:
            results["tasks"] = await self._tasks.health_check()
        if self._queues:
            results["queues"] = await self._queues.health_check()
        if self._cron:
            results["cron"] = await self._cron.health_check()
        if self._functions:
            results["functions"] = await self._functions.health_check()

        return results

    async def __aenter__(self) -> HanzoInfra:
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
