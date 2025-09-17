"""MCP Bridge for inter-Claude communication.

This module provides MCP server functionality that allows Claude instances
to communicate with each other, enabling peer-to-peer agent networks.
"""

import os
import sys
import json
import asyncio
import logging
import argparse
from typing import Any, Dict, List, Optional
from dataclasses import asdict, dataclass

import mcp.server.fastmcp as mcp
from mcp import tool
from mcp.types import INTERNAL_ERROR, Tool, TextContent
from mcp.server.stdio import stdio_server
from mcp.server.models import InitializationOptions
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)


@dataclass
class BridgeConfig:
    """Configuration for MCP bridge."""

    target_port: int
    instance_id: int
    role: str
    source_instance: Optional[int] = None
    target_instance: Optional[int] = None


class ClaudeBridge(FastMCP):
    """MCP Bridge server for Claude-to-Claude communication."""

    def __init__(self, config: BridgeConfig):
        """Initialize the bridge.

        Args:
            config: Bridge configuration
        """
        # Set server name based on target instance
        super().__init__(f"claude_instance_{config.instance_id}")

        self.config = config
        self.conversation_history: List[Dict[str, Any]] = []
        self.shared_context: Dict[str, Any] = {}

        # Register tools
        self._register_tools()

    def _register_tools(self):
        """Register MCP tools for inter-Claude communication."""

        @self.tool()
        async def chat_with_claude(message: str, context: Optional[str] = None) -> str:
            """Chat with another Claude instance.

            Args:
                message: Message to send to the other Claude
                context: Optional context to provide

            Returns:
                Response from the other Claude instance
            """
            logger.info(f"Bridge {self.config.instance_id}: Received chat request")

            # Record in conversation history
            self.conversation_history.append(
                {
                    "from": self.config.source_instance,
                    "to": self.config.target_instance,
                    "message": message,
                    "context": context,
                }
            )

            # Simulate response (in production, this would make actual API call)
            response = await self._forward_to_claude(message, context)

            self.conversation_history.append(
                {
                    "from": self.config.target_instance,
                    "to": self.config.source_instance,
                    "response": response,
                }
            )

            return response

        @self.tool()
        async def ask_claude_to_review(
            code: str, description: str, focus_areas: Optional[List[str]] = None
        ) -> Dict[str, Any]:
            """Ask another Claude to review code.

            Args:
                code: Code to review
                description: Description of what the code does
                focus_areas: Specific areas to focus on (e.g., ["security", "performance"])

            Returns:
                Review feedback from the other Claude
            """
            logger.info(f"Bridge {self.config.instance_id}: Code review request")

            review_prompt = self._build_review_prompt(code, description, focus_areas)
            review = await self._forward_to_claude(review_prompt)

            return {
                "reviewer": f"claude_{self.config.instance_id}",
                "role": self.config.role,
                "feedback": review,
                "focus_areas": focus_areas or ["general"],
            }

        @self.tool()
        async def delegate_to_claude(
            task: str, requirements: List[str], constraints: Optional[List[str]] = None
        ) -> Dict[str, Any]:
            """Delegate a task to another Claude instance.

            Args:
                task: Task description
                requirements: List of requirements
                constraints: Optional constraints

            Returns:
                Task completion result from the other Claude
            """
            logger.info(f"Bridge {self.config.instance_id}: Task delegation")

            delegation_prompt = self._build_delegation_prompt(task, requirements, constraints)
            result = await self._forward_to_claude(delegation_prompt)

            return {
                "delegated_to": f"claude_{self.config.instance_id}",
                "role": self.config.role,
                "task": task,
                "result": result,
                "status": "completed",
            }

        @self.tool()
        async def get_claude_opinion(
            question: str,
            options: Optional[List[str]] = None,
            criteria: Optional[List[str]] = None,
        ) -> Dict[str, Any]:
            """Get another Claude's opinion on a decision.

            Args:
                question: The question or decision to get opinion on
                options: Optional list of options to choose from
                criteria: Optional evaluation criteria

            Returns:
                Opinion and reasoning from the other Claude
            """
            logger.info(f"Bridge {self.config.instance_id}: Opinion request")

            opinion_prompt = self._build_opinion_prompt(question, options, criteria)
            opinion = await self._forward_to_claude(opinion_prompt)

            return {
                "advisor": f"claude_{self.config.instance_id}",
                "role": self.config.role,
                "question": question,
                "opinion": opinion,
                "options_considered": options,
                "criteria_used": criteria,
            }

        @self.tool()
        async def share_context_with_claude(key: str, value: Any, description: Optional[str] = None) -> bool:
            """Share context with another Claude instance.

            Args:
                key: Context key
                value: Context value
                description: Optional description of the context

            Returns:
                Success status
            """
            logger.info(f"Bridge {self.config.instance_id}: Sharing context '{key}'")

            self.shared_context[key] = {
                "value": value,
                "description": description,
                "shared_by": self.config.source_instance,
                "shared_with": self.config.target_instance,
            }

            return True

        @self.tool()
        async def get_shared_context(key: Optional[str] = None) -> Dict[str, Any]:
            """Get shared context from Claude network.

            Args:
                key: Optional specific key to retrieve

            Returns:
                Shared context data
            """
            if key:
                return self.shared_context.get(key, {})
            return self.shared_context

        @self.tool()
        async def brainstorm_with_claude(
            topic: str, num_ideas: int = 5, constraints: Optional[List[str]] = None
        ) -> List[str]:
            """Brainstorm ideas with another Claude.

            Args:
                topic: Topic to brainstorm about
                num_ideas: Number of ideas to generate
                constraints: Optional constraints

            Returns:
                List of brainstormed ideas
            """
            logger.info(f"Bridge {self.config.instance_id}: Brainstorming request")

            brainstorm_prompt = f"""
            Please brainstorm {num_ideas} ideas about: {topic}
            
            {"Constraints: " + ", ".join(constraints) if constraints else ""}
            
            Provide creative and practical ideas.
            """

            response = await self._forward_to_claude(brainstorm_prompt)

            # Parse response into list (simplified)
            ideas = response.split("\n")
            ideas = [idea.strip() for idea in ideas if idea.strip()]

            return ideas[:num_ideas]

        @self.tool()
        async def get_claude_status() -> Dict[str, Any]:
            """Get status of the connected Claude instance.

            Returns:
                Status information
            """
            return {
                "instance_id": self.config.instance_id,
                "role": self.config.role,
                "status": "available",
                "conversation_count": len(self.conversation_history),
                "shared_context_keys": list(self.shared_context.keys()),
            }

    def _build_review_prompt(self, code: str, description: str, focus_areas: Optional[List[str]]) -> str:
        """Build a code review prompt."""
        prompt = f"""
        Please review the following code:
        
        Description: {description}
        
        Code:
        ```
        {code}
        ```
        """

        if focus_areas:
            prompt += f"\n\nPlease focus particularly on: {', '.join(focus_areas)}"

        prompt += """
        
        Provide constructive feedback on:
        1. Potential bugs or issues
        2. Code quality and best practices
        3. Performance considerations
        4. Security concerns
        5. Suggestions for improvement
        """

        return prompt

    def _build_delegation_prompt(self, task: str, requirements: List[str], constraints: Optional[List[str]]) -> str:
        """Build a task delegation prompt."""
        prompt = f"""
        Please complete the following task:
        
        Task: {task}
        
        Requirements:
        {chr(10).join(f"- {req}" for req in requirements)}
        """

        if constraints:
            prompt += f"""
        
        Constraints:
        {chr(10).join(f"- {con}" for con in constraints)}
        """

        prompt += """
        
        Provide a complete solution that meets all requirements.
        """

        return prompt

    def _build_opinion_prompt(self, question: str, options: Optional[List[str]], criteria: Optional[List[str]]) -> str:
        """Build an opinion request prompt."""
        prompt = f"""
        I need your opinion on the following:
        
        Question: {question}
        """

        if options:
            prompt += f"""
        
        Options to consider:
        {chr(10).join(f"{i + 1}. {opt}" for i, opt in enumerate(options))}
        """

        if criteria:
            prompt += f"""
        
        Please evaluate based on these criteria:
        {chr(10).join(f"- {crit}" for crit in criteria)}
        """

        prompt += """
        
        Provide your recommendation with clear reasoning.
        """

        return prompt

    async def _forward_to_claude(self, prompt: str, context: Optional[str] = None) -> str:
        """Forward a request to the target Claude instance.

        In production, this would make an actual API call to the Claude instance.
        For now, it returns a simulated response.
        """
        # Add context if provided
        full_prompt = prompt
        if context:
            full_prompt = f"Context: {context}\n\n{prompt}"

        # Log the forwarding
        logger.info(f"Forwarding from instance {self.config.source_instance} to {self.config.target_instance}")
        logger.debug(f"Prompt: {full_prompt[:200]}...")

        # In production, this would:
        # 1. Connect to the target Claude instance API
        # 2. Send the prompt
        # 3. Receive and return the response

        # Simulated response based on role
        if self.config.role.startswith("critic"):
            return f"""
            As {self.config.role}, I've analyzed your request:
            
            Strengths:
            - The approach is logical and well-structured
            - Good attention to requirements
            
            Areas for improvement:
            - Consider edge cases more thoroughly
            - Add more comprehensive error handling
            - Optimize for performance in high-load scenarios
            
            Recommendation: Proceed with suggested improvements.
            """
        else:
            return f"""
            Response from {self.config.role} (instance {self.config.instance_id}):
            
            I've processed your request: "{prompt[:100]}..."
            
            The task has been completed successfully with the following approach:
            1. Analyzed the requirements
            2. Implemented the solution
            3. Validated the results
            
            The solution meets all specified criteria.
            """


