# hanzo-s3

Hanzo S3 -- Python client for S3-compatible object storage.

Thin wrapper around the [minio](https://pypi.org/project/minio/) package that
re-exports its public API under the `hanzo_s3` namespace with Hanzo-flavoured
aliases.

## Install

```bash
pip install hanzo-s3
# or
uv add hanzo-s3
```

## Quick start

```python
from hanzo_s3 import S3Client

client = S3Client(
    "s3-api.hanzo.ai",
    access_key="YOUR-ACCESS-KEY",
    secret_key="YOUR-SECRET-KEY",
)

# List buckets
for bucket in client.list_buckets():
    print(bucket.name, bucket.creation_date)

# Upload a file
client.fput_object("my-bucket", "remote/path.txt", "/local/path.txt")

# Download a file
client.fget_object("my-bucket", "remote/path.txt", "/local/download.txt")
```

## Admin operations

```python
from hanzo_s3.admin import S3Admin

admin = S3Admin("s3-api.hanzo.ai", credentials=provider)
info = admin.info()
```

## API

| hanzo_s3 | minio |
|----------|-------|
| `S3Client` / `Client` | `Minio` |
| `S3Admin` / `Admin` | `MinioAdmin` |
| `S3Error` / `Error` | `S3Error` |
| `S3Exception` | `MinioException` |
| `S3AdminException` | `MinioAdminException` |

All original `minio` names are also re-exported for backward compatibility.

## Links

- Documentation: https://docs.hanzo.ai/s3
- Hanzo Storage: https://s3.hanzo.ai
- Source (upstream): https://github.com/hanzos3/py-sdk
- Source (SDK): https://github.com/hanzoai/python-sdk
