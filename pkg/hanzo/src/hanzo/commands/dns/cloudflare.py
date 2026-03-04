"""Cloudflare DNS provider."""

from __future__ import annotations

from typing import Any

import click

from .provider import DNSProvider, DNSRecord, DNSZone, register_provider

CF_API = "https://api.cloudflare.com/client/v4"


class CloudflareProvider(DNSProvider):
    name = "cloudflare"

    def __init__(self, config: dict[str, Any]) -> None:
        self.email = config.get("email", "")
        self.api_key = config.get("api_key", "")
        if not self.email or not self.api_key:
            raise ValueError("Cloudflare requires 'email' and 'api_key'")

    def _headers(self) -> dict[str, str]:
        return {
            "X-Auth-Email": self.email,
            "X-Auth-Key": self.api_key,
            "Content-Type": "application/json",
        }

    def _client(self):
        import httpx
        return httpx.Client(headers=self._headers(), timeout=30.0)

    def _get(self, client, path: str, params: dict[str, Any] | None = None) -> Any:
        resp = client.get(f"{CF_API}{path}", params=params)
        data = resp.json()
        if not data.get("success"):
            errors = data.get("errors", [])
            msg = "; ".join(e.get("message", str(e)) for e in errors)
            raise click.ClickException(f"Cloudflare API error: {msg}")
        return data

    def _resolve_zone_id(self, client, zone_name: str) -> str:
        data = self._get(client, "/zones", params={"name": zone_name, "per_page": "1"})
        zones = data.get("result", [])
        if not zones:
            raise click.ClickException(
                f"Zone '{zone_name}' not found in Cloudflare account."
            )
        return zones[0]["id"]

    # ── Interface implementation ─────────────────────────────────────

    def list_zones(self) -> list[DNSZone]:
        with self._client() as client:
            data = self._get(client, "/zones", params={"per_page": "50"})

        return [
            DNSZone(
                id=z.get("id", ""),
                name=z.get("name", ""),
                status=z.get("status", ""),
                plan=z.get("plan", {}).get("name", ""),
                provider=self.name,
                raw=z,
            )
            for z in data.get("result", [])
        ]

    def list_records(
        self, zone: str, record_type: str | None = None
    ) -> list[DNSRecord]:
        with self._client() as client:
            zone_id = self._resolve_zone_id(client, zone)

            params: dict[str, str] = {"per_page": "100"}
            if record_type:
                params["type"] = record_type

            data = self._get(client, f"/zones/{zone_id}/dns_records", params=params)

        return [
            DNSRecord(
                id=r.get("id", ""),
                zone=zone,
                type=r.get("type", ""),
                name=r.get("name", ""),
                content=r.get("content", ""),
                ttl=r.get("ttl", 1),
                proxied=r.get("proxied", False),
                provider=self.name,
                raw=r,
            )
            for r in data.get("result", [])
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
            zone_id = self._resolve_zone_id(client, zone)

            payload = {
                "type": record_type.upper(),
                "name": full_name,
                "content": content,
                "ttl": ttl,
                "proxied": proxied,
            }

            resp = client.post(
                f"{CF_API}/zones/{zone_id}/dns_records", json=payload
            )
            result = resp.json()

            if result.get("success"):
                rec = result.get("result", {})
                return DNSRecord(
                    id=rec.get("id", ""),
                    zone=zone,
                    type=record_type.upper(),
                    name=rec.get("name", full_name),
                    content=content,
                    ttl=ttl,
                    proxied=proxied,
                    provider=self.name,
                    raw=rec,
                )
            else:
                errors = result.get("errors", [])
                msg = "; ".join(e.get("message", str(e)) for e in errors)
                raise click.ClickException(f"Cloudflare: {msg}")

    def remove_records(
        self, zone: str, name: str, record_type: str | None = None
    ) -> int:
        full_name = name if name.endswith(zone) else f"{name}.{zone}"

        with self._client() as client:
            zone_id = self._resolve_zone_id(client, zone)

            params: dict[str, str] = {"name": full_name, "per_page": "100"}
            if record_type:
                params["type"] = record_type

            data = self._get(client, f"/zones/{zone_id}/dns_records", params=params)
            records = data.get("result", [])

            deleted = 0
            for r in records:
                resp = client.delete(
                    f"{CF_API}/zones/{zone_id}/dns_records/{r['id']}"
                )
                if resp.json().get("success"):
                    deleted += 1
            return deleted

    def update_records(
        self, zone: str, old_content: str, new_content: str, record_type: str = "A"
    ) -> tuple[int, int]:
        with self._client() as client:
            zone_id = self._resolve_zone_id(client, zone)

            data = self._get(
                client,
                f"/zones/{zone_id}/dns_records",
                params={
                    "type": record_type,
                    "content": old_content,
                    "per_page": "100",
                },
            )

            records = data.get("result", [])
            updated = 0
            failed = 0

            for r in records:
                try:
                    resp = client.patch(
                        f"{CF_API}/zones/{zone_id}/dns_records/{r['id']}",
                        json={"content": new_content},
                    )
                    if resp.json().get("success"):
                        updated += 1
                    else:
                        failed += 1
                except Exception:
                    failed += 1

            return updated, failed


register_provider("cloudflare", CloudflareProvider)
