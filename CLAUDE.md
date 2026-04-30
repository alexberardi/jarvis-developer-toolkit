# jarvis-developer-toolkit

CLI toolkit (`jdt`) for building, testing, and deploying Jarvis voice assistant packages.

**This is the primary tool for creating Jarvis packages.** When asked to build a command, device protocol, agent, or any other component — use `jdt init` to scaffold, implement the logic, then `jdt test` to validate.

## Quick Reference

```bash
cd jarvis-developer-toolkit
python3 -m venv .venv
.venv/bin/pip install -e ../jarvis-command-sdk
.venv/bin/pip install -e ".[dev]"
jdt --help
pytest
```

## Workflow: Building a Package

```bash
# 1. Scaffold
jdt init my_weather --type command --author username

# 2. Implement (edit the stub files)
cd my_weather
# ... write your code ...

# 3. Test
jdt test . --install-deps    # full Pantry-compatible validation
jdt test . -v                # verbose output

# 4. Deploy
jdt deploy local .                        # local node
jdt deploy docker jarvis-node-kitchen .   # Docker container
jdt deploy ssh pi@jarvis-dev.local .      # Pi Zero over SSH
```

## CLI Commands

| Command | Purpose |
|---------|---------|
| `jdt init <name> --type <types>` | Scaffold a new package |
| `jdt test [path]` | Run Pantry-compatible tests (manifest + AST + imports) |
| `jdt validate [path]` | Fast manifest-only check |
| `jdt manifest [path]` | Generate/update jarvis_package.yaml from code |
| `jdt deploy <local\|docker\|ssh> [path]` | Install to a node |

## Toolkit Architecture

```
src/jdt/
├── cli.py              # Argparse CLI entry point
├── commands/           # Subcommand handlers (init, manifest, test, deploy, validate)
├── core/               # Manifest models, introspection, constants
├── analysis/           # Static analysis (AST), import checks, manifest validation
├── scaffold/           # Template stubs and directory generation
└── deploy/             # Local, Docker, SSH deployment
```

---

# Jarvis Package Development Guide

Everything below is the reference material needed to build Jarvis packages from scratch. This is the accumulated knowledge from the SDK interfaces, validation rules, real-world packages, and lessons learned.

## What Is a Jarvis Package?

A standalone repo that extends a Jarvis voice node with one or more components. The node's Pantry system installs packages by scattering components to type-specific directories.

## Component Types

| Type | Entry File | Convention Dir | SDK Interface | Async |
|------|-----------|----------------|---------------|-------|
| command | command.py | `commands/{name}/` | IJarvisCommand | No |
| agent | agent.py | `agents/{name}/` | IJarvisAgent | Yes |
| device_protocol | protocol.py | `device_families/{name}/` | IJarvisDeviceProtocol | Yes |
| device_manager | manager.py | `device_managers/{name}/` | IJarvisDeviceManager | Yes |
| prompt_provider | provider.py | `prompt_providers/{name}/` | IJarvisPromptProvider | No |
| routine | routine.json | `routines/{name}/` | (JSON schema) | N/A |

## Package Repo Structure

### Single command
```
my_command/
├── jarvis_package.yaml
├── commands/my_command/
│   ├── __init__.py
│   └── command.py
├── README.md
├── LICENSE
└── .gitignore
```

### Multi-component bundle
```
my_integration/
├── jarvis_package.yaml
├── commands/control_thing/
│   ├── __init__.py
│   └── command.py
├── agents/thing_watcher/
│   ├── __init__.py
│   └── agent.py
├── device_families/thing/
│   ├── __init__.py
│   ├── protocol.py
│   └── thing_client.py      # helper module
├── my_integration_shared/    # shared code (MUST be package-specific name)
│   ├── __init__.py
│   └── api_client.py
├── README.md
├── LICENSE
└── .gitignore
```

## Manifest (jarvis_package.yaml)

