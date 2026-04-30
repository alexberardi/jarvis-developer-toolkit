"""Import and instantiation checks for Jarvis package components.

Ported from jarvis-node-setup/scripts/verify_package.py.
Imports each component, finds the SDK subclass, instantiates it,
and validates that properties return correct types.
"""

import importlib
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jdt.core.manifest_model import ManifestComponent


@dataclass
class TestResult:
    name: str
    passed: bool
    error: str | None = None


@dataclass
class ImportCheckResult:
    tests: list[TestResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(t.passed for t in self.tests)

    @property
    def pass_count(self) -> int:
        return sum(1 for t in self.tests if t.passed)

    @property
    def fail_count(self) -> int:
        return sum(1 for t in self.tests if not t.passed)


# SDK base class cache
_SDK_CLASSES: dict[str, type] = {}


def _get_sdk_class(comp_type: str) -> type | None:
    """Lazy-load SDK base classes."""
    if not _SDK_CLASSES:
        try:
            from jarvis_command_sdk import (
                IJarvisCommand,
                IJarvisDeviceProtocol,
                IJarvisDeviceManager,
            )
            from jarvis_command_sdk.agent import IJarvisAgent
            _SDK_CLASSES.update({
                "command": IJarvisCommand,
                "agent": IJarvisAgent,
                "device_protocol": IJarvisDeviceProtocol,
                "device_manager": IJarvisDeviceManager,
            })
        except ImportError:
            return None
    return _SDK_CLASSES.get(comp_type)


def run_import_checks(
    pkg_dir: Path,
    components: list[ManifestComponent],
    install_deps: bool = False,
) -> ImportCheckResult:
    """Run import and instantiation checks on all components."""
    result = ImportCheckResult()

    # Optionally install package dependencies first
    if install_deps:
        _install_manifest_deps(pkg_dir)

    for comp in components:
        if comp.type == "routine":
            # Already validated in static analysis
            continue
        if comp.type == "prompt_provider":
            # Prompt providers depend on CC internals, skip import
            result.tests.append(TestResult(
                name=f"{comp.name}/skip",
                passed=True,
                error=None,
            ))
            continue

        comp_tests = _check_component(pkg_dir, comp)
        result.tests.extend(comp_tests)

    return result


def _install_manifest_deps(pkg_dir: Path) -> None:
    """Install pip dependencies declared in the manifest."""
    import subprocess
    import yaml

    for name in ("jarvis_package.yaml", "jarvis_command.yaml"):
        manifest_path = pkg_dir / name
        if manifest_path.exists():
            break
    else:
        return

    with open(manifest_path) as f:
        data = yaml.safe_load(f) or {}

    packages = data.get("packages", [])
    if not packages:
        return

    pip_specs = []
    for pkg in packages:
        pkg_name = pkg.get("name", "") if isinstance(pkg, dict) else str(pkg)
        pkg_version = pkg.get("version", "") if isinstance(pkg, dict) else ""
        if pkg_version and not any(c in pkg_version for c in ("=", "<", ">")):
            pip_specs.append(f"{pkg_name}=={pkg_version}")
        elif pkg_version:
            pip_specs.append(f"{pkg_name}{pkg_version}")
        else:
            pip_specs.append(pkg_name)

    if pip_specs:
        print(f"  Installing dependencies: {', '.join(pip_specs)}")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet", *pip_specs],
            capture_output=True,
        )


def _check_component(pkg_dir: Path, comp: ManifestComponent) -> list[TestResult]:
    """Import, find class, instantiate, and validate a component."""
    results: list[TestResult] = []

    def record(name: str, passed: bool, error: str | None = None) -> None:
        results.append(TestResult(name=f"{comp.name}/{name}", passed=passed, error=error))

    base_class = _get_sdk_class(comp.type)
    if base_class is None:
        record("sdk_available", False, "jarvis-command-sdk not installed or type unknown")
        return results

    # Setup import paths
    comp_file = Path(comp.path)
    parent = pkg_dir / comp_file.parent
    saved_path = sys.path[:]

    paths_to_add = [str(parent), str(pkg_dir)]
    for p in paths_to_add:
        if p not in sys.path:
            sys.path.insert(0, p)

    mod_name = comp_file.stem
    # Clear cached module
    for key in list(sys.modules.keys()):
        if key == mod_name or key.startswith(f"{mod_name}."):
            del sys.modules[key]

    # Import
    try:
        mod = importlib.import_module(mod_name)
        record("import", True)
    except Exception as e:
        record("import", False, f"Import failed: {e}")
        sys.path[:] = saved_path
        return results

    # Find subclass
    cls = None
    for attr_name in dir(mod):
        obj = getattr(mod, attr_name)
        if isinstance(obj, type) and issubclass(obj, base_class) and obj is not base_class:
            cls = obj
            break

    if cls is None:
        record("find_class", False, f"No {base_class.__name__} subclass found")
        sys.path[:] = saved_path
        return results
    record("find_class", True)

    # Instantiate
    try:
        instance = cls()
        record("instantiate", True)
    except Exception as e:
        record("instantiate", False, f"Instantiation failed: {e}")
        sys.path[:] = saved_path
        return results

    # Type-specific property checks
    checker = _TYPE_CHECKERS.get(comp.type)
    if checker:
        checker(instance, record)

    sys.path[:] = saved_path
    return results


def _check_command(instance: Any, record) -> None:
    _check_attr(instance, "command_name", str, record)
    _check_attr(instance, "description", str, record)
    _check_attr(instance, "parameters", list, record, prop_name="parameters_type")
    _check_attr(instance, "required_secrets", list, record, prop_name="required_secrets_type")

    try:
        kw = instance.keywords
        assert isinstance(kw, list) and all(isinstance(k, str) for k in kw)
        record("keywords_type", True)
    except Exception as e:
        record("keywords_type", False, str(e))

    try:
        examples = instance.generate_prompt_examples()
        assert isinstance(examples, list)
        record("prompt_examples", True)
    except Exception as e:
        record("prompt_examples", False, str(e))

    try:
        examples = instance.generate_adapter_examples()
        assert isinstance(examples, list)
        record("adapter_examples", True)
    except Exception as e:
        record("adapter_examples", False, str(e))


def _check_agent(instance: Any, record) -> None:
    _check_attr(instance, "name", str, record)
    _check_attr(instance, "description", str, record)
    try:
        _ = instance.schedule
        record("schedule", True)
    except Exception as e:
        record("schedule", False, str(e))
    _check_attr(instance, "required_secrets", list, record, prop_name="required_secrets_type")


def _check_protocol(instance: Any, record) -> None:
    _check_attr(instance, "protocol_name", str, record)
    _check_attr(instance, "supported_domains", list, record)


def _check_device_manager(instance: Any, record) -> None:
    _check_attr(instance, "name", str, record)
    _check_attr(instance, "friendly_name", str, record)
    _check_attr(instance, "description", str, record)


def _check_attr(
    instance: Any,
    attr: str,
    expected_type: type,
    record,
    prop_name: str | None = None,
) -> None:
    label = prop_name or attr
    try:
        val = getattr(instance, attr)
        assert isinstance(val, expected_type) and (not isinstance(val, str) or len(val) > 0)
        record(label, True)
    except Exception as e:
        record(label, False, str(e))


_TYPE_CHECKERS = {
    "command": _check_command,
    "agent": _check_agent,
    "device_protocol": _check_protocol,
    "device_manager": _check_device_manager,
}
