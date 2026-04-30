"""jdt deploy — Install package to a target node."""

import argparse
import sys
from pathlib import Path

from jdt.deploy.local import deploy_local
from jdt.deploy.docker import deploy_docker
from jdt.deploy.ssh import deploy_ssh


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("deploy", help="Deploy package to a node")
    deploy_sub = parser.add_subparsers(dest="target", help="Deploy target")

    # jdt deploy local [path]
    local_parser = deploy_sub.add_parser("local", help="Install to local node-setup")
    local_parser.add_argument("path", nargs="?", default=".", help="Package directory")
    local_parser.add_argument("--node-dir", help="Path to jarvis-node-setup (auto-detected)")
    local_parser.set_defaults(func=_run_local)

    # jdt deploy docker <container> [path]
    docker_parser = deploy_sub.add_parser("docker", help="Install into Docker node container")
    docker_parser.add_argument("container", help="Container name (partial match OK)")
    docker_parser.add_argument("path", nargs="?", default=".", help="Package directory")
    docker_parser.set_defaults(func=_run_docker)

    # jdt deploy ssh <host> [path]
    ssh_parser = deploy_sub.add_parser("ssh", help="Install on Pi node over SSH")
    ssh_parser.add_argument("host", help="SSH target (e.g., pi@jarvis-dev.local)")
    ssh_parser.add_argument("path", nargs="?", default=".", help="Package directory")
    ssh_parser.add_argument("--node-dir", default="/opt/jarvis-node", help="Remote node install dir")
    ssh_parser.set_defaults(func=_run_ssh)


def _run_local(args: argparse.Namespace) -> None:
    pkg_dir = Path(args.path).resolve()
    if not pkg_dir.is_dir():
        print(f"Error: '{pkg_dir}' is not a directory", file=sys.stderr)
        sys.exit(1)

    success = deploy_local(pkg_dir, node_dir=args.node_dir)
    sys.exit(0 if success else 1)


def _run_docker(args: argparse.Namespace) -> None:
    pkg_dir = Path(args.path).resolve()
    if not pkg_dir.is_dir():
        print(f"Error: '{pkg_dir}' is not a directory", file=sys.stderr)
        sys.exit(1)

    success = deploy_docker(pkg_dir, args.container)
    sys.exit(0 if success else 1)


def _run_ssh(args: argparse.Namespace) -> None:
    pkg_dir = Path(args.path).resolve()
    if not pkg_dir.is_dir():
        print(f"Error: '{pkg_dir}' is not a directory", file=sys.stderr)
        sys.exit(1)

    success = deploy_ssh(pkg_dir, args.host, remote_node_dir=args.node_dir)
    sys.exit(0 if success else 1)