```yaml
schema_version: 1
name: "my_command"                    # snake_case, unique
display_name: "My Command"           # human-readable
description: "What it does"          # 1-2 sentences
version: "1.0.0"                     # semver (X.Y.Z)
min_jarvis_version: "0.9.0"
license: "MIT"
author:
  github: "username"

categories: ["utilities"]            # see valid list below
platforms: ["darwin", "linux"]       # empty = all platforms
keywords: ["search", "find"]

components:
  - type: command
    name: my_command
    path: commands/my_command/command.py

packages:                            # pip dependencies
  - name: httpx
  - name: pydantic
    version: ">=2.0,<3.0"

secrets:
  - key: MY_API_KEY
    scope: integration               # integration | node
    value_type: string               # string | int | bool
    description: "API key for the service"
    required: true
    is_sensitive: true
    friendly_name: "API Key"         # shown in mobile UI
```

### Valid Categories
`automation`, `calendar`, `communication`, `entertainment`, `finance`, `fitness`, `food`, `games`, `health`, `home`, `information`, `media`, `music`, `news`, `productivity`, `shopping`, `smart-home`, `sports`, `travel`, `utilities`, `weather`

### Valid Parameter Types
`string`, `int`, `float`, `bool`, `enum`, `date`, `time`, `datetime`, plus array variants like `array<string>`, `array<datetime>`

### Secret Scopes
- `integration` — shared across all nodes in a household (e.g., API key)
- `node` — per-node (e.g., a location setting specific to one Pi)

---

## SDK Interface Reference

### IJarvisCommand — Voice Commands

Commands handle voice intents. The LLM parses voice input, selects a command, extracts parameters, and calls `run()`.

```python
from jarvis_command_sdk import (
    IJarvisCommand, CommandResponse, CommandExample,
    JarvisParameter, JarvisSecret, RequestInformation, JarvisStorage,
)

try:
    from jarvis_log_client import JarvisLogger
except ImportError:
    import logging
    class JarvisLogger:
        def __init__(self, **kw): self._log = logging.getLogger(kw.get("service", __name__))
        def info(self, msg, **kw): self._log.info(msg)
        def error(self, msg, **kw): self._log.error(msg)

logger = JarvisLogger(service="cmd.my_command")
_storage = JarvisStorage("my_command")

class MyCommand(IJarvisCommand):
    @property
    def command_name(self) -> str:
        return "my_command"                    # snake_case, unique across all commands

    @property
    def description(self) -> str:
        return "Does something useful"         # 1-2 sentences for LLM context

    @property
    def parameters(self) -> list[JarvisParameter]:
        return [
            JarvisParameter(
                name="query",
                param_type="string",
                required=True,
                description="What to search for",  # tells LLM what to extract from voice
            ),
            JarvisParameter(
                name="count",
                param_type="int",
                required=False,
                description="Number of results",
                default="5",
            ),
        ]

    @property
    def required_secrets(self) -> list[JarvisSecret]:
        return [
            JarvisSecret(
                key="MY_API_KEY",
                description="API key for the service",
                scope="integration",
                value_type="string",
                is_sensitive=True,
                required=True,
            ),
        ]

    @property
    def keywords(self) -> list[str]:
        return ["search", "find", "lookup"]    # fuzzy-match terms for command routing

    def generate_prompt_examples(self) -> list[CommandExample]:
        """3-5 concise examples shown in LLM system prompt for tool selection."""
        return [
            CommandExample(
                voice_command="search for pizza restaurants",
                expected_parameters={"query": "pizza restaurants"},
                is_primary=True,
            ),
            CommandExample(
                voice_command="find coffee shops nearby",
                expected_parameters={"query": "coffee shops nearby"},
            ),
            CommandExample(
                voice_command="look up the top 3 bookstores",
                expected_parameters={"query": "bookstores", "count": 3},
            ),
        ]

    def generate_adapter_examples(self) -> list[CommandExample]:
        """10-20 varied examples for LoRA adapter fine-tuning."""
        queries = ["restaurants", "hotels", "gas stations", "libraries", "gyms",
                   "pharmacies", "parks", "theaters", "bakeries", "clinics"]
        return [
            CommandExample(
                voice_command=f"search for {q}",
                expected_parameters={"query": q},
            )
            for q in queries
        ]

    def run(self, request_info: RequestInformation, **kwargs) -> CommandResponse:
        query = kwargs.get("query", "")
        api_key = _storage.get_secret("MY_API_KEY", scope="integration")

        if not api_key:
            return CommandResponse.error_response(error_details="API key not configured")

        # ... business logic ...
        result = f"Found results for: {query}"

        return CommandResponse.success_response(
            context_data={"message": result},    # "message" key is spoken by TTS
            wait_for_input=False,                # False = conversation ends
        )
```

