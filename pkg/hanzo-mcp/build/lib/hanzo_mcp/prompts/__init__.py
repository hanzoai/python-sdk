import os

from mcp.server import FastMCP

from hanzo_mcp.prompts.utils import (
    get_os_info,
    get_git_info,
    get_directory_structure,
)
from hanzo_mcp.prompts.tool_explorer import (
    AGENT_TOOLS_HELP,
    SHELL_TOOLS_HELP,
    BATCH_TOOL_EXAMPLES,
    TOOL_EXPLORER_PROMPT,
    FILESYSTEM_TOOLS_HELP,
)
from hanzo_mcp.prompts.create_release import CREATE_RELEASE_PROMPT
from hanzo_mcp.prompts.project_system import PROJECT_SYSTEM_PROMPT
from hanzo_mcp.prompts.enhanced_prompts import (
    QUICK_START_PROMPT,
    LSP_TOOLS_HELP_PROMPT,
    PAGINATION_GUIDE_PROMPT,
    PERFORMANCE_TIPS_PROMPT,
    MEMORY_VECTOR_HELP_PROMPT,
    CONFIGURATION_GUIDE_PROMPT,
    DATABASE_TOOLS_HELP_PROMPT,
    NETWORK_AGENT_GUIDE_PROMPT,
    TROUBLESHOOTING_GUIDE_PROMPT,
    SECURITY_BEST_PRACTICES_PROMPT,
)
from hanzo_mcp.prompts.compact_conversation import COMPACT_CONVERSATION_PROMPT
from hanzo_mcp.prompts.project_todo_reminder import (
    PROJECT_TODO_EMPTY_REMINDER,
    get_project_todo_reminder,
)

CONTINUE_FROM_LAST_SESSION_PROMPT = """<system-reminder>
This is a reminder that your todo list is currently empty. DO NOT mention this to the user explicitly because they are already aware. If you are working on tasks that would benefit from a todo list please use the TodoWrite tool to create one. If not, please feel free to ignore. Again do not mention this message to the user.
</system-reminder>
"""


def create_project_system_prompt(project_path: str):
    """Factory function to create a project system prompt function."""

    def project_system_prompt() -> str:
        """
        Summarize the conversation so far for a specific project.
        """
        working_directory = project_path
        is_git_repo = os.path.isdir(os.path.join(working_directory, ".git"))
        platform, _, os_version = get_os_info()

        # Get directory structure
        directory_structure = get_directory_structure(working_directory, max_depth=3, include_filtered=False)

        # Get git information
        git_info = get_git_info(working_directory)
        current_branch = git_info.get("current_branch", "")
        main_branch = git_info.get("main_branch", "")
        git_status = git_info.get("git_status", "")
        recent_commits = git_info.get("recent_commits", "")

        return PROJECT_SYSTEM_PROMPT.format(
            working_directory=working_directory,
            is_git_repo=is_git_repo,
            platform=platform,
            os_version=os_version,
            directory_structure=directory_structure,
            current_branch=current_branch,
            main_branch=main_branch,
            git_status=git_status,
            recent_commits=recent_commits,
        )

    return project_system_prompt


