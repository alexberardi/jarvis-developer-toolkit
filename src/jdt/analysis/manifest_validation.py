"""Fast manifest-only validation (no imports, no AST).

Checks schema, semver, categories, component paths.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from jdt.core.constants import (
    VALID_CATEGORIES,
    VALID_PARAM_TYPES,
    VALID_SECRET_SCOPES,
    VALID_COMPONENT_TYPES,
)
from jdt.core.manifest_model import ManifestComponent
from jdt.core.manifest_io import infer_components


SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


@dataclass
class ManifestValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    components: list[ManifestComponent] = field(default_factory=list)
    manifest_data: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0

    @property
    def component_count(self) -> int:
        return len(self.components)


def validate_manifest(pkg_dir: Path) -> ManifestValidationResult:
    """Validate the package manifest.

    Returns a result with errors (blocking) and warnings (informational).
    """
    result = ManifestValidationResult()

    # Find manifest file
    manifest_path = None
    for name in ("jarvis_package.yaml", "jarvis_command.yaml"):
        candidate = pkg_dir / name
        if candidate.exists():
            manifest_path = candidate
            break

    if manifest_path is None:
        result.errors.append("No jarvis_package.yaml or jarvis_command.yaml found")
        return result

    # Parse YAML
    try:
        with open(manifest_path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        result.errors.append(f"Invalid YAML: {e}")
        return result

    if not data or not isinstance(data, dict):
        result.errors.append("Manifest is empty or not a mapping")
        return result

    result.manifest_data = data

    # Required fields
    for field_name in ("name", "description", "version"):
        if not data.get(field_name):
            result.errors.append(f"Missing required field: {field_name}")

    # Semver version
    version = data.get("version", "")
    if version and not SEMVER_RE.match(version):
        result.errors.append(f"Version '{version}' is not valid semver (expected X.Y.Z)")

    # Author
    author = data.get("author")
    if not author or not isinstance(author, dict) or not author.get("github"):
        result.warnings.append("Missing author.github field")

    # Categories
    categories = data.get("categories", [])
    if categories:
        invalid = [c for c in categories if c not in VALID_CATEGORIES]
        if invalid:
            result.warnings.append(f"Unknown categories: {', '.join(invalid)}")

    # Parameters
    for param in data.get("parameters", []):
        param_type = param.get("param_type", "")
        if param_type and param_type not in VALID_PARAM_TYPES:
            # Allow array types like array<string>
            if not param_type.startswith("array<"):
                result.warnings.append(f"Unknown parameter type: {param_type}")

    # Secrets
    for secret in data.get("secrets", []):
        scope = secret.get("scope", "")
        if scope and scope not in VALID_SECRET_SCOPES:
            result.warnings.append(f"Unknown secret scope: {scope} (key: {secret.get('key', '?')})")

    # Components
    components_raw = data.get("components", [])
    if components_raw:
        # Explicit components declared
        for comp in components_raw:
            comp_type = comp.get("type", "")
            comp_name = comp.get("name", "")
            comp_path = comp.get("path", "")

            if comp_type not in VALID_COMPONENT_TYPES:
                result.errors.append(f"Invalid component type: {comp_type}")
                continue

            if not comp_name:
                result.errors.append(f"Component missing name (type: {comp_type})")
                continue

            if not comp_path:
                result.errors.append(f"Component '{comp_name}' missing path")
                continue

            # Verify path exists
            full_path = pkg_dir / comp_path
            if not full_path.exists():
                result.errors.append(f"Component path not found: {comp_path}")
                continue

            result.components.append(ManifestComponent(
                type=comp_type,  # type: ignore[arg-type]
                name=comp_name,
                path=comp_path,
            ))
    else:
        # Infer from directory structure
        pkg_name = data.get("name", pkg_dir.name)
        inferred = infer_components(pkg_dir, pkg_name)
        if not inferred:
            result.errors.append(
                "No components field in manifest and no components found via directory convention"
            )
        else:
            result.components = inferred
            result.warnings.append(
                f"Components inferred from directory structure ({len(inferred)} found). "
                "Consider declaring them explicitly in the manifest."
            )

    return result