**Key patterns:**
- `context_data["message"]` is what gets spoken aloud by TTS
- Never raise exceptions from `run()` — return `CommandResponse.error_response()` instead
- Use `JarvisStorage` for secrets and persistent data, not raw DB access
- The `try: from jarvis_log_client` pattern is required — the logger is optional at runtime

**CommandResponse factory methods:**
- `CommandResponse.success_response(context_data, wait_for_input=True)` — normal response
- `CommandResponse.error_response(error_details)` — error with message
- `CommandResponse.final_response(context_data)` — no follow-up expected
- `CommandResponse.follow_up_response(context_data)` — expects user follow-up

**Optional command features:**
- `validate_call(**kwargs) -> list[ValidationResult]` — validate parameters before run
- `pre_route(voice_command) -> PreRouteResult | None` — deterministic bypass of LLM routing
- `post_process_tool_call(args, voice_command) -> dict` — fix LLM parameter mistakes
- `required_packages -> list[JarvisPackage]` — pip dependencies
- `authentication -> AuthenticationConfig` — OAuth config for mobile app flow
- `setup_guide -> str | None` — markdown instructions shown in mobile settings

### IJarvisAgent — Background Data Collection

Agents run on a schedule, cache data, and inject it into voice command context.

```python
from jarvis_command_sdk import IJarvisAgent, AgentSchedule, JarvisSecret

class MyAgent(IJarvisAgent):
    def __init__(self):
        self._cached_data: dict = {}

    @property
    def name(self) -> str:
        return "my_agent"

    @property
    def description(self) -> str:
        return "Fetches and caches background data"

    @property
    def schedule(self) -> AgentSchedule:
        return AgentSchedule(
            interval_seconds=300,       # run every 5 minutes
            run_on_startup=True,
        )

    @property
    def required_secrets(self) -> list[JarvisSecret]:
        return []

    async def run(self) -> None:
        """Called on schedule. Fetch data and cache it."""
        # ... fetch from API ...
        self._cached_data = {"status": "ok", "devices": [...]}

    def get_context_data(self) -> dict:
        """Returned data is injected into the LLM system prompt for voice commands."""
        return self._cached_data
```

**Optional:** `get_alerts() -> list[Alert]` — return time-sensitive notifications (announced via TTS).

### IJarvisDeviceProtocol — Device Control

Protocols handle discovery and control for a specific manufacturer or API. Used by the `control_device` built-in command.

```python
from jarvis_command_sdk import (
    IJarvisDeviceProtocol, DiscoveredDevice, DeviceControlResult,
    IJarvisButton, JarvisSecret, JarvisStorage,
)

_storage = JarvisStorage("my_protocol", secret_scope="integration")

class MyProtocol(IJarvisDeviceProtocol):
    @property
    def protocol_name(self) -> str:
        return "my_protocol"

    @property
    def supported_domains(self) -> list[str]:
        return ["switch", "light"]             # HA-style domains

    @property
    def connection_type(self) -> str:
        return "cloud"                         # "cloud" | "lan" | "hybrid"

    @property
    def required_secrets(self) -> list[JarvisSecret]:
        return [
            JarvisSecret("MY_API_KEY", "API key", "integration", "string",
                         is_sensitive=True, required=True),
        ]

    @property
    def supported_actions(self) -> list[IJarvisButton]:
        return [
            IJarvisButton("Turn On", "turn_on", "primary", "power"),
            IJarvisButton("Turn Off", "turn_off", "secondary", "power-off"),
        ]

    async def discover(self, timeout: float = 5.0) -> list[DiscoveredDevice]:
        """Scan for devices (called by mobile app and node)."""
        api_key = _storage.get_secret("MY_API_KEY", scope="integration")
        # ... query API ...
        return [
            DiscoveredDevice(
                entity_id="switch.living_room",   # must be unique
                name="Living Room Switch",
                domain="switch",
                protocol=self.protocol_name,
                model="Smart Switch v2",
                manufacturer="MyBrand",
                cloud_id="device-123",            # cloud API identifier
            ),
        ]

    async def control(
        self, ip: str, action: str, data: dict | None = None, **kwargs
    ) -> DeviceControlResult:
        """Send control command. ip may be a cloud_id for cloud protocols."""
        device = kwargs.get("device")  # DiscoveredDevice if available
        # ... send command to API ...
        return DeviceControlResult(success=True, entity_id="switch.living_room", action=action)

    async def get_state(self, ip: str, **kwargs) -> dict | None:
        """Query current device state."""
        return {"is_on": True, "brightness": 80}
```

