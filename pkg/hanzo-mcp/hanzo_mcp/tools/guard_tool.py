"""
Guard Tool - Repository invariants and boundaries
================================================

Purpose: enforce repo invariants (boundaries, forbidden imports/strings, generated dirs).

Rules:
- regex rule: {id, glob, pattern} - Match regex patterns in files
- import rule: {id, glob, forbid_import_prefix} - Forbidden import prefixes
- generated rule: {id, glob, forbid_writes: true} - Protect generated files

Example rules for Hanzo ecosystem:
- no node in sdk: forbid import prefix in sdk/** of github.com/luxfi/node/
- no net/http in api/** contracts
- no edits under generated: api/pb/**, api/capnp/**
"""

import re
import glob
from typing import Optional, Dict, Any, List
from pathlib import Path
from dataclasses import dataclass

from .dev_tools import DevToolBase, DevResult, create_dev_result

@dataclass
class GuardRule:
    """Base guard rule"""
    id: str
    glob: str
    description: str = ""

@dataclass 
class RegexRule(GuardRule):
    """Regex pattern rule"""
    pattern: str
    message: str = "Pattern match found"

@dataclass
class ImportRule(GuardRule):  
    """Import prefix rule"""
    forbid_import_prefix: str
    message: str = "Forbidden import found"

@dataclass
class GeneratedRule(GuardRule):
    """Generated file protection rule"""
    forbid_writes: bool = True
    message: str = "Modification of generated files forbidden"

@dataclass
class Violation:
    """Rule violation"""
    file: str
    line: int
    text: str
    rule_id: str
    message: str

class GuardTool(DevToolBase):
    """Repository invariant enforcement tool"""
    
    def __init__(self, target: str, **kwargs):
        super().__init__(target, **kwargs)
        self.rules = self._parse_rules(kwargs.get('rules', []))
        
    async def execute(self) -> DevResult:
        """Execute guard operation"""
        try:
            violations = []
            
            # Get files to check
            files = self._get_files_to_check()
            
            # Run each rule
            for rule in self.rules:
                rule_violations = await self._check_rule(rule, files)
                violations.extend(rule_violations)
            
            return create_dev_result(
                ok=len(violations) == 0,
                root=self.workspace["root"],
                language_used=self.language,
                backend_used="guard",
                scope_resolved=self.resolved["scope"],
                stdout=self._format_violations(violations),
                stderr="",
                exit_code=0 if len(violations) == 0 else 1,
                errors=[f"Found {len(violations)} violations"] if violations else []
            )
            
        except Exception as e:
            return create_dev_result(
                ok=False,
                root=self.workspace["root"],
                language_used=self.language,
                backend_used="guard",
                scope_resolved=self.target,
                errors=[str(e)]
            )
    
    def _parse_rules(self, rules_data: List[Dict[str, Any]]) -> List[GuardRule]:
        """Parse rule definitions into rule objects"""
        rules = []
        
        for rule_data in rules_data:
            rule_id = rule_data.get('id', 'unnamed')
            glob_pattern = rule_data.get('glob', '**')
            description = rule_data.get('description', '')
            
            if 'pattern' in rule_data:
                # Regex rule
                rules.append(RegexRule(
                    id=rule_id,
                    glob=glob_pattern,
                    description=description,
                    pattern=rule_data['pattern'],
                    message=rule_data.get('message', 'Pattern match found')
                ))
            elif 'forbid_import_prefix' in rule_data:
                # Import rule
                rules.append(ImportRule(
                    id=rule_id,
                    glob=glob_pattern,
                    description=description,
                    forbid_import_prefix=rule_data['forbid_import_prefix'],
                    message=rule_data.get('message', 'Forbidden import found')
                ))
            elif 'forbid_writes' in rule_data:
                # Generated file rule
                rules.append(GeneratedRule(
                    id=rule_id,
                    glob=glob_pattern,
                    description=description,
                    forbid_writes=rule_data['forbid_writes'],
                    message=rule_data.get('message', 'Modification of generated files forbidden')
                ))
        
        return rules
    
    def _get_files_to_check(self) -> List[str]:
        """Get list of files to check"""
        if self.resolved["type"] == "file":
            return [self.resolved["scope"]]
        elif self.resolved["type"] == "directory":
            return self._scan_directory(self.resolved["scope"])
        elif self.resolved["type"] == "workspace":
            return self._scan_directory(self.workspace["root"])
        else:
            return self.resolved["files"]
    
    def _scan_directory(self, directory: str) -> List[str]:
        """Scan directory for source files"""
        dir_path = Path(directory)
        files = []
        
        # Common source file patterns
        patterns = [
            "**/*.go", "**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx",
            "**/*.py", "**/*.rs", "**/*.c", "**/*.cpp", "**/*.cc",
            "**/*.h", "**/*.hpp", "**/*.sol", "**/*.proto"
        ]
        
        for pattern in patterns:
            files.extend([str(f) for f in dir_path.glob(pattern) if f.is_file()])
        
        return files
    
    async def _check_rule(self, rule: GuardRule, files: List[str]) -> List[Violation]:
        """Check a rule against files"""
        violations = []
        
        # Filter files by glob pattern
        matching_files = self._filter_files_by_glob(files, rule.glob)
        
        if isinstance(rule, RegexRule):
            violations.extend(await self._check_regex_rule(rule, matching_files))
        elif isinstance(rule, ImportRule):
            violations.extend(await self._check_import_rule(rule, matching_files))
        elif isinstance(rule, GeneratedRule):
            violations.extend(await self._check_generated_rule(rule, matching_files))
        
        return violations
    
    def _filter_files_by_glob(self, files: List[str], glob_pattern: str) -> List[str]:
        """Filter files by glob pattern"""
        root_path = Path(self.workspace["root"])
        matching_files = []
        
        for file_path in files:
            # Make path relative to workspace root for matching
            try:
                rel_path = Path(file_path).relative_to(root_path)
                if Path(file_path).match(glob_pattern):
                    matching_files.append(file_path)
            except ValueError:
                # File outside workspace
                continue
        
        return matching_files
    
    async def _check_regex_rule(self, rule: RegexRule, files: List[str]) -> List[Violation]:
        """Check regex rule against files"""
        violations = []
        pattern = re.compile(rule.pattern)
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        if pattern.search(line):
                            violations.append(Violation(
                                file=file_path,
                                line=line_num,
                                text=line.strip(),
                                rule_id=rule.id,
                                message=rule.message
                            ))
            except Exception:
                # Skip files that can't be read
                continue
        
        return violations
    
    async def _check_import_rule(self, rule: ImportRule, files: List[str]) -> List[Violation]:
        """Check import rule against files"""
        violations = []
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Check for import statements containing forbidden prefix
                        if self._line_has_forbidden_import(line, rule.forbid_import_prefix):
                            violations.append(Violation(
                                file=file_path,
                                line=line_num,
                                text=line.strip(),
                                rule_id=rule.id,
                                message=f"{rule.message}: {rule.forbid_import_prefix}"
                            ))
            except Exception:
                continue
        
        return violations
    
    async def _check_generated_rule(self, rule: GeneratedRule, files: List[str]) -> List[Violation]:
        """Check generated file rule"""
        violations = []
        
        if not rule.forbid_writes:
            return violations
        
        # Check if any matching files have been modified
        for file_path in files:
            if self._is_file_modified(file_path):
                violations.append(Violation(
                    file=file_path,
                    line=1,
                    text="[Generated file was modified]",
                    rule_id=rule.id,
                    message=rule.message
                ))
        
        return violations
    
    def _line_has_forbidden_import(self, line: str, forbidden_prefix: str) -> bool:
        """Check if line contains forbidden import"""
        line = line.strip()
        
        # Go imports
        if line.startswith('import ') or ('"' in line and 'import' in line):
            return forbidden_prefix in line
        
        # Python imports  
        if line.startswith('import ') or line.startswith('from '):
            return forbidden_prefix in line
        
        # TypeScript/JavaScript imports
        if 'import' in line and ('from' in line or 'require(' in line):
            return forbidden_prefix in line
        
        # Rust use statements
        if line.startswith('use '):
            return forbidden_prefix in line
        
        return False
    
    def _is_file_modified(self, file_path: str) -> bool:
        """Check if file has been modified (simplified check)"""
        # For now, just check if file exists and is not empty
        # In a real implementation, this would check git status,
        # modification times, or other indicators
        try:
            path = Path(file_path)
            return path.exists() and path.stat().st_size > 0
        except:
            return False
    
    def _format_violations(self, violations: List[Violation]) -> str:
        """Format violations for output"""
        if not violations:
            return "✅ All guard rules passed"
        
        output = [f"❌ Found {len(violations)} guard violations:"]
        output.append("")
        
        # Group by rule
        by_rule = {}
        for violation in violations:
            if violation.rule_id not in by_rule:
                by_rule[violation.rule_id] = []
            by_rule[violation.rule_id].append(violation)
        
        for rule_id, rule_violations in by_rule.items():
            output.append(f"Rule: {rule_id}")
            for violation in rule_violations:
                output.append(f"  {violation.file}:{violation.line} - {violation.message}")
                output.append(f"    {violation.text}")
            output.append("")
        
        return "\n".join(output)

