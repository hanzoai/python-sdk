#!/usr/bin/env python3
"""
Hanzo MCP Installation and Setup Tool
=====================================

Easy installation script for all Hanzo MCP components:
- MCP server (for Claude/AI tools) 
- VS Code extension
- Browser extension
- Python package
- Backend service

Usage:
    python install_hanzo_mcp.py --all
    python install_hanzo_mcp.py --mcp-server --vscode
    python install_hanzo_mcp.py --backend-only
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
import json
import shutil
import requests
from typing import Dict, List, Optional


class HanzoMCPInstaller:
    """Unified installer for all Hanzo MCP components"""
    
    def __init__(self):
        self.hanzo_dir = Path.home() / ".hanzo"
        self.install_dir = self.hanzo_dir / "mcp"
        self.config_dir = self.hanzo_dir / "config"
        
        # Ensure directories exist
        self.hanzo_dir.mkdir(exist_ok=True)
        self.install_dir.mkdir(exist_ok=True) 
        self.config_dir.mkdir(exist_ok=True)
    
    def install_python_package(self):
        """Install hanzo-mcp Python package"""
        print("📦 Installing Hanzo MCP Python package...")
        
        try:
            # Install from PyPI or local package
            subprocess.run([
                sys.executable, "-m", "pip", "install", "hanzo-mcp"
            ], check=True)
            
            print("✅ Python package installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install Python package: {e}")
            return False
    
    def install_mcp_server(self):
        """Install and configure MCP server"""
        print("🔌 Setting up MCP server...")
        
        try:
            # Install MCP package if not already installed
            if not self.install_python_package():
                return False
            
            # Create MCP server configuration
            server_config = {
                "mcpServers": {
                    "hanzo": {
                        "command": sys.executable,
                        "args": ["-m", "hanzo_mcp.mcp_server"],
                        "env": {
                            "HANZO_MCP_CONFIG": str(self.config_dir / "mcp.json")
                        }
                    }
                }
            }
            
            # Write configuration for different MCP clients
            claude_config_dir = Path.home() / ".config" / "claude-desktop"
            claude_config_dir.mkdir(parents=True, exist_ok=True)
            
            claude_config_file = claude_config_dir / "claude_desktop_config.json"
            
            if claude_config_file.exists():
                # Merge with existing configuration
                with open(claude_config_file) as f:
                    existing_config = json.load(f)
                existing_config.setdefault("mcpServers", {}).update(server_config["mcpServers"])
                server_config = existing_config
            
            with open(claude_config_file, "w") as f:
                json.dump(server_config, f, indent=2)
            
            print(f"✅ MCP server configured at {claude_config_file}")
            print("   Restart Claude Desktop to use Hanzo MCP tools")
            return True
            
        except Exception as e:
            print(f"❌ Failed to install MCP server: {e}")
            return False
    
    def install_vscode_extension(self):
        """Install VS Code extension"""
        print("🆚 Installing VS Code extension...")
        
        try:
            # Check if VS Code is installed
            vscode_cmd = None
            for cmd in ["code", "code-insiders"]:
                if shutil.which(cmd):
                    vscode_cmd = cmd
                    break
            
            if not vscode_cmd:
                print("❌ VS Code not found in PATH")
                print("   Please install VS Code first: https://code.visualstudio.com/")
                return False
            
            # Build and install extension
            extension_dir = Path(__file__).parent / "vscode-extension"
            
            if not extension_dir.exists():
                print("❌ VS Code extension source not found")
                return False
            
            # Install dependencies and build
            subprocess.run(["npm", "install"], cwd=extension_dir, check=True)
            subprocess.run(["npm", "run", "compile"], cwd=extension_dir, check=True)
            
            # Package and install extension
            subprocess.run(["npm", "run", "package"], cwd=extension_dir, check=True)
            
            # Find the .vsix file
            vsix_files = list(extension_dir.glob("*.vsix"))
            if not vsix_files:
                print("❌ Extension package not found")
                return False
            
            vsix_file = vsix_files[0]
            subprocess.run([vscode_cmd, "--install-extension", str(vsix_file)], check=True)
            
            print("✅ VS Code extension installed successfully")
            print("   Restart VS Code to activate Hanzo MCP tools")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install VS Code extension: {e}")
            return False
        except FileNotFoundError as e:
            print(f"❌ Dependency not found: {e}")
            print("   Please install Node.js and npm first")
            return False
    
    def install_browser_extension(self):
        """Install browser extension"""
        print("🌐 Browser extension setup...")
        
        # For now, provide manual installation instructions
        print("📋 Browser Extension Installation:")
        print("   1. Open Chrome/Edge/Firefox")
        print("   2. Go to Extensions page")
        print("   3. Enable Developer mode")
        print("   4. Load unpacked extension from:")
        print(f"      {Path(__file__).parent / 'browser-extension'}")
        print("   5. The extension will connect to your local backend")
        
        return True
    
    def install_backend_service(self):
        """Install and configure backend service"""
        print("⚙️ Setting up backend service...")
        
        try:
            if not self.install_python_package():
                return False
            
            # Create systemd service (Linux) or launchd plist (macOS)
            if sys.platform.startswith("linux"):
                return self._install_systemd_service()
            elif sys.platform == "darwin":
                return self._install_launchd_service()
            elif sys.platform.startswith("win"):
                return self._install_windows_service()
            else:
                print("❌ Unsupported platform for auto-service installation")
                print("   You can manually run: python -m hanzo_mcp.backend")
                return False
        
        except Exception as e:
            print(f"❌ Failed to install backend service: {e}")
            return False
    
    def _install_systemd_service(self):
        """Install systemd service on Linux"""
        service_content = f"""[Unit]
