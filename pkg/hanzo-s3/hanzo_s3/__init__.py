"""Hanzo S3 -- Python client for S3-compatible object storage.

Backed by hanzoai/s3 (a SeaweedFS fork with Hanzo consensus + ZAP). The S3
wire protocol is standard, so this client is a thin, native adapter over
``boto3`` exposing a small, stable surface.

Usage::

    from hanzo_s3 import S3Client

    client = S3Client(
        "s3.hanzo.ai",
        access_key="YOUR-ACCESS-KEY",
        secret_key="YOUR-SECRET-KEY",
    )

    for bucket in client.list_buckets():
        print(bucket.name, bucket.creation_date)
"""

from hanzo_s3.client import (
    Bucket,
    Object,
    S3Client,
    S3Error,
    Stat,
)

# Convenience aliases
Client = S3Client
Error = S3Error
S3Exception = S3Error

__version__ = "1.0.0"

__all__ = [
    "S3Client",
    "Client",
    "S3Error",
    "Error",
    "S3Exception",
    "Bucket",
    "Object",
    "Stat",
]
