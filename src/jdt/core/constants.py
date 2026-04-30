"""Shared constants for the Jarvis Developer Toolkit.

Ported from:
- jarvis-node-setup/core/command_manifest.py (component types, categories, entry points)
- jarvis-pantry/app/services/static_analysis.py (dangerous patterns, validation lists)
"""

SCHEMA_VERSION: int = 1

VALID_COMPONENT_TYPES: list[str] = [
    "command",
    "agent",
    "device_protocol",
    "device_manager",
    "prompt_provider",
    "routine",
]

VALID_CATEGORIES: list[str] = [
    "automation",
    "calendar",
    "communication",
    "entertainment",
    "finance",
    "fitness",
    "food",
    "games",
    "health",
    "home",
    "information",
    "media",
    "music",
    "news",
    "productivity",
    "shopping",
    "smart-home",
    "sports",
    "travel",
    "utilities",
    "weather",
]

VALID_PARAM_TYPES: set[str] = {
    "string", "int", "float", "bool", "enum", "date", "time", "datetime",
}

VALID_SECRET_SCOPES: set[str] = {"integration", "node"}

# Convention: directory name -> component type
COMPONENT_DIR_TYPES: dict[str, str] = {
    "commands": "command",
    "agents": "agent",
    "device_families": "device_protocol",
    "device_managers": "device_manager",
    "prompt_providers": "prompt_provider",
    "routines": "routine",
}

# Convention: component type -> expected entry point filename
COMPONENT_ENTRY_POINTS: dict[str, str] = {
    "command": "command.py",
    "agent": "agent.py",
    "device_protocol": "protocol.py",
    "device_manager": "manager.py",
    "prompt_provider": "provider.py",
    "routine": "routine.json",
}

# Component type -> (base class name, required methods/properties)
COMPONENT_TYPE_INFO: dict[str, tuple[str, list[str]]] = {
    "command": (
        "IJarvisCommand",
        ["command_name", "description", "parameters", "required_secrets",
         "keywords", "run", "generate_prompt_examples", "generate_adapter_examples"],
    ),
    "agent": (
        "IJarvisAgent",
        ["name", "description", "schedule", "required_secrets", "run", "get_context_data"],
    ),
    "device_protocol": (
        "IJarvisDeviceProtocol",
        ["protocol_name", "supported_domains", "discover", "control", "get_state"],
    ),
    "device_manager": (
        "IJarvisDeviceManager",
        ["name", "friendly_name", "description", "collect_devices"],
    ),
    "prompt_provider": (
        "IJarvisPromptProvider",
        ["name", "build_system_prompt", "get_capabilities"],
    ),
}

# --------------------------------------------------------------------------
# Static analysis: dangerous patterns
# --------------------------------------------------------------------------

DANGEROUS_MODULES: set[str] = {"subprocess", "os", "shutil", "ctypes", "importlib"}

DANGEROUS_CALLS: set[str] = {
    "eval", "exec", "compile", "__import__",
    "os.system", "os.popen", "os.exec", "os.execl", "os.execle",
    "os.execlp", "os.execv", "os.execve", "os.execvp", "os.execvpe",
    "os.spawn", "os.spawnl", "os.spawnle",
    "subprocess.run", "subprocess.call", "subprocess.Popen",
    "subprocess.check_call", "subprocess.check_output",
}

DATABASE_MODULES: set[str] = {
    "sqlite3", "sqlalchemy", "alembic", "psycopg2", "asyncpg", "aiosqlite", "peewee",
}

ALLOWED_DB_IMPORTS: set[str] = {"db", "repositories", "repositories.command_data_repository"}

SQL_MUTATION_KEYWORDS: list[str] = [
    "CREATE TABLE", "ALTER TABLE", "DROP TABLE", "CREATE INDEX", "DROP INDEX",
    "INSERT INTO", "UPDATE ", "DELETE FROM", "TRUNCATE",
    "CREATE DATABASE", "DROP DATABASE", "GRANT ", "REVOKE ",
]

# --------------------------------------------------------------------------
# Shared directory conflict detection
# --------------------------------------------------------------------------

# Node built-in package names that must not be shadowed
NODE_BUILTIN_PACKAGES: set[str] = {
    "commands", "services", "utils", "core", "agents",
    "device_families", "device_managers", "provisioning",
    "repositories", "db", "vendor", "scripts",
}

# Generic names that collide when multiple packages install shared code to
# sys.path via ~/.jarvis/packages/<name>/lib/
GENERIC_COLLISION_NAMES: set[str] = {
    "shared", "lib", "helpers", "common", "internal",
    "models", "types", "config", "api", "client",
}

# All blocked shared directory names (union of both sets)
BLOCKED_SHARED_DIR_NAMES: set[str] = NODE_BUILTIN_PACKAGES | GENERIC_COLLISION_NAMES
