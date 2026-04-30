"""Introspect SDK classes to extract manifest metadata.

Generalized from jarvis-node-setup/scripts/generate_manifest.py to support
all component types, not just commands.
"""

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Any

from jdt.core.manifest_model import ManifestComponent, ManifestSecret, ManifestPackage


def introspect_components(pkg_dir: Path, components: list[ManifestComponent]) -> dict[str, Any]:
    """Introspect all components and merge their metadata.

    Returns a dict with aggregated secrets, packages, keywords, description,
    and authentication config from the discovered classes.
    """
    result: dict[str, Any] = {
        "secrets": [],
        "packages": [],
        "keywords": [],
        "description": "",
        "authentication": None,
    }

    for comp in components:
        if comp.type == "routine":
            # Routines are JSON, nothing to introspect
            continue
        try:
            data = _introspect_component(pkg_dir, comp)
            if data:
                result["secrets"].extend(data.get("secrets", []))
                result["packages"].extend(data.get("packages", []))
                result["keywords"].extend(data.get("keywords", []))
                if data.get("description") and not result["description"]:
                    result["description"] = data["description"]
                if data.get("authentication") and not result["authentication"]:
                    result["authentication"] = data["authentication"]
        except Exception:
            # Introspection is best-effort — don't block manifest generation
            continue

    # Deduplicate
    seen_secrets: set[str] = set()
    unique_secrets = []
    for s in result["secrets"]:
        key = s.key if isinstance(s, ManifestSecret) else s.get("key", "")
        if key not in seen_secrets:
            seen_secrets.add(key)
            unique_secrets.append(s)
    result["secrets"] = unique_secrets

    seen_pkgs: set[str] = set()
    unique_pkgs = []
    for p in result["packages"]:
        name = p.name if isinstance(p, ManifestPackage) else p.get("name", "")
        if name not in seen_pkgs:
            seen_pkgs.add(name)
            unique_pkgs.append(p)
    result["packages"] = unique_pkgs

    result["keywords"] = list(dict.fromkeys(result["keywords"]))

    return result


def _introspect_component(pkg_dir: Path, comp: ManifestComponent) -> dict[str, Any] | None:
    """Introspect a single component by importing and reading its properties."""
    comp_file = Path(comp.path)
    parent = pkg_dir / comp_file.parent
    mod_name = comp_file.stem

    # Temporarily add paths for import
    saved_path = sys.path[:]
    paths_to_add = [str(parent), str(pkg_dir)]
    for p in paths_to_add:
        if p not in sys.path:
            sys.path.insert(0, p)

    # Clear cached module
    for key in list(sys.modules.keys()):
        if key == mod_name or key.startswith(f"{mod_name}."):
            del sys.modules[key]

    try:
        mod = importlib.import_module(mod_name)
    except Exception:
        sys.path[:] = saved_path
        return None

    # Find the class based on component type
    instance = _find_and_instantiate(mod, comp.type)
    if instance is None:
        sys.path[:] = saved_path
        return None

    data = _extract_metadata(instance, comp.type)
    sys.path[:] = saved_path
    return data


def _find_and_instantiate(mod: Any, comp_type: str) -> Any | None:
    """Find the SDK subclass in a module and instantiate it."""
    base_class = _get_base_class(comp_type)
    if base_class is None:
        return None

    for attr_name in dir(mod):
        obj = getattr(mod, attr_name)
        if (isinstance(obj, type) and issubclass(obj, base_class) and obj is not base_class):
            try:
                return obj()
            except Exception:
                return None
    return None


def _get_base_class(comp_type: str) -> type | None:
    """Get the SDK base class for a component type."""
    try:
        from jarvis_command_sdk import IJarvisCommand
        from jarvis_command_sdk.agent import IJarvisAgent
        from jarvis_command_sdk.device_protocol import IJarvisDeviceProtocol
        from jarvis_command_sdk.device_manager import IJarvisDeviceManager
    except ImportError:
        return None

    mapping: dict[str, type] = {
        "command": IJarvisCommand,
        "agent": IJarvisAgent,
        "device_protocol": IJarvisDeviceProtocol,
        "device_manager": IJarvisDeviceManager,
    }
    return mapping.get(comp_type)


def _extract_metadata(instance: Any, comp_type: str) -> dict[str, Any]:
    """Extract manifest-relevant metadata from an instantiated component."""
    data: dict[str, Any] = {}

    # Description
    desc = getattr(instance, "description", None)
    if desc and isinstance(desc, str):
        data["description"] = desc

    # Keywords (commands only)
    if comp_type == "command":
        keywords = getattr(instance, "keywords", None)
        if keywords and isinstance(keywords, list):
            data["keywords"] = list(keywords)

    # Secrets (all types)
    secrets = getattr(instance, "required_secrets", None)
    if secrets and isinstance(secrets, list):
        data["secrets"] = [
            ManifestSecret(
                key=s.key,
                scope=getattr(s, "scope", "integration"),
                value_type=getattr(s, "value_type", "string"),
                required=getattr(s, "required", True),
                description=getattr(s, "description", ""),
                is_sensitive=getattr(s, "is_sensitive", True),
                friendly_name=getattr(s, "friendly_name", None),
            )
            for s in secrets
        ]

    # Packages (commands have required_packages)
    packages = getattr(instance, "required_packages", None)
    if packages and isinstance(packages, list):
        data["packages"] = [
            ManifestPackage(
                name=getattr(p, "name", str(p)),
                version=getattr(p, "version", None),
            )
            for p in packages
        ]

    # Authentication
    auth = getattr(instance, "authentication", None)
    if auth:
        data["authentication"] = auth

    return data
