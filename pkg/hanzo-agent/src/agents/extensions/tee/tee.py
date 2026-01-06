"""Trusted Execution Environment (TEE) support for confidential agent computing.

This module provides interfaces for running agents in secure enclaves,
enabling confidential AI computations with attestation capabilities.
"""

import json
import time
import hashlib
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import field, dataclass


class TEEProvider(Enum):
    """Supported TEE providers."""

    INTEL_SGX = "sgx"
    AMD_SEV = "sev"
    NVIDIA_H100 = "h100"
    MOCK = "mock"


@dataclass
class AttestationReport:
    """TEE attestation report."""

    provider: TEEProvider
    enclave_id: str
    code_hash: str
    timestamp: float
    quote: bytes
    signature: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "provider": self.provider.value,
            "enclave_id": self.enclave_id,
            "code_hash": self.code_hash,
            "timestamp": self.timestamp,
            "quote": self.quote.hex() if isinstance(self.quote, bytes) else self.quote,
            "signature": self.signature,
            "metadata": self.metadata,
        }

    def verify(self, expected_code_hash: Optional[str] = None) -> bool:
        """Verify attestation report.

        In a real implementation, this would verify the TEE provider's
        signature on the quote and optionally check code hash.
        """
        if expected_code_hash and self.code_hash != expected_code_hash:
            return False

        # TODO: Implement actual verification based on provider
        # For now, just check signature format
        return len(self.signature) > 0


@dataclass
class TEEConfig:
    """Configuration for TEE execution."""

    provider: TEEProvider = TEEProvider.MOCK
    max_memory_mb: int = 4096
    max_execution_time_s: int = 300
    enable_network: bool = False
    allowed_endpoints: List[str] = field(default_factory=list)
    attestation_server: Optional[str] = None


class TEEExecutor(ABC):
    """Abstract interface for TEE execution."""

    @abstractmethod
    def execute(
        self, code: str, inputs: Dict[str, Any], config: TEEConfig
    ) -> Dict[str, Any]:
        """Execute code in TEE with given inputs."""
        pass

    @abstractmethod
    def get_attestation(self) -> AttestationReport:
        """Get attestation report for current execution."""
        pass

    @abstractmethod
    def verify_remote_attestation(
        self, report: AttestationReport, expected_code_hash: Optional[str] = None
    ) -> bool:
        """Verify a remote attestation report."""
        pass


class MockTEEExecutor(TEEExecutor):
    """Mock TEE executor for testing."""

    def __init__(self):
        """Initialize mock TEE."""
        self.enclave_id = "mock_enclave_" + str(int(time.time()))
        self.last_code_hash = None
        self.last_result = None

    def execute(
        self, code: str, inputs: Dict[str, Any], config: TEEConfig
    ) -> Dict[str, Any]:
        """Execute code in mock TEE."""
        # Compute code hash
        self.last_code_hash = hashlib.sha256(code.encode()).hexdigest()

        # Simulate execution
        # In real TEE, this would run in isolated enclave
        namespace = {"inputs": inputs, "result": None}

        try:
            exec(code, namespace)
            self.last_result = namespace.get("result", {})

            return {
                "success": True,
                "result": self.last_result,
                "attestation": self.get_attestation().to_dict(),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "attestation": self.get_attestation().to_dict(),
            }

    def get_attestation(self) -> AttestationReport:
        """Get attestation for last execution."""
        return AttestationReport(
            provider=TEEProvider.MOCK,
            enclave_id=self.enclave_id,
            code_hash=self.last_code_hash or "",
            timestamp=time.time(),
            quote=b"mock_quote_data",
            signature="mock_signature_" + (self.last_code_hash or "")[:16],
            metadata={
                "mock": True,
                "result_hash": (
                    hashlib.sha256(
                        json.dumps(self.last_result, sort_keys=True).encode()
                    ).hexdigest()
                    if self.last_result
                    else None
                ),
            },
        )

    def verify_remote_attestation(
        self, report: AttestationReport, expected_code_hash: Optional[str] = None
    ) -> bool:
        """Verify mock attestation."""
        return report.verify(expected_code_hash)


