"""Tests for jdt init scaffold generation."""

import ast
from pathlib import Path

import yaml

from jdt.scaffold.generator import scaffold_package
from jdt.analysis.manifest_validation import validate_manifest


class TestScaffoldPackage:
    def test_single_command(self, tmp_path: Path):
        pkg = scaffold_package("my_weather", ["command"], "tester", "weather", tmp_path)
        assert pkg.exists()
        assert (pkg / "jarvis_package.yaml").exists()
        assert (pkg / "commands" / "my_weather" / "command.py").exists()
        assert (pkg / "README.md").exists()
        assert (pkg / "LICENSE").exists()
        assert (pkg / ".gitignore").exists()

    def test_single_protocol(self, tmp_path: Path):
        pkg = scaffold_package("my_device", ["device_protocol"], "tester", "smart-home", tmp_path)
        assert (pkg / "device_families" / "my_device" / "protocol.py").exists()
        assert (pkg / "device_families" / "my_device" / "__init__.py").exists()

    def test_single_agent(self, tmp_path: Path):
        pkg = scaffold_package("my_agent", ["agent"], "tester", "utilities", tmp_path)
        assert (pkg / "agents" / "my_agent" / "agent.py").exists()

    def test_single_manager(self, tmp_path: Path):
        pkg = scaffold_package("my_mgr", ["device_manager"], "tester", "smart-home", tmp_path)
        assert (pkg / "device_managers" / "my_mgr" / "manager.py").exists()

    def test_single_routine(self, tmp_path: Path):
        pkg = scaffold_package("my_routine", ["routine"], "tester", "automation", tmp_path)
        assert (pkg / "routines" / "my_routine" / "routine.json").exists()

    def test_multi_component_bundle(self, tmp_path: Path):
        pkg = scaffold_package(
            "my_bundle", ["command", "agent", "device_protocol"],
            "tester", "smart-home", tmp_path,
        )
        assert (pkg / "commands" / "my_bundle" / "command.py").exists()
        assert (pkg / "agents" / "my_bundle" / "agent.py").exists()
        assert (pkg / "device_families" / "my_bundle" / "protocol.py").exists()

    def test_manifest_valid(self, tmp_path: Path):
        pkg = scaffold_package("valid_pkg", ["command"], "tester", "utilities", tmp_path)
        result = validate_manifest(pkg)
        assert result.passed, f"Errors: {result.errors}"

    def test_manifest_components_match(self, tmp_path: Path):
        pkg = scaffold_package(
            "multi", ["command", "agent"], "tester", "utilities", tmp_path,
        )
        with open(pkg / "jarvis_package.yaml") as f:
            data = yaml.safe_load(f)
        assert len(data["components"]) == 2
        types = {c["type"] for c in data["components"]}
        assert types == {"command", "agent"}

    def test_stubs_are_valid_python(self, tmp_path: Path):
        pkg = scaffold_package(
            "syn_check", ["command", "agent", "device_protocol", "device_manager"],
            "tester", "utilities", tmp_path,
        )
        py_files = list(pkg.rglob("*.py"))
        assert len(py_files) > 0
        for f in py_files:
            if f.name == "__init__.py":
                continue
            source = f.read_text()
            try:
                ast.parse(source)
            except SyntaxError as e:
                raise AssertionError(f"Syntax error in {f}: {e}") from e

    def test_manifest_author(self, tmp_path: Path):
        pkg = scaffold_package("auth_test", ["command"], "myuser", "utilities", tmp_path)
        with open(pkg / "jarvis_package.yaml") as f:
            data = yaml.safe_load(f)
        assert data["author"]["github"] == "myuser"
