"""Tests for manifest model and I/O."""

from pathlib import Path

import yaml

from jdt.core.manifest_model import CommandManifest, ManifestComponent, ManifestAuthor
from jdt.core.manifest_io import infer_components, write_manifest, find_manifest


class TestManifestModel:
    def test_basic_manifest(self):
        m = CommandManifest(
            name="test", description="Test", version="1.0.0",
            author=ManifestAuthor(github="user"),
        )
        assert m.name == "test"
        assert m.version == "1.0.0"
        assert m.is_bundle is False

    def test_bundle_detection(self):
        m = CommandManifest(
            name="test", description="Test", version="1.0.0",
            components=[
                ManifestComponent(type="command", name="cmd1", path="cmd.py"),
                ManifestComponent(type="agent", name="agt1", path="agt.py"),
            ],
        )
        assert m.is_bundle is True

    def test_single_protocol_is_bundle(self):
        m = CommandManifest(
            name="test", description="Test", version="1.0.0",
            components=[
                ManifestComponent(type="device_protocol", name="proto", path="proto.py"),
            ],
        )
        assert m.is_bundle is True


class TestInferComponents:
    def test_infer_root_command(self, tmp_path: Path):
        (tmp_path / "command.py").write_text("class Cmd: pass")
        result = infer_components(tmp_path, "my_cmd")
        assert len(result) == 1
        assert result[0].type == "command"
        assert result[0].name == "my_cmd"

    def test_infer_convention_command(self, tmp_path: Path):
        cmd_dir = tmp_path / "commands" / "weather"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "command.py").write_text("class Cmd: pass")
        result = infer_components(tmp_path, "pkg")
        assert len(result) == 1
        assert result[0].type == "command"
        assert result[0].name == "weather"
        assert result[0].path == "commands/weather/command.py"

    def test_infer_protocol(self, tmp_path: Path):
        proto_dir = tmp_path / "device_families" / "lifx"
        proto_dir.mkdir(parents=True)
        (proto_dir / "protocol.py").write_text("class Proto: pass")
        result = infer_components(tmp_path, "pkg")
        assert len(result) == 1
        assert result[0].type == "device_protocol"

    def test_infer_agent(self, tmp_path: Path):
        agent_dir = tmp_path / "agents" / "news"
        agent_dir.mkdir(parents=True)
        (agent_dir / "agent.py").write_text("class Agent: pass")
        result = infer_components(tmp_path, "pkg")
        assert len(result) == 1
        assert result[0].type == "agent"

    def test_infer_routine(self, tmp_path: Path):
        (tmp_path / "routine.json").write_text('{"steps": []}')
        result = infer_components(tmp_path, "my_routine")
        assert len(result) == 1
        assert result[0].type == "routine"

    def test_infer_multi_component(self, tmp_path: Path):
        (tmp_path / "commands" / "cmd").mkdir(parents=True)
        (tmp_path / "commands" / "cmd" / "command.py").write_text("pass")
        (tmp_path / "agents" / "agt").mkdir(parents=True)
        (tmp_path / "agents" / "agt" / "agent.py").write_text("pass")
        result = infer_components(tmp_path, "pkg")
        assert len(result) == 2
        types = {r.type for r in result}
        assert types == {"command", "agent"}

    def test_skip_hidden_dirs(self, tmp_path: Path):
        (tmp_path / "commands" / ".hidden").mkdir(parents=True)
        (tmp_path / "commands" / ".hidden" / "command.py").write_text("pass")
        (tmp_path / "commands" / "_private").mkdir(parents=True)
        (tmp_path / "commands" / "_private" / "command.py").write_text("pass")
        result = infer_components(tmp_path, "pkg")
        assert len(result) == 0

    def test_empty_dir_returns_nothing(self, tmp_path: Path):
        result = infer_components(tmp_path, "pkg")
        assert len(result) == 0


class TestWriteManifest:
    def test_roundtrip(self, tmp_path: Path):
        m = CommandManifest(
            name="test", description="Test desc", version="1.0.0",
            author=ManifestAuthor(github="user"),
            categories=["utilities"],
        )
        output = write_manifest(m, tmp_path)
        assert output.exists()
        assert output.name == "jarvis_package.yaml"

        with open(output) as f:
            data = yaml.safe_load(f)
        assert data["name"] == "test"
        assert data["version"] == "1.0.0"
        assert data["categories"] == ["utilities"]


class TestFindManifest:
    def test_find_package_yaml(self, tmp_path: Path):
        (tmp_path / "jarvis_package.yaml").write_text("name: test")
        assert find_manifest(tmp_path) is not None

    def test_find_command_yaml(self, tmp_path: Path):
        (tmp_path / "jarvis_command.yaml").write_text("name: test")
        assert find_manifest(tmp_path) is not None

    def test_prefer_package_over_command(self, tmp_path: Path):
        (tmp_path / "jarvis_package.yaml").write_text("name: pkg")
        (tmp_path / "jarvis_command.yaml").write_text("name: cmd")
        result = find_manifest(tmp_path)
        assert result is not None
        assert result.name == "jarvis_package.yaml"

    def test_missing_returns_none(self, tmp_path: Path):
        assert find_manifest(tmp_path) is None
