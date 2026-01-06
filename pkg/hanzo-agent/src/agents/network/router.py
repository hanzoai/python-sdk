"""Intelligent routing for agent networks."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Union

from ..items import TResponseInputItem
from ..run_context import RunContextWrapper
from ..logger import logger
from ..tool import function_tool


@dataclass
class RoutingDecision:
    """Result of a routing decision."""
    
    selected_agent: str | None
    """The agent selected to handle the request."""
    
    confidence: float
    """Confidence in the routing decision (0.0 to 1.0)."""
    
    reason: str | None = None
    """Optional explanation for the routing decision."""
    
    fallback_agents: List[str] = None
    """Ordered list of fallback agents if primary fails."""
    
    metadata: Dict[str, Any] = None
    """Additional metadata about the routing decision."""


class Router(ABC):
    """Abstract base class for routing strategies."""
    
    def __init__(self):
        self.agent_info: Dict[str, Dict[str, Any]] = {}
        
    def update_agent_info(self, agent_name: str, capabilities: List[str], metadata: Dict[str, Any]) -> None:
        """Update information about an agent."""
        self.agent_info[agent_name] = {
            "capabilities": capabilities,
            "metadata": metadata,
        }
        
    def remove_agent_info(self, agent_name: str) -> None:
        """Remove information about an agent."""
        self.agent_info.pop(agent_name, None)
        
    @abstractmethod
    async def route(
        self,
        input: str | list[TResponseInputItem],
        available_agents: List[str],
        context: RunContextWrapper[Any] | None = None,
    ) -> RoutingDecision:
        """Route the input to the most appropriate agent.
        
        Args:
            input: The input to route
            available_agents: List of available agent names
            context: Optional context for routing decisions
            
        Returns:
            Routing decision with selected agent
        """
        pass


class SemanticRouter(Router):
    """Router that uses semantic understanding to route requests."""
    
    def __init__(self, model: str | None = None):
        super().__init__()
        self.model = model
        
    async def route(
        self,
        input: str | list[TResponseInputItem],
        available_agents: List[str],
        context: RunContextWrapper[Any] | None = None,
    ) -> RoutingDecision:
        """Route based on semantic understanding of the input."""
        if not available_agents:
            return RoutingDecision(selected_agent=None, confidence=0.0)
            
        # Extract text from input
        if isinstance(input, str):
            text = input
        else:
            # Get the last user message
            text = ""
            for item in reversed(input):
                if isinstance(item, dict) and item.get("role") == "user":
                    text = item.get("content", "")
                    break
                    
        if not text:
            # Default to first available agent
            return RoutingDecision(
                selected_agent=available_agents[0],
                confidence=0.5,
                reason="No user input found, using default agent",
            )
            
        # Score each agent based on capabilities
        scores: Dict[str, float] = {}
        
        for agent_name in available_agents:
            if agent_name not in self.agent_info:
                scores[agent_name] = 0.5  # Default score
                continue
                
            info = self.agent_info[agent_name]
            capabilities = info.get("capabilities", [])
            
            # Simple keyword matching for now
            score = 0.0
            matches = []
            
            for capability in capabilities:
                if capability.lower() in text.lower():
                    score += 1.0
                    matches.append(capability)
                    
            # Normalize score
            if capabilities:
                score = score / len(capabilities)
            else:
                score = 0.5
                
            scores[agent_name] = score
            
            if matches:
                logger.debug(f"Agent '{agent_name}' matched capabilities: {matches}")
                
        # Select agent with highest score
        best_agent = max(scores.keys(), key=lambda k: scores[k])
        best_score = scores[best_agent]
        
        # Get fallback agents
        sorted_agents = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)
        fallback_agents = sorted_agents[1:] if len(sorted_agents) > 1 else []
        
        return RoutingDecision(
            selected_agent=best_agent,
            confidence=best_score,
            reason=f"Best match based on capabilities (score: {best_score:.2f})",
            fallback_agents=fallback_agents,
            metadata={"scores": scores},
        )


class RuleBasedRouter(Router):
    """Router that uses predefined rules to route requests."""
    
    def __init__(self):
        super().__init__()
        self.rules: List[RoutingRule] = []
        
    def add_rule(
        self,
        pattern: str | re.Pattern,
        agent: str,
        priority: int = 0,
        condition: Callable[[str], bool] | None = None,
    ) -> None:
        """Add a routing rule.
        
        Args:
            pattern: Regex pattern to match
            agent: Agent to route to if pattern matches
            priority: Priority of the rule (higher = higher priority)
            condition: Optional additional condition function
        """
        if isinstance(pattern, str):
            pattern = re.compile(pattern, re.IGNORECASE)
            
        self.rules.append(RoutingRule(
            pattern=pattern,
            agent=agent,
            priority=priority,
            condition=condition,
        ))
        
        # Sort rules by priority
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        
    async def route(
        self,
        input: str | list[TResponseInputItem],
        available_agents: List[str],
        context: RunContextWrapper[Any] | None = None,
    ) -> RoutingDecision:
        """Route based on predefined rules."""
        # Extract text from input
        if isinstance(input, str):
            text = input
        else:
            # Get the last user message
            text = ""
            for item in reversed(input):
                if isinstance(item, dict) and item.get("role") == "user":
                    text = item.get("content", "")
                    break
                    
        # Check each rule
        for rule in self.rules:
            if rule.agent not in available_agents:
                continue
                
            if rule.pattern.search(text):
                # Check additional condition if provided
                if rule.condition and not rule.condition(text):
                    continue
                    
                return RoutingDecision(
                    selected_agent=rule.agent,
                    confidence=1.0,
                    reason=f"Matched rule: {rule.pattern.pattern}",
                )
                
        # No rule matched
        if available_agents:
            return RoutingDecision(
                selected_agent=available_agents[0],
                confidence=0.3,
                reason="No rule matched, using default agent",
            )
        else:
            return RoutingDecision(
                selected_agent=None,
                confidence=0.0,
                reason="No agents available",
            )


class LoadBalancingRouter(Router):
    """Router that distributes load across agents."""
    
    def __init__(self, strategy: str = "round_robin"):
        super().__init__()
        self.strategy = strategy
        self.agent_loads: Dict[str, int] = {}
        self.last_index = 0
        
    async def route(
        self,
        input: str | list[TResponseInputItem],
        available_agents: List[str],
        context: RunContextWrapper[Any] | None = None,
    ) -> RoutingDecision:
        """Route based on load balancing strategy."""
        if not available_agents:
            return RoutingDecision(selected_agent=None, confidence=0.0)
            
        if self.strategy == "round_robin":
            # Round-robin selection
            self.last_index = (self.last_index + 1) % len(available_agents)
            selected = available_agents[self.last_index]
            
            return RoutingDecision(
                selected_agent=selected,
                confidence=1.0,
                reason="Round-robin selection",
            )
            
        elif self.strategy == "least_loaded":
            # Select agent with least load
            loads = [(agent, self.agent_loads.get(agent, 0)) for agent in available_agents]
            loads.sort(key=lambda x: x[1])
            
            selected = loads[0][0]
            self.agent_loads[selected] = self.agent_loads.get(selected, 0) + 1
            
            return RoutingDecision(
                selected_agent=selected,
                confidence=1.0,
                reason=f"Least loaded agent (load: {loads[0][1]})",
                metadata={"loads": dict(loads)},
            )
            
        else:
            # Default to first agent
            return RoutingDecision(
                selected_agent=available_agents[0],
                confidence=0.5,
                reason="Unknown strategy, using default",
            )
            
    def reset_load(self, agent: str | None = None) -> None:
        """Reset load counters."""
        if agent:
            self.agent_loads[agent] = 0
        else:
            self.agent_loads.clear()


@dataclass
class RoutingRule:
    """A rule for rule-based routing."""
    pattern: re.Pattern
    agent: str
    priority: int = 0
    condition: Callable[[str], bool] | None = None


class RoutingStrategy:
    """Composite routing strategy that can combine multiple routers."""
    
    def __init__(self):
        self.routers: List[Tuple[Router, float]] = []
        
    def add_router(self, router: Router, weight: float = 1.0) -> None:
        """Add a router with optional weight."""
        self.routers.append((router, weight))
        
    async def route(
        self,
        input: str | list[TResponseInputItem],
        available_agents: List[str],
        context: RunContextWrapper[Any] | None = None,
    ) -> RoutingDecision:
        """Route using weighted combination of routers."""
        if not self.routers:
            return RoutingDecision(selected_agent=None, confidence=0.0)
            
        # Get decisions from all routers
        decisions: List[Tuple[RoutingDecision, float]] = []
        
        for router, weight in self.routers:
            decision = await router.route(input, available_agents, context)
            decisions.append((decision, weight))
            
        # Weighted voting
        agent_scores: Dict[str, float] = {}
        total_weight = sum(weight for _, weight in decisions)
        
        for decision, weight in decisions:
            if decision.selected_agent:
                score = decision.confidence * weight / total_weight
                agent_scores[decision.selected_agent] = agent_scores.get(decision.selected_agent, 0) + score
                
        if not agent_scores:
            return RoutingDecision(selected_agent=None, confidence=0.0)
            
        # Select agent with highest weighted score
        best_agent = max(agent_scores.keys(), key=lambda k: agent_scores[k])
        confidence = agent_scores[best_agent]
        
        return RoutingDecision(
            selected_agent=best_agent,
            confidence=confidence,
            reason="Weighted routing decision",
            metadata={"agent_scores": agent_scores},
        )


def routing_strategy(
    semantic_weight: float = 1.0,
    rules: List[Dict[str, Any]] | None = None,
    load_balancing: str | None = None,
) -> RoutingStrategy:
    """Create a composite routing strategy.
    
    Args:
        semantic_weight: Weight for semantic routing (0 to disable)
        rules: List of rule definitions
        load_balancing: Load balancing strategy ("round_robin" or "least_loaded")
        
    Returns:
        Configured routing strategy
    """
    strategy = RoutingStrategy()
    
    # Add semantic router
    if semantic_weight > 0:
        strategy.add_router(SemanticRouter(), semantic_weight)
        
    # Add rule-based router
    if rules:
        rule_router = RuleBasedRouter()
        for rule in rules:
            rule_router.add_rule(
                pattern=rule["pattern"],
                agent=rule["agent"],
                priority=rule.get("priority", 0),
                condition=rule.get("condition"),
            )
        strategy.add_router(rule_router, 2.0)  # Higher weight for explicit rules
        
    # Add load balancing router
    if load_balancing:
        strategy.add_router(LoadBalancingRouter(load_balancing), 0.5)
        
    return strategy