**Key patterns:**
- Use `asyncio.to_thread()` to wrap synchronous API calls
- Cache authenticated clients at module level to avoid re-auth on every call
- Return errors via `DeviceControlResult(success=False, error="...")` — never raise
- Entity IDs must be unique — prefix with domain if names can collide
- `ip` parameter is overloaded: may be local IP, cloud ID, or entity ID depending on `connection_type`

**Mobile UI domains:** The mobile app renders domain-specific controls: `light` (brightness/color), `switch` (on/off), `lock` (lock/unlock), `climate` (temperature/mode), `cover` (open/close), `security_system` (arm/disarm), `camera` (stream), `kettle` (boil/warm). Unknown domains fall back to `supported_actions` buttons.

### IJarvisDeviceManager — Device Listing

Aggregates device listings from a backend (e.g., Home Assistant, a proprietary hub).

```python
from jarvis_command_sdk import IJarvisDeviceManager, DeviceManagerDevice

class MyManager(IJarvisDeviceManager):
    @property
    def name(self) -> str:
        return "my_service"

    @property
    def friendly_name(self) -> str:
        return "My Service"

    @property
    def description(self) -> str:
        return "Lists devices from My Service"

    @property
    def can_edit_devices(self) -> bool:
        return False

    async def collect_devices(self) -> list[DeviceManagerDevice]:
        return [
            DeviceManagerDevice(
                name="Device 1", domain="light", entity_id="light.device_1",
                manufacturer="MyBrand", model="Smart Light",
                is_controllable=True,
            ),
        ]
```

### Routines (JSON)

Multi-step voice routines — no Python code needed.

```json
{
    "trigger_phrases": ["good morning", "start my day"],
    "steps": [
        {"command": "get_weather", "parameters": {}},
        {"command": "get_calendar", "parameters": {"timeframe": "today"}},
        {"command": "control_device", "parameters": {"action": "turn_on", "device": "coffee maker"}}
    ],
    "response_instruction": "Summarize the weather, today's calendar, and confirm the coffee maker is on."
}
```

### OAuth Device Protocols

For protocols requiring OAuth (e.g., SimpliSafe, Google Nest):

```python
from jarvis_command_sdk.authentication import AuthenticationConfig

@property
def authentication(self) -> AuthenticationConfig:
    return AuthenticationConfig(
        type="oauth",
        provider="my_provider",
        friendly_name="My Service",
        client_id="...",
        keys=["refresh_token"],
        authorize_url="https://auth.example.com/authorize",
        exchange_url="https://auth.example.com/oauth/token",
        supports_pkce=True,
        native_redirect_uri="com.example.app://callback",
        scopes=["openid", "offline_access"],
    )
```

The mobile app handles the OAuth flow natively. Implement `store_auth_values(values)` to persist tokens.

---

## JarvisStorage — Data Persistence

All data access goes through `JarvisStorage`. Never use raw SQLite/SQLAlchemy.

