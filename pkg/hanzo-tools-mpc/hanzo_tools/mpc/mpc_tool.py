"""MCP tool for MPC threshold signing -- vaults, wallets, transactions, policies.

Provides a unified interface for managing MPC (Multi-Party Computation)
threshold signing operations including vault management, wallet keygen,
transaction signing, approval workflows, and cross-chain bridge signing.

Auth: Uses HanzoSession from hanzo-tools-auth for authenticated API calls.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Annotated, final

from pydantic import Field
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core.base import BaseTool

logger = logging.getLogger(__name__)

DESCRIPTION = """MPC threshold signing -- vaults, wallets, transactions, policies.

Requires authentication via `hanzo login` (stored at ~/.hanzo/auth/token.json).

Status:
- status: MPC service health and status

Vault actions:
- vaults: List vaults
- vault: Get vault details (params: vault_id)
- create_vault: Create a new vault (params: name, description)

Wallet actions:
- wallets: List wallets in a vault (params: vault_id)
- wallet: Get wallet details (params: wallet_id)
- create_wallet: Create wallet / initiate keygen (params: vault_id, name, curve, threshold, parties)

Transaction actions:
- transactions: List transactions
- transaction: Get transaction details (params: transaction_id)
- create_transaction: Create a signing request (params: wallet_id, type, chain, to, amount)
- approve: Approve a transaction (params: transaction_id)
- reject: Reject a transaction (params: transaction_id)
- broadcast: Broadcast a signed transaction (params: transaction_id)

Policy actions:
- policies: List signing policies

Smart wallet actions:
- smart_wallets: List smart contract wallets

Whitelist actions:
- whitelist: List whitelisted addresses

