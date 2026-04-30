"""Package scaffold generator — creates directory structure and stub files."""

import json
from pathlib import Path

import yaml

from jdt.core.constants import SCHEMA_VERSION
from jdt.scaffold.templates import (
    TEMPLATE_MAP,
    GITIGNORE_TEMPLATE,
    README_TEMPLATE,
    LICENSE_TEMPLATE,
)


def scaffold_package(
    name: str,
    component_types: list[str],
    author: str,
    category: str,
    output_dir: Path,
) -> Path:
    """Create a new package directory with stubs and manifest.

    Returns the path to the created package directory.
    """
    pkg_dir = output_dir / name
    pkg_dir.mkdir(parents=True, exist_ok=True)

    display_name = name.replace("_", " ").title()
    description = f"{display_name} package for Jarvis"

    # Generate class name from package name
    class_base = "".join(word.capitalize() for word in name.split("_"))

    # Build component list and create stub files
    components = []
    for comp_type in component_types:
        if comp_type not in TEMPLATE_MAP:
            raise ValueError(f"Unknown component type: {comp_type}")

        template_str, entry_filename, dir_pattern = TEMPLATE_MAP[comp_type]
        comp_dir_rel = dir_pattern.format(name=name)
        comp_dir = pkg_dir / comp_dir_rel
        comp_dir.mkdir(parents=True, exist_ok=True)

        # Class name suffix by type
        suffix_map = {
            "command": "Command",
            "agent": "Agent",
            "device_protocol": "Protocol",
            "device_manager": "Manager",
            "prompt_provider": "PromptProvider",
            "routine": "",
        }
        class_name = f"{class_base}{suffix_map[comp_type]}"

        # Write stub file
        entry_path = comp_dir / entry_filename
        if comp_type == "routine":
            routine_data = {
                "trigger_phrases": [f"run {name.replace('_', ' ')}"],
                "steps": [
                    {"command": "calculate", "parameters": {"expression": "1+1"}},
                ],
                "response_instruction": f"Tell the user the {display_name} routine completed.",
            }
            content = json.dumps(routine_data, indent=2)
        else:
            content = template_str.format(
                name=name,
                display_name=display_name,
                description=description,
                class_name=class_name,
            )
        entry_path.write_text(content)

        # Write __init__.py for Python components
        if comp_type != "routine":
            init_file = comp_dir / "__init__.py"
            init_file.write_text("")

        # Track component
        comp_path = f"{comp_dir_rel}/{entry_filename}"
        components.append({
            "type": comp_type,
            "name": name,
            "path": comp_path,
        })

    # Write manifest
    manifest_data = {
        "schema_version": SCHEMA_VERSION,
        "name": name,
        "display_name": display_name,
        "description": description,
        "version": "0.1.0",
        "min_jarvis_version": "0.9.0",
        "license": "MIT",
        "author": {"github": author},
        "categories": [category] if category else [],
        "platforms": ["darwin", "linux"],
        "keywords": [name.replace("_", " ")],
        "components": components,
        "secrets": [],
        "packages": [],
    }
    manifest_path = pkg_dir / "jarvis_package.yaml"
    with open(manifest_path, "w") as f:
        yaml.dump(manifest_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    # Write supporting files
    (pkg_dir / ".gitignore").write_text(GITIGNORE_TEMPLATE)
    (pkg_dir / "README.md").write_text(
        README_TEMPLATE.format(display_name=display_name, description=description)
    )
    (pkg_dir / "LICENSE").write_text(LICENSE_TEMPLATE)

    return pkg_dir
