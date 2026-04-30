"""Tests for manifest validation."""

from pathlib import Path

import yaml

from jdt.analysis.manifest_validation import validate_manifest


class TestValidateManifest:
    def test_valid_package(self, tmp_pkg: Path):
        result = validate_manifest(tmp_pkg)
        assert result.passed
        assert len(result.errors) == 0
        assert len(result.components) == 1

    def test_missing_manifest(self, tmp_path: Path):
        result = validate_manifest(tmp_path)
        assert not result.passed
        assert any("No jarvis_package.yaml" in e for e in result.errors)

    def test_invalid_yaml(self, tmp_path: Path):
        (tmp_path / "jarvis_package.yaml").write_text(": invalid: yaml: [")
        result = validate_manifest(tmp_path)
        assert not result.passed

    def test_missing_required_fields(self, tmp_path: Path):
        (tmp_path / "jarvis_package.yaml").write_text("categories: [utilities]")
        result = validate_manifest(tmp_path)
        assert not result.passed
        assert any("name" in e for e in result.errors)
        assert any("description" in e for e in result.errors)
        assert any("version" in e for e in result.errors)

    def test_invalid_semver(self, tmp_path: Path):
        manifest = {"name": "test", "description": "Test", "version": "1.0"}
        with open(tmp_path / "jarvis_package.yaml", "w") as f:
            yaml.dump(manifest, f)
        result = validate_manifest(tmp_path)
        assert not result.passed
        assert any("semver" in e for e in result.errors)

    def test_valid_semver(self, tmp_path: Path):
        manifest = {
            "name": "test", "description": "Test", "version": "1.0.0",
            "components": [{"type": "command", "name": "test", "path": "command.py"}],
        }
        (tmp_path / "command.py").write_text("pass")
        with open(tmp_path / "jarvis_package.yaml", "w") as f:
            yaml.dump(manifest, f)
        result = validate_manifest(tmp_path)
        assert result.passed

    def test_unknown_categories_warns(self, tmp_path: Path):
        manifest = {
            "name": "test", "description": "Test", "version": "1.0.0",
            "categories": ["utilities", "doesnotexist"],
            "components": [{"type": "command", "name": "test", "path": "command.py"}],
        }
        (tmp_path / "command.py").write_text("pass")
        with open(tmp_path / "jarvis_package.yaml", "w") as f:
            yaml.dump(manifest, f)
        result = validate_manifest(tmp_path)
        assert result.passed  # Warnings don't fail
        assert any("doesnotexist" in w for w in result.warnings)

    def test_missing_component_path(self, tmp_path: Path):
        manifest = {
            "name": "test", "description": "Test", "version": "1.0.0",
            "components": [{"type": "command", "name": "test", "path": "nonexistent.py"}],
        }
        with open(tmp_path / "jarvis_package.yaml", "w") as f:
            yaml.dump(manifest, f)
        result = validate_manifest(tmp_path)
        assert not result.passed
        assert any("not found" in e for e in result.errors)

    def test_inferred_components(self, tmp_pkg: Path):
        """Remove components from manifest and verify inference works."""
        with open(tmp_pkg / "jarvis_package.yaml") as f:
            data = yaml.safe_load(f)
        del data["components"]
        with open(tmp_pkg / "jarvis_package.yaml", "w") as f:
            yaml.dump(data, f)

        result = validate_manifest(tmp_pkg)
        assert result.passed
        assert len(result.components) == 1
        assert any("inferred" in w.lower() for w in result.warnings)

    def test_bundle_validation(self, tmp_bundle: Path):
        result = validate_manifest(tmp_bundle)
        assert result.passed
        assert len(result.components) == 2

    def test_routine_validation(self, tmp_routine: Path):
        result = validate_manifest(tmp_routine)
        assert result.passed
        assert len(result.components) == 1
