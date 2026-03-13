"""Hanzo S3 Admin -- re-export of MinioAdmin for administrative operations.

Usage::

    from hanzo_s3.admin import S3Admin

    admin = S3Admin(
        "s3-api.hanzo.ai",
        credentials=provider,
    )

    info = admin.info()
"""

from minio.error import MinioAdminException as S3AdminException
from minio.minioadmin import MinioAdmin  # backward compat
from minio.minioadmin import MinioAdmin as S3Admin

# Convenience alias
Admin = S3Admin

__all__ = [
    "S3Admin",
    "Admin",
    "MinioAdmin",
    "S3AdminException",
]