Description=Hanzo MCP Backend Service
After=network.target

[Service]
Type=simple
User={os.getenv('USER')}
WorkingDirectory={Path.home()}
Environment=HANZO_MCP_CONFIG={self.config_dir / 'backend.json'}
ExecStart={sys.executable} -m hanzo_mcp.unified_backend
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
        
        service_file = Path("/tmp/hanzo-mcp.service")
        with open(service_file, "w") as f:
            f.write(service_content)
        
        try:
            subprocess.run(["sudo", "mv", str(service_file), "/etc/systemd/system/"], check=True)
            subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
            subprocess.run(["sudo", "systemctl", "enable", "hanzo-mcp"], check=True)
            subprocess.run(["sudo", "systemctl", "start", "hanzo-mcp"], check=True)
            
            print("✅ Backend service installed and started")
            print("   Service will auto-start on boot")
            return True
            
        except subprocess.CalledProcessError:
            print("❌ Failed to install systemd service (requires sudo)")
            print("   You can manually run: python -m hanzo_mcp.unified_backend")
            return False
    
    def _install_launchd_service(self):
        """Install launchd service on macOS"""
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>ai.hanzo.mcp.backend</string>
    <key>Program</key>
    <string>{sys.executable}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>-m</string>
        <string>hanzo_mcp.unified_backend</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{Path.home()}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>HANZO_MCP_CONFIG</key>
        <string>{self.config_dir / 'backend.json'}</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{self.hanzo_dir / 'logs' / 'backend.log'}</string>
    <key>StandardErrorPath</key>
    <string>{self.hanzo_dir / 'logs' / 'backend.error.log'}</string>
