"""jdt validate — Fast manifest-only validation."""

import argparse
import sys
from pathlib import Path

from jdt.analysis.manifest_validation import validate_manifest


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("validate", help="Validate package manifest (fast, no imports)")
    parser.add_argument("path", nargs="?", default=".", help="Path to package directory")
    parser.set_defaults(func=run)


def run(args: argparse.Namespace) -> None:
    pkg_dir = Path(args.path).resolve()

    if not pkg_dir.is_dir():
        print(f"Error: '{pkg_dir}' is not a directory", file=sys.stderr)
        sys.exit(1)

    result = validate_manifest(pkg_dir)

    if result.errors:
        print("FAIL — Manifest validation failed:\n")
        for err in result.errors:
            print(f"  x {err}")
    if result.warnings:
        print("\nWarnings:")
        for warn in result.warnings:
            print(f"  ! {warn}")

    if not result.errors:
        print(f"PASS — Manifest valid ({result.component_count} component(s))")
        sys.exit(0)
    else:
        sys.exit(1)
