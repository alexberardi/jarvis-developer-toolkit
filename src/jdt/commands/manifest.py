"""jdt manifest — Generate/update jarvis_package.yaml from code."""

import argparse
import sys
from pathlib import Path

from jdt.core.manifest_io import find_manifest, write_manifest, infer_components
from jdt.core.manifest_model import CommandManifest, ManifestAuthor, ManifestComponent
from jdt.core.introspect import introspect_components
from jdt.core.constants import VALID_CATEGORIES


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("manifest", help="Generate/update jarvis_package.yaml")
    parser.add_argument("path", nargs="?", default=".", help="Path to package directory")
    parser.add_argument("--non-interactive", action="store_true", help="Use defaults without prompting")
    parser.add_argument("--output", "-o", help="Output directory (default: same as path)")
    parser.set_defaults(func=run)


def _prompt(msg: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    result = input(f"{msg}{suffix}: ").strip()
    return result or default


def run(args: argparse.Namespace) -> None:
    pkg_dir = Path(args.path).resolve()
    output_dir = Path(args.output).resolve() if args.output else pkg_dir

    if not pkg_dir.is_dir():
        print(f"Error: '{pkg_dir}' is not a directory", file=sys.stderr)
        sys.exit(1)

    # Load existing manifest for defaults
    existing = find_manifest(pkg_dir)
    existing_data: dict = {}
    if existing:
        import yaml
        with open(existing) as f:
            existing_data = yaml.safe_load(f) or {}

    # Discover components
    components = infer_components(pkg_dir, existing_data.get("name", pkg_dir.name))
    if not components:
        print("Error: no components found in directory", file=sys.stderr)
        print("  Expected: commands/*/command.py, agents/*/agent.py, etc.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(components)} component(s):")
    for comp in components:
        print(f"  [{comp.type}] {comp.name} -> {comp.path}")

    # Introspect classes for metadata
    introspected = introspect_components(pkg_dir, components)

    # Resolve metadata
    name = existing_data.get("name", pkg_dir.name.replace("-", "_").replace("jarvis_", "").replace("jarvis-", ""))
    if not args.non_interactive:
        name = _prompt("\nPackage name", name)

    display_name = existing_data.get("display_name", name.replace("_", " ").title())
    description = existing_data.get("description", introspected.get("description", ""))
    version = existing_data.get("version", "0.1.0")
    author_github = existing_data.get("author", {}).get("github", "")
    categories = existing_data.get("categories", [])
    keywords = existing_data.get("keywords", introspected.get("keywords", []))

    if not args.non_interactive:
        display_name = _prompt("Display name", display_name)
        description = _prompt("Description", description)
        version = _prompt("Version", version)
        author_github = _prompt("GitHub username", author_github)
        print(f"\nCategories: {', '.join(VALID_CATEGORIES)}")
        cat_input = _prompt("Categories (comma-separated)", ", ".join(categories))
        categories = [c.strip() for c in cat_input.split(",") if c.strip()]

    # Build manifest
    manifest = CommandManifest(
        name=name,
        display_name=display_name,
        description=description,
        version=version,
        author=ManifestAuthor(github=author_github or "community"),
        categories=categories,
        keywords=keywords,
        platforms=existing_data.get("platforms", []),
        secrets=introspected.get("secrets", existing_data.get("secrets", [])),
        packages=introspected.get("packages", existing_data.get("packages", [])),
        components=[
            ManifestComponent(type=c.type, name=c.name, path=c.path)
            for c in components
        ],
        authentication=introspected.get("authentication"),
    )

    # Write
    output_path = write_manifest(manifest, output_dir)
    print(f"\nManifest written to: {output_path}")
    print(f"  name: {manifest.name}")
    print(f"  version: {manifest.version}")
    print(f"  components: {len(manifest.components)}")
