"""Stub templates for all Jarvis component types.

Each template is the minimal valid implementation that passes jdt test.
"""

COMMAND_TEMPLATE = '''"""Voice command: {display_name}."""

from jarvis_command_sdk import (
    IJarvisCommand, CommandResponse, CommandExample,
    JarvisParameter, JarvisSecret, RequestInformation,
)

try:
    from jarvis_log_client import JarvisLogger
except ImportError:
    import logging

    class JarvisLogger:
        def __init__(self, **kw):
            self._log = logging.getLogger(kw.get("service", __name__))

        def info(self, msg, **kw):
            self._log.info(msg)

        def error(self, msg, **kw):
            self._log.error(msg)


logger = JarvisLogger(service="cmd.{name}")


class {class_name}(IJarvisCommand):
    @property
    def command_name(self) -> str:
        return "{name}"

    @property
    def description(self) -> str:
        return "{description}"

    @property
    def parameters(self) -> list[JarvisParameter]:
        return [
            JarvisParameter(
                name="query",
                param_type="string",
                required=True,
                description="The query to process",
            ),
        ]

    @property
    def required_secrets(self) -> list[JarvisSecret]:
        return []

    @property
    def keywords(self) -> list[str]:
        return ["{name}"]

    def generate_prompt_examples(self) -> list[CommandExample]:
        return [
            CommandExample(
                voice_command="run {name}",
                expected_parameters={{"query": "test"}},
                is_primary=True,
            ),
        ]

    def generate_adapter_examples(self) -> list[CommandExample]:
        return [
            CommandExample(
                voice_command=f"run {name} with {{q}}",
                expected_parameters={{"query": q}},
            )
            for q in ["test one", "test two", "test three", "test four", "test five",
                       "alpha", "beta", "gamma", "delta", "epsilon"]
        ]

    def run(self, request_info: RequestInformation, **kwargs) -> CommandResponse:
        query = kwargs.get("query", "")
        logger.info(f"Running {name} with query: {{query}}")
        return CommandResponse.success_response(
            context_data={{"message": f"Processed: {{query}}"}},
            wait_for_input=False,
        )
'''

AGENT_TEMPLATE = '''"""Background agent: {display_name}."""

from jarvis_command_sdk import IJarvisAgent, AgentSchedule, JarvisSecret

try:
    from jarvis_log_client import JarvisLogger
except ImportError:
    import logging

    class JarvisLogger:
        def __init__(self, **kw):
            self._log = logging.getLogger(kw.get("service", __name__))

        def info(self, msg, **kw):
            self._log.info(msg)

        def error(self, msg, **kw):
            self._log.error(msg)


logger = JarvisLogger(service="agent.{name}")


class {class_name}(IJarvisAgent):
    def __init__(self):
        self._cached_data: dict = {{}}

    @property
    def name(self) -> str:
        return "{name}"

    @property
    def description(self) -> str:
        return "{description}"

    @property
    def schedule(self) -> AgentSchedule:
        return AgentSchedule(interval_seconds=300, run_on_startup=True)

    @property
    def required_secrets(self) -> list[JarvisSecret]:
        return []

    async def run(self) -> None:
        logger.info("Running {name} agent")
        self._cached_data = {{"status": "ok"}}

    def get_context_data(self) -> dict:
        return self._cached_data
'''

