"""Deploy to local jarvis-node-setup installation."""

import os
import subprocess
import sys
from pathlib import Path


def _find_node_dir(hint: str | None = None) -> Path | None:
    """Find the jarvis-node-setup directory.

    Search order:
    1. Explicit hint (--node-dir flag)
    2. JARVIS_NODE_DIR environment variable
    3. ../jarvis-node-setup (sibling repo)
    4. /opt/jarvis-node (production Pi install)
    """
    candidates = []

    if hint:
        candidates.append(Path(hint))

    env_dir = os.environ.get("JARVIS_NODE_DIR")
    if env_dir:
        candidates.append(Path(env_dir))

    # Sibling repo (common in dev)
    cwd = Path.cwd()
    candidates.append(cwd.parent / "jarvis-node-setup")

    # Production install
    candidates.append(Path("/opt/jarvis-node"))

    for candidate in candidates:
        store_script = candidate / "scripts" / "command_store.py"
        if store_script.exists():
            return candidate

    return None


def deploy_local(pkg_dir: Path, node_dir: str | None = None) -> bool:
    """Install package to local node-setup via command_store.py."""
    node_path = _find_node_dir(node_dir)
    if node_path is None:
        print("Error: Cannot find jarvis-node-setup installation.", file=sys.stderr)
        print("  Set JARVIS_NODE_DIR or use --node-dir to specify the path.", file=sys.stderr)
        return False

    store_script = node_path / "scripts" / "command_store.py"
    python = node_path / ".venv" / "bin" / "python"
    if not python.exists():
        python = Path(sys.executable)

    cmd = [str(python), str(store_script), "install", "--local", str(pkg_dir)]
    print(f"Installing to {node_path}...")
    print(f"  {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, cwd=str(node_path), capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        if result.returncode == 0:
            print("Installed successfully. Discovery caches will auto-refresh.")
            return True
        else:
            print(f"Install failed (exit code {result.returncode})", file=sys.stderr)
            return False
    except FileNotFoundError:
        print(f"Error: Python not found at {python}", file=sys.stderr)
        return False
