"""store — a KV round-trip: provision a store, read it back, delete it.

    POST   /v1/kv          post_kv         provision
    GET    /v1/kv/{name}   get_kv_by_name     read back
    DELETE /v1/kv/{name}   delete_kv_by_name  tear down

This is the PROVISIONING plane. The per-key data plane the spec also describes
(``/v1/kv/keys/{key}``) is not mounted anywhere — every verb 404s at
api.hanzo.ai, and kv.hanzo.ai 404s the whole prefix — so a set/get/delete
round-trip on keys would be an example that cannot run. These three answer 403
"a validated principal is required" unauthenticated, i.e. routed and gated.

The delete runs in ``finally``, so a failed read still tears the store down
rather than leaving it billable for the next run to collide with.

    python -m examples.store
"""

import time

from hanzoai.cloud import ProvisionRequest, ProvisioningApi

from examples.client import client, run

NAME = f"example-store-{time.time_ns()}"


def main() -> None:
    with client() as api:
        kv = ProvisioningApi(api)

        kv.post_provisioning_kv(ProvisionRequest(name=NAME))
        print(f"provisioned {NAME}")

        try:
            store = kv.get_provisioning_kv_by_name(NAME)
            print(f"read back: {store.name} · {store.kind} · status {store.status}")
            print(f"  host {store.host}:{store.port}")
        finally:
            kv.delete_provisioning_kv_by_name(NAME)
            print(f"deleted {NAME}")


if __name__ == "__main__":
    run(main)
