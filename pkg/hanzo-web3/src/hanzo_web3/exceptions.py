"""Hanzo Web3 SDK exceptions."""


class HanzoWeb3Error(Exception):
    """Base exception for Hanzo Web3 SDK."""

    pass


class AuthenticationError(HanzoWeb3Error):
    """Invalid or missing API key."""

    pass


class RateLimitError(HanzoWeb3Error):
    """Rate limit exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
    ):
        super().__init__(message)
        self.retry_after = retry_after


class ChainNotSupportedError(HanzoWeb3Error):
    """Chain or network not supported."""

    def __init__(self, chain: str, network: str | None = None):
        msg = f"Chain '{chain}' not supported"
        if network:
            msg = f"Network '{network}' on chain '{chain}' not supported"
        super().__init__(msg)
        self.chain = chain
        self.network = network


class QuotaExceededError(HanzoWeb3Error):
    """Compute unit quota exceeded."""

    def __init__(
        self,
        message: str = "Compute unit quota exceeded",
        current_usage: int | None = None,
        limit: int | None = None,
    ):
        super().__init__(message)
        self.current_usage = current_usage
        self.limit = limit


class RPCError(HanzoWeb3Error):
    """JSON-RPC error from the node."""

    def __init__(self, code: int, message: str, data: str | None = None):
        super().__init__(f"RPC Error {code}: {message}")
        self.code = code
        self.message = message
        self.data = data


class WebhookError(HanzoWeb3Error):
    """Webhook configuration or delivery error."""

    pass


class WalletError(HanzoWeb3Error):
    """Smart wallet operation error."""

    pass


class TransactionError(HanzoWeb3Error):
    """Transaction submission or execution error."""

    def __init__(self, message: str, tx_hash: str | None = None):
        super().__init__(message)
        self.tx_hash = tx_hash
