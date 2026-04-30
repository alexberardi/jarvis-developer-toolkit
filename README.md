# Jarvis Developer Toolkit (`jdt`)

CLI toolkit for building, testing, and deploying [Jarvis](https://github.com/alexberardi/jarvis) voice assistant packages.

## Install

```bash
pip install jarvis-developer-toolkit
```

Or from source:

```bash
git clone https://github.com/alexberardi/jarvis-developer-toolkit
cd jarvis-developer-toolkit
pip install -e .
```

## Quick Start

```bash
# Scaffold a new command package
jdt init my_weather --type command --author yourname

# Run Pantry-compatible tests
jdt test my_weather/

# Deploy to your local node
jdt deploy local my_weather/
```

## Commands

### `jdt init` -- Scaffold a New Package

```bash
jdt init my_weather                          # interactive wizard
jdt init my_weather --type command           # single command
jdt init my_lights --type protocol           # device protocol
jdt init my_ha --type command,agent,manager  # multi-component bundle
jdt init my_pkg --non-interactive            # skip prompts, use defaults
```

Creates a complete package directory with:
- Convention directory layout
- Stub implementations that pass `jdt test`
- `jarvis_package.yaml` manifest
- README.md, LICENSE, .gitignore

### `jdt test` -- Run Pantry-Compatible Tests

```bash
jdt test                   # test current directory
jdt test /path/to/package  # test specific package
jdt test -v                # verbose output
jdt test --install-deps    # auto-install pip dependencies
```

Three-phase validation pipeline:
1. **Manifest validation** -- schema, semver, categories, component paths
2. **Static analysis** -- AST checks for dangerous patterns, required methods, shared dir conflicts
3. **Import checks** -- import each component, find SDK subclass, instantiate, validate properties

### `jdt validate` -- Quick Manifest Check

```bash
jdt validate              # fast manifest-only check (no imports)
```

### `jdt manifest` -- Generate/Update Manifest

```bash
jdt manifest               # auto-detect components, interactive
jdt manifest --non-interactive  # use defaults
```

Introspects your classes to extract secrets, parameters, keywords, and description. Supports all component types and multi-component bundles.

### `jdt deploy` -- Install to a Node

```bash
jdt deploy local                          # local jarvis-node-setup
jdt deploy docker jarvis-node-kitchen     # Docker node container
jdt deploy ssh pi@jarvis-dev.local        # Pi Zero over SSH
```

## Shared Directory Naming

Packages that include shared code must use package-specific directory names. Generic names will be blocked:

```
my_package/
  shared/           # BLOCKED -- will collide with other packages
  lib/              # BLOCKED
  helpers/          # BLOCKED
  my_package_shared/  # OK -- package-specific name
```

After installation, shared code is placed on `sys.path`. Generic names like `shared/` or `lib/` clash when multiple packages are installed.

## Component Types

| Type | Entry File | Convention Dir | SDK Interface |
|------|-----------|----------------|---------------|
| command | command.py | commands/{name}/ | IJarvisCommand |
| agent | agent.py | agents/{name}/ | IJarvisAgent |
| device_protocol | protocol.py | device_families/{name}/ | IJarvisDeviceProtocol |
| device_manager | manager.py | device_managers/{name}/ | IJarvisDeviceManager |
| prompt_provider | provider.py | prompt_providers/{name}/ | IJarvisPromptProvider |
| routine | routine.json | routines/{name}/ | (JSON schema) |

## License

MIT
