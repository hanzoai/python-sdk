"""Decentralized marketplace for agent services and resources."""

import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import field, dataclass

from .web3_agent import Web3Agent


class ServiceType(Enum):
    """Types of services agents can offer."""

    DATA = "data"
    COMPUTE = "compute"
    INFERENCE = "inference"
    ANALYSIS = "analysis"
    CODING = "coding"
    RESEARCH = "research"
    CUSTOM = "custom"


@dataclass
class ServiceOffer:
    """Service offered by an agent."""

    id: str
    agent_address: str
    agent_name: str
    service_type: ServiceType
    description: str
    price_eth: float
    min_reputation: float = 0.0
    max_duration_hours: float = 24.0
    requires_tee: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None

    def is_expired(self) -> bool:
        """Check if offer has expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

    def matches_request(self, request: "ServiceRequest") -> bool:
        """Check if offer matches a request."""
        if self.is_expired():
            return False

        # Check service type
        if request.service_type != ServiceType.CUSTOM:
            if self.service_type != request.service_type:
                return False

        # Check price
        if self.price_eth > request.max_price_eth:
            return False

        # Check duration
        if request.duration_hours > self.max_duration_hours:
            return False

        # Check TEE requirement
        if request.requires_tee and not self.requires_tee:
            return False

        return True


@dataclass
class ServiceRequest:
    """Request for a service."""

    id: str
    requester_address: str
    requester_name: str
    service_type: ServiceType
    description: str
    max_price_eth: float
    duration_hours: float = 1.0
    min_reputation: float = 0.0
    requires_tee: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None

    def is_expired(self) -> bool:
        """Check if request has expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


@dataclass
class ServiceMatch:
    """Matched offer and request."""

    match_id: str
    offer: ServiceOffer
    request: ServiceRequest
    agreed_price_eth: float
    escrow_tx: Optional[str] = None
    status: str = "pending"  # pending, active, completed, disputed
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    attestation: Optional[Dict[str, Any]] = None


