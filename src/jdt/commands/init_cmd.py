"""jdt init — Scaffold a new Jarvis package."""

import argparse
import sys
from pathlib import Path

from jdt.scaffold.generator import scaffold_package


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("init", help="Scaffold a new Jarvis package")
    parser.add_argument("name", nargs="?", help="Package name (snake_case)")
    parser.add_argument(
        "--type", "-t",
        dest="component_types",
        help="Component types (comma-separated): command,agent,protocol,manager,routine,prompt_provider",
    )
    parser.add_argument("--author", help="GitHub username")
    parser.add_argument("--category", help="Package category")
    parser.add_argument("--output", "-o", default=".", help="Output directory (default: current)")
    parser.add_argument("--non-interactive", action="store_true", help="Skip interactive prompts")
    parser.set_defaults(func=run)


def _prompt(msg: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    result = input(f"{msg}{suffix}: ").strip()
    return result or default


def run(args: argparse.Namespace) -> None:
    # Resolve package name
    name = args.name
    if not name and not args.non_interactive:
        name = _prompt("Package name (snake_case)")
    if not name:
        print("Error: package name is required", file=sys.stderr)
        sys.exit(1)

    # Validate name
    if not name.replace("_", "").isalnum():
        print(f"Error: package name must be snake_case (got '{name}')", file=sys.stderr)
        sys.exit(1)

    # Resolve component types
    type_map = {
        "command": "command",
        "agent": "agent",
        "protocol": "device_protocol",
        "device_protocol": "device_protocol",
        "manager": "device_manager",
        "device_manager": "device_manager",
        "routine": "routine",
        "prompt_provider": "prompt_provider",
    }

    if args.component_types:
        raw_types = [t.strip() for t in args.component_types.split(",")]
        component_types = []
        for t in raw_types:
            if t not in type_map:
                print(f"Error: unknown component type '{t}'", file=sys.stderr)
                print(f"  Valid types: {', '.join(sorted(type_map.keys()))}", file=sys.stderr)
                sys.exit(1)
            component_types.append(type_map[t])
    elif not args.non_interactive:
        print("\nComponent types:")
        print("  command          - Voice command (IJarvisCommand)")
        print("  agent            - Background agent (IJarvisAgent)")
        print("  protocol         - Device protocol (IJarvisDeviceProtocol)")
        print("  manager          - Device manager (IJarvisDeviceManager)")
        print("  routine          - Multi-step routine (JSON)")
        print("  prompt_provider  - LLM prompt provider (IJarvisPromptProvider)")
        raw = _prompt("\nTypes (comma-separated)", "command")
        raw_types = [t.strip() for t in raw.split(",")]
        component_types = [type_map.get(t, t) for t in raw_types]
    else:
        component_types = ["command"]

    # Resolve author
    author = args.author
    if not author and not args.non_interactive:
        author = _prompt("GitHub username", "")
    author = author or "community"

    # Resolve category
    category = args.category
    if not category and not args.non_interactive:
        from jdt.core.constants import VALID_CATEGORIES
        print(f"\nCategories: {', '.join(VALID_CATEGORIES)}")
        category = _prompt("Category", "utilities")
    category = category or "utilities"

    # Create package
    output_dir = Path(args.output).resolve()
    pkg_dir = scaffold_package(
        name=name,
        component_types=component_types,
        author=author,
        category=category,
        output_dir=output_dir,
    )

    print(f"\nPackage scaffolded at: {pkg_dir}")
    print(f"  Components: {', '.join(component_types)}")
    print(f"\nNext steps:")
    print(f"  cd {pkg_dir.name}")
    print(f"  jdt test .          # verify it passes")
    print(f"  jdt deploy local .  # install to local node")
