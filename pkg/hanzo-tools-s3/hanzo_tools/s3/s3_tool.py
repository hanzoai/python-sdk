"""MCP tool for Hanzo S3 — S3-compatible object storage.

Single tool over the ``hanzo_s3`` client (MinIO-compatible) at s3.hanzo.ai.
Buckets and objects: list, create, remove, stat, and presign.

Auth: credentials from the environment — inject them from KMS, never store
plaintext:

    eval "$(hanzo kms inject <project> <env>)"   # exports HANZO_S3_*
"""

from __future__ import annotations

import os
import json
import logging
from typing import Any, Annotated, final
from datetime import timedelta

from pydantic import Field
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core.base import BaseTool

logger = logging.getLogger(__name__)

DESCRIPTION = """Hanzo S3 — S3-compatible object storage (s3.hanzo.ai).

Credentials from env: HANZO_S3_ENDPOINT, HANZO_S3_ACCESS_KEY, HANZO_S3_SECRET_KEY
(inject from KMS — never plaintext).

Bucket actions:
- buckets: List buckets
- make_bucket: Create a bucket (params: bucket)
- remove_bucket: Remove an empty bucket (params: bucket)

Object actions:
- objects: List objects (params: bucket, prefix, recursive)
- stat: Object metadata (params: bucket, object_name)
- remove_object: Delete an object (params: bucket, object_name)
- presign: Presigned GET URL (params: bucket, object_name, expires)
"""


def _get_client():
    """Build an S3 client from environment credentials."""
    from hanzo_s3 import S3Client

    endpoint = os.getenv("HANZO_S3_ENDPOINT", "s3.hanzo.ai")
    access_key = os.getenv("HANZO_S3_ACCESS_KEY") or os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("HANZO_S3_SECRET_KEY") or os.getenv("AWS_SECRET_ACCESS_KEY")
    secure = os.getenv("HANZO_S3_SECURE", "true").lower() not in ("0", "false", "no")

    if not access_key or not secret_key:
        raise RuntimeError(
            "Missing S3 credentials. Set HANZO_S3_ACCESS_KEY and HANZO_S3_SECRET_KEY "
            "(inject from KMS)."
        )

    return S3Client(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)


