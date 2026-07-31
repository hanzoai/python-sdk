"""store — a KV round-trip: set, read it back, delete.

    PUT    /v1/kv/keys/{key}   kv_setKey
    GET    /v1/kv/keys/{key}   kv_getKey
    DELETE /v1/kv/keys/{key}   kv_deleteKey

The delete runs in ``finally``, so a failed read still cleans up rather than
leaving the key behind for the next run to collide with.

    python -m examples.store
"""

import time

from hanzoai.cloud import KeysApi, KvSetKeyRequest

from examples.client import client, run

KEY = f"examples/store/{time.time_ns()}"
VALUE = "hello from the hanzoai SDK"


def main() -> None:
    with client() as api:
        kv = KeysApi(api)

        kv.kv_set_key(KEY, KvSetKeyRequest(value=VALUE, ttl=60))
        print(f"set {KEY}")

        try:
            print("read back:", kv.kv_get_key(KEY).to_str())
        finally:
            kv.kv_delete_key(KEY)
            print(f"deleted {KEY}")


if __name__ == "__main__":
    run(main)