class AgentMarketplace:
    """Marketplace for agent services."""

    def __init__(self):
        """Initialize marketplace."""
        self.offers: Dict[str, ServiceOffer] = {}
        self.requests: Dict[str, ServiceRequest] = {}
        self.matches: Dict[str, ServiceMatch] = {}

        # Reputation tracking
        self.reputation_scores: Dict[str, float] = {}
        self.completed_transactions: Dict[str, int] = {}

        # Statistics
        self.total_volume_eth = 0.0
        self.total_transactions = 0

    def post_offer(
        self,
        agent: Web3Agent,
        service_type: ServiceType,
        description: str,
        price_eth: float,
        **kwargs,
    ) -> str:
        """Post a service offer.

        Args:
            agent: Agent posting the offer
            service_type: Type of service
            description: Service description
            price_eth: Price in ETH
            **kwargs: Additional offer parameters

        Returns:
            Offer ID
        """
        offer_id = f"offer_{uuid.uuid4().hex[:8]}"

        offer = ServiceOffer(
            id=offer_id,
            agent_address=agent.address or "mock_address",
            agent_name=agent.name,
            service_type=service_type,
            description=description,
            price_eth=price_eth,
            min_reputation=kwargs.get("min_reputation", 0.0),
            max_duration_hours=kwargs.get("max_duration_hours", 24.0),
            requires_tee=kwargs.get("requires_tee", False),
            metadata=kwargs.get("metadata", {}),
            expires_at=kwargs.get("expires_at"),
        )

        self.offers[offer_id] = offer

        # Try to match with existing requests
        self._try_match_offers()

        return offer_id

    def post_request(
        self,
        agent: Web3Agent,
        service_type: ServiceType,
        description: str,
        max_price_eth: float,
        **kwargs,
    ) -> str:
        """Post a service request.

        Args:
            agent: Agent posting the request
            service_type: Type of service needed
            description: Service description
            max_price_eth: Maximum price willing to pay
            **kwargs: Additional request parameters

        Returns:
            Request ID
        """
        request_id = f"request_{uuid.uuid4().hex[:8]}"

        request = ServiceRequest(
            id=request_id,
            requester_address=agent.address or "mock_address",
            requester_name=agent.name,
            service_type=service_type,
            description=description,
            max_price_eth=max_price_eth,
            duration_hours=kwargs.get("duration_hours", 1.0),
            min_reputation=kwargs.get("min_reputation", 0.0),
            requires_tee=kwargs.get("requires_tee", False),
            metadata=kwargs.get("metadata", {}),
            expires_at=kwargs.get("expires_at"),
        )

        self.requests[request_id] = request

        # Try to match with existing offers
        self._try_match_offers()

        return request_id

    def _try_match_offers(self):
        """Try to match offers with requests."""
        # Remove expired items first
        self._clean_expired()

        # Try to match each request
        for _req_id, request in list(self.requests.items()):
            best_offer = None
            best_price = float("inf")

            # Find best matching offer
            for _offer_id, offer in self.offers.items():
                if offer.matches_request(request):
                    # Check reputation requirements
                    provider_rep = self.get_reputation(offer.agent_address)
                    if provider_rep < request.min_reputation:
                        continue

                    requester_rep = self.get_reputation(request.requester_address)
                    if requester_rep < offer.min_reputation:
                        continue

                    # Track best price
                    if offer.price_eth < best_price:
                        best_offer = offer
                        best_price = offer.price_eth

            # Create match if found
            if best_offer:
                self._create_match(best_offer, request)

    def _create_match(self, offer: ServiceOffer, request: ServiceRequest):
        """Create a match between offer and request."""
        match_id = f"match_{uuid.uuid4().hex[:8]}"

        # Agreed price is the offer price (could implement negotiation)
        agreed_price = offer.price_eth

        match = ServiceMatch(
            match_id=match_id,
            offer=offer,
            request=request,
            agreed_price_eth=agreed_price,
            status="pending",
        )

        self.matches[match_id] = match

        # Remove from active lists
        del self.offers[offer.id]
        del self.requests[request.id]

        # Update statistics
        self.total_transactions += 1

        print(
            f"Match created: {offer.agent_name} -> {request.requester_name} for {agreed_price} ETH"
        )

    def complete_match(
        self,
        match_id: str,
        result: Dict[str, Any],
        attestation: Optional[Dict[str, Any]] = None,
    ):
        """Mark a match as completed.

        Args:
            match_id: Match ID
            result: Result of the service
            attestation: Optional TEE attestation
        """
        if match_id not in self.matches:
            raise ValueError(f"Unknown match: {match_id}")

        match = self.matches[match_id]
        match.status = "completed"
        match.completed_at = time.time()
        match.result = result
        match.attestation = attestation

        # Update reputation
        self._update_reputation(
            match.offer.agent_address,
            1.0,  # Positive for completion
        )

        # Update statistics
        self.total_volume_eth += match.agreed_price_eth

        # Track completed transactions
        provider = match.offer.agent_address
        self.completed_transactions[provider] = (
            self.completed_transactions.get(provider, 0) + 1
        )

    def dispute_match(self, match_id: str, reason: str):
        """Dispute a match.

        Args:
            match_id: Match ID
            reason: Dispute reason
        """
        if match_id not in self.matches:
            raise ValueError(f"Unknown match: {match_id}")

        match = self.matches[match_id]
        match.status = "disputed"
        match.result = {"dispute_reason": reason}

        # Negative reputation for provider
        self._update_reputation(match.offer.agent_address, -0.5)

    def get_reputation(self, agent_address: str) -> float:
        """Get agent reputation score.

        Args:
            agent_address: Agent's blockchain address

        Returns:
            Reputation score (0-1)
        """
        return self.reputation_scores.get(agent_address, 0.5)

    def _update_reputation(self, agent_address: str, delta: float):
        """Update agent reputation.

        Args:
            agent_address: Agent's address
            delta: Change in reputation
        """
        current = self.get_reputation(agent_address)
        new_score = max(0, min(1, current + delta * 0.1))  # Damped update
        self.reputation_scores[agent_address] = new_score

    def _clean_expired(self):
        """Remove expired offers and requests."""
        # Clean offers
        expired_offers = [
            oid for oid, offer in self.offers.items() if offer.is_expired()
        ]
        for oid in expired_offers:
            del self.offers[oid]

        # Clean requests
        expired_requests = [
            rid for rid, request in self.requests.items() if request.is_expired()
        ]
        for rid in expired_requests:
            del self.requests[rid]

    def get_active_offers(
        self, service_type: Optional[ServiceType] = None
    ) -> List[ServiceOffer]:
        """Get active offers, optionally filtered by type."""
        self._clean_expired()

        offers = list(self.offers.values())
        if service_type:
            offers = [o for o in offers if o.service_type == service_type]

        return sorted(offers, key=lambda o: o.price_eth)

    def get_active_requests(
        self, service_type: Optional[ServiceType] = None
    ) -> List[ServiceRequest]:
        """Get active requests, optionally filtered by type."""
        self._clean_expired()

        requests = list(self.requests.values())
        if service_type:
            requests = [r for r in requests if r.service_type == service_type]

        return sorted(requests, key=lambda r: r.max_price_eth, reverse=True)

    def get_matches_for_agent(self, agent_address: str) -> List[ServiceMatch]:
        """Get all matches involving an agent."""
        matches = []
        for match in self.matches.values():
            if (
                match.offer.agent_address == agent_address
                or match.request.requester_address == agent_address
            ):
                matches.append(match)

        return sorted(matches, key=lambda m: m.created_at, reverse=True)

    def get_stats(self) -> Dict[str, Any]:
        """Get marketplace statistics."""
        return {
            "active_offers": len(self.offers),
            "active_requests": len(self.requests),
            "total_matches": len(self.matches),
            "total_volume_eth": self.total_volume_eth,
            "total_transactions": self.total_transactions,
            "unique_providers": len(set(o.agent_address for o in self.offers.values())),
            "unique_requesters": len(
                set(r.requester_address for r in self.requests.values())
            ),
        }


# Global marketplace instance (in production, this would be on-chain)
marketplace = AgentMarketplace()
