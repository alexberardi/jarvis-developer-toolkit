"""Deploy to a Pi node over SSH."""

import subprocess
import sys
from pathlib import Path


def deploy_ssh(
    pkg_dir: Path, host: str, remote_node_dir: str = "/opt/jarvis-node"
) -> bool:
    """Install package on a Pi node over SSH.

    Steps:
    1. scp -r <pkg_dir> <host>:/tmp/jarvis-pkg-install/
    2. ssh <host> command_store.py install --local /tmp/jarvis-pkg-install
    3. ssh <host> rm -rf /tmp/jarvis-pkg-install
    """
    staging_path = "/tmp/jarvis-pkg-install"
    python = f"{remote_node_dir}/.venv/bin/python"
    store_script = f"{remote_node_dir}/scripts/command_store.py"

    # Copy package to remote
    print(f"Copying package to {host}:{staging_path}...")
    scp_result = subprocess.run(
        ["scp", "-r", str(pkg_dir), f"{host}:{staging_path}"],
        capture_output=True, text=True,
    )
    if scp_result.returncode != 0:
        print(f"Error: scp failed: {scp_result.stderr.strip()}", file=sys.stderr)
        return False

    # Run install on remote
    install_cmd = f"sudo {python} {store_script} install --local {staging_path}"
    print(f"Installing on {host}...")
    install_result = subprocess.run(
        ["ssh", host, install_cmd],
        capture_output=True, text=True,
    )
    if install_result.stdout:
        print(install_result.stdout)
    if install_result.stderr:
        print(install_result.stderr, file=sys.stderr)

    # Cleanup
    subprocess.run(
        ["ssh", host, f"rm -rf {staging_path}"],
        capture_output=True,
    )

    if install_result.returncode == 0:
        print("Installed successfully. Discovery caches will auto-refresh.")
        return True
    else:
        print(f"Install failed (exit code {install_result.returncode})", file=sys.stderr)
        return False
