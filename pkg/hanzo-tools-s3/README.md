# hanzo-tools-s3

MCP tool for Hanzo S3 — S3-compatible object storage (s3.hanzo.ai).

Exposes a single `s3` tool with bucket and object actions: `buckets`,
`make_bucket`, `remove_bucket`, `objects`, `stat`, `remove_object`, `presign`.

Credentials come from the environment — inject them from KMS, never plaintext:

```bash
eval "$(hanzo kms inject <project> <env>)"   # exports HANZO_S3_*
```

Env: `HANZO_S3_ENDPOINT` (default `s3.hanzo.ai`), `HANZO_S3_ACCESS_KEY`,
`HANZO_S3_SECRET_KEY`, `HANZO_S3_SECURE` (default `true`).
