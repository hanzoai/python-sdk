"""S3 client over boto3 -- native adapter for hanzoai/s3 (SeaweedFS fork).

Exposes the small surface the Hanzo CLI and MCP tool need: buckets, objects,
stat, presign. The object model (``Bucket``/``Object``/``Stat``) is stable and
independent of the underlying boto3 response shapes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

S3Error = ClientError


@dataclass(frozen=True)
class Bucket:
    name: str
    creation_date: datetime | None


@dataclass(frozen=True)
class Object:
    object_name: str
    size: int | None
    last_modified: datetime | None
    is_dir: bool


@dataclass(frozen=True)
class Stat:
    size: int
    etag: str | None
    content_type: str | None
    last_modified: datetime | None


def _endpoint_url(endpoint: str, secure: bool) -> str:
    if endpoint.startswith(("http://", "https://")):
        return endpoint
    return f"{'https' if secure else 'http'}://{endpoint}"


class S3Client:
    """S3-compatible client backed by hanzoai/s3 (SeaweedFS fork).

    Mirrors the host+credentials constructor used across the Hanzo stack;
    credentials must be injected from KMS, never stored in plaintext.
    """

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        secure: bool = True,
        region: str = "us-east-1",
    ) -> None:
        self._s3 = boto3.client(
            "s3",
            endpoint_url=_endpoint_url(endpoint, secure),
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )

    def list_buckets(self) -> list[Bucket]:
        resp = self._s3.list_buckets()
        return [
            Bucket(name=b["Name"], creation_date=b.get("CreationDate"))
            for b in resp.get("Buckets", [])
        ]

    def make_bucket(self, bucket: str) -> None:
        self._s3.create_bucket(Bucket=bucket)

    def remove_bucket(self, bucket: str) -> None:
        self._s3.delete_bucket(Bucket=bucket)

    def list_objects(
        self, bucket: str, prefix: str = "", recursive: bool = False
    ) -> list[Object]:
        kwargs: dict = {"Bucket": bucket, "Prefix": prefix}
        if not recursive:
            kwargs["Delimiter"] = "/"

        objects: list[Object] = []
        paginator = self._s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(**kwargs):
            for cp in page.get("CommonPrefixes", []):
                objects.append(
                    Object(object_name=cp["Prefix"], size=None, last_modified=None, is_dir=True)
                )
            for obj in page.get("Contents", []):
                objects.append(
                    Object(
                        object_name=obj["Key"],
                        size=obj.get("Size"),
                        last_modified=obj.get("LastModified"),
                        is_dir=False,
                    )
                )
        return objects

    def stat_object(self, bucket: str, object_name: str) -> Stat:
        resp = self._s3.head_object(Bucket=bucket, Key=object_name)
        etag = resp.get("ETag")
        return Stat(
            size=resp.get("ContentLength", 0),
            etag=etag.strip('"') if etag else None,
            content_type=resp.get("ContentType"),
            last_modified=resp.get("LastModified"),
        )

    def remove_object(self, bucket: str, object_name: str) -> None:
        self._s3.delete_object(Bucket=bucket, Key=object_name)

    def presigned_get_object(
        self, bucket: str, object_name: str, expires: timedelta = timedelta(hours=1)
    ) -> str:
        return self._s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": object_name},
            ExpiresIn=int(expires.total_seconds()),
        )
