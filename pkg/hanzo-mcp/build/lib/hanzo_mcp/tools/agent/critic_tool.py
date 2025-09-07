"""Critic tool for agents to request critical review from main loop."""

from enum import Enum
from typing import List, Optional, override

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_mcp.tools.common.base import BaseTool


class ReviewType(Enum):
    """Types of review requests."""

    CODE_QUALITY = "code_quality"
    CORRECTNESS = "correctness"
    PERFORMANCE = "performance"
    SECURITY = "security"
    COMPLETENESS = "completeness"
    BEST_PRACTICES = "best_practices"
    GENERAL = "general"


class CriticTool(BaseTool):
    """Tool for agents to request critical review from the main loop."""

    name = "critic"

    @property
    @override
    def description(self) -> str:
        """Get the tool description."""
        return """Request critical review and feedback from the main loop.

Use this tool to get automated critical analysis of your work. The main loop will:
- Review your implementation for bugs, edge cases, and improvements
- Check for security issues and best practices
- Suggest performance optimizations
- Ensure completeness and correctness
- Provide actionable feedback for improvements

Parameters:
- review_type: Type of review (CODE_QUALITY, CORRECTNESS, PERFORMANCE, SECURITY, COMPLETENESS, BEST_PRACTICES, GENERAL)
- work_description: Clear description of what you've done
- code_snippets: Optional code snippets to review (as a list of strings)
- file_paths: Optional list of file paths you've modified
- specific_concerns: Optional specific areas you want reviewed

The critic will provide harsh but constructive feedback to ensure high quality.

Example:
critic(
    review_type="CODE_QUALITY",
    work_description="Added import statements to fix undefined symbols in Go files",
    code_snippets=["import (\n    \"fmt\"\n    \"github.com/luxfi/node/common\"\n)"],
    file_paths=["/path/to/atomic.go", "/path/to/network.go"],
    specific_concerns="Are the imports in the correct format and location?"
)"""

    async def call(
        self,
        ctx: MCPContext,
        review_type: str,
        work_description: str,
        code_snippets: Optional[List[str]] = None,
        file_paths: Optional[List[str]] = None,
        specific_concerns: Optional[str] = None,
    ) -> str:
        """This is a placeholder - actual implementation happens in AgentTool."""
        # This tool is handled specially in the agent execution
        return f"Critic review requested for: {work_description}"

    def register(self, server: FastMCP) -> None:
        """Register the tool with the MCP server."""
        tool_self = self

        @server.tool(name=self.name, description=self.description)
        async def critic(
            ctx: MCPContext,
            review_type: str,
            work_description: str,
            code_snippets: Optional[List[str]] = None,
            file_paths: Optional[List[str]] = None,
            specific_concerns: Optional[str] = None,
        ) -> str:
            return await tool_self.call(
                ctx,
                review_type,
                work_description,
                code_snippets,
                file_paths,
                specific_concerns,
            )


