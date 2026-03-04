"""CoreDNS (Hanzo DNS) provider.

Manages DNS via Hanzo's CoreDNS API (K8s-native DNS for Hanzo infrastructure).
Endpoint: configurable, defaults to https://dns.hanzo.ai/api/v1
"""

from __future__ import annotations

from typing import Any

import click

from .provider import DNSProvider, DNSRecord, DNSZone, register_provider

DEFAULT_ENDPOINT = "https://dns.hanzo.ai/api/v1"


class CoreDNSProvider(DNSProvider):
    name = "coredns"

    def __init__(self, config: dict[str, Any]) -> None:
        self.endpoint = config.get("endpoint", DEFAULT_ENDPOINT).rstrip("/")
        self.api_key = config.get("api_key", "")
        self.token = config.get("token", self.api_key)
        if not self.token:
            raise ValueError("CoreDNS requires 'api_key' or 'token'")

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def _client(self):
        import httpx
        return httpx.Client(headers=self._headers(), timeout=30.0)

    def _get(self, client, path: str, params: dict[str, Any] | None = None) -> Any:
        resp = client.get(f"{self.endpoint}{path}", params=params)
        resp.raise_for_status()
        return resp.json()

    # ── Interface implementation ─────────────────────────────────────

    def list_zones(self) -> list[DNSZone]:
        with self._client() as client:
            data = self._get(client, "/zones")

        zones = data if isinstance(data, list) else data.get("zones", data.get("result", []))
        return [
            DNSZone(
                id=z.get("id", z.get("name", "")),
                name=z.get("name", ""),
                status=z.get("status", "active"),
                plan="CoreDNS",
                provider=self.name,
                raw=z,
            )
            for z in zones
        ]

    def list_records(
        self, zone: str, record_type: str | None = None
    ) -> list[DNSRecord]:
        with self._client() as client:
            params: dict[str, str] = {}
            if record_type:
                params["type"] = record_type

            data = self._get(client, f"/zones/{zone}/records", params=params)

        records = data if isinstance(data, list) else data.get("records", data.get("result", []))
        return [
            DNSRecord(
                id=r.get("id", ""),
                zone=zone,
                type=r.get("type", ""),
                name=r.get("name", ""),
                content=r.get("content", r.get("value", "")),
                ttl=r.get("ttl", 1),
                proxied=False,
                provider=self.name,
                raw=r,
            )
            for r in records
        ]

    def add_record(
        self,
        zone: str,
        name: str,
        content: str,
        record_type: str = "A",
        proxied: bool = True,
        ttl: int = 1,
    ) -> DNSRecord | None:
        full_name = name if name.endswith(zone) else f"{name}.{zone}"

        with self._client() as client:
            payload = {
                "type": record_type.upper(),
                "name": full_name,
                "content": content,
                "ttl": ttl,
            }

            resp = client.post(
                f"{self.endpoint}/zones/{zone}/records", json=payload
            )
            resp.raise_for_status()
            rec = resp.json()

            return DNSRecord(
                id=rec.get("id", ""),
                zone=zone,
                type=record_type.upper(),
                name=rec.get("name", full_name),
                content=content,
                ttl=ttl,
                proxied=False,
                provider=self.name,
                raw=rec,
            )

    def remove_records(
        self, zone: str, name: str, record_type: str | None = None
    ) -> int:
        full_name = name if name.endswith(zone) else f"{name}.{zone}"

        records = self.list_records(zone, record_type)
        matching = [r for r in records if r.name == full_name]

        with self._client() as client:
            deleted = 0
            for r in matching:
                try:
                    resp = client.delete(
                        f"{self.endpoint}/zones/{zone}/records/{r.id}"
                    )
                    resp.raise_for_status()
                    deleted += 1
                except Exception:
                    pass
            return deleted

    def update_records(
        self, zone: str, old_content: str, new_content: str, record_type: str = "A"
    ) -> tuple[int, int]:
        records = self.list_records(zone, record_type)
        matching = [r for r in records if r.content == old_content]

        with self._client() as client:
            updated = 0
            failed = 0
            for r in matching:
                try:
                    resp = client.patch(
                        f"{self.endpoint}/zones/{zone}/records/{r.id}",
                        json={"content": new_content},
                    )
                    resp.raise_for_status()
                    updated += 1
                except Exception:
                    failed += 1
            return updated, failed


register_provider("coredns", CoreDNSProvider)