async def run_bridge_server(config: BridgeConfig):
    """Run the MCP bridge server.

    Args:
        config: Bridge configuration
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info(f"Starting MCP Bridge for Claude instance {config.instance_id}")
    logger.info(f"Role: {config.role}")
    logger.info(f"Target port: {config.target_port}")

    # Create and run the bridge
    bridge = ClaudeBridge(config)

    # Run the stdio server
    async with stdio_server() as (read_stream, write_stream):
        await bridge.run(
            read_stream=read_stream,
            write_stream=write_stream,
            initialization_options=InitializationOptions(
                server_name=bridge.name,
                server_version="1.0.0",
                capabilities=bridge.get_capabilities(),
            ),
        )


def main():
    """Main entry point for the bridge."""
    parser = argparse.ArgumentParser(description="MCP Bridge for Claude-to-Claude communication")
    parser.add_argument(
        "--target-port",
        type=int,
        required=True,
        help="Port of the target Claude instance",
    )
    parser.add_argument(
        "--instance-id",
        type=int,
        required=True,
        help="ID of the target Claude instance",
    )
    parser.add_argument(
        "--role",
        type=str,
        required=True,
        help="Role of the target instance (primary, critic_1, etc.)",
    )

    args = parser.parse_args()

    # Get source/target from environment
    source_instance = int(os.environ.get("SOURCE_INSTANCE", "0"))
    target_instance = int(os.environ.get("TARGET_INSTANCE", args.instance_id))

    config = BridgeConfig(
        target_port=args.target_port,
        instance_id=args.instance_id,
        role=args.role,
        source_instance=source_instance,
        target_instance=target_instance,
    )

    # Run the bridge
    asyncio.run(run_bridge_server(config))


if __name__ == "__main__":
    main()
