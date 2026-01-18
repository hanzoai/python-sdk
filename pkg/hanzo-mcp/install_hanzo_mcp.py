#!/usr/bin/env python3
"""
Hanzo MCP Installation Script
============================

Unified installer for Hanzo MCP tools that provides:
1. MCP server installation 
2. VS Code extension setup
3. Browser extension setup (future)
4. CLI tools installation
5. Unified backend configuration

Usage:
    python install_hanzo_mcp.py --all                    # Install everything
    python install_hanzo_mcp.py --mcp                    # MCP server only  
    python install_hanzo_mcp.py --vscode                 # VS Code extension only
    python install_hanzo_mcp.py --cli                    # CLI tools only
    python install_hanzo_mcp.py --check                  # Check installation
"""

import os
import sys
import json
import shutil
import argparse
import subprocess
from typing import Dict, List, Optional
from pathlib import Path


class HanzoMCPInstaller:
    """Unified installer for all Hanzo MCP components"""
    
    def __init__(self):
        self.home = Path.home()
        self.hanzo_dir = self.home / ".hanzo"
        self.sessions_dir = self.hanzo_dir / "sessions"
        self.config_file = self.hanzo_dir / "config.json"
        
        # Create directories
        self.hanzo_dir.mkdir(exist_ok=True)
        self.sessions_dir.mkdir(exist_ok=True)
    
    def install_all(self) -> bool:
        """Install all components"""
        print("🚀 Installing Hanzo MCP - Complete Development Environment")
        print("=" * 60)
        
        success = True
        success &= self.install_python_packages()
        success &= self.setup_mcp_server()
        success &= self.install_vscode_extension()
        success &= self.install_cli_tools()
        success &= self.create_config()
        
        if success:
            print("\n✅ Hanzo MCP installation completed successfully!")
            print("\nNext steps:")
            print("1. Restart VS Code to activate the extension")
            print("2. Run `hanzo-mcp` to start the development server")
            print("3. Check ~/.hanzo/config.json for configuration options")
        else:
            print("\n❌ Installation failed. Check errors above.")
        
        return success
    
    def install_python_packages(self) -> bool:
        """Install Python packages with uv"""
        print("📦 Installing Python packages...")
        
        try:
            # Install hanzo-mcp and all tools
            subprocess.run([
                "uv", "pip", "install", "-e", ".", "--all-extras"
            ], check=True, cwd=Path(__file__).parent)
            
            print("✓ Python packages installed")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install Python packages: {e}")
            return False
        except FileNotFoundError:
            print("❌ uv not found. Please install uv first: curl -LsSf https://astral.sh/uv/install.sh | sh")
            return False
    
    def setup_mcp_server(self) -> bool:
        """Setup MCP server for Claude/other AI tools"""
        print("🔌 Setting up MCP server...")
        
        # Create MCP server config
        mcp_config = {
            "mcpServers": {
                "hanzo": {
                    "command": "hanzo-mcp",
                    "args": ["--server"],
                    "env": {
                        "HANZO_SESSION_DIR": str(self.sessions_dir),
                        "HANZO_CONFIG": str(self.config_file)
                    }
                }
            }
        }
        
        # Write to Claude MCP config location
        claude_config_dir = self.home / ".config" / "claude-desktop"
        claude_config_dir.mkdir(parents=True, exist_ok=True)
        claude_config_file = claude_config_dir / "claude_desktop_config.json"
        
        try:
            if claude_config_file.exists():
                # Merge with existing config
                with open(claude_config_file) as f:
                    existing = json.load(f)
                existing.update(mcp_config)
                mcp_config = existing
            
            with open(claude_config_file, "w") as f:
                json.dump(mcp_config, f, indent=2)
            
            print(f"✓ MCP server configured at {claude_config_file}")
            return True
        except Exception as e:
            print(f"❌ Failed to setup MCP server: {e}")
            return False
    
    def install_vscode_extension(self) -> bool:
        """Install and build VS Code extension"""
        print("🔧 Installing VS Code extension...")
        
        extension_dir = Path(__file__).parent / "vscode-extension"
        
        try:
            # Install Node.js dependencies
            subprocess.run(["npm", "install"], check=True, cwd=extension_dir)
            
            # Compile TypeScript
            subprocess.run(["npm", "run", "compile"], check=True, cwd=extension_dir)
            
            # Package extension
            subprocess.run(["npx", "vsce", "package"], check=True, cwd=extension_dir)
            
            # Install extension
            vsix_files = list(extension_dir.glob("*.vsix"))
            if vsix_files:
                subprocess.run([
                    "code", "--install-extension", str(vsix_files[0])
                ], check=True)
                print("✓ VS Code extension installed")
                return True
            else:
                print("❌ No .vsix file found")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install VS Code extension: {e}")
            print("Note: Make sure you have Node.js, npm, and VS Code installed")
            return False
        except FileNotFoundError as e:
            print(f"❌ Required tool not found: {e}")
            return False
    
    def install_cli_tools(self) -> bool:
        """Install CLI tools and create shell aliases"""
        print("💻 Installing CLI tools...")
        
        try:
            # Create CLI wrapper scripts
            cli_script = """#!/usr/bin/env python3
import sys
import asyncio
from hanzo_mcp.dev_tools import DevToolsCore

async def main():
    tools = DevToolsCore()
    
    if len(sys.argv) < 2:
        print("Usage: hanzo-dev <tool> <args>")
        print("Tools: edit, fmt, test, build, lint, guard")
        return 1
    
    tool = sys.argv[1]
    args = sys.argv[2:]
    
    try:
        if tool == "edit" and len(args) >= 2:
            result = await tools.edit(target=args[0], op=args[1])
        elif tool == "fmt" and len(args) >= 1:
            result = await tools.fmt(target=args[0])
        elif tool == "test" and len(args) >= 1:
            result = await tools.test(target=args[0])
        elif tool == "build" and len(args) >= 1:
            result = await tools.build(target=args[0])
        elif tool == "lint" and len(args) >= 1:
            result = await tools.lint(target=args[0])
        elif tool == "guard" and len(args) >= 1:
            result = await tools.guard(target=args[0])
        else:
            print(f"Invalid usage for {tool}")
            return 1
        
        print(f"Result: {result.ok}")
        if result.stdout:
            print(f"Output: {result.stdout}")
        if result.stderr:
            print(f"Error: {result.stderr}")
        if result.touched_files:
            print(f"Modified files: {result.touched_files}")
        
        return 0 if result.ok else 1
        
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
"""
            
            # Install CLI script
            cli_bin = Path("/usr/local/bin/hanzo-dev")
            with open(cli_bin, "w") as f:
                f.write(cli_script)
            cli_bin.chmod(0o755)
            
            # Create shell aliases
            aliases = """
# Hanzo MCP Development Tools
alias hedit='hanzo-dev edit'
alias hfmt='hanzo-dev fmt' 
alias htest='hanzo-dev test'
alias hbuild='hanzo-dev build'
alias hlint='hanzo-dev lint'
alias hguard='hanzo-dev guard'
"""
            
            # Add to shell profiles
            for shell_profile in [".bashrc", ".zshrc", ".profile"]:
                profile_path = self.home / shell_profile
                if profile_path.exists():
                    with open(profile_path, "a") as f:
                        f.write(f"\n# Hanzo MCP aliases\n{aliases}\n")
            
            print("✓ CLI tools installed")
            return True
            
        except Exception as e:
            print(f"❌ Failed to install CLI tools: {e}")
            return False
    
    def create_config(self) -> bool:
        """Create default configuration"""
        print("⚙️  Creating configuration...")
        
        config = {
            "version": "1.0.0",
            "session_tracking": True,
            "codebase_indexing": True,
            "workspace_detection": "auto",
            "default_language": "auto",
            "backends": {
                "go": {
                    "fmt": "goimports",
                    "local_prefix": "github.com/luxfi"
                },
                "ts": {
                    "fmt": "prettier",
                    "package_manager": "pnpm"
                },
                "py": {
                    "fmt": "ruff",
                    "test": "pytest"
                }
            },
            "guard_rules": [
                {
                    "id": "no_node_in_sdk",
                    "type": "import",
                    "glob": "sdk/**",
                    "forbid_import_prefix": "github.com/luxfi/node/"
                },
                {
                    "id": "no_generated_edits",
                    "type": "generated",
                    "glob": "api/pb/**",
                    "forbid_writes": True
                }
            ]
        }
        
        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=2)
            
            print(f"✓ Configuration created at {self.config_file}")
            return True
        except Exception as e:
            print(f"❌ Failed to create configuration: {e}")
            return False
    
    def check_installation(self) -> bool:
        """Check if installation is working"""
        print("🔍 Checking Hanzo MCP installation...")
        
        checks = [
            ("Python package", self.check_python_package),
            ("MCP server", self.check_mcp_server),
            ("CLI tools", self.check_cli_tools),
            ("Configuration", self.check_config),
            ("Session directory", self.check_session_dir)
        ]
        
        all_good = True
        for name, check_fn in checks:
            try:
                result = check_fn()
                status = "✓" if result else "❌"
                print(f"{status} {name}")
                all_good &= result
            except Exception as e:
                print(f"❌ {name}: {e}")
                all_good = False
        
        return all_good
    
    def check_python_package(self) -> bool:
        """Check if Python package is installed"""
        try:
            import hanzo_mcp
            return True
        except ImportError:
            return False
    
    def check_mcp_server(self) -> bool:
        """Check if MCP server is configured"""
        claude_config_file = self.home / ".config" / "claude-desktop" / "claude_desktop_config.json"
        if not claude_config_file.exists():
            return False
        
        try:
            with open(claude_config_file) as f:
                config = json.load(f)
            return "hanzo" in config.get("mcpServers", {})
        except (OSError, json.JSONDecodeError, KeyError):
            return False
    
    def check_cli_tools(self) -> bool:
        """Check if CLI tools are installed"""
        return Path("/usr/local/bin/hanzo-dev").exists()
    
    def check_config(self) -> bool:
        """Check if configuration exists"""
        return self.config_file.exists()
    
    def check_session_dir(self) -> bool:
        """Check if session directory exists"""
        return self.sessions_dir.exists()


def main():
    parser = argparse.ArgumentParser(description="Install Hanzo MCP Development Environment")
    parser.add_argument("--all", action="store_true", help="Install all components")
    parser.add_argument("--mcp", action="store_true", help="Install MCP server only")
    parser.add_argument("--vscode", action="store_true", help="Install VS Code extension only")
    parser.add_argument("--cli", action="store_true", help="Install CLI tools only")
    parser.add_argument("--check", action="store_true", help="Check installation")
    
    args = parser.parse_args()
    
    if not any([args.all, args.mcp, args.vscode, args.cli, args.check]):
        args.all = True  # Default to installing everything
    
    installer = HanzoMCPInstaller()
    
    success = True
    
    if args.check:
        success = installer.check_installation()
    else:
        if args.all:
            success = installer.install_all()
        else:
            if args.mcp:
                success &= installer.setup_mcp_server()
            if args.vscode:
                success &= installer.install_vscode_extension()
            if args.cli:
                success &= installer.install_cli_tools()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()