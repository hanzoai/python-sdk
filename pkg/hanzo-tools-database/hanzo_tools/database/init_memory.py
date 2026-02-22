"""Initialize default memory structure for new projects."""

import os
from typing import Optional
from pathlib import Path


def init_global_memory():
    """Initialize global memory structure in ~/.hanzo/memory/."""
    hanzo_dir = Path.home() / ".hanzo"
    memory_dir = hanzo_dir / "memory"

    # Create directories
    memory_dir.mkdir(parents=True, exist_ok=True)

    # Template directory
    template_dir = Path(__file__).parent.parent.parent / "templates"

    # Copy templates if they don't exist
    templates = [
        ("global_rules.md", "rules.md"),
        ("user_preferences.md", "user_preferences.md"),
        ("coding_standards.md", "coding_standards.md"),
    ]

    for template_file, target_file in templates:
        target_path = memory_dir / target_file
        if not target_path.exists():
            template_path = template_dir / template_file
            if template_path.exists():
                target_path.write_text(template_path.read_text())
                print(f"Created global memory file: {target_path}")

    print(f"Global memory initialized at: {memory_dir}")


def init_project_memory(project_path: Optional[str] = None):
    """Initialize project memory structure in project/.hanzo/memory/."""
    if not project_path:
        project_path = os.getcwd()

    project_path = Path(project_path)
    memory_dir = project_path / ".hanzo" / "memory"

    # Create directories
    memory_dir.mkdir(parents=True, exist_ok=True)
    sessions_dir = memory_dir / "sessions"
    sessions_dir.mkdir(exist_ok=True)

    # Template directory
    template_dir = Path(__file__).parent.parent.parent / "templates"

    # Create architecture.md if it doesn't exist
    arch_file = memory_dir / "architecture.md"
    if not arch_file.exists():
        template_path = template_dir / "architecture.md"
        if template_path.exists():
            content = template_path.read_text()
            # Customize for this project
            project_name = project_path.name
            content = content.replace(
                "# Project Architecture Decisions",
                f"# {project_name} Architecture Decisions",
            )
            arch_file.write_text(content)
            print(f"Created project architecture file: {arch_file}")

    # Create patterns.md template
    patterns_file = memory_dir / "patterns.md"
    if not patterns_file.exists():
        patterns_content = f"""# {project_path.name} Code Patterns

## Common Patterns

### Tool Implementation Pattern
```python
@final
class MyTool(BaseTool):
    def __init__(self, permission_manager: PermissionManager):
        super().__init__(permission_manager)
    
    @property
    @override
    def name(self) -> str:
        return "my_tool"
    
    @property  
    @override
    def description(self) -> str:
        return "Tool description"
    
    @override
    @auto_timeout("my_tool")
    async def call(self, ctx: MCPContext, **params) -> str:
        tool_ctx = self.create_tool_context(ctx)
        # Implementation
        return "Result"
```

### Database Connection Pattern
```python
def get_connection(self, db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn
```

### Error Handling Pattern
```python
try:
    result = operation()
except SpecificError as e:
    await tool_ctx.error(f"Operation failed: {{str(e)}}")
    return f"Error: {{str(e)}}"
```

---

*Add project-specific patterns as they emerge*
"""
        patterns_file.write_text(patterns_content)
        print(f"Created project patterns file: {patterns_file}")

    # Create README for memory system
    readme_file = memory_dir / "README.md"
    if not readme_file.exists():
        readme_content = f"""# {project_path.name} Memory

This directory contains project-specific memories and context files.

## Structure
- `architecture.md` - Architectural decisions and design rationale
- `patterns.md` - Common code patterns used in this project  
- `sessions/` - Daily session logs and insights
- Additional `.md` files - Topic-specific memories

## Usage
```bash
# Read memory
memory --action read --file-path architecture.md

# Append to session
memory --action append --file-path sessions/today.md --content "New insight"

# Search memories
memory --action search --content "database" --scope project

# List all memories  
memory --action list --scope project
```

## Integration
These files are automatically indexed in `.hanzo/db/memory.db` for fast full-text search.
"""
        readme_file.write_text(readme_content)
        print(f"Created memory README: {readme_file}")

    print(f"Project memory initialized at: {memory_dir}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        init_project_memory(sys.argv[1])
    else:
        init_global_memory()
        init_project_memory()