</dict>
</plist>
"""
        
        # Create logs directory
        logs_dir = self.hanzo_dir / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        plist_file = Path.home() / "Library/LaunchAgents/ai.hanzo.mcp.backend.plist"
        plist_file.parent.mkdir(exist_ok=True)
        
        with open(plist_file, "w") as f:
            f.write(plist_content)
        
        try:
            subprocess.run(["launchctl", "load", str(plist_file)], check=True)
            print("✅ Backend service installed and started")
            print("   Service will auto-start on login")
            return True
            
        except subprocess.CalledProcessError:
            print("❌ Failed to install launchd service")
            print("   You can manually run: python -m hanzo_mcp.unified_backend")
            return False
    
    def _install_windows_service(self):
        """Install Windows service"""
        print("🪟 Windows service installation not yet implemented")
        print("   You can manually run: python -m hanzo_mcp.unified_backend")
        print("   Or add to Windows startup folder")
        return False
    
    def create_default_config(self):
        """Create default configuration files"""
        print("⚙️ Creating default configuration...")
        
        # Backend configuration
        backend_config = {
            "backend": {
                "host": "localhost",
                "port": 8765,
                "log_level": "INFO"
            },
            "tools": {
                "edit": {"enabled": True},
                "fmt": {"enabled": True}, 
                "test": {"enabled": True},
                "build": {"enabled": True},
                "lint": {"enabled": True},
                "guard": {"enabled": True}
            },
            "indexing": {
                "enabled": True,
                "auto_index": True,
                "excluded_dirs": [".git", "node_modules", "__pycache__", ".venv"]
            },
            "guard_rules": [
                {
                    "id": "no-node-in-sdk",
                    "type": "import",
                    "glob": "sdk/**/*.py",
                    "forbid_import_prefix": "node"
                },
                {
                    "id": "no-http-in-contracts",
                    "type": "import", 
                    "glob": "api/**/*.py",
                    "forbid_import_prefix": "requests"
                },
                {
                    "id": "no-edits-in-generated",
                    "type": "generated",
                    "glob": "api/pb/**",
                    "forbid_writes": True
                }
            ]
        }
        
        with open(self.config_dir / "backend.json", "w") as f:
            json.dump(backend_config, f, indent=2)
        
        # MCP server configuration
        mcp_config = {
            "backend_url": "http://localhost:8765",
            "session_logging": True
        }
        
        with open(self.config_dir / "mcp.json", "w") as f:
            json.dump(mcp_config, f, indent=2)
        
        print("✅ Configuration files created")
    
    def verify_installation(self):
        """Verify all components are working"""
        print("🔍 Verifying installation...")
        
        # Check Python package
        try:
            import hanzo_mcp
            print("✅ Python package: OK")
        except ImportError:
            print("❌ Python package: Not found")
        
        # Check MCP server config
        claude_config = Path.home() / ".config/claude-desktop/claude_desktop_config.json"
        if claude_config.exists():
            print("✅ MCP server config: OK")
        else:
            print("❌ MCP server config: Not found")
        
        # Check VS Code extension
        vscode_extensions_dir = Path.home() / ".vscode/extensions"
        hanzo_extensions = list(vscode_extensions_dir.glob("hanzo-ai.hanzo-mcp-vscode*"))
        if hanzo_extensions:
            print("✅ VS Code extension: OK")
        else:
            print("❌ VS Code extension: Not found")
        
        # Check backend service
        try:
            response = requests.get("http://localhost:8765/health", timeout=2)
            if response.status_code == 200:
                print("✅ Backend service: Running")
            else:
                print("⚠️ Backend service: Running but not healthy")
        except requests.RequestException:
            print("❌ Backend service: Not running")
        
        print("\n🚀 Installation verification complete!")
        print("   See ~/.hanzo/logs/ for service logs")
        print("   Configuration: ~/.hanzo/config/")
    
    def uninstall(self):
        """Uninstall all components"""
        print("🗑️ Uninstalling Hanzo MCP...")
        
        # Remove Python package
        try:
            subprocess.run([sys.executable, "-m", "pip", "uninstall", "hanzo-mcp", "-y"], check=True)
        except subprocess.CalledProcessError:
            pass
        
        # Remove services
        if sys.platform.startswith("linux"):
            try:
                subprocess.run(["sudo", "systemctl", "stop", "hanzo-mcp"], check=True)
                subprocess.run(["sudo", "systemctl", "disable", "hanzo-mcp"], check=True)
                subprocess.run(["sudo", "rm", "/etc/systemd/system/hanzo-mcp.service"], check=True)
            except subprocess.CalledProcessError:
                pass
        elif sys.platform == "darwin":
            plist_file = Path.home() / "Library/LaunchAgents/ai.hanzo.mcp.backend.plist"
            try:
                subprocess.run(["launchctl", "unload", str(plist_file)], check=True)
                plist_file.unlink()
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
        
        # Remove VS Code extension
        vscode_cmd = shutil.which("code") or shutil.which("code-insiders")
        if vscode_cmd:
            try:
                subprocess.run([vscode_cmd, "--uninstall-extension", "hanzo-ai.hanzo-mcp-vscode"], check=True)
            except subprocess.CalledProcessError:
                pass
        
        # Remove configuration (optional)
        response = input("Remove configuration files? [y/N]: ")
        if response.lower().startswith('y'):
            shutil.rmtree(self.hanzo_dir, ignore_errors=True)
            
            # Remove Claude config (only Hanzo part)
            claude_config = Path.home() / ".config/claude-desktop/claude_desktop_config.json"
            if claude_config.exists():
                try:
                    with open(claude_config) as f:
                        config = json.load(f)
                    if "mcpServers" in config and "hanzo" in config["mcpServers"]:
                        del config["mcpServers"]["hanzo"]
                        with open(claude_config, "w") as f:
                            json.dump(config, f, indent=2)
                except Exception:
                    pass
        
        print("✅ Uninstallation complete")


def main():
    parser = argparse.ArgumentParser(description="Install Hanzo MCP components")
    parser.add_argument("--all", action="store_true", help="Install all components")
    parser.add_argument("--python-package", action="store_true", help="Install Python package")
    parser.add_argument("--mcp-server", action="store_true", help="Install MCP server")
    parser.add_argument("--vscode", action="store_true", help="Install VS Code extension")
    parser.add_argument("--browser", action="store_true", help="Install browser extension")
    parser.add_argument("--backend", action="store_true", help="Install backend service")
    parser.add_argument("--verify", action="store_true", help="Verify installation")
    parser.add_argument("--uninstall", action="store_true", help="Uninstall all components")
    
    args = parser.parse_args()
    
    installer = HanzoMCPInstaller()
    
    if args.uninstall:
        installer.uninstall()
        return
    
    # Create default configuration
    installer.create_default_config()
    
    success = True
    
    if args.all:
        print("🚀 Installing all Hanzo MCP components...\n")
        success &= installer.install_python_package()
        success &= installer.install_mcp_server()
        success &= installer.install_vscode_extension()
        success &= installer.install_browser_extension()
        success &= installer.install_backend_service()
    else:
        if args.python_package:
            success &= installer.install_python_package()
        if args.mcp_server:
            success &= installer.install_mcp_server()
        if args.vscode:
            success &= installer.install_vscode_extension()
        if args.browser:
            success &= installer.install_browser_extension()
        if args.backend:
            success &= installer.install_backend_service()
    
    if args.verify or args.all:
        print()
        installer.verify_installation()
    
    if success:
        print("\n🎉 Hanzo MCP installation completed!")
        print("\nNext steps:")
        print("1. Restart Claude Desktop (if using MCP server)")
        print("2. Restart VS Code (if using extension)")
        print("3. Try the tools in your IDE or AI assistant")
        print("4. Check ~/.hanzo/sessions/ for usage logs")
        print("\nExample usage:")
        print("  - In Claude: 'Format my Go code'")
        print("  - In VS Code: Ctrl+Shift+H F")
        print("  - In terminal: python -m hanzo_mcp.unified_backend fmt ws")
    else:
        print("\n❌ Some components failed to install")
        print("Check the error messages above and try installing components individually")
        sys.exit(1)


if __name__ == "__main__":
    main()