"""Review tool for agents to request balanced code review from main loop."""

from enum import Enum
from typing import List, Optional, override

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_mcp.tools.common.base import BaseTool


class ReviewFocus(Enum):
    """Types of review focus areas."""

    GENERAL = "general"
    FUNCTIONALITY = "functionality"
    READABILITY = "readability"
    MAINTAINABILITY = "maintainability"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    ARCHITECTURE = "architecture"


class ReviewTool(BaseTool):
    """Tool for agents to request balanced code review from the main loop."""

    name = "review"

    @property
    @override
    def description(self) -> str:
        """Get the tool description."""
        return """Request a balanced, constructive code review from the main loop.

Unlike the critic tool (which plays devil's advocate), this provides:
- Objective assessment of code quality
- Recognition of what's done well
- Constructive suggestions for improvement
- Focus on practical concerns
- No predetermined bias or harsh judgment

Parameters:
- focus: Review focus area (GENERAL, FUNCTIONALITY, READABILITY, MAINTAINABILITY, TESTING, DOCUMENTATION, ARCHITECTURE)
- work_description: Clear description of what you've implemented
- code_snippets: Optional code snippets to review (as a list of strings)
- file_paths: Optional list of file paths you've modified
- context: Optional additional context about the implementation

The review will be balanced, highlighting both strengths and areas for improvement.

Example:
review(
    focus="FUNCTIONALITY",
    work_description="Implemented auto-import feature for Go files",
    code_snippets=["func AddImport(file string, importPath string) error { ... }"],
    file_paths=["/path/to/import_handler.go"],
    context="This will be used to automatically fix missing imports in Go files"
)"""

    async def call(
        self,
        ctx: MCPContext,
        focus: str,
        work_description: str,
        code_snippets: Optional[List[str]] = None,
        file_paths: Optional[List[str]] = None,
        context: Optional[str] = None,
    ) -> str:
        """This is a placeholder - actual implementation happens in AgentTool."""
        # This tool is handled specially in the agent execution
        return f"Review requested for: {work_description}"

    def register(self, server: FastMCP) -> None:
        """Register the tool with the MCP server."""
        tool_self = self

        @server.tool(name=self.name, description=self.description)
        async def review(
            ctx: MCPContext,
            focus: str,
            work_description: str,
            code_snippets: Optional[List[str]] = None,
            file_paths: Optional[List[str]] = None,
            context: Optional[str] = None,
        ) -> str:
            return await tool_self.call(
                ctx, focus, work_description, code_snippets, file_paths, context
            )


