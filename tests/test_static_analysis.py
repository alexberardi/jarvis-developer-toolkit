"""Tests for static analysis."""

from pathlib import Path

from jdt.analysis.static_analysis import run_static_analysis
from jdt.core.manifest_model import ManifestComponent


class TestStaticAnalysis:
    def test_clean_command_passes(self, tmp_pkg: Path):
        comps = [ManifestComponent(type="command", name="test_cmd", path="commands/test_cmd/command.py")]
        result = run_static_analysis(tmp_pkg, comps)
        assert result.passed

    def test_syntax_error_fails(self, tmp_path: Path):
        cmd_dir = tmp_path / "commands" / "bad"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "command.py").write_text("def broken(:\n  pass")
        comps = [ManifestComponent(type="command", name="bad", path="commands/bad/command.py")]
        result = run_static_analysis(tmp_path, comps)
        assert not result.passed

    def test_missing_base_class(self, tmp_path: Path):
        cmd_dir = tmp_path / "commands" / "no_base"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "command.py").write_text("class Foo:\n    pass")
        comps = [ManifestComponent(type="command", name="no_base", path="commands/no_base/command.py")]
        result = run_static_analysis(tmp_path, comps)
        assert not result.passed

    def test_dangerous_import_flagged(self, tmp_path: Path):
        cmd_dir = tmp_path / "commands" / "danger"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "command.py").write_text(
            "import subprocess\n"
            "from jarvis_command_sdk import IJarvisCommand\n"
            "class Cmd(IJarvisCommand):\n"
            "    pass\n"
        )
        comps = [ManifestComponent(type="command", name="danger", path="commands/danger/command.py")]
        result = run_static_analysis(tmp_path, comps)
        assert any("subprocess" in p for cr in result.component_results for p in cr.dangerous_patterns)

    def test_eval_call_flagged(self, tmp_path: Path):
        cmd_dir = tmp_path / "commands" / "evalcmd"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "command.py").write_text(
            "from jarvis_command_sdk import IJarvisCommand\n"
            "class Cmd(IJarvisCommand):\n"
            "    def run(self, **kw):\n"
            "        return eval('1+1')\n"
        )
        comps = [ManifestComponent(type="command", name="evalcmd", path="commands/evalcmd/command.py")]
        result = run_static_analysis(tmp_path, comps)
        assert any("eval" in p for cr in result.component_results for p in cr.dangerous_patterns)

    def test_sql_mutation_flagged(self, tmp_path: Path):
        cmd_dir = tmp_path / "commands" / "sqlcmd"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "command.py").write_text(
            "from jarvis_command_sdk import IJarvisCommand\n"
            "class Cmd(IJarvisCommand):\n"
            "    q = 'CREATE TABLE users (id INTEGER)'\n"
        )
        comps = [ManifestComponent(type="command", name="sqlcmd", path="commands/sqlcmd/command.py")]
        result = run_static_analysis(tmp_path, comps)
        assert any("SQL" in p for cr in result.component_results for p in cr.dangerous_patterns)


class TestSharedDirConflicts:
    def test_node_builtin_blocked(self, tmp_path: Path):
        (tmp_path / "services").mkdir()
        (tmp_path / "services" / "helper.py").write_text("x = 1")
        comps = [ManifestComponent(type="command", name="cmd", path="commands/cmd/command.py")]
        result = run_static_analysis(tmp_path, comps)
        assert any("services" in e for e in result.errors)

    def test_generic_name_blocked(self, tmp_path: Path):
        (tmp_path / "shared").mkdir()
        (tmp_path / "shared" / "util.py").write_text("x = 1")
        comps = [ManifestComponent(type="command", name="cmd", path="commands/cmd/command.py")]
        result = run_static_analysis(tmp_path, comps)
        assert any("shared" in e for e in result.errors)

    def test_lib_blocked(self, tmp_path: Path):
        (tmp_path / "lib").mkdir()
        (tmp_path / "lib" / "module.py").write_text("x = 1")
        comps = [ManifestComponent(type="command", name="cmd", path="commands/cmd/command.py")]
        result = run_static_analysis(tmp_path, comps)
        assert any("lib" in e for e in result.errors)

    def test_helpers_blocked(self, tmp_path: Path):
        (tmp_path / "helpers").mkdir()
        (tmp_path / "helpers" / "module.py").write_text("x = 1")
        comps = [ManifestComponent(type="command", name="cmd", path="commands/cmd/command.py")]
        result = run_static_analysis(tmp_path, comps)
        assert any("helpers" in e for e in result.errors)

    def test_package_specific_name_allowed(self, tmp_path: Path):
        (tmp_path / "my_protocol_shared").mkdir()
        (tmp_path / "my_protocol_shared" / "client.py").write_text("x = 1")
        comps = [ManifestComponent(type="command", name="cmd", path="commands/cmd/command.py")]
        result = run_static_analysis(tmp_path, comps)
        assert not any("my_protocol_shared" in e for e in result.errors)

    def test_component_dir_not_flagged(self, tmp_path: Path):
        """Component directories (commands/, agents/) should not be flagged."""
        cmd_dir = tmp_path / "commands" / "my_cmd"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "command.py").write_text("pass")
        comps = [ManifestComponent(type="command", name="my_cmd", path="commands/my_cmd/command.py")]
        result = run_static_analysis(tmp_path, comps)
        assert not any("commands" in e for e in result.errors)

    def test_empty_dir_not_flagged(self, tmp_path: Path):
        """Dirs without .py files should not be flagged."""
        (tmp_path / "shared").mkdir()
        (tmp_path / "shared" / "readme.md").write_text("docs")
        comps = []
        result = run_static_analysis(tmp_path, comps)
        assert len(result.errors) == 0

    def test_error_message_suggests_rename(self, tmp_path: Path):
        (tmp_path / "lib").mkdir()
        (tmp_path / "lib" / "module.py").write_text("x = 1")
        comps = [ManifestComponent(type="command", name="cmd", path="commands/cmd/command.py")]
        result = run_static_analysis(tmp_path, comps)
        # Should suggest a package-specific name
        errors_text = " ".join(result.errors)
        assert "_shared" in errors_text


class TestRoutineValidation:
    def test_valid_routine(self, tmp_routine: Path):
        comps = [ManifestComponent(type="routine", name="test_routine", path="routines/test_routine/routine.json")]
        result = run_static_analysis(tmp_routine, comps)
        assert result.passed

    def test_missing_steps(self, tmp_path: Path):
        routine_dir = tmp_path / "routines" / "bad"
        routine_dir.mkdir(parents=True)
        import json
        with open(routine_dir / "routine.json", "w") as f:
            json.dump({"trigger_phrases": ["test"]}, f)
        comps = [ManifestComponent(type="routine", name="bad", path="routines/bad/routine.json")]
        result = run_static_analysis(tmp_path, comps)
        assert not result.passed

    def test_invalid_json(self, tmp_path: Path):
        routine_dir = tmp_path / "routines" / "bad"
        routine_dir.mkdir(parents=True)
        (routine_dir / "routine.json").write_text("{invalid json")
        comps = [ManifestComponent(type="routine", name="bad", path="routines/bad/routine.json")]
        result = run_static_analysis(tmp_path, comps)
        assert not result.passed