# Default rules for Hanzo ecosystem
HANZO_DEFAULT_RULES = [
    {
        "id": "no-node-in-sdk",
        "glob": "sdk/**/*.go",
        "forbid_import_prefix": "github.com/luxfi/node/",
        "description": "SDK packages should not import node internals",
        "message": "SDK boundary violation - importing node package"
    },
    {
        "id": "no-http-in-contracts",
        "glob": "api/**/*.go",
        "forbid_import_prefix": "net/http",
        "description": "API contracts should not import net/http",
        "message": "API contract should be transport agnostic"
    },
    {
        "id": "protect-generated-pb",
        "glob": "api/pb/**/*",
        "forbid_writes": True,
        "description": "Protect generated protobuf files",
        "message": "Generated protobuf files should not be manually edited"
    },
    {
        "id": "protect-generated-capnp",
        "glob": "api/capnp/**/*",
        "forbid_writes": True,
        "description": "Protect generated Cap'n Proto files",
        "message": "Generated Cap'n Proto files should not be manually edited"
    },
    {
        "id": "no-todo-in-main",
        "glob": "**/*.go",
        "pattern": r"// TODO.*(?:FIXME|HACK|XXX)",
        "description": "No TODO/FIXME in production code",
        "message": "Remove TODO/FIXME before merging"
    }
]

# MCP tool integration
async def guard_tool_handler(
    target: str,
    rules: Optional[List[Dict[str, Any]]] = None,
    language: str = "auto",
    backend: str = "auto",
    root: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    dry_run: bool = False,
    use_defaults: bool = True
) -> Dict[str, Any]:
    """MCP handler for guard tool"""
    
    # Combine provided rules with defaults if requested
    all_rules = []
    if use_defaults:
        all_rules.extend(HANZO_DEFAULT_RULES)
    if rules:
        all_rules.extend(rules)
    
    tool = GuardTool(
        target=target,
        language=language,
        backend=backend,
        root=root,
        env=env,
        dry_run=dry_run,
        rules=all_rules
    )
    
    result = await tool.execute()
    return result.dict()