class AutoCritic:
    """Automated critic that provides harsh but constructive feedback."""

    def __init__(self):
        self.review_patterns = {
            ReviewType.CODE_QUALITY: self._review_code_quality,
            ReviewType.CORRECTNESS: self._review_correctness,
            ReviewType.PERFORMANCE: self._review_performance,
            ReviewType.SECURITY: self._review_security,
            ReviewType.COMPLETENESS: self._review_completeness,
            ReviewType.BEST_PRACTICES: self._review_best_practices,
            ReviewType.GENERAL: self._review_general,
        }

    def review(
        self,
        review_type: ReviewType,
        work_description: str,
        code_snippets: Optional[List[str]] = None,
        file_paths: Optional[List[str]] = None,
        specific_concerns: Optional[str] = None,
    ) -> str:
        """Perform automated critical review."""
        review_func = self.review_patterns.get(review_type, self._review_general)
        return review_func(
            work_description, code_snippets, file_paths, specific_concerns
        )

    def _review_code_quality(
        self,
        work_description: str,
        code_snippets: Optional[List[str]],
        file_paths: Optional[List[str]],
        specific_concerns: Optional[str],
    ) -> str:
        """Review code quality aspects."""
        issues = []
        suggestions = []

        # Check for common code quality issues
        if code_snippets:
            for snippet in code_snippets:
                # Check for proper error handling
                if "error" in snippet.lower() and "if err" not in snippet:
                    issues.append(
                        "❌ Missing error handling - always check errors in Go"
                    )

                # Check for magic numbers
                if any(char.isdigit() for char in snippet) and "const" not in snippet:
                    suggestions.append(
                        "💡 Consider extracting magic numbers to named constants"
                    )

                # Check for proper imports
                if "import" in snippet:
                    if '"fmt"' in snippet and snippet.count("fmt.") == 0:
                        issues.append("❌ Unused import 'fmt' - remove unused imports")
                    if not snippet.strip().endswith(")") and "import (" in snippet:
                        issues.append("❌ Import block not properly closed")

        # General quality checks
        if "fix" in work_description.lower():
            suggestions.append("💡 Ensure you've tested the fix thoroughly")
            suggestions.append("💡 Consider edge cases and error scenarios")

        if file_paths and len(file_paths) > 5:
            suggestions.append(
                "💡 Large number of files modified - consider breaking into smaller PRs"
            )

        # Build response
        response = "🔍 CODE QUALITY REVIEW:\n\n"

        if issues:
            response += "Issues Found:\n" + "\n".join(issues) + "\n\n"
        else:
            response += "✅ No major code quality issues detected.\n\n"

        if suggestions:
            response += (
                "Suggestions for Improvement:\n" + "\n".join(suggestions) + "\n\n"
            )

        if specific_concerns:
            response += f"Regarding your concern: '{specific_concerns}'\n"
            if "import" in specific_concerns.lower():
                response += "→ Imports look properly formatted. Ensure they're in the standard order: stdlib, external, internal.\n"

        response += "\nOverall: " + (
            "⚠️ Address the issues before proceeding."
            if issues
            else "✅ Good work, but always room for improvement!"
        )

        return response

    def _review_correctness(
        self,
        work_description: str,
        code_snippets: Optional[List[str]],
        file_paths: Optional[List[str]],
        specific_concerns: Optional[str],
    ) -> str:
        """Review correctness aspects."""
        return """🔍 CORRECTNESS REVIEW:

Critical Questions:
❓ Have you verified the changes compile without errors?
❓ Do the changes actually fix the reported issue?
❓ Have you introduced any new bugs or regressions?
❓ Are all edge cases handled properly?

Specific Checks:
- If fixing imports: Verify the import paths are correct for the project
- If modifying logic: Ensure the logic is sound and handles all cases
- If refactoring: Confirm behavior is preserved

⚠️ Remember: Working code > elegant code. Make sure it works first!"""

    def _review_performance(
        self,
        work_description: str,
        code_snippets: Optional[List[str]],
        file_paths: Optional[List[str]],
        specific_concerns: Optional[str],
    ) -> str:
        """Review performance aspects."""
        return """🔍 PERFORMANCE REVIEW:

Performance Considerations:
- Are you doing any operations in loops that could be moved outside?
- Are there any unnecessary allocations or copies?
- Could any synchronous operations be made concurrent?
- Are you caching results that might be reused?

For file operations:
- Consider batch operations over individual ones
- Use buffered I/O for large files
- Avoid reading entire files into memory if possible

💡 Remember: Premature optimization is evil, but obvious inefficiencies should be fixed."""

    def _review_security(
        self,
        work_description: str,
        code_snippets: Optional[List[str]],
        file_paths: Optional[List[str]],
        specific_concerns: Optional[str],
    ) -> str:
        """Review security aspects."""
        return """🔍 SECURITY REVIEW:

Security Checklist:
🔐 No hardcoded secrets or credentials
🔐 All user inputs are validated/sanitized
🔐 File paths are properly validated
🔐 No SQL injection vulnerabilities
🔐 Proper access control checks
🔐 Sensitive data is not logged

⚠️ If in doubt, err on the side of caution!"""

    def _review_completeness(
        self,
        work_description: str,
        code_snippets: Optional[List[str]],
        file_paths: Optional[List[str]],
        specific_concerns: Optional[str],
    ) -> str:
        """Review completeness aspects."""
        tasks_mentioned = work_description.lower()

        response = "🔍 COMPLETENESS REVIEW:\n\n"

        if "fix" in tasks_mentioned and "test" not in tasks_mentioned:
            response += (
                "❌ No mention of tests - have you verified the fix with tests?\n"
            )

        if "import" in tasks_mentioned:
            response += "✓ Import fixes mentioned\n"
            response += "❓ Have you checked for other files with similar issues?\n"
            response += "❓ Are all undefined symbols now resolved?\n"

        if file_paths:
            response += f"\n✓ Modified {len(file_paths)} files\n"
            response += "❓ Are there any related files that also need updates?\n"

        response += "\n💡 Completeness means not just fixing the immediate issue, but considering the broader impact."

        return response

    def _review_best_practices(
        self,
        work_description: str,
        code_snippets: Optional[List[str]],
        file_paths: Optional[List[str]],
        specific_concerns: Optional[str],
    ) -> str:
        """Review best practices."""
        return """🔍 BEST PRACTICES REVIEW:

Go Best Practices (if applicable):
✓ Imports are grouped: stdlib, external, internal
✓ Error handling follows Go idioms
✓ Variable names are clear and idiomatic
✓ Comments explain why, not what
✓ Functions do one thing well

General Best Practices:
✓ Code is self-documenting
✓ DRY principle is followed
✓ SOLID principles are respected
✓ Changes are minimal and focused

💡 Good code is code that others (including future you) can understand and modify."""

    def _review_general(
        self,
        work_description: str,
        code_snippets: Optional[List[str]],
        file_paths: Optional[List[str]],
        specific_concerns: Optional[str],
    ) -> str:
        """General review covering multiple aspects."""
        response = "🔍 GENERAL CRITICAL REVIEW:\n\n"
        response += f"Work Description: {work_description}\n\n"

        # Quick assessment
        response += "Quick Assessment:\n"

        if "fix" in work_description.lower():
            response += "- Type: Bug fix / Error resolution\n"
            response += "- Critical: Ensure the fix is complete and tested\n"
        elif "add" in work_description.lower():
            response += "- Type: Feature addition\n"
            response += "- Critical: Ensure no regressions introduced\n"
        elif "refactor" in work_description.lower():
            response += "- Type: Code refactoring\n"
            response += "- Critical: Ensure behavior is preserved\n"

        if file_paths:
            response += f"- Scope: {len(file_paths)} files affected\n"
            if len(file_paths) > 10:
                response += "- ⚠️ Large scope - consider breaking down\n"

        response += "\nCritical Questions:\n"
        response += "1. Is this the minimal change needed?\n"
        response += "2. Have you considered all edge cases?\n"
        response += "3. Will this work in production?\n"
        response += "4. Is there a simpler solution?\n"

        if specific_concerns:
            response += f"\nYour Concern: {specific_concerns}\n"
            response += "→ Valid concern. Double-check this area carefully.\n"

        response += "\n🎯 Bottom Line: Good work needs critical thinking. Question everything, verify everything."

        return response


class CriticProtocol:
    """Protocol for critic interactions."""

    def __init__(self):
        self.auto_critic = AutoCritic()
        self.review_count = 0
        self.max_reviews = 2  # Allow up to 2 reviews per task

    def request_review(
        self,
        review_type: str,
        work_description: str,
        code_snippets: Optional[List[str]] = None,
        file_paths: Optional[List[str]] = None,
        specific_concerns: Optional[str] = None,
    ) -> str:
        """Request a critical review."""
        if self.review_count >= self.max_reviews:
            return "❌ Review limit exceeded. Time to move forward with what you have."

        self.review_count += 1

        try:
            review_enum = ReviewType[review_type.upper()]
        except KeyError:
            review_enum = ReviewType.GENERAL

        review = self.auto_critic.review(
            review_enum, work_description, code_snippets, file_paths, specific_concerns
        )

        return f"Review {self.review_count}/{self.max_reviews}:\n\n{review}"
