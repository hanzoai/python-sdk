"""Hanzo S3 -- Python client for S3-compatible object storage.

Thin wrapper around the ``minio`` package that re-exports its public API
under the ``hanzo_s3`` namespace with Hanzo-flavoured aliases.

Usage::

    from hanzo_s3 import S3Client

    client = S3Client(
        "s3.hanzo.space",
        access_key="YOUR-ACCESS-KEY",
        secret_key="YOUR-SECRET-KEY",
    )

    for bucket in client.list_buckets():
        print(bucket.name, bucket.creation_date)
"""

from minio import Minio as S3Client
from minio import Minio  # backward compat
from minio.error import (
    InvalidResponseError,
    S3Error,
    ServerError,
)
from minio.datatypes import Object
from minio.helpers import ObjectWriteResult

# Convenience aliases
Client = S3Client
Error = S3Error
S3Exception = S3Error
ObjectWriteResponse = ObjectWriteResult

# Re-export useful sub-modules
from minio import credentials  # noqa: F401
from minio import sse  # noqa: F401

__version__ = "1.0.0"

__all__ = [
    # Clients
    "S3Client",
    "Client",
    "Minio",
    # Errors
    "S3Error",
    "Error",
    "S3Exception",
    "InvalidResponseError",
    "ServerError",
    # Data types
    "Object",
    "ObjectWriteResult",
    "ObjectWriteResponse",
    # Sub-modules
    "credentials",
    "sse",
]
