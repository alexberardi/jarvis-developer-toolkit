"""Shared test fixtures."""

import json
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def tmp_pkg(tmp_path: Path) -> Path:
    """Create a minimal valid command package in a temp directory."""
    pkg_dir = tmp_path / "test_cmd"
    cmd_dir = pkg_dir / "commands" / "test_cmd"
    cmd_dir.mkdir(parents=True)

    # Minimal command stub
    (cmd_dir / "__init__.py").write_text("")
    (cmd_dir / "command.py").write_text('''
from jarvis_command_sdk import (
    IJarvisCommand, CommandResponse, CommandExample,
    JarvisParameter, JarvisSecret, RequestInformation,
)

class TestCmdCommand(IJarvisCommand):
    @property
    def command_name(self) -> str:
        return "test_cmd"

    @property
    def description(self) -> str:
        return "A test command"

    @property
    def parameters(self) -> list[JarvisParameter]:
        return [JarvisParameter(name="query", param_type="string", required=True, description="Query")]

    @property
    def required_secrets(self) -> list[JarvisSecret]:
        return []

    @property
    def keywords(self) -> list[str]:
        return ["test"]

    def generate_prompt_examples(self) -> list[CommandExample]:
        return [CommandExample(voice_command="test", expected_parameters={"query": "x"}, is_primary=True)]

    def generate_adapter_examples(self) -> list[CommandExample]:
        return [CommandExample(voice_command=f"test {i}", expected_parameters={"query": str(i)}) for i in range(10)]

    def run(self, request_info: RequestInformation, **kwargs) -> CommandResponse:
        return CommandResponse.success_response(context_data={"message": "ok"}, wait_for_input=False)
''')

    # Manifest
    manifest = {
        "name": "test_cmd",
        "display_name": "Test Command",
        "description": "A test command",
        "version": "0.1.0",
        "author": {"github": "tester"},
        "categories": ["utilities"],
        "platforms": ["darwin", "linux"],
        "keywords": ["test"],
        "components": [
            {"type": "command", "name": "test_cmd", "path": "commands/test_cmd/command.py"},
        ],
        "secrets": [],
        "packages": [],
    }
    with open(pkg_dir / "jarvis_package.yaml", "w") as f:
        yaml.dump(manifest, f)

    return pkg_dir


@pytest.fixture
def tmp_bundle(tmp_path: Path) -> Path:
    """Create a multi-component bundle package."""
    pkg_dir = tmp_path / "test_bundle"

    # Command
    cmd_dir = pkg_dir / "commands" / "test_bundle"
    cmd_dir.mkdir(parents=True)
    (cmd_dir / "__init__.py").write_text("")
    (cmd_dir / "command.py").write_text('''
from jarvis_command_sdk import IJarvisCommand, CommandResponse, CommandExample, JarvisParameter, JarvisSecret, RequestInformation

class TestBundleCommand(IJarvisCommand):
    @property
    def command_name(self): return "test_bundle"
    @property
    def description(self): return "Test"
    @property
    def parameters(self): return [JarvisParameter(name="q", param_type="string", required=True, description="Q")]
    @property
    def required_secrets(self): return []
    @property
    def keywords(self): return ["test"]
    def generate_prompt_examples(self): return [CommandExample(voice_command="test", expected_parameters={"q": "x"}, is_primary=True)]
    def generate_adapter_examples(self): return [CommandExample(voice_command=f"test {i}", expected_parameters={"q": str(i)}) for i in range(10)]
    def run(self, request_info, **kwargs): return CommandResponse.success_response(context_data={"message": "ok"}, wait_for_input=False)
''')

    # Agent
    agent_dir = pkg_dir / "agents" / "test_bundle"
    agent_dir.mkdir(parents=True)
    (agent_dir / "__init__.py").write_text("")
    (agent_dir / "agent.py").write_text('''
from jarvis_command_sdk import IJarvisAgent, AgentSchedule, JarvisSecret

class TestBundleAgent(IJarvisAgent):
    def __init__(self): self._data = {}
    @property
    def name(self): return "test_bundle"
    @property
    def description(self): return "Test agent"
    @property
    def schedule(self): return AgentSchedule(interval_seconds=60, run_on_startup=True)
    @property
    def required_secrets(self): return []
    async def run(self): self._data = {"ok": True}
    def get_context_data(self): return self._data
''')

    # Manifest
    manifest = {
        "name": "test_bundle",
        "description": "A test bundle",
        "version": "0.1.0",
        "author": {"github": "tester"},
        "components": [
            {"type": "command", "name": "test_bundle", "path": "commands/test_bundle/command.py"},
            {"type": "agent", "name": "test_bundle", "path": "agents/test_bundle/agent.py"},
        ],
        "secrets": [],
        "packages": [],
    }
    with open(pkg_dir / "jarvis_package.yaml", "w") as f:
        yaml.dump(manifest, f)

    return pkg_dir


@pytest.fixture
def tmp_routine(tmp_path: Path) -> Path:
    """Create a routine-only package."""
    pkg_dir = tmp_path / "test_routine"
    routine_dir = pkg_dir / "routines" / "test_routine"
    routine_dir.mkdir(parents=True)

    routine = {
        "trigger_phrases": ["run test routine"],
        "steps": [{"command": "calculate", "parameters": {"expression": "1+1"}}],
        "response_instruction": "Tell the user the result.",
    }
    with open(routine_dir / "routine.json", "w") as f:
        json.dump(routine, f)

    manifest = {
        "name": "test_routine",
        "description": "A test routine",
        "version": "0.1.0",
        "author": {"github": "tester"},
        "components": [
            {"type": "routine", "name": "test_routine", "path": "routines/test_routine/routine.json"},
        ],
    }
    with open(pkg_dir / "jarvis_package.yaml", "w") as f:
        yaml.dump(manifest, f)

    return pkg_dir
