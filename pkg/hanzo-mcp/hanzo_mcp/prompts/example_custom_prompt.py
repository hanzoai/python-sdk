"""Example custom prompt for demonstration."""

# This is the actual prompt text that will be sent to Claude
EXAMPLE_GREETING_PROMPT = """You are a friendly assistant. Please greet the user warmly and ask how you can help them today. 
Make your greeting personalized based on the time of day if possible."""

EXAMPLE_CODE_REVIEW_PROMPT = """Please perform a thorough code review of the most recent code changes in our conversation. 
Focus on:
1. Code quality and best practices
2. Potential bugs or edge cases
3. Performance considerations
4. Security implications
5. Suggestions for improvement

Be constructive and specific in your feedback."""


# You can also create dynamic prompts that take parameters
def create_custom_analysis_prompt(file_path: str, analysis_type: str = "general"):
    """Create a dynamic analysis prompt for a specific file."""

    analysis_types = {
        "general": "Provide a general analysis including structure, purpose, and quality",
        "security": "Focus on security vulnerabilities and best practices",
        "performance": "Analyze performance bottlenecks and optimization opportunities",
        "refactor": "Suggest refactoring opportunities to improve code maintainability",
    }

    analysis_instruction = analysis_types.get(analysis_type, analysis_types["general"])

    return f"""Please analyze the file at {file_path}.

{analysis_instruction}

Your analysis should include:
1. Overview of the file's purpose and structure
2. Key findings based on the analysis type
3. Specific recommendations with code examples where applicable
4. Priority ranking of any issues found

Be thorough but concise in your analysis."""
