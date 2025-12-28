"""Metastable consensus protocol.

Two-phase finality for distributed agreement.

Phase I (Sampling):
- Each participant proposes initial response
- k-peer sampling per round
- Confidence accumulation toward β₁

Phase II (Finality):
- Threshold aggregation
- β₂ finality threshold
- Winner synthesis

Reference: https://github.com/luxfi/consensus
"""

import random
import asyncio
from typing import Any, Dict, List, TypeVar, Callable, Optional, Coroutine
from dataclasses import field, dataclass

T = TypeVar("T")


@dataclass
class Result:
    """Participant result."""
    id: str
    output: str
    ok: bool
    error: Optional[str] = None
    ms: int = 0
    round: int = 0


@dataclass
class State:
    """Consensus state."""
    prompt: str
    participants: List[str]
    rounds: int
    k: int  # Sample size per round
    alpha: float  # Agreement threshold (0-1)
    beta_1: float  # Preference threshold (Phase I)
    beta_2: float  # Decision threshold (Phase II)
    
    # State
    responses: Dict[str, List[str]] = field(default_factory=dict)
    confidence: Dict[str, float] = field(default_factory=dict)
    luminance: Dict[str, float] = field(default_factory=dict)
    finalized: bool = False
    winner: Optional[str] = None
    synthesis: Optional[str] = None
    discussion_history: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class Consensus:
    """Metastable consensus protocol.
    
    Args:
        participants: List of participant IDs
        execute: Async function (id, prompt) -> Result
        rounds: Number of sampling rounds (default: 3)
        k: Sample size per round (default: 3)
        alpha: Agreement threshold (default: 0.6)
        beta_1: Preference threshold (default: 0.5)
        beta_2: Decision threshold (default: 0.8)
    """
    participants: List[str]
    execute: Callable[[str, str], Coroutine[Any, Any, Result]]
    rounds: int = 3
    k: int = 3
    alpha: float = 0.6
    beta_1: float = 0.5
    beta_2: float = 0.8
    
    async def run(self, prompt: str) -> State:
        """Run consensus protocol."""
        state = State(
            prompt=prompt,
            participants=self.participants,
            rounds=self.rounds,
            k=min(self.k, len(self.participants)),
            alpha=self.alpha,
            beta_1=self.beta_1,
            beta_2=self.beta_2,
        )
        
        # Initialize
        for p in self.participants:
            state.luminance[p] = 1.0
            state.confidence[p] = 0.0
            state.responses[p] = []
        
        # Phase I: Sampling - initial proposals
        initial = await asyncio.gather(*[
            self.execute(p, prompt) for p in self.participants
        ])
        
        for r in initial:
            state.responses[r.id].append(r.output)
            if r.ok and r.ms > 0:
                # Faster = higher luminance
                state.luminance[r.id] = 1.0 / (1.0 + r.ms / 1000.0)
        
        # Sampling rounds
        for _ in range(self.rounds):
            # Luminance-weighted peer selection
            weights = [state.luminance[p] for p in self.participants]
            total = sum(weights)
            sampled = random.choices(
                self.participants, 
                [w / total for w in weights], 
                k=state.k
            )
            
            # Build context from sampled peers
            context = [f"Query: {prompt}", "", "Peers:"]
            for p in sampled:
                if state.responses[p]:
                    context.append(f"[{p}] {state.responses[p][-1][:1000]}")
            context.append("\nRefine your response:")
            
            # Each participant refines
            round_results = await asyncio.gather(*[
                self.execute(p, "\n".join(context)) for p in self.participants
            ])
            
            for r in round_results:
                state.responses[r.id].append(r.output)
                if r.ok:
                    # Agreement metric
                    agreement = self._agreement(r.output, sampled, state)
                    state.confidence[r.id] = state.confidence[r.id] * 0.5 + agreement * 0.5
            
            # Check β₁ threshold
            if max(state.confidence.values()) >= self.beta_1:
                break
        
        # Phase II: Finality
        scores = {p: state.confidence[p] * state.luminance[p] for p in self.participants}
        state.winner = max(scores, key=lambda p: scores[p])
        
        if scores[state.winner] >= self.beta_2:
            state.finalized = True
        
        # Synthesis
        if state.responses[state.winner]:
            state.synthesis = state.responses[state.winner][-1]
        
        return state
    
    def _agreement(self, output: str, sampled: List[str], state: State) -> float:
        """Calculate agreement with sampled peers."""
        if not sampled:
            return 0.0
        
        total = 0.0
        for p in sampled:
            if state.responses[p]:
                r_words = set(output.lower().split())
                p_words = set(state.responses[p][-1].lower().split())
                if r_words and p_words:
                    overlap = len(r_words & p_words) / len(r_words | p_words)
                    total += overlap
        
        return total / len(sampled)


async def run(
    prompt: str,
    participants: List[str],
    execute: Callable[[str, str], Coroutine[Any, Any, Result]],
    rounds: int = 3,
    k: int = 3,
    alpha: float = 0.6,
    beta_1: float = 0.5,
    beta_2: float = 0.8,
) -> State:
    """Run metastable consensus.
    
    Args:
        prompt: Query to reach consensus on
        participants: List of participant IDs
        execute: Async function (id, prompt) -> Result
        rounds: Sampling rounds
        k: Sample size per round
        alpha: Agreement threshold
        beta_1: Preference threshold
        beta_2: Decision threshold
    
    Returns:
        Final consensus state
    """
    consensus = Consensus(
        participants=participants,
        execute=execute,
        rounds=rounds,
        k=k,
        alpha=alpha,
        beta_1=beta_1,
        beta_2=beta_2,
    )
    return await consensus.run(prompt)