```python
from jarvis_command_sdk import JarvisStorage

storage = JarvisStorage("my_command")

# Secrets (stored encrypted on node)
api_key = storage.get_secret("MY_API_KEY", scope="integration")
storage.set_secret("MY_API_KEY", "sk-...", scope="integration", value_type="string")

# Command data (key-value store with optional expiry)
storage.save(key="cache_key", data={"result": "value"}, expires_at=None)
data = storage.get(key="cache_key")          # -> dict | None
all_data = storage.get_all()                  # -> list[dict]
storage.delete(key="cache_key")
```

---

## Critical Rules

### Shared Directory Naming
Packages with shared code **must** use package-specific directory names. These names are **blocked** and will fail `jdt test`:

**Node built-ins (shadow the runtime):** `commands`, `services`, `utils`, `core`, `agents`, `device_families`, `device_managers`, `provisioning`, `repositories`, `db`, `vendor`, `scripts`

**Generic collision risks (clash between packages on sys.path):** `shared`, `lib`, `helpers`, `common`, `internal`, `models`, `types`, `config`, `api`, `client`

**Correct pattern:** `{package_name}_shared/` (e.g., `schlage_shared/`, `my_integration_shared/`)

### Import Pattern
Always use the `try/except` pattern for the logger — it's optional at runtime:
```python
try:
    from jarvis_log_client import JarvisLogger
except ImportError:
    import logging
    class JarvisLogger:
        def __init__(self, **kw): self._log = logging.getLogger(kw.get("service", __name__))
        def info(self, msg, **kw): self._log.info(msg)
        def error(self, msg, **kw): self._log.error(msg)
```

### Error Handling
- Commands: return `CommandResponse.error_response(...)`, never raise
- Protocols: return `DeviceControlResult(success=False, error="...")`, never raise
- Log errors via `JarvisLogger`, don't print

### What the Tests Check
`jdt test` runs three phases:

1. **Manifest validation** — schema, semver format, valid categories, component paths exist
2. **Static analysis (AST)** — correct base class, required methods defined, no dangerous imports (`subprocess`, `os`, `eval`, `exec`), no raw DB access, no SQL in string literals, no blocked shared dir names
3. **Import checks** — import succeeds, SDK subclass found, instantiation works, properties return correct types, `generate_prompt_examples()` and `generate_adapter_examples()` return lists

---

## Reference Packages

Use these as templates when implementing real packages:

| Type | Package | Notes |
|------|---------|-------|
| Simple command | `jarvis-cmd-meteo-weather` | REST API, secrets, parameters |
| Command with deps | `jarvis-cmd-rotten-tomatoes` | pip dependency (httpx) |
| Cloud device protocol | `jarvis-device-schlage` | Custom auth client, secrets |
| OAuth device protocol | `jarvis-device-simplisafe` | OAuth2+PKCE, token rotation |
| Hybrid LAN/cloud protocol | `jarvis-device-govee` | Cloud discovery + LAN control |
| Multi-component bundle | `jarvis-device-zwave` | Protocol + agent, websockets |
| Complex OAuth + setup | `jarvis-device-nest` | OAuth, 8 secrets, setup_guide |

---

## Toolkit Internals

### Adding a New Component Type to the Toolkit

If a new component type is added to the SDK:

1. Add to constants in `core/constants.py` (COMPONENT_TYPE_INFO, DIR_TYPES, ENTRY_POINTS)
2. Add stub template in `scaffold/templates.py`
3. Add introspection handler in `core/introspect.py`
4. Add import checker in `analysis/import_checks.py`
5. Update manifest model if needed in `core/manifest_model.py`

### Ported Logic Origins

| Module | Ported From | Notes |
|--------|-------------|-------|
| analysis/static_analysis.py | jarvis-pantry | + improved shared dir check |
| analysis/import_checks.py | jarvis-node-setup/scripts/verify_package.py | |
| core/manifest_model.py | jarvis-node-setup/core/command_manifest.py | |
| core/introspect.py | jarvis-node-setup/scripts/generate_manifest.py | generalized to all types |

### Testing

```bash
pytest                    # 59 tests, all component types covered
pytest -v                 # verbose
pytest tests/test_init.py # single file
```
