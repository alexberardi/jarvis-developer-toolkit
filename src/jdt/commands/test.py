"""jdt test — Run Pantry-compatible validation locally."""

import argparse
import sys
from pathlib import Path

from jdt.analysis.manifest_validation import validate_manifest
from jdt.analysis.static_analysis import run_static_analysis
from jdt.analysis.import_checks import run_import_checks


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("test", help="Run Pantry-compatible tests locally")
    parser.add_argument("path", nargs="?", default=".", help="Path to package directory")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show all test results")
    parser.set_defaults(func=run)


def run(args: argparse.Namespace) -> None:
    pkg_dir = Path(args.path).resolve()

    if not pkg_dir.is_dir():
        print(f"Error: '{pkg_dir}' is not a directory", file=sys.stderr)
        sys.exit(1)

    all_passed = True
    total_checks = 0
    passed_checks = 0

    # Phase 1: Manifest validation
    print("Validating manifest...", end=" ")
    manifest_result = validate_manifest(pkg_dir)
    if manifest_result.errors:
        print("FAIL")
        for err in manifest_result.errors:
            print(f"  x {err}")
        all_passed = False
        total_checks += 1
    else:
        print("OK")
        total_checks += 1
        passed_checks += 1
        if manifest_result.warnings and args.verbose:
            for warn in manifest_result.warnings:
                print(f"  ! {warn}")

    # Phase 2: Static analysis (only if manifest is valid)
    if not manifest_result.errors and manifest_result.components:
        print("Static analysis...")
        sa_result = run_static_analysis(pkg_dir, manifest_result.components)

        for comp_result in sa_result.component_results:
            total_checks += 1
            if comp_result.passed:
                passed_checks += 1
                if args.verbose:
                    print(f"  {comp_result.path} ... OK")
            else:
                all_passed = False
                print(f"  {comp_result.path} ... FAIL")
                for err in comp_result.errors:
                    print(f"    x {err}")

        if sa_result.warnings:
            print(f"  WARNING: {len(sa_result.warnings)} issue(s)")
            for warn in sa_result.warnings:
                print(f"    - {warn}")

        if sa_result.errors:
            all_passed = False
            for err in sa_result.errors:
                print(f"  x {err}")

    # Phase 3: Import checks (only if manifest is valid)
    if not manifest_result.errors and manifest_result.components:
        print("Import checks...")
        import_result = run_import_checks(pkg_dir, manifest_result.components)

        for test_result in import_result.tests:
            total_checks += 1
            if test_result.passed:
                passed_checks += 1
                if args.verbose:
                    print(f"  {test_result.name} ... OK")
            else:
                all_passed = False
                print(f"  {test_result.name} ... FAIL")
                if test_result.error:
                    print(f"    x {test_result.error}")

    # Summary
    print()
    if all_passed:
        print(f"PASS - {passed_checks}/{total_checks} checks passed")
        sys.exit(0)
    else:
        print(f"FAIL - {passed_checks}/{total_checks} checks passed")
        sys.exit(1)
