# jarvis-developer-toolkit

CLI toolkit (`jdt`) for building, testing, and deploying Jarvis voice assistant packages.

## Quick Reference

```bash
cd jarvis-developer-toolkit
python3 -m venv .venv
.venv/bin/pip install -e ../jarvis-command-sdk
.venv/bin/pip install -e ".[dev]"
pytest
jdt --help
```

## Architecture

```
src/jdt/
├── cli.py              # Argparse CLI entry point
├── commands/           # Subcommand handlers (init, manifest, test, deploy, validate)
├── core/               # Manifest models, introspection, constants
├── analysis/           # Static analysis (AST), import checks, manifest validation
├── scaffold/           # Template stubs and directory generation
└── deploy/             # Local, Docker, SSH deployment
```

## Key Design Decisions

- Uses argparse (no click) to keep dependencies minimal
- Depends on jarvis-command-sdk for interface classes
- Does NOT depend on jarvis-node-setup or jarvis-pantry (self-contained)
- Static analysis logic ported from Pantry's static_analysis.py
- Import checks ported from node-setup's verify_package.py
- Deploy shells out to node-setup's command_store.py (doesn't replicate install logic)
- Manifest models ported from node-setup's core/command_manifest.py

## Adding a New Component Type

If a new component type is added to the SDK:

1. Add to constants in `core/constants.py`
2. Add stub template in `scaffold/templates.py`
3. Add introspection handler in `core/introspect.py`
4. Add import checker in `analysis/import_checks.py`
5. Update manifest model if needed in `core/manifest_model.py`

## Ported Logic Origins

| Module | Ported From | Original File |
|--------|-------------|---------------|
| analysis/static_analysis.py | jarvis-pantry | app/services/static_analysis.py |
| analysis/import_checks.py | jarvis-node-setup | scripts/verify_package.py |
| core/manifest_model.py | jarvis-node-setup | core/command_manifest.py |
| core/introspect.py | jarvis-node-setup | scripts/generate_manifest.py |

When the originals change, sync relevant updates here.

## Dependencies

- jarvis-command-sdk (interfaces for introspection and testing)
- pyyaml (manifest I/O)
- pydantic (manifest validation)

## Testing

```bash
pytest                    # all tests
pytest -v                 # verbose
pytest tests/test_init.py # single file
```
