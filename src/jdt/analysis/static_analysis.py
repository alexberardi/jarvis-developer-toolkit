"""AST-based static analysis for Jarvis packages.

Ported from jarvis-pantry/app/services/static_analysis.py with improvements:
- Expanded shared directory conflict detection (blocks generic names like shared/, lib/)
- Better error messages with actionable fix suggestions
"""

import ast
from dataclasses import dataclass, field
from pathlib import Path

from jdt.core.constants import (
    BLOCKED_SHARED_DIR_NAMES,
    COMPONENT_TYPE_INFO,
    DANGEROUS_CALLS,
    DANGEROUS_MODULES,
    DATABASE_MODULES,
    SQL_MUTATION_KEYWORDS,
)
from jdt.core.manifest_model import ManifestComponent


@dataclass
class ComponentAnalysisResult:
    path: str
    passed: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    dangerous_patterns: list[str] = field(default_factory=list)


@dataclass
class StaticAnalysisResult:
    component_results: list[ComponentAnalysisResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.errors and all(cr.passed for cr in self.component_results)


def run_static_analysis(
    pkg_dir: Path, components: list[ManifestComponent]
) -> StaticAnalysisResult:
    """Run static analysis on all components in a package."""
    result = StaticAnalysisResult()

    # Check shared directory conflicts
    _check_shared_dir_conflicts(pkg_dir, components, result)

    # Analyze each Python component
    for comp in components:
        if comp.type == "routine":
            # Validate routine JSON structure
            comp_result = _validate_routine(pkg_dir, comp)
        else:
            comp_result = _analyze_python_component(pkg_dir, comp)
        result.component_results.append(comp_result)

    return result


def _analyze_python_component(
    pkg_dir: Path, comp: ManifestComponent
) -> ComponentAnalysisResult:
    """Analyze a single Python component file."""
    comp_result = ComponentAnalysisResult(path=comp.path)
    comp_file = pkg_dir / comp.path

    if not comp_file.exists():
        comp_result.passed = False
        comp_result.errors.append(f"File not found: {comp.path}")
        return comp_result

    # Read and parse
    try:
        source = comp_file.read_text()
    except OSError as e:
        comp_result.passed = False
        comp_result.errors.append(f"Cannot read file: {e}")
        return comp_result

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        comp_result.passed = False
        comp_result.errors.append(f"Syntax error: {e}")
        return comp_result

    # Check class structure
    if comp.type in COMPONENT_TYPE_INFO:
        base_class_name, required_methods = COMPONENT_TYPE_INFO[comp.type]
        _check_class_structure(tree, base_class_name, required_methods, comp_result)

    # Check dangerous patterns
    _find_dangerous_patterns(tree, source, comp_result)

    return comp_result


def _check_class_structure(
    tree: ast.Module,
    base_class_name: str,
    required_methods: list[str],
    result: ComponentAnalysisResult,
) -> None:
    """Verify a class exists with the correct base class and required methods."""
    cls = _find_class_by_base(tree, base_class_name)
    if cls is None:
        result.passed = False
        result.errors.append(f"No class inheriting from {base_class_name} found")
        return

    # Check required methods/properties
    defined_names = _get_class_defined_names(cls)
    missing = [m for m in required_methods if m not in defined_names]
    if missing:
        result.warnings.append(
            f"Missing methods/properties: {', '.join(missing)} "
            f"(may be inherited from base class)"
        )


def _find_class_by_base(tree: ast.Module, base_class_name: str) -> ast.ClassDef | None:
    """Find a class that inherits from the given base class name."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for base in node.bases:
            name = _get_name(base)
            if name and (name == base_class_name or name.endswith(f".{base_class_name}")):
                return node
    return None


def _get_class_defined_names(cls: ast.ClassDef) -> set[str]:
    """Get all method and property names defined in a class."""
    names: set[str] = set()
    for item in cls.body:
        if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
            names.add(item.name)
        elif isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
    # Also check for properties decorated with @property
    for item in cls.body:
        if isinstance(item, ast.FunctionDef):
            for decorator in item.decorator_list:
                if _get_name(decorator) == "property":
                    names.add(item.name)
    return names


def _get_name(node: ast.expr) -> str | None:
    """Extract name from an AST Name or Attribute node."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _get_name(node.value)
        if parent:
            return f"{parent}.{node.attr}"
        return node.attr
    return None


def _find_dangerous_patterns(
    tree: ast.Module, _source: str, result: ComponentAnalysisResult
) -> None:
    """Scan for dangerous imports, calls, and patterns."""
    for node in ast.walk(tree):
        # Check imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod_name = alias.name.split(".")[0]
                if mod_name in DANGEROUS_MODULES:
                    result.dangerous_patterns.append(f"Dangerous import: {alias.name}")
                if mod_name in DATABASE_MODULES:
                    result.dangerous_patterns.append(
                        f"Raw database access: {alias.name} "
                        "(use JarvisStorage instead)"
                    )

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                mod_name = node.module.split(".")[0]
                if mod_name in DANGEROUS_MODULES:
                    result.dangerous_patterns.append(f"Dangerous import: from {node.module}")
                if mod_name in DATABASE_MODULES:
                    result.dangerous_patterns.append(
                        f"Raw database access: from {node.module} "
                        "(use JarvisStorage instead)"
                    )

        # Check function calls
        elif isinstance(node, ast.Call):
            func_name = _get_name(node.func)
            if func_name and func_name in DANGEROUS_CALLS:
                result.dangerous_patterns.append(f"Dangerous call: {func_name}()")

    # Check string literals for SQL mutations
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            upper_val = node.value.upper()
            for keyword in SQL_MUTATION_KEYWORDS:
                if keyword.upper() in upper_val:
                    result.dangerous_patterns.append(
                        f"SQL mutation pattern in string: '{keyword}'"
                    )
                    break  # One match per string is enough


def _check_shared_dir_conflicts(
    pkg_dir: Path,
    components: list[ManifestComponent],
    result: StaticAnalysisResult,
) -> None:
    """Check for shared directories that will collide after installation.

    Catches:
    1. Node built-in package names (services/, utils/, core/, etc.)
    2. Generic names (shared/, lib/, helpers/, etc.) that collide between packages
    """
    # Collect top-level dirs used by component entry points
    component_top_dirs: set[str] = set()
    for comp in components:
        parts = Path(comp.path).parts
        if len(parts) > 1:
            component_top_dirs.add(parts[0])

    # Get package name for suggestion
    manifest_name = pkg_dir.name.replace("-", "_").replace("jarvis_", "").replace("jarvis-", "")

    skip = {".git", ".venv", "__pycache__", ".pytest_cache", "node_modules", ".mypy_cache"}
    for entry in pkg_dir.iterdir():
        if not entry.is_dir():
            continue
        if entry.name in skip or entry.name.startswith("."):
            continue
        if entry.name in component_top_dirs:
            continue

        # Only flag if directory contains Python files
        if not any(entry.rglob("*.py")):
            continue

        if entry.name in BLOCKED_SHARED_DIR_NAMES:
            suggested_name = f"{manifest_name}_shared"
            result.errors.append(
                f"Shared directory '{entry.name}/' will collide with other packages "
                f"after installation.\n"
                f"       Please rename to '{suggested_name}/' to avoid conflicts.\n"
                f"       (After install, shared code lands on sys.path — "
                f"generic names clash between packages.)"
            )


def _validate_routine(pkg_dir: Path, comp: ManifestComponent) -> ComponentAnalysisResult:
    """Validate a routine JSON component."""
    import json

    comp_result = ComponentAnalysisResult(path=comp.path)
    routine_file = pkg_dir / comp.path

    if not routine_file.exists():
        comp_result.passed = False
        comp_result.errors.append(f"File not found: {comp.path}")
        return comp_result

    try:
        with open(routine_file) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        comp_result.passed = False
        comp_result.errors.append(f"Invalid JSON: {e}")
        return comp_result

    # Required fields
    if "steps" not in data:
        comp_result.passed = False
        comp_result.errors.append("Routine missing required 'steps' field")

    if "trigger_phrases" not in data:
        comp_result.warnings.append("Routine missing 'trigger_phrases' (recommended)")

    if "response_instruction" not in data:
        comp_result.warnings.append("Routine missing 'response_instruction' (recommended)")

    # Validate steps
    steps = data.get("steps", [])
    for i, step in enumerate(steps):
        if "command" not in step:
            comp_result.passed = False
            comp_result.errors.append(f"Step {i + 1} missing required 'command' field")

    return comp_result
