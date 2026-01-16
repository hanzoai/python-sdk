"""
Build Tool - Compile/build artifacts narrowly by default
=======================================================

Purpose: compile/build artifacts with smart scope resolution.

Same scope logic as test tool:
- file → derive owning package/project and build it
- dir → build that subtree
- pkg → use explicitly  
- ws → workspace-wide

Backends:
- go: go build
- ts: tsc or workspace build (pnpm build)
- py: optional (python -m build) for packaging
- rs: cargo build
- cc: cmake --build, ninja, make
- sol: forge build / hardhat compile
"""

from typing import Optional, Dict, Any, List
from pathlib import Path

from .dev_tools import DevToolBase, DevResult, create_dev_result

class BuildTool(DevToolBase):
    """Build/compilation tool"""
    
    def __init__(self, target: str, **kwargs):
        super().__init__(target, **kwargs)
        self.opts = kwargs.get('opts', {})
        
    async def execute(self) -> DevResult:
        """Execute build operation"""
        try:
            if self.language == "go":
                return await self._build_go()
            elif self.language == "ts":
                return await self._build_typescript()
            elif self.language == "py":
                return await self._build_python()
            elif self.language == "rs":
                return await self._build_rust()
            elif self.language == "cc":
                return await self._build_cpp()
            elif self.language == "sol":
                return await self._build_solidity()
            else:
                return create_dev_result(
                    ok=False,
                    root=self.workspace["root"],
                    language_used=self.language,
                    backend_used=self.backend,
                    scope_resolved=self.target,
                    errors=[f"Build not supported for language: {self.language}"]
                )
        except Exception as e:
            return create_dev_result(
                ok=False,
                root=self.workspace["root"],
                language_used=self.language,
                backend_used=self.backend,
                scope_resolved=self.target,
                errors=[str(e)]
            )
    
    async def _build_go(self) -> DevResult:
        """Build Go packages"""
        cmd = ["go", "build"]
        
        # Determine build scope
        if self.resolved["type"] == "file":
            pkg = self.resolved["package"]
            if pkg and pkg != ".":
                cmd.append(f"./{pkg}")
            else:
                cmd.append(".")
        elif self.resolved["type"] == "directory":
            dir_path = self.resolved["scope"]
            cmd.append(f"./{dir_path}/...")
        elif self.resolved["type"] == "package":
            pkg_spec = self.resolved["scope"]
            cmd.append(pkg_spec)
        elif self.resolved["type"] == "workspace":
            cmd.append("./...")
        else:
            cmd.append(".")
        
        # Add build options
        if self.opts.get('race'):
            cmd.append("-race")
        if self.opts.get('tags'):
            cmd.extend(["-tags", self.opts['tags']])
        if self.opts.get('ldflags'):
            cmd.extend(["-ldflags", self.opts['ldflags']])
        
        result = self._run_command(cmd)
        
        return create_dev_result(
            ok=result.returncode == 0,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used="go",
            scope_resolved=self.resolved["scope"],
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode
        )
    
    async def _build_typescript(self) -> DevResult:
        """Build TypeScript/JavaScript"""
        # Try different build approaches
        if self.backend == "tsc" or self._has_tsconfig():
            return await self._build_with_tsc()
        elif self.backend in ["pnpm", "npm", "yarn"]:
            return await self._build_with_package_script()
        else:
            return create_dev_result(
                ok=False,
                root=self.workspace["root"],
                language_used=self.language,
                backend_used=self.backend,
                scope_resolved=self.target,
                errors=["No build configuration found (tsconfig.json or package.json build script)"]
            )
    
    async def _build_python(self) -> DevResult:
        """Build Python packages"""
        # Python builds are typically for packaging
        if Path(self.workspace["root"], "pyproject.toml").exists():
            cmd = ["python", "-m", "build"]
        elif Path(self.workspace["root"], "setup.py").exists():
            cmd = ["python", "setup.py", "build"]
        else:
            return create_dev_result(
                ok=True,
                root=self.workspace["root"],
                language_used=self.language,
                backend_used="python",
                scope_resolved=self.resolved["scope"],
                stdout="Python doesn't require explicit build - interpret/lint is the main verification"
            )
        
        result = self._run_command(cmd)
        
        return create_dev_result(
            ok=result.returncode == 0,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used="python",
            scope_resolved=self.resolved["scope"],
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode
        )
    
    async def _build_rust(self) -> DevResult:
        """Build Rust packages"""
        cmd = ["cargo", "build"]
        
        # Add package filter if building specific package
        if self.resolved["type"] == "file":
            cargo_toml = self._find_rust_package(self.resolved["scope"])
            if cargo_toml:
                package_name = self._get_rust_package_name(cargo_toml)
                if package_name:
                    cmd.extend(["-p", package_name])
        
        # Add build options
        if self.opts.get('release'):
            cmd.append("--release")
        if self.opts.get('features'):
            cmd.extend(["--features", self.opts['features']])
        
        result = self._run_command(cmd)
        
        return create_dev_result(
            ok=result.returncode == 0,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used="cargo",
            scope_resolved=self.resolved["scope"],
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode
        )
    
    async def _build_cpp(self) -> DevResult:
        """Build C/C++ projects"""
        build_dir = Path(self.workspace["root"]) / "build"
        
        if self.backend == "cmake":
            return await self._build_with_cmake()
        elif self.backend == "ninja":
            return await self._build_with_ninja()
        elif self.backend == "make":
            return await self._build_with_make()
        else:
            # Auto-detect
            if (Path(self.workspace["root"]) / "CMakeLists.txt").exists():
                return await self._build_with_cmake()
            elif (build_dir / "build.ninja").exists():
                return await self._build_with_ninja()
            elif (Path(self.workspace["root"]) / "Makefile").exists():
                return await self._build_with_make()
            else:
                return create_dev_result(
                    ok=False,
                    root=self.workspace["root"],
                    language_used=self.language,
                    backend_used=self.backend,
                    scope_resolved=self.target,
                    errors=["No build system detected (CMakeLists.txt, build.ninja, or Makefile)"]
                )
    
    async def _build_solidity(self) -> DevResult:
        """Build Solidity contracts"""
        if self.backend == "forge" or self._has_forge():
            cmd = ["forge", "build"]
            backend = "forge"
        elif self.backend == "hardhat" or self._has_hardhat():
            cmd = ["npx", "hardhat", "compile"]
            backend = "hardhat"
        else:
            return create_dev_result(
                ok=False,
                root=self.workspace["root"],
                language_used=self.language,
                backend_used=self.backend,
                scope_resolved=self.target,
                errors=["No Solidity build system detected (forge or hardhat)"]
            )
        
        result = self._run_command(cmd)
        
        return create_dev_result(
            ok=result.returncode == 0,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used=backend,
            scope_resolved=self.resolved["scope"],
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode
        )
    
    async def _build_with_tsc(self) -> DevResult:
        """Build with TypeScript compiler"""
        cmd = ["tsc"]
        
        # Add project file if exists
        if self.resolved["type"] != "workspace":
            # Look for nearest tsconfig.json
            tsconfig = self._find_tsconfig(self.resolved["scope"])
            if tsconfig:
                cmd.extend(["-p", str(tsconfig.parent)])
        
        result = self._run_command(cmd)
        
        return create_dev_result(
            ok=result.returncode == 0,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used="tsc",
            scope_resolved=self.resolved["scope"],
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode
        )
    
    async def _build_with_package_script(self) -> DevResult:
        """Build via package.json script"""
        if self.backend == "pnpm":
            cmd = ["pnpm", "build"]
        elif self.backend == "yarn":
            cmd = ["yarn", "build"]
        else:
            cmd = ["npm", "run", "build"]
        
        result = self._run_command(cmd)
        
        return create_dev_result(
            ok=result.returncode == 0,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used=self.backend,
            scope_resolved=self.resolved["scope"],
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode
        )
    
    async def _build_with_cmake(self) -> DevResult:
        """Build with CMake"""
        build_dir = Path(self.workspace["root"]) / "build"
        
        # Configure if needed
        if not build_dir.exists():
            config_result = self._run_command(["cmake", "-B", "build", "-S", "."])
            if config_result.returncode != 0:
                return create_dev_result(
                    ok=False,
                    root=self.workspace["root"],
                    language_used=self.language,
                    backend_used="cmake",
                    scope_resolved=self.resolved["scope"],
                    stdout=config_result.stdout,
                    stderr=config_result.stderr,
                    exit_code=config_result.returncode,
                    errors=["CMake configure failed"]
                )
        
        # Build
        result = self._run_command(["cmake", "--build", "build"])
        
        return create_dev_result(
            ok=result.returncode == 0,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used="cmake",
            scope_resolved=self.resolved["scope"],
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode
        )
    
    async def _build_with_ninja(self) -> DevResult:
        """Build with Ninja"""
        result = self._run_command(["ninja"], cwd=str(Path(self.workspace["root"]) / "build"))
        
        return create_dev_result(
            ok=result.returncode == 0,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used="ninja",
            scope_resolved=self.resolved["scope"],
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode
        )
    
    async def _build_with_make(self) -> DevResult:
        """Build with Make"""
        result = self._run_command(["make"])
        
        return create_dev_result(
            ok=result.returncode == 0,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used="make",
            scope_resolved=self.resolved["scope"],
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode
        )
    
    def _has_tsconfig(self) -> bool:
        """Check if tsconfig.json exists"""
        return Path(self.workspace["root"], "tsconfig.json").exists()
    
    def _find_tsconfig(self, file_path: str) -> Optional[Path]:
        """Find nearest tsconfig.json"""
        path = Path(file_path)
        current = path.parent if path.is_file() else path
        
        while current >= Path(self.workspace["root"]):
            tsconfig = current / "tsconfig.json"
            if tsconfig.exists():
                return tsconfig
            current = current.parent
        
        return None
    
    def _has_forge(self) -> bool:
        """Check if Forge is available"""
        try:
            result = self._run_command(["forge", "--version"])
            return result.returncode == 0
        except:
            return False
    
    def _has_hardhat(self) -> bool:
        """Check if Hardhat is available"""
        return Path(self.workspace["root"], "hardhat.config.js").exists() or \
               Path(self.workspace["root"], "hardhat.config.ts").exists()
    
    def _find_rust_package(self, file_path: str) -> Optional[str]:
        """Find Cargo.toml for given file"""
        path = Path(file_path)
        current = path.parent if path.is_file() else path
        
        while current >= Path(self.workspace["root"]):
            cargo_toml = current / "Cargo.toml"
            if cargo_toml.exists():
                return str(cargo_toml)
            current = current.parent
        
        return None
    
    def _get_rust_package_name(self, cargo_toml_path: str) -> Optional[str]:
        """Extract package name from Cargo.toml"""
        try:
            import toml
            with open(cargo_toml_path) as f:
                data = toml.load(f)
            return data.get("package", {}).get("name")
        except:
            return None

# MCP tool integration
async def build_tool_handler(
    target: str,
    language: str = "auto",
    backend: str = "auto", 
    root: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    dry_run: bool = False,
    opts: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """MCP handler for build tool"""
    
    tool = BuildTool(
        target=target,
        language=language,
        backend=backend,
        root=root,
        env=env,
        dry_run=dry_run,
        opts=opts or {}
    )
    
    result = await tool.execute()
    return result.dict()