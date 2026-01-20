"""S3/MinIO object storage client wrapper for Hanzo infrastructure.

Provides async interface to S3-compatible object storage including
AWS S3, MinIO, and other compatible services.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from io import BytesIO
from typing import Any, AsyncIterator, BinaryIO, Optional, Union

from pydantic import BaseModel, Field


class StorageConfig(BaseModel):
    """Configuration for S3/MinIO connection."""

    endpoint_url: Optional[str] = Field(default=None, description="Endpoint URL (required for MinIO)")
    region: str = Field(default="us-east-1", description="AWS region")
    access_key: Optional[str] = Field(default=None, description="Access key ID")
    secret_key: Optional[str] = Field(default=None, description="Secret access key")
    bucket: str = Field(default="hanzo", description="Default bucket name")
    use_ssl: bool = Field(default=True, description="Use SSL/TLS")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")
    session_token: Optional[str] = Field(default=None, description="Session token (for temporary credentials)")
    addressing_style: str = Field(default="auto", description="Path or virtual addressing style")

    @classmethod
    def from_env(cls) -> StorageConfig:
        """Create config from environment variables.

        Environment variables:
            S3_ENDPOINT_URL: Endpoint URL (for MinIO/custom S3)
            S3_REGION / AWS_REGION: AWS region (default: us-east-1)
            S3_ACCESS_KEY / AWS_ACCESS_KEY_ID: Access key
            S3_SECRET_KEY / AWS_SECRET_ACCESS_KEY: Secret key
            S3_BUCKET: Default bucket name (default: hanzo)
            S3_USE_SSL: Use SSL (default: true)
        """
        return cls(
            endpoint_url=os.getenv("S3_ENDPOINT_URL") or os.getenv("MINIO_ENDPOINT"),
            region=os.getenv("S3_REGION") or os.getenv("AWS_REGION", "us-east-1"),
            access_key=os.getenv("S3_ACCESS_KEY") or os.getenv("AWS_ACCESS_KEY_ID"),
            secret_key=os.getenv("S3_SECRET_KEY") or os.getenv("AWS_SECRET_ACCESS_KEY"),
            bucket=os.getenv("S3_BUCKET", "hanzo"),
            use_ssl=os.getenv("S3_USE_SSL", "true").lower() in ("true", "1", "yes"),
            session_token=os.getenv("AWS_SESSION_TOKEN"),
        )


@dataclass
class ObjectInfo:
    """Metadata about a stored object."""

    key: str
    size: int
    etag: str
    last_modified: datetime
    content_type: Optional[str] = None
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class UploadResult:
    """Result of an upload operation."""

    key: str
    etag: str
    version_id: Optional[str] = None


@dataclass
class PresignedUrl:
    """A presigned URL for temporary access."""

    url: str
    expires_in: int  # seconds


class StorageClient:
    """Async client for S3-compatible object storage.

    Wraps aiobotocore/boto3 for async S3 operations with Hanzo conventions.
    Supports AWS S3, MinIO, and other S3-compatible services.

    Example:
        ```python
        client = StorageClient(StorageConfig.from_env())
        await client.connect()

        # Upload
        await client.put_object("files/doc.txt", b"Hello, World!")

        # Download
        data = await client.get_object("files/doc.txt")

        # List objects
        async for obj in client.list_objects("files/"):
            print(obj.key, obj.size)

        # Presigned URLs
        url = await client.presign_get("files/doc.txt", expires_in=3600)
        ```
    """

    def __init__(self, config: Optional[StorageConfig] = None) -> None:
        """Initialize storage client.

        Args:
            config: S3 configuration. If None, loads from environment.
        """
        self.config = config or StorageConfig.from_env()
        self._session: Any = None
        self._client: Any = None
        self._exit_stack: Any = None

    async def connect(self) -> None:
        """Establish connection to S3 service."""
        try:
            from aiobotocore.session import get_session
            from contextlib import AsyncExitStack
        except ImportError as e:
            raise ImportError(
                "aiobotocore is required for StorageClient. "
                "Install with: pip install aiobotocore"
            ) from e

        self._session = get_session()
        self._exit_stack = AsyncExitStack()

        client_kwargs: dict[str, Any] = {
            "service_name": "s3",
            "region_name": self.config.region,
        }

        if self.config.endpoint_url:
            client_kwargs["endpoint_url"] = self.config.endpoint_url

        if self.config.access_key and self.config.secret_key:
            client_kwargs["aws_access_key_id"] = self.config.access_key
            client_kwargs["aws_secret_access_key"] = self.config.secret_key

        if self.config.session_token:
            client_kwargs["aws_session_token"] = self.config.session_token

        client_kwargs["config"] = self._get_client_config()

        ctx_manager = self._session.create_client(**client_kwargs)
        self._client = await self._exit_stack.enter_async_context(ctx_manager)

    def _get_client_config(self) -> Any:
        """Get boto client config."""
        from botocore.config import Config

        return Config(
            signature_version="s3v4",
            s3={"addressing_style": self.config.addressing_style},
        )

    async def close(self) -> None:
        """Close the connection."""
        if self._exit_stack:
            await self._exit_stack.aclose()
            self._exit_stack = None
            self._client = None
            self._session = None

    async def health_check(self) -> bool:
        """Check if S3 service is healthy.

        Returns:
            True if service is reachable.
        """
        if not self._client:
            return False
        try:
            await self._client.list_buckets()
            return True
        except Exception:
            return False

    # Bucket operations

    async def create_bucket(self, bucket: Optional[str] = None) -> None:
        """Create a bucket.

        Args:
            bucket: Bucket name (uses default if not specified).
        """
        bucket_name = bucket or self.config.bucket
        create_config = {}
        if self.config.region != "us-east-1":
            create_config["CreateBucketConfiguration"] = {
                "LocationConstraint": self.config.region
            }
        await self._client.create_bucket(Bucket=bucket_name, **create_config)

    async def delete_bucket(self, bucket: Optional[str] = None) -> None:
        """Delete a bucket.

        Args:
            bucket: Bucket name (uses default if not specified).
        """
        bucket_name = bucket or self.config.bucket
        await self._client.delete_bucket(Bucket=bucket_name)

    async def bucket_exists(self, bucket: Optional[str] = None) -> bool:
        """Check if a bucket exists.

        Args:
            bucket: Bucket name (uses default if not specified).

        Returns:
            True if bucket exists.
        """
        bucket_name = bucket or self.config.bucket
        try:
            await self._client.head_bucket(Bucket=bucket_name)
            return True
        except Exception:
            return False

    async def list_buckets(self) -> list[str]:
        """List all buckets.

        Returns:
            List of bucket names.
        """
        response = await self._client.list_buckets()
        return [b["Name"] for b in response.get("Buckets", [])]

    # Object operations

    async def put_object(
        self,
        key: str,
        data: Union[bytes, BinaryIO, BytesIO],
        content_type: Optional[str] = None,
        metadata: Optional[dict[str, str]] = None,
        bucket: Optional[str] = None,
    ) -> UploadResult:
        """Upload an object.

        Args:
            key: Object key.
            data: Object data as bytes or file-like object.
            content_type: Content type (auto-detected if not specified).
            metadata: Custom metadata.
            bucket: Bucket name (uses default if not specified).

        Returns:
            Upload result with etag.
        """
        bucket_name = bucket or self.config.bucket

        put_kwargs: dict[str, Any] = {
            "Bucket": bucket_name,
            "Key": key,
            "Body": data,
        }

        if content_type:
            put_kwargs["ContentType"] = content_type
        if metadata:
            put_kwargs["Metadata"] = metadata

        response = await self._client.put_object(**put_kwargs)
        return UploadResult(
            key=key,
            etag=response.get("ETag", "").strip('"'),
            version_id=response.get("VersionId"),
        )

    async def get_object(
        self,
        key: str,
        bucket: Optional[str] = None,
    ) -> bytes:
        """Download an object.

        Args:
            key: Object key.
            bucket: Bucket name (uses default if not specified).

        Returns:
            Object data as bytes.
        """
        bucket_name = bucket or self.config.bucket
        response = await self._client.get_object(Bucket=bucket_name, Key=key)
        async with response["Body"] as stream:
            return await stream.read()

    async def get_object_stream(
        self,
        key: str,
        bucket: Optional[str] = None,
    ) -> AsyncIterator[bytes]:
        """Stream an object in chunks.

        Args:
            key: Object key.
            bucket: Bucket name (uses default if not specified).

        Yields:
            Chunks of object data.
        """
        bucket_name = bucket or self.config.bucket
        response = await self._client.get_object(Bucket=bucket_name, Key=key)
        async with response["Body"] as stream:
            async for chunk in stream.iter_chunks():
                yield chunk[0]  # iter_chunks returns (chunk, final)

    async def delete_object(
        self,
        key: str,
        bucket: Optional[str] = None,
    ) -> None:
        """Delete an object.

        Args:
            key: Object key.
            bucket: Bucket name (uses default if not specified).
        """
        bucket_name = bucket or self.config.bucket
        await self._client.delete_object(Bucket=bucket_name, Key=key)

    async def delete_objects(
        self,
        keys: list[str],
        bucket: Optional[str] = None,
    ) -> list[str]:
        """Delete multiple objects.

        Args:
            keys: Object keys to delete.
            bucket: Bucket name (uses default if not specified).

        Returns:
            List of deleted keys.
        """
        bucket_name = bucket or self.config.bucket
        response = await self._client.delete_objects(
            Bucket=bucket_name,
            Delete={"Objects": [{"Key": k} for k in keys]},
        )
        return [d["Key"] for d in response.get("Deleted", [])]

    async def head_object(
        self,
        key: str,
        bucket: Optional[str] = None,
    ) -> ObjectInfo:
        """Get object metadata without downloading.

        Args:
            key: Object key.
            bucket: Bucket name (uses default if not specified).

        Returns:
            Object info with metadata.
        """
        bucket_name = bucket or self.config.bucket
        response = await self._client.head_object(Bucket=bucket_name, Key=key)
        return ObjectInfo(
            key=key,
            size=response.get("ContentLength", 0),
            etag=response.get("ETag", "").strip('"'),
            last_modified=response.get("LastModified", datetime.now()),
            content_type=response.get("ContentType"),
            metadata=response.get("Metadata", {}),
        )

    async def object_exists(
        self,
        key: str,
        bucket: Optional[str] = None,
    ) -> bool:
        """Check if an object exists.

        Args:
            key: Object key.
            bucket: Bucket name (uses default if not specified).

        Returns:
            True if object exists.
        """
        try:
            await self.head_object(key, bucket)
            return True
        except Exception:
            return False

    async def list_objects(
        self,
        prefix: str = "",
        bucket: Optional[str] = None,
        max_keys: int = 1000,
    ) -> AsyncIterator[ObjectInfo]:
        """List objects with a prefix.

        Args:
            prefix: Key prefix filter.
            bucket: Bucket name (uses default if not specified).
            max_keys: Maximum keys per request.

        Yields:
            Object info for each matching object.
        """
        bucket_name = bucket or self.config.bucket
        continuation_token = None

        while True:
            kwargs: dict[str, Any] = {
                "Bucket": bucket_name,
                "Prefix": prefix,
                "MaxKeys": max_keys,
            }
            if continuation_token:
                kwargs["ContinuationToken"] = continuation_token

            response = await self._client.list_objects_v2(**kwargs)

            for obj in response.get("Contents", []):
                yield ObjectInfo(
                    key=obj["Key"],
                    size=obj["Size"],
                    etag=obj["ETag"].strip('"'),
                    last_modified=obj["LastModified"],
                )

            if not response.get("IsTruncated"):
                break
            continuation_token = response.get("NextContinuationToken")

    # Copy operations

    async def copy_object(
        self,
        source_key: str,
        dest_key: str,
        source_bucket: Optional[str] = None,
        dest_bucket: Optional[str] = None,
    ) -> UploadResult:
        """Copy an object.

        Args:
            source_key: Source object key.
            dest_key: Destination object key.
            source_bucket: Source bucket (uses default if not specified).
            dest_bucket: Destination bucket (uses default if not specified).

        Returns:
            Upload result for the copy.
        """
        src_bucket = source_bucket or self.config.bucket
        dst_bucket = dest_bucket or self.config.bucket

        response = await self._client.copy_object(
            Bucket=dst_bucket,
            Key=dest_key,
            CopySource={"Bucket": src_bucket, "Key": source_key},
        )
        return UploadResult(
            key=dest_key,
            etag=response.get("CopyObjectResult", {}).get("ETag", "").strip('"'),
            version_id=response.get("VersionId"),
        )

    # Presigned URLs

    async def presign_get(
        self,
        key: str,
        expires_in: int = 3600,
        bucket: Optional[str] = None,
    ) -> PresignedUrl:
        """Generate a presigned URL for download.

        Args:
            key: Object key.
            expires_in: URL validity in seconds (default: 1 hour).
            bucket: Bucket name (uses default if not specified).

        Returns:
            Presigned URL.
        """
        bucket_name = bucket or self.config.bucket
        url = await self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": key},
            ExpiresIn=expires_in,
        )
        return PresignedUrl(url=url, expires_in=expires_in)

    async def presign_put(
        self,
        key: str,
        expires_in: int = 3600,
        content_type: Optional[str] = None,
        bucket: Optional[str] = None,
    ) -> PresignedUrl:
        """Generate a presigned URL for upload.

        Args:
            key: Object key.
            expires_in: URL validity in seconds (default: 1 hour).
            content_type: Required content type.
            bucket: Bucket name (uses default if not specified).

        Returns:
            Presigned URL.
        """
        bucket_name = bucket or self.config.bucket
        params: dict[str, Any] = {"Bucket": bucket_name, "Key": key}
        if content_type:
            params["ContentType"] = content_type

        url = await self._client.generate_presigned_url(
            "put_object",
            Params=params,
            ExpiresIn=expires_in,
        )
        return PresignedUrl(url=url, expires_in=expires_in)

    async def __aenter__(self) -> StorageClient:
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