class ConfidentialAgent:
    """Agent that can execute in TEE for confidential computing."""

    def __init__(
        self,
        agent,
        tee_config: Optional[TEEConfig] = None,
        tee_executor: Optional[TEEExecutor] = None,
    ):
        """Initialize confidential agent.

        Args:
            agent: Base agent to wrap
            tee_config: TEE configuration
            tee_executor: TEE executor implementation
        """
        self.agent = agent
        self.tee_config = tee_config or TEEConfig()
        self.tee_executor = tee_executor or MockTEEExecutor()
        self.attestation_history: List[AttestationReport] = []

    def execute_confidential(
        self,
        task_code: str,
        inputs: Dict[str, Any],
        verify_code_hash: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute task in TEE.

        Args:
            task_code: Python code to execute
            inputs: Input data for the task
            verify_code_hash: Expected code hash for verification

        Returns:
            Execution result with attestation
        """
        # Execute in TEE
        result = self.tee_executor.execute(task_code, inputs, self.tee_config)

        # Get and store attestation
        if result.get("success"):
            attestation = AttestationReport(**result["attestation"])
            self.attestation_history.append(attestation)

            # Verify if requested
            if verify_code_hash:
                if not attestation.verify(verify_code_hash):
                    result["warning"] = "Code hash mismatch"

        return result

    def verify_computation(
        self, result: Dict[str, Any], expected_code_hash: Optional[str] = None
    ) -> bool:
        """Verify a computation result came from valid TEE.

        Args:
            result: Result dict with attestation
            expected_code_hash: Expected code hash

        Returns:
            True if verification passes
        """
        if "attestation" not in result:
            return False

        attestation = AttestationReport(**result["attestation"])
        return self.tee_executor.verify_remote_attestation(
            attestation, expected_code_hash
        )

    def get_attestation_history(self) -> List[AttestationReport]:
        """Get history of attestations."""
        return self.attestation_history.copy()


# Precompiled functions for on-chain TEE verification
def create_attestation_verifier_tool():
    """Create a tool for verifying TEE attestations."""
    from ..tool import Tool

    class AttestationVerifierTool(Tool):
        """Tool for verifying TEE attestations."""

        def __init__(self):
            self.name = "verify_attestation"
            self.description = "Verify TEE attestation reports"

        async def verify_attestation(
            self,
            attestation_dict: Dict[str, Any],
            expected_code_hash: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Verify a TEE attestation.

            Args:
                attestation_dict: Attestation report as dict
                expected_code_hash: Expected code hash

            Returns:
                Verification result
            """
            try:
                report = AttestationReport(**attestation_dict)
                is_valid = report.verify(expected_code_hash)

                return {
                    "valid": is_valid,
                    "provider": report.provider.value,
                    "enclave_id": report.enclave_id,
                    "code_hash": report.code_hash,
                    "timestamp": report.timestamp,
                }
            except Exception as e:
                return {"valid": False, "error": str(e)}

        async def compare_attestations(
            self, attestation1: Dict[str, Any], attestation2: Dict[str, Any]
        ) -> Dict[str, Any]:
            """Compare two attestation reports.

            Args:
                attestation1: First attestation
                attestation2: Second attestation

            Returns:
                Comparison result
            """
            try:
                report1 = AttestationReport(**attestation1)
                report2 = AttestationReport(**attestation2)

                return {
                    "same_provider": report1.provider == report2.provider,
                    "same_enclave": report1.enclave_id == report2.enclave_id,
                    "same_code": report1.code_hash == report2.code_hash,
                    "time_diff": abs(report1.timestamp - report2.timestamp),
                }
            except Exception as e:
                return {"error": str(e)}

    return AttestationVerifierTool


# Computation marketplace for TEE resources
@dataclass
class ComputeOffer:
    """Offer to provide computation resources."""

    provider_address: str
    provider_enclave_id: str
    price_per_second: float  # In ETH
    max_duration: int  # Seconds
    supported_providers: List[TEEProvider]
    attestation: Optional[AttestationReport] = None


@dataclass
class ComputeRequest:
    """Request for computation resources."""

    requester_address: str
    code_hash: str
    max_price_per_second: float
    required_duration: int
    required_provider: Optional[TEEProvider] = None


class ComputeMarketplace:
    """Marketplace for TEE compute resources."""

    def __init__(self):
        """Initialize marketplace."""
        self.offers: Dict[str, ComputeOffer] = {}
        self.requests: Dict[str, ComputeRequest] = {}
        self.matches: List[Dict[str, Any]] = []

    def post_offer(self, offer: ComputeOffer) -> str:
        """Post a compute offer."""
        offer_id = f"offer_{len(self.offers)}"
        self.offers[offer_id] = offer
        self._try_match_offers()
        return offer_id

    def post_request(self, request: ComputeRequest) -> str:
        """Post a compute request."""
        request_id = f"request_{len(self.requests)}"
        self.requests[request_id] = request
        self._try_match_offers()
        return request_id

    def _try_match_offers(self):
        """Try to match offers with requests."""
        for req_id, request in list(self.requests.items()):
            for offer_id, offer in list(self.offers.items()):
                # Check if offer matches request
                if (
                    offer.price_per_second <= request.max_price_per_second
                    and offer.max_duration >= request.required_duration
                    and (
                        not request.required_provider
                        or request.required_provider in offer.supported_providers
                    )
                ):
                    # Create match
                    match = {
                        "request_id": req_id,
                        "offer_id": offer_id,
                        "provider": offer.provider_address,
                        "requester": request.requester_address,
                        "price_per_second": offer.price_per_second,
                        "duration": request.required_duration,
                        "total_price": offer.price_per_second
                        * request.required_duration,
                        "timestamp": time.time(),
                    }

                    self.matches.append(match)

                    # Remove matched items
                    del self.requests[req_id]
                    del self.offers[offer_id]

                    break

    def get_matches(self) -> List[Dict[str, Any]]:
        """Get all matches."""
        return self.matches.copy()

    def get_active_offers(self) -> Dict[str, ComputeOffer]:
        """Get active offers."""
        return self.offers.copy()

    def get_active_requests(self) -> Dict[str, ComputeRequest]:
        """Get active requests."""
        return self.requests.copy()