Bridge actions:
- bridge_sign: Sign a cross-chain bridge transaction (params: wallet_id, source_chain, dest_chain, token, amount, recipient)
"""


def _get_session():
    """Get HanzoSession singleton."""
    from hanzo_tools.auth.session import HanzoSession
    return HanzoSession.get()


@final
class MPCTool(BaseTool):
    """MCP tool for MPC threshold signing operations."""

    @property
    def name(self) -> str:
        return "mpc"

    @property
    def description(self) -> str:
        return DESCRIPTION

    async def call(
        self,
        ctx: MCPContext,
        action: str = "status",
        vault_id: str | None = None,
        wallet_id: str | None = None,
        transaction_id: str | None = None,
        name: str | None = None,
        description: str | None = None,
        curve: str | None = None,
        threshold: int | None = None,
        parties: int | None = None,
        type: str | None = None,
        chain: str | None = None,
        to: str | None = None,
        amount: str | None = None,
        source_chain: str | None = None,
        dest_chain: str | None = None,
        token: str | None = None,
        recipient: str | None = None,
        **kwargs: Any,
    ) -> str:
        try:
            # Status
            if action == "status":
                return await self._status()
            # Vault actions
            elif action == "vaults":
                return await self._vaults()
            elif action == "vault":
                return await self._vault(vault_id)
            elif action == "create_vault":
                return await self._create_vault(name, description)
            # Wallet actions
            elif action == "wallets":
                return await self._wallets(vault_id)
            elif action == "wallet":
                return await self._wallet(wallet_id)
            elif action == "create_wallet":
                return await self._create_wallet(vault_id, name, curve, threshold, parties)
            # Transaction actions
            elif action == "transactions":
                return await self._transactions()
            elif action == "transaction":
                return await self._transaction(transaction_id)
            elif action == "create_transaction":
                return await self._create_transaction(wallet_id, type, chain, to, amount)
            elif action == "approve":
                return await self._approve(transaction_id)
            elif action == "reject":
                return await self._reject(transaction_id)
            elif action == "broadcast":
                return await self._broadcast(transaction_id)
            # Policy / smart wallet / whitelist
            elif action == "policies":
                return await self._policies()
            elif action == "smart_wallets":
                return await self._smart_wallets()
            elif action == "whitelist":
                return await self._whitelist()
            # Bridge
            elif action == "bridge_sign":
                return await self._bridge_sign(
                    wallet_id, source_chain, dest_chain, token, amount, recipient,
                )
            else:
                return json.dumps({
                    "error": f"Unknown action: {action}",
                    "available": [
                        "status",
                        "vaults", "vault", "create_vault",
                        "wallets", "wallet", "create_wallet",
                        "transactions", "transaction", "create_transaction",
                        "approve", "reject", "broadcast",
                        "policies", "smart_wallets", "whitelist",
                        "bridge_sign",
                    ],
                })
        except RuntimeError as e:
            return json.dumps({"error": str(e)})
        except Exception as e:
            logger.exception(f"MPC tool error: {e}")
            return json.dumps({"error": f"MPC error: {e}"})

    # -- Helpers -------------------------------------------------------------

    async def _mpc_get(self, path: str) -> Any:
        """GET from the MPC API via the PaaS gateway."""
        session = _get_session()
        paas = session.get_paas_client()
        return paas.get(f"/v1/mpc{path}")

    async def _mpc_post(self, path: str, body: dict | None = None) -> Any:
        """POST to the MPC API via the PaaS gateway."""
        session = _get_session()
        paas = session.get_paas_client()
        return paas.post(f"/v1/mpc{path}", json=body or {})

    async def _mpc_delete(self, path: str) -> Any:
        """DELETE from the MPC API via the PaaS gateway."""
        session = _get_session()
        paas = session.get_paas_client()
        return paas.delete(f"/v1/mpc{path}")

    # -- Status --------------------------------------------------------------

    async def _status(self) -> str:
        data = await self._mpc_get("/status")
        return json.dumps(data, indent=2)

    # -- Vault actions -------------------------------------------------------

    async def _vaults(self) -> str:
        data = await self._mpc_get("/vaults")
        vaults = data if isinstance(data, list) else []
        result = []
        for v in vaults:
            result.append({
                "id": v.get("id"),
                "name": v.get("name"),
                "description": v.get("description"),
                "wallet_count": v.get("walletCount"),
                "created_at": v.get("createdAt"),
            })
        return json.dumps({"count": len(result), "vaults": result}, indent=2)

    async def _vault(self, vault_id: str | None) -> str:
        if not vault_id:
            return json.dumps({"error": "Required: vault_id"})

        data = await self._mpc_get(f"/vaults/{vault_id}")
        return json.dumps(data, indent=2)

    async def _create_vault(self, name: str | None, description: str | None) -> str:
        if not name:
            return json.dumps({"error": "Required: name"})

        body = {"name": name}
        if description:
            body["description"] = description

        result = await self._mpc_post("/vaults", body)
        return json.dumps({
            "action": "create_vault",
            "result": result,
        }, indent=2)

    # -- Wallet actions ------------------------------------------------------

    async def _wallets(self, vault_id: str | None) -> str:
        if not vault_id:
            return json.dumps({"error": "Required: vault_id"})

        data = await self._mpc_get(f"/vaults/{vault_id}/wallets")
        wallets = data if isinstance(data, list) else []
        result = []
        for w in wallets:
            result.append({
                "id": w.get("id"),
                "name": w.get("name"),
                "curve": w.get("curve"),
                "threshold": w.get("threshold"),
                "parties": w.get("parties"),
                "address": w.get("address"),
                "status": w.get("status"),
                "created_at": w.get("createdAt"),
            })
        return json.dumps({
            "vault_id": vault_id,
            "count": len(result),
            "wallets": result,
        }, indent=2)

    async def _wallet(self, wallet_id: str | None) -> str:
        if not wallet_id:
            return json.dumps({"error": "Required: wallet_id"})

        data = await self._mpc_get(f"/wallets/{wallet_id}")
        return json.dumps(data, indent=2)

    async def _create_wallet(
        self,
        vault_id: str | None,
        name: str | None,
        curve: str | None,
        threshold: int | None,
        parties: int | None,
    ) -> str:
        if not vault_id or not name:
            return json.dumps({"error": "Required: vault_id and name"})

        body: dict[str, Any] = {"name": name}
        if curve:
            body["curve"] = curve
        if threshold is not None:
            body["threshold"] = threshold
        if parties is not None:
            body["parties"] = parties

        result = await self._mpc_post(f"/vaults/{vault_id}/wallets", body)
        return json.dumps({
            "action": "create_wallet",
            "vault_id": vault_id,
            "result": result,
        }, indent=2)

    # -- Transaction actions -------------------------------------------------

    async def _transactions(self) -> str:
        data = await self._mpc_get("/transactions")
        txns = data if isinstance(data, list) else []
        result = []
        for t in txns:
            result.append({
                "id": t.get("id"),
                "wallet_id": t.get("walletId"),
                "type": t.get("type"),
                "chain": t.get("chain"),
                "status": t.get("status"),
                "to": t.get("to"),
                "amount": t.get("amount"),
                "created_at": t.get("createdAt"),
            })
        return json.dumps({"count": len(result), "transactions": result}, indent=2)

    async def _transaction(self, transaction_id: str | None) -> str:
        if not transaction_id:
            return json.dumps({"error": "Required: transaction_id"})

        data = await self._mpc_get(f"/transactions/{transaction_id}")
        return json.dumps(data, indent=2)

    async def _create_transaction(
        self,
        wallet_id: str | None,
        type: str | None,
        chain: str | None,
        to: str | None,
        amount: str | None,
    ) -> str:
        if not wallet_id:
            return json.dumps({"error": "Required: wallet_id"})

        body: dict[str, Any] = {"walletId": wallet_id}
        if type:
            body["type"] = type
        if chain:
            body["chain"] = chain
        if to:
            body["to"] = to
        if amount:
            body["amount"] = amount

        result = await self._mpc_post("/transactions", body)
        return json.dumps({
            "action": "create_transaction",
            "result": result,
        }, indent=2)

    async def _approve(self, transaction_id: str | None) -> str:
        if not transaction_id:
            return json.dumps({"error": "Required: transaction_id"})

        result = await self._mpc_post(f"/transactions/{transaction_id}/approve")
        return json.dumps({
            "action": "approve",
            "transaction_id": transaction_id,
            "result": result,
        }, indent=2)

    async def _reject(self, transaction_id: str | None) -> str:
        if not transaction_id:
            return json.dumps({"error": "Required: transaction_id"})

        result = await self._mpc_post(f"/transactions/{transaction_id}/reject")
        return json.dumps({
            "action": "reject",
            "transaction_id": transaction_id,
            "result": result,
        }, indent=2)

    async def _broadcast(self, transaction_id: str | None) -> str:
        if not transaction_id:
            return json.dumps({"error": "Required: transaction_id"})

        result = await self._mpc_post(f"/transactions/{transaction_id}/broadcast")
        return json.dumps({
            "action": "broadcast",
            "transaction_id": transaction_id,
            "result": result,
        }, indent=2)

    # -- Policies / Smart Wallets / Whitelist --------------------------------

    async def _policies(self) -> str:
        data = await self._mpc_get("/policies")
        policies = data if isinstance(data, list) else []
        result = []
        for p in policies:
            result.append({
                "id": p.get("id"),
                "name": p.get("name"),
                "type": p.get("type"),
                "rules": p.get("rules"),
                "created_at": p.get("createdAt"),
            })
        return json.dumps({"count": len(result), "policies": result}, indent=2)

    async def _smart_wallets(self) -> str:
        data = await self._mpc_get("/smart-wallets")
        wallets = data if isinstance(data, list) else []
        result = []
        for w in wallets:
            result.append({
                "id": w.get("id"),
                "name": w.get("name"),
                "chain": w.get("chain"),
                "address": w.get("address"),
                "type": w.get("type"),
                "status": w.get("status"),
            })
        return json.dumps({"count": len(result), "smart_wallets": result}, indent=2)

    async def _whitelist(self) -> str:
        data = await self._mpc_get("/whitelist")
        addresses = data if isinstance(data, list) else []
        result = []
        for a in addresses:
            result.append({
                "id": a.get("id"),
                "address": a.get("address"),
                "chain": a.get("chain"),
                "label": a.get("label"),
                "created_at": a.get("createdAt"),
            })
        return json.dumps({"count": len(result), "addresses": result}, indent=2)

    # -- Bridge signing ------------------------------------------------------

    async def _bridge_sign(
        self,
        wallet_id: str | None,
        source_chain: str | None,
        dest_chain: str | None,
        token: str | None,
        amount: str | None,
        recipient: str | None,
    ) -> str:
        if not wallet_id or not source_chain or not dest_chain:
            return json.dumps({"error": "Required: wallet_id, source_chain, dest_chain"})

        body: dict[str, Any] = {
            "walletId": wallet_id,
            "sourceChain": source_chain,
            "destChain": dest_chain,
        }
        if token:
            body["token"] = token
        if amount:
            body["amount"] = amount
        if recipient:
            body["recipient"] = recipient

        result = await self._mpc_post("/bridge/sign", body)
        return json.dumps({
            "action": "bridge_sign",
            "wallet_id": wallet_id,
            "source_chain": source_chain,
            "dest_chain": dest_chain,
            "result": result,
        }, indent=2)

    # -- Registration --------------------------------------------------------

    def register(self, mcp_server: FastMCP) -> None:
        """Register MPC tool with explicit parameters."""
        tool_instance = self

        @mcp_server.tool(
            name="mpc",
            description=DESCRIPTION,
        )
        async def mpc(
            action: Annotated[
                str,
                Field(
                    description=(
                        "Action to perform. "
                        "Status: status. "
                        "Vaults: vaults, vault, create_vault. "
                        "Wallets: wallets, wallet, create_wallet. "
                        "Transactions: transactions, transaction, create_transaction, approve, reject, broadcast. "
                        "Policies: policies. Smart wallets: smart_wallets. Whitelist: whitelist. "
                        "Bridge: bridge_sign."
                    ),
                ),
            ] = "status",
            vault_id: Annotated[
                str | None,
                Field(description="Vault ID (for vault, wallets, create_wallet)"),
            ] = None,
            wallet_id: Annotated[
                str | None,
                Field(description="Wallet ID (for wallet, create_transaction, bridge_sign)"),
            ] = None,
            transaction_id: Annotated[
                str | None,
                Field(description="Transaction ID (for transaction, approve, reject, broadcast)"),
            ] = None,
            name: Annotated[
                str | None,
                Field(description="Name (for create_vault, create_wallet)"),
            ] = None,
            description: Annotated[
                str | None,
                Field(description="Description (for create_vault)"),
            ] = None,
            curve: Annotated[
                str | None,
                Field(description="Elliptic curve: secp256k1, ed25519 (for create_wallet)"),
            ] = None,
            threshold: Annotated[
                int | None,
                Field(description="Signing threshold (for create_wallet)"),
            ] = None,
            parties: Annotated[
                int | None,
                Field(description="Number of parties (for create_wallet)"),
            ] = None,
            type: Annotated[
                str | None,
                Field(description="Transaction type: transfer, contract_call (for create_transaction)"),
            ] = None,
            chain: Annotated[
                str | None,
                Field(description="Chain identifier (for create_transaction)"),
            ] = None,
            to: Annotated[
                str | None,
                Field(description="Destination address (for create_transaction)"),
            ] = None,
            amount: Annotated[
                str | None,
                Field(description="Amount as string (for create_transaction, bridge_sign)"),
            ] = None,
            source_chain: Annotated[
                str | None,
                Field(description="Source chain (for bridge_sign)"),
            ] = None,
            dest_chain: Annotated[
                str | None,
                Field(description="Destination chain (for bridge_sign)"),
            ] = None,
            token: Annotated[
                str | None,
                Field(description="Token identifier (for bridge_sign)"),
            ] = None,
            recipient: Annotated[
                str | None,
                Field(description="Recipient address (for bridge_sign)"),
            ] = None,
            ctx: MCPContext = None,
        ) -> str:
            return await tool_instance.call(
                ctx,
                action=action,
                vault_id=vault_id,
                wallet_id=wallet_id,
                transaction_id=transaction_id,
                name=name,
                description=description,
                curve=curve,
                threshold=threshold,
                parties=parties,
                type=type,
                chain=chain,
                to=to,
                amount=amount,
                source_chain=source_chain,
                dest_chain=dest_chain,
                token=token,
                recipient=recipient,
            )
