"""Main CLI entry point for jdt."""

import argparse
import sys

from jdt import __version__


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="jdt",
        description="Jarvis Developer Toolkit — build, test, and deploy Jarvis packages",
    )
    parser.add_argument("--version", action="version", version=f"jdt {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Register subcommands
    from jdt.commands import init_cmd, manifest, test, validate, deploy

    init_cmd.register(subparsers)
    manifest.register(subparsers)
    test.register(subparsers)
    validate.register(subparsers)
    deploy.register(subparsers)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    # Dispatch to subcommand handler
    args.func(args)


if __name__ == "__main__":
    main()
