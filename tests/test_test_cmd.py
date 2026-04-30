"""Integration tests for jdt test (import checks)."""

from pathlib import Path

from jdt.analysis.import_checks import run_import_checks
from jdt.core.manifest_model import ManifestComponent


class TestImportChecks:
    def test_valid_command(self, tmp_pkg: Path):
        comps = [ManifestComponent(type="command", name="test_cmd", path="commands/test_cmd/command.py")]
        result = run_import_checks(tmp_pkg, comps)
        assert result.passed, f"Failed: {[(t.name, t.error) for t in result.tests if not t.passed]}"
        assert result.pass_count >= 10  # import, find_class, instantiate, 7+ property checks

    def test_bundle_all_pass(self, tmp_bundle: Path):
        comps = [
            ManifestComponent(type="command", name="test_bundle", path="commands/test_bundle/command.py"),
            ManifestComponent(type="agent", name="test_bundle", path="agents/test_bundle/agent.py"),
        ]
        result = run_import_checks(tmp_bundle, comps)
        assert result.passed
        assert result.pass_count >= 14  # command (10) + agent (4+)

    def test_import_failure(self, tmp_path: Path):
        cmd_dir = tmp_path / "commands" / "broken"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "__init__.py").write_text("")
        (cmd_dir / "command.py").write_text("import nonexistent_module_xyz")
        comps = [ManifestComponent(type="command", name="broken", path="commands/broken/command.py")]
        result = run_import_checks(tmp_path, comps)
        assert not result.passed
        assert any("Import failed" in (t.error or "") for t in result.tests)

    def test_missing_class(self, tmp_path: Path):
        cmd_dir = tmp_path / "commands" / "nope"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "__init__.py").write_text("")
        (cmd_dir / "command.py").write_text("class NotACommand:\n    pass")
        comps = [ManifestComponent(type="command", name="nope", path="commands/nope/command.py")]
        result = run_import_checks(tmp_path, comps)
        assert not result.passed
        assert any("No IJarvisCommand" in (t.error or "") for t in result.tests)

    def test_routine_skipped(self, tmp_routine: Path):
        comps = [ManifestComponent(type="routine", name="test_routine", path="routines/test_routine/routine.json")]
        result = run_import_checks(tmp_routine, comps)
        assert result.passed
        assert result.pass_count == 0  # Routines produce no import tests