@final
class S3Tool(BaseTool):
    """MCP tool for Hanzo S3 object storage."""

    @property
    def name(self) -> str:
        return "s3"

    @property
    def description(self) -> str:
        return DESCRIPTION

    async def call(
        self,
        ctx: MCPContext,
        action: str = "buckets",
        bucket: str | None = None,
        object_name: str | None = None,
        prefix: str = "",
        recursive: bool = False,
        expires: int = 3600,
        **kwargs: Any,
    ) -> str:
        try:
            if action == "buckets":
                return self._buckets()
            elif action == "make_bucket":
                return self._make_bucket(bucket)
            elif action == "remove_bucket":
                return self._remove_bucket(bucket)
            elif action == "objects":
                return self._objects(bucket, prefix, recursive)
            elif action == "stat":
                return self._stat(bucket, object_name)
            elif action == "remove_object":
                return self._remove_object(bucket, object_name)
            elif action == "presign":
                return self._presign(bucket, object_name, expires)
            else:
                return json.dumps({
                    "error": f"Unknown action: {action}",
                    "available": [
                        "buckets", "make_bucket", "remove_bucket",
                        "objects", "stat", "remove_object", "presign",
                    ],
                })
        except RuntimeError as e:
            return json.dumps({"error": str(e)})
        except Exception as e:
            logger.exception(f"S3 tool error: {e}")
            return json.dumps({"error": f"S3 error: {e}"})

    # -- Bucket actions ------------------------------------------------------

    def _buckets(self) -> str:
        client = _get_client()
        result = [
            {
                "name": b.name,
                "creation_date": str(b.creation_date) if b.creation_date else None,
            }
            for b in client.list_buckets()
        ]
        return json.dumps({"count": len(result), "buckets": result}, indent=2)

    def _make_bucket(self, bucket: str | None) -> str:
        if not bucket:
            return json.dumps({"error": "Required: bucket"})
        client = _get_client()
        client.make_bucket(bucket)
        return json.dumps({"action": "created", "bucket": bucket}, indent=2)

    def _remove_bucket(self, bucket: str | None) -> str:
        if not bucket:
            return json.dumps({"error": "Required: bucket"})
        client = _get_client()
        client.remove_bucket(bucket)
        return json.dumps({"action": "removed", "bucket": bucket}, indent=2)

    # -- Object actions ------------------------------------------------------

    def _objects(self, bucket: str | None, prefix: str, recursive: bool) -> str:
        if not bucket:
            return json.dumps({"error": "Required: bucket"})
        client = _get_client()
        result = [
            {
                "key": o.object_name,
                "size": None if o.is_dir else o.size,
                "last_modified": str(o.last_modified) if o.last_modified else None,
                "is_dir": o.is_dir,
            }
            for o in client.list_objects(bucket, prefix=prefix, recursive=recursive)
        ]
        return json.dumps(
            {"bucket": bucket, "prefix": prefix, "count": len(result), "objects": result},
            indent=2,
        )

    def _stat(self, bucket: str | None, object_name: str | None) -> str:
        if not bucket or not object_name:
            return json.dumps({"error": "Required: bucket, object_name"})
        client = _get_client()
        obj = client.stat_object(bucket, object_name)
        return json.dumps({
            "bucket": bucket,
            "object_name": object_name,
            "size": obj.size,
            "etag": obj.etag,
            "content_type": obj.content_type,
            "last_modified": str(obj.last_modified) if obj.last_modified else None,
        }, indent=2)

    def _remove_object(self, bucket: str | None, object_name: str | None) -> str:
        if not bucket or not object_name:
            return json.dumps({"error": "Required: bucket, object_name"})
        client = _get_client()
        client.remove_object(bucket, object_name)
        return json.dumps({"action": "removed", "bucket": bucket, "object_name": object_name}, indent=2)

    def _presign(self, bucket: str | None, object_name: str | None, expires: int) -> str:
        if not bucket or not object_name:
            return json.dumps({"error": "Required: bucket, object_name"})
        client = _get_client()
        url = client.presigned_get_object(
            bucket, object_name, expires=timedelta(seconds=expires)
        )
        return json.dumps({"bucket": bucket, "object_name": object_name, "url": url}, indent=2)

    # -- Registration --------------------------------------------------------

    def register(self, mcp_server: FastMCP) -> None:
        """Register S3 tool with explicit parameters."""
        tool_instance = self

        @mcp_server.tool(
            name="s3",
            description=DESCRIPTION,
        )
        async def s3(
            action: Annotated[
                str,
                Field(
                    description=(
                        "Action to perform. "
                        "Buckets: buckets, make_bucket, remove_bucket. "
                        "Objects: objects, stat, remove_object, presign."
                    ),
                ),
            ] = "buckets",
            bucket: Annotated[
                str | None,
                Field(description="Bucket name"),
            ] = None,
            object_name: Annotated[
                str | None,
                Field(description="Object key (for stat, remove_object, presign)"),
            ] = None,
            prefix: Annotated[
                str,
                Field(description="Object key prefix (for objects)"),
            ] = "",
            recursive: Annotated[
                bool,
                Field(description="Recurse into prefixes (for objects)"),
            ] = False,
            expires: Annotated[
                int,
                Field(description="Presigned URL lifetime in seconds (for presign)"),
            ] = 3600,
            ctx: MCPContext = None,
        ) -> str:
            return await tool_instance.call(
                ctx,
                action=action,
                bucket=bucket,
                object_name=object_name,
                prefix=prefix,
                recursive=recursive,
                expires=expires,
            )
