"""Read, write, and infer manifest files.

Ported from jarvis-node-setup/core/command_manifest.py (infer_components).
"""

from pathlib import Path
from typing import Any

import yaml

from jdt.core.manifest_model import CommandManifest, ManifestComponent
from jdt.core.constants import COMPONENT_DIR_TYPES, COMPONENT_ENTRY_POINTS


def find_manifest(pkg_dir: Path) -> Path | None:
    """Find the manifest file in a package directory.

    Prefers jarvis_package.yaml over jarvis_command.yaml.
    """
    for name in ("jarvis_package.yaml", "jarvis_command.yaml"):
        candidate = pkg_dir / name
        if candidate.exists():
            return candidate
    return None


def read_manifest(pkg_dir: Path) -> dict[str, Any] | None:
    """Read and parse manifest YAML. Returns None if not found."""
    path = find_manifest(pkg_dir)
    if path is None:
        return None
    with open(path) as f:
        return yaml.safe_load(f) or {}


def write_manifest(manifest: CommandManifest, output_dir: Path) -> Path:
    """Write manifest to jarvis_package.yaml."""
    output_path = output_dir / "jarvis_package.yaml"

    data = manifest.model_dump(mode="json", exclude_none=True)

    # Clean up empty/default fields for readability
    if not data.get("parameters"):
        data.pop("parameters", None)
    if not data.get("homepage"):
        data.pop("homepage", None)
    if not data.get("setup_guide"):
        data.pop("setup_guide", None)
    if data.get("authentication") is None:
        data.pop("authentication", None)

    with open(output_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    return output_path


def infer_components(pkg_dir: Path, manifest_name: str) -> list[ManifestComponent]:
    """Infer components from directory structure when not declared in manifest.

    Scans for:
    - command.py at root -> single command
    - commands/<name>/command.py -> command(s)
    - agents/<name>/agent.py -> agent(s)
    - device_families/<name>/protocol.py -> device protocol(s)
    - device_managers/<name>/manager.py -> device manager(s)
    - prompt_providers/<name>/provider.py -> prompt provider(s)
    - routines/<name>/routine.json -> routine(s)
    - routine.json at root -> single routine
    """
    components: list[ManifestComponent] = []

    # Root-level command.py
    if (pkg_dir / "command.py").exists():
        components.append(ManifestComponent(
            type="command",
            name=manifest_name,
            path="command.py",
        ))

    # Convention directories
    for dir_name, comp_type in COMPONENT_DIR_TYPES.items():
        type_dir = pkg_dir / dir_name
        if not type_dir.is_dir():
            continue

        entry_filename = COMPONENT_ENTRY_POINTS[comp_type]
        for sub_dir in sorted(type_dir.iterdir()):
            if not sub_dir.is_dir() or sub_dir.name.startswith(("_", ".")):
                continue
            entry_point = sub_dir / entry_filename
            if entry_point.exists():
                components.append(ManifestComponent(
                    type=comp_type,  # type: ignore[arg-type]
                    name=sub_dir.name,
                    path=str(entry_point.relative_to(pkg_dir)),
                ))

    # Root-level routine.json
    if (pkg_dir / "routine.json").exists() and not any(c.type == "routine" for c in components):
        components.append(ManifestComponent(
            type="routine",
            name=manifest_name,
            path="routine.json",
        ))

    return components
