# hanzo-cli

A Python CLI for Hanzo IAM, KMS, PaaS and S3. It predates the native Hanzo CLI
and is kept for the scripts that already depend on it.

## Use the native CLI instead

```bash
curl -fsSL https://hanzo.sh | sh
hanzo auth login
hanzo iam users list
hanzo kms secrets list
```

One binary, one command group per Hanzo Cloud product, generated from the same
contract the API and SDKs serve.

## If you still need this one

```bash
pip install hanzo-cli
hanzo-cli login
hanzo-cli whoami
hanzo-cli iam users
hanzo-cli kms list
hanzo-cli paas deploy list
```

The console script is `hanzo-cli`, not `hanzo`. `hanzo` is the native CLI, where
the sign-in verb is `hanzo auth login` — a bare `hanzo login` there is read as an
AI task, not a command. Naming this program after its distribution keeps the two
from shadowing each other on PATH.
