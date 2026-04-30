"""Deploy to a Docker node container."""

import subprocess
import sys
from pathlib import Path


def deploy_docker(pkg_dir: Path, container: str) -> bool:
    """Install package into a running Docker node container.

    Steps:
    1. docker cp <pkg_dir> <container>:/tmp/jarvis-pkg-install/
    2. docker exec <container> python command_store.py install --local /tmp/jarvis-pkg-install
    3. docker exec <container> rm -rf /tmp/jarvis-pkg-install
    """
    staging_path = "/tmp/jarvis-pkg-install"
    store_script = "/app/scripts/command_store.py"

    # Copy package into container
    print(f"Copying package to {container}:{staging_path}...")
    cp_result = subprocess.run(
        ["docker", "cp", str(pkg_dir), f"{container}:{staging_path}"],
        capture_output=True, text=True,
    )
    if cp_result.returncode != 0:
        print(f"Error: docker cp failed: {cp_result.stderr.strip()}", file=sys.stderr)
        return False

    # Run install inside container
    print(f"Installing in container {container}...")
    install_result = subprocess.run(
        ["docker", "exec", container, "python", store_script,
         "install", "--local", staging_path],
        capture_output=True, text=True,
    )
    if install_result.stdout:
        print(install_result.stdout)
    if install_result.stderr:
        print(install_result.stderr, file=sys.stderr)

    # Cleanup
    subprocess.run(
        ["docker", "exec", container, "rm", "-rf", staging_path],
        capture_output=True,
    )

    if install_result.returncode == 0:
        print("Installed successfully. Discovery caches will auto-refresh.")
        return True
    else:
        print(f"Install failed (exit code {install_result.returncode})", file=sys.stderr)
        return False