def register_all_prompts(mcp_server: FastMCP, projects: list[str] | None = None) -> None:
    @mcp_server.prompt(name="Compact current conversation")
    def compact() -> str:
        """
        Summarize the conversation so far.
        """
        return COMPACT_CONVERSATION_PROMPT

    @mcp_server.prompt(name="Create a new release")
    def create_release() -> str:
        """
        Create a new release for my project.
        """
        return CREATE_RELEASE_PROMPT

    @mcp_server.prompt(name="Continue todo by session id")
    def continue_todo_by_session_id(session_id: str) -> str:
        """
        Continue from the last todo list for the current session.
        """
        return get_project_todo_reminder(session_id)

    @mcp_server.prompt(name="Continue latest todo")
    def continue_latest_todo() -> str:
        """
        Continue from the last todo list for the current session.
        """
        return get_project_todo_reminder()

    @mcp_server.prompt(name="System prompt")
    def manual_project_system_prompt(project_path: str) -> str:
        """
        Detailed system prompt include env,git etc information about the specified project.
        """
        return create_project_system_prompt(project_path)()

    @mcp_server.prompt(name="Explore all tools")
    def explore_tools() -> str:
        """
        Comprehensive guide to all available Hanzo MCP tools and how to use them.
        """
        return TOOL_EXPLORER_PROMPT

    @mcp_server.prompt(name="Filesystem tools help")
    def filesystem_help() -> str:
        """
        Detailed guide for filesystem tools (read, write, edit, search, etc).
        """
        return FILESYSTEM_TOOLS_HELP

    @mcp_server.prompt(name="Agent tools help")
    def agent_help() -> str:
        """
        Guide for using agent tools to delegate complex tasks.
        """
        return AGENT_TOOLS_HELP

    @mcp_server.prompt(name="Shell tools help")
    def shell_help() -> str:
        """
        Guide for shell and command execution tools.
        """
        return SHELL_TOOLS_HELP

    @mcp_server.prompt(name="Batch tool examples")
    def batch_examples() -> str:
        """
        Advanced examples of using the batch tool for parallel operations.
        """
        return BATCH_TOOL_EXAMPLES

    # Enhanced prompts for better discoverability
    @mcp_server.prompt(name="Quick start guide")
    def quick_start() -> str:
        """
        Common workflows and recipes for getting started quickly.
        """
        return QUICK_START_PROMPT

    @mcp_server.prompt(name="Pagination guide")
    def pagination_guide() -> str:
        """
        How to use pagination for large result sets.
        """
        return PAGINATION_GUIDE_PROMPT

    @mcp_server.prompt(name="Memory and vector tools help")
    def memory_vector_help() -> str:
        """
        Guide for semantic search and memory tools.
        """
        return MEMORY_VECTOR_HELP_PROMPT

    @mcp_server.prompt(name="Database tools help")
    def database_help() -> str:
        """
        SQL and graph database operations guide.
        """
        return DATABASE_TOOLS_HELP_PROMPT

    @mcp_server.prompt(name="LSP tools help")
    def lsp_help() -> str:
        """
        Language Server Protocol features and code intelligence.
        """
        return LSP_TOOLS_HELP_PROMPT

    @mcp_server.prompt(name="Configuration guide")
    def config_guide() -> str:
        """
        How to configure tools, presets, and settings.
        """
        return CONFIGURATION_GUIDE_PROMPT

    @mcp_server.prompt(name="Network agent guide")
    def network_guide() -> str:
        """
        Distributed AI orchestration with network/swarm tools.
        """
        return NETWORK_AGENT_GUIDE_PROMPT

    @mcp_server.prompt(name="Performance tips")
    def performance_tips() -> str:
        """
        Optimization strategies for better performance.
        """
        return PERFORMANCE_TIPS_PROMPT

    @mcp_server.prompt(name="Security best practices")
    def security_practices() -> str:
        """
        Safe usage patterns and security guidelines.
        """
        return SECURITY_BEST_PRACTICES_PROMPT

    @mcp_server.prompt(name="Troubleshooting guide")
    def troubleshooting() -> str:
        """
        Common issues and their solutions.
        """
        return TROUBLESHOOTING_GUIDE_PROMPT

    if projects is None:
        return

    for project in projects:
        # Register the prompt with the factory function
        mcp_server.prompt(
            name=f"System prompt for {os.path.basename(project)}",
            description=f"Detailed system prompt include env,git etc information about {project}",
        )(create_project_system_prompt(project))

    return


__all__ = [
    "register_all_prompts",
    "get_project_todo_reminder",
    "PROJECT_TODO_EMPTY_REMINDER",
]