class BalancedReviewer:
    """Provides balanced, constructive code reviews."""

    def __init__(self):
        self.review_handlers = {
            ReviewFocus.GENERAL: self._review_general,
            ReviewFocus.FUNCTIONALITY: self._review_functionality,
            ReviewFocus.READABILITY: self._review_readability,
            ReviewFocus.MAINTAINABILITY: self._review_maintainability,
            ReviewFocus.TESTING: self._review_testing,
            ReviewFocus.DOCUMENTATION: self._review_documentation,
            ReviewFocus.ARCHITECTURE: self._review_architecture,
        }

    def review(
        self,
        focus: ReviewFocus,
        work_description: str,
        code_snippets: Optional[List[str]] = None,
        file_paths: Optional[List[str]] = None,
        context: Optional[str] = None,
    ) -> str:
        """Perform a balanced code review."""
        review_func = self.review_handlers.get(focus, self._review_general)
        return review_func(work_description, code_snippets, file_paths, context)

    def _review_general(
        self,
        work_description: str,
        code_snippets: Optional[List[str]],
        file_paths: Optional[List[str]],
        context: Optional[str],
    ) -> str:
        """Provide a general balanced review."""
        response = "📋 GENERAL CODE REVIEW:\n\n"
        response += f"**Work Reviewed:** {work_description}\n\n"

        # Positive observations
        response += "**Positive Aspects:**\n"
        if "fix" in work_description.lower():
            response += "✓ Addressing identified issues proactively\n"
        if "implement" in work_description.lower():
            response += "✓ Adding new functionality to enhance the system\n"
        if code_snippets:
            response += "✓ Code structure appears organized\n"
        if file_paths and len(file_paths) == 1:
            response += "✓ Focused changes in a single file (good for reviewability)\n"
        elif file_paths and len(file_paths) > 1:
            response += "✓ Comprehensive approach across multiple files\n"

        # Constructive suggestions
        response += "\n**Suggestions for Consideration:**\n"
        response += "• Ensure all edge cases are handled appropriately\n"
        response += "• Consider adding unit tests if not already present\n"
        response += "• Verify the changes integrate well with existing code\n"

        if context:
            response += f"\n**Context Consideration:**\n{context}\n"
            response += "→ This context helps understand the implementation choices.\n"

        # Summary
        response += "\n**Summary:**\n"
        response += "The implementation appears sound. Consider the suggestions above to further strengthen the code."

        return response

    def _review_functionality(
        self,
        work_description: str,
        code_snippets: Optional[List[str]],
        file_paths: Optional[List[str]],
        context: Optional[str],
    ) -> str:
        """Review functionality aspects."""
        response = "📋 FUNCTIONALITY REVIEW:\n\n"
        response += f"**Implementation:** {work_description}\n\n"

        response += "**Functional Assessment:**\n"

        # Analyze code snippets if provided
        if code_snippets:
            for i, snippet in enumerate(code_snippets, 1):
                response += f"\nCode Snippet {i}:\n"

                # Check for function definitions
                if "func " in snippet or "def " in snippet or "function " in snippet:
                    response += "✓ Function definition looks properly structured\n"

                # Check for error handling
                if "error" in snippet or "err" in snippet or "try" in snippet:
                    response += "✓ Error handling is present\n"
                elif "return" in snippet:
                    response += "• Consider adding error handling if applicable\n"

                # Check for input validation
                if "if " in snippet or "check" in snippet.lower():
                    response += "✓ Input validation appears to be present\n"

        response += "\n**Functional Considerations:**\n"
        response += "• Does the implementation handle all expected inputs?\n"
        response += "• Are return values meaningful and consistent?\n"
        response += "• Is the functionality easily testable?\n"
        response += "• Does it integrate well with existing features?\n"

        response += "\n**Overall:** The functionality appears to meet the described requirements."

        return response

    def _review_readability(
        self,
        work_description: str,
        code_snippets: Optional[List[str]],
        file_paths: Optional[List[str]],
        context: Optional[str],
    ) -> str:
        """Review code readability."""
        response = "📋 READABILITY REVIEW:\n\n"

        response += "**Readability Factors:**\n"

        if code_snippets:
            total_lines = sum(snippet.count("\n") + 1 for snippet in code_snippets)
            avg_line_length = sum(
                len(line) for snippet in code_snippets for line in snippet.split("\n")
            ) / max(total_lines, 1)

            if avg_line_length < 80:
                response += "✓ Line lengths are reasonable\n"
            else:
                response += (
                    "• Some lines might be too long, consider breaking them up\n"
                )

            # Check naming
            has_good_names = any(
                any(
                    word in snippet
                    for word in ["Add", "Get", "Set", "Create", "Update", "Delete"]
                )
                for snippet in code_snippets
            )
            if has_good_names:
                response += "✓ Function/method names appear descriptive\n"

        response += "\n**Readability Suggestions:**\n"
        response += "• Use meaningful variable and function names\n"
        response += "• Keep functions focused on a single responsibility\n"
        response += "• Add comments for complex logic sections\n"
        response += "• Maintain consistent indentation and formatting\n"

        response += "\n**Overall:** Code readability appears acceptable with room for minor improvements."

        return response

    def _review_maintainability(
        self,
        work_description: str,
        code_snippets: Optional[List[str]],
        file_paths: Optional[List[str]],
        context: Optional[str],
    ) -> str:
        """Review maintainability aspects."""
        response = "📋 MAINTAINABILITY REVIEW:\n\n"

        response += "**Maintainability Factors:**\n"

        # Check file organization
        if file_paths:
            if len(file_paths) == 1:
                response += "✓ Changes are localized to a single file\n"
            else:
                response += "✓ Changes are logically distributed across files\n"

        # Check for modularity in code
        if code_snippets:
            function_count = sum(
                snippet.count("func ")
                + snippet.count("def ")
                + snippet.count("function ")
                for snippet in code_snippets
            )
            if function_count > 0:
                response += "✓ Code is broken into functions/methods\n"

        response += "\n**Maintainability Considerations:**\n"
        response += "• Is the code modular and reusable?\n"
        response += "• Are dependencies clearly defined?\n"
        response += "• Will future developers understand the intent?\n"
        response += "• Is the code structured to allow easy updates?\n"

        response += "\n**Recommendations:**\n"
        response += "• Consider extracting common patterns into utilities\n"
        response += "• Ensure consistent patterns across the codebase\n"
        response += "• Document any non-obvious design decisions\n"

        return response

    def _review_testing(
        self,
        work_description: str,
        code_snippets: Optional[List[str]],
        file_paths: Optional[List[str]],
        context: Optional[str],
    ) -> str:
        """Review testing aspects."""
        response = "📋 TESTING REVIEW:\n\n"

        has_test_files = any("test" in str(path).lower() for path in (file_paths or []))

        if has_test_files:
            response += "✓ Test files are included with the changes\n\n"
        else:
            response += "⚠️ No test files detected in the changes\n\n"

        response += "**Testing Checklist:**\n"
        response += "□ Unit tests for new functions\n"
        response += "□ Integration tests for feature interactions\n"
        response += "□ Edge case coverage\n"
        response += "□ Error condition testing\n"
        response += "□ Performance tests (if applicable)\n"

        response += "\n**Testing Recommendations:**\n"
        response += "• Write tests that document expected behavior\n"
        response += "• Include both positive and negative test cases\n"
        response += "• Ensure tests are maintainable and clear\n"
        response += "• Aim for good coverage of critical paths\n"

        if not has_test_files:
            response += "\n💡 Consider adding tests to ensure reliability and prevent regressions."

        return response

    def _review_documentation(
        self,
        work_description: str,
        code_snippets: Optional[List[str]],
        file_paths: Optional[List[str]],
        context: Optional[str],
    ) -> str:
        """Review documentation aspects."""
        response = "📋 DOCUMENTATION REVIEW:\n\n"

        # Check for documentation in code
        has_comments = False
        if code_snippets:
            has_comments = any(
                "//" in snippet or "/*" in snippet or "#" in snippet or '"""' in snippet
                for snippet in code_snippets
            )

        if has_comments:
            response += "✓ Code includes some documentation\n"
        else:
            response += "• Consider adding documentation comments\n"

        response += "\n**Documentation Guidelines:**\n"
        response += "• Document the 'why' not just the 'what'\n"
        response += "• Include examples for complex functions\n"
        response += "• Document any assumptions or limitations\n"
        response += "• Keep documentation up-to-date with code changes\n"

        response += "\n**Recommended Documentation:**\n"
        response += "• Function/method purpose and parameters\n"
        response += "• Complex algorithm explanations\n"
        response += "• API usage examples\n"
        response += "• Configuration requirements\n"

        return response

    def _review_architecture(
        self,
        work_description: str,
        code_snippets: Optional[List[str]],
        file_paths: Optional[List[str]],
        context: Optional[str],
    ) -> str:
        """Review architectural aspects."""
        response = "📋 ARCHITECTURE REVIEW:\n\n"

        response += "**Architectural Considerations:**\n"

        # Analyze file structure
        if file_paths:
            # Check for separation of concerns
            has_separation = (
                len(set(str(p).split("/")[-2] for p in file_paths if "/" in str(p))) > 1
            )
            if has_separation:
                response += "✓ Changes span multiple modules (good separation)\n"
            else:
                response += "✓ Changes are cohesive within a module\n"

        response += "\n**Architectural Principles:**\n"
        response += "• Single Responsibility - Each component has one clear purpose\n"
        response += "• Open/Closed - Open for extension, closed for modification\n"
        response += "• Dependency Inversion - Depend on abstractions, not concretions\n"
        response += "• Interface Segregation - Keep interfaces focused and minimal\n"

        response += "\n**Questions to Consider:**\n"
        response += "• Does this fit well with the existing architecture?\n"
        response += "• Are the right abstractions in place?\n"
        response += "• Is the coupling between components appropriate?\n"
        response += "• Will this scale as requirements grow?\n"

        if context:
            response += f"\n**Context Impact:**\n{context}\n"
            response += "→ Ensure the architectural choices align with this context.\n"

        return response


class ReviewProtocol:
    """Protocol for review interactions."""

    def __init__(self):
        self.reviewer = BalancedReviewer()
        self.review_count = 0
        self.max_reviews = 3  # Allow up to 3 reviews per task

    def request_review(
        self,
        focus: str,
        work_description: str,
        code_snippets: Optional[List[str]] = None,
        file_paths: Optional[List[str]] = None,
        context: Optional[str] = None,
    ) -> str:
        """Request a balanced review."""
        if self.review_count >= self.max_reviews:
            return "📋 Review limit reached. You've received comprehensive feedback - time to finalize your implementation."

        self.review_count += 1

        try:
            focus_enum = ReviewFocus[focus.upper()]
        except KeyError:
            focus_enum = ReviewFocus.GENERAL

        review = self.reviewer.review(
            focus_enum, work_description, code_snippets, file_paths, context
        )

        header = f"Review {self.review_count}/{self.max_reviews} (Focus: {focus_enum.value}):\n\n"
        footer = "\n\n💡 This is a balanced review - consider both strengths and suggestions."

        return header + review + footer
