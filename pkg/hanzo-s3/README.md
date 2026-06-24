# hanzo-s3

Hanzo S3 -- Python client for S3-compatible object storage.

Backed by [hanzoai/s3](https://github.com/hanzoai/s3) (a SeaweedFS fork with
Hanzo consensus + ZAP) at `s3.hanzo.ai`. The S3 wire protocol is standard, so
this is a thin native adapter over `boto3` exposing a small, stable surface.

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
    "s3.hanzo.ai",
    access_key="YOUR-ACCESS-KEY",
    secret_key="YOUR-SECRET-KEY",
)

# List buckets
for bucket in client.list_buckets():
    print(bucket.name, bucket.creation_date)

# List objects
for obj in client.list_objects("my-bucket", prefix="logs/", recursive=True):
    print(obj.object_name, obj.size)

# Stat and presign
stat = client.stat_object("my-bucket", "remote/path.txt")
url = client.presigned_get_object("my-bucket", "remote/path.txt")
```

## API

| Name | Purpose |
|------|---------|
| `S3Client` / `Client` | Buckets and objects: `list_buckets`, `make_bucket`, `remove_bucket`, `list_objects`, `stat_object`, `remove_object`, `presigned_get_object` |
| `Bucket` / `Object` / `Stat` | Result types |
| `S3Error` / `Error` / `S3Exception` | Errors |

## Links

- Documentation: https://docs.hanzo.ai/s3
- Hanzo Storage: https://s3.hanzo.ai
- Backend: https://github.com/hanzoai/s3
- Source (SDK): https://github.com/hanzoai/python-sdk
