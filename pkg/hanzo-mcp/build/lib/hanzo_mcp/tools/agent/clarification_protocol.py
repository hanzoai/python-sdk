"""Clarification protocol for agent-to-mainloop communication.

This module provides a protocol for agents to request clarification
from the main loop without human intervention.
"""

import json
from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


class ClarificationType(Enum):
    """Types of clarification requests."""

    AMBIGUOUS_INSTRUCTION = "ambiguous_instruction"
    MISSING_CONTEXT = "missing_context"
    MULTIPLE_OPTIONS = "multiple_options"
    CONFIRMATION_NEEDED = "confirmation_needed"
    ADDITIONAL_INFO = "additional_info"


@dataclass
class ClarificationRequest:
    """A request for clarification from an agent."""

    agent_id: str
    request_type: ClarificationType
    question: str
    context: Dict[str, Any]
    options: Optional[List[str]] = None

    def to_json(self) -> str:
        """Convert to JSON for transport."""
        return json.dumps(
            {
                "agent_id": self.agent_id,
                "request_type": self.request_type.value,
                "question": self.question,
                "context": self.context,
                "options": self.options,
            }
        )

    @classmethod
    def from_json(cls, data: str) -> "ClarificationRequest":
        """Create from JSON string."""
        obj = json.loads(data)
        return cls(
            agent_id=obj["agent_id"],
            request_type=ClarificationType(obj["request_type"]),
            question=obj["question"],
            context=obj["context"],
            options=obj.get("options"),
        )


@dataclass
class ClarificationResponse:
    """A response to a clarification request."""

    request_id: str
    answer: str
    additional_context: Optional[Dict[str, Any]] = None

    def to_json(self) -> str:
        """Convert to JSON for transport."""
        return json.dumps(
            {
                "request_id": self.request_id,
                "answer": self.answer,
                "additional_context": self.additional_context,
            }
        )


class ClarificationHandler:
    """Handles clarification requests from agents."""

    def __init__(self):
        self.pending_requests: Dict[str, ClarificationRequest] = {}
        self.request_counter = 0

    def create_request(
        self,
        agent_id: str,
        request_type: ClarificationType,
        question: str,
        context: Dict[str, Any],
        options: Optional[List[str]] = None,
    ) -> str:
        """Create a new clarification request.

        Returns:
            Request ID for tracking
        """
        request = ClarificationRequest(
            agent_id=agent_id,
            request_type=request_type,
            question=question,
            context=context,
            options=options,
        )

        request_id = f"clarify_{self.request_counter}"
        self.request_counter += 1
        self.pending_requests[request_id] = request

        return request_id

    def handle_request(self, request: ClarificationRequest) -> ClarificationResponse:
        """Handle a clarification request automatically.

        This method implements automatic clarification resolution
        based on context and common patterns.
        """
        request_id = f"clarify_{len(self.pending_requests)}"

        # Handle different types of clarification
        if request.request_type == ClarificationType.AMBIGUOUS_INSTRUCTION:
            # Try to clarify based on context
            if "file_path" in request.context:
                if request.context["file_path"].endswith(".go"):
                    answer = "For Go files, ensure you add imports in the correct format and handle both single import and import block cases."
                elif request.context["file_path"].endswith(".py"):
                    answer = "For Python files, add imports at the top of the file after any module docstring."
                else:
                    answer = "Add imports according to the language's conventions."
            else:
                answer = "Proceed with the most reasonable interpretation based on the context."

        elif request.request_type == ClarificationType.MISSING_CONTEXT:
            # Provide additional context based on what's missing
            if "import_path" in request.question.lower():
                answer = "Use the standard import path based on the project structure. Check existing imports in similar files for patterns."
            elif "format" in request.question.lower():
                answer = "Match the existing code style in the file. Use the same indentation and formatting patterns."
            else:
                answer = "Analyze the surrounding code and project structure to infer the missing information."

        elif request.request_type == ClarificationType.MULTIPLE_OPTIONS:
            # Choose the best option based on context
            if request.options:
                # Simple heuristic: choose the first option that seems most standard
                for option in request.options:
                    if "common" in option or "standard" in option:
                        answer = f"Choose option: {option}"
                        break
                else:
                    answer = f"Choose option: {request.options[0]}"
            else:
                answer = "Choose the most conventional approach based on the codebase patterns."

        elif request.request_type == ClarificationType.CONFIRMATION_NEEDED:
            # Auto-confirm safe operations
            if "add import" in request.question.lower():
                answer = "Yes, proceed with adding the import."
            elif "multi_edit" in request.question.lower():
                answer = "Yes, use multi_edit for efficiency."
            else:
                answer = "Proceed if the operation is safe and reversible."

        else:  # ADDITIONAL_INFO
            answer = "Continue with available information and make reasonable assumptions based on context."

        return ClarificationResponse(
            request_id=request_id,
            answer=answer,
            additional_context={"auto_resolved": True},
        )


class AgentClarificationMixin:
    """Mixin for agents to request clarification."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clarification_handler = ClarificationHandler()
        self.clarification_count = 0
        self.max_clarifications = 1  # Allow up to 1 clarification per task

    async def request_clarification(
        self,
        request_type: ClarificationType,
        question: str,
        context: Dict[str, Any],
        options: Optional[List[str]] = None,
    ) -> str:
        """Request clarification from the main loop.

        Args:
            request_type: Type of clarification needed
            question: The question to ask
            context: Relevant context for the question
            options: Optional list of choices

        Returns:
            The clarification response

        Raises:
            RuntimeError: If clarification limit exceeded
        """
        if self.clarification_count >= self.max_clarifications:
            raise RuntimeError("Clarification limit exceeded")

        self.clarification_count += 1

        # Create request
        request = ClarificationRequest(
            agent_id=getattr(self, "agent_id", "unknown"),
            request_type=request_type,
            question=question,
            context=context,
            options=options,
        )

        # In real implementation, this would communicate with main loop
        # For now, use the automatic handler
        response = self.clarification_handler.handle_request(request)

        return response.answer

    def format_clarification_in_output(self, question: str, answer: str) -> str:
        """Format clarification exchange for output."""
        return f"\n🤔 Clarification needed: {question}\n✅ Resolved: {answer}\n"