PROTOCOL_TEMPLATE = '''"""Device protocol: {display_name}."""

from jarvis_command_sdk import (
    IJarvisDeviceProtocol, DiscoveredDevice, DeviceControlResult, JarvisSecret,
)

try:
    from jarvis_log_client import JarvisLogger
except ImportError:
    import logging

    class JarvisLogger:
        def __init__(self, **kw):
            self._log = logging.getLogger(kw.get("service", __name__))

        def info(self, msg, **kw):
            self._log.info(msg)

        def error(self, msg, **kw):
            self._log.error(msg)


logger = JarvisLogger(service="protocol.{name}")


class {class_name}(IJarvisDeviceProtocol):
    @property
    def protocol_name(self) -> str:
        return "{name}"

    @property
    def supported_domains(self) -> list[str]:
        return ["switch"]

    @property
    def required_secrets(self) -> list[JarvisSecret]:
        return []

    async def discover(self, timeout: float = 5.0) -> list[DiscoveredDevice]:
        logger.info("Discovering {name} devices")
        return []

    async def control(
        self, ip: str, action: str, data: dict | None = None, **kwargs
    ) -> DeviceControlResult:
        return DeviceControlResult(
            success=False,
            entity_id="unknown",
            action=action,
            error="Not implemented",
        )

    async def get_state(self, ip: str, **kwargs) -> dict | None:
        return None
'''

MANAGER_TEMPLATE = '''"""Device manager: {display_name}."""

from jarvis_command_sdk import IJarvisDeviceManager, DeviceManagerDevice

try:
    from jarvis_log_client import JarvisLogger
except ImportError:
    import logging

    class JarvisLogger:
        def __init__(self, **kw):
            self._log = logging.getLogger(kw.get("service", __name__))

        def info(self, msg, **kw):
            self._log.info(msg)

        def error(self, msg, **kw):
            self._log.error(msg)


logger = JarvisLogger(service="manager.{name}")


class {class_name}(IJarvisDeviceManager):
    @property
    def name(self) -> str:
        return "{name}"

    @property
    def friendly_name(self) -> str:
        return "{display_name}"

    @property
    def description(self) -> str:
        return "{description}"

    @property
    def can_edit_devices(self) -> bool:
        return False

    async def collect_devices(self) -> list[DeviceManagerDevice]:
        logger.info("Collecting {name} devices")
        return []
'''

ROUTINE_TEMPLATE = '''{routine_json}
'''

PROMPT_PROVIDER_TEMPLATE = '''"""Prompt provider: {display_name}."""

from jarvis_command_sdk import IJarvisPromptProvider


class {class_name}(IJarvisPromptProvider):
    @property
    def name(self) -> str:
        return "{name}"

    def build_system_prompt(
        self,
        node_context: dict,
        timezone: str | None,
        tools: list[dict],
        available_commands: list[dict] | None = None,
    ) -> str:
        prompt = "You are a helpful voice assistant.\\n\\n"
        prompt += "## Available Tools\\n"
        for tool in tools:
            prompt += f"- {{tool.get('name', 'unknown')}}\\n"
        return prompt

    def get_capabilities(self) -> dict:
        return {{
            "provider_name": "{display_name}",
            "model_family": "custom",
            "size_tier": "medium",
            "training_tier": "untrained",
            "use_tool_classifier": True,
        }}
'''

GITIGNORE_TEMPLATE = """__pycache__/
*.py[cod]
*$py.class
*.egg-info/
dist/
build/
.venv/
.env
.pytest_cache/
"""

README_TEMPLATE = """# {display_name}

{description}

## Installation

```bash
jdt deploy local .
```

## Development

```bash
jdt test .        # Run tests
jdt validate .    # Quick manifest check
jdt manifest .    # Regenerate manifest from code
```
"""

LICENSE_TEMPLATE = """MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


# Map component type -> (template, entry_filename, convention_dir_pattern)
TEMPLATE_MAP: dict[str, tuple[str, str, str]] = {
    "command": (COMMAND_TEMPLATE, "command.py", "commands/{name}"),
    "agent": (AGENT_TEMPLATE, "agent.py", "agents/{name}"),
    "device_protocol": (PROTOCOL_TEMPLATE, "protocol.py", "device_families/{name}"),
    "device_manager": (MANAGER_TEMPLATE, "manager.py", "device_managers/{name}"),
    "prompt_provider": (PROMPT_PROVIDER_TEMPLATE, "provider.py", "prompt_providers/{name}"),
    "routine": (ROUTINE_TEMPLATE, "routine.json", "routines/{name}"),
}
