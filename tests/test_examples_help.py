import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = sorted((ROOT / "examples").glob("*.py"))
NEW_EXAMPLES = {
    "backup_manager.py",
    "download_center.py",
    "ip_blocker.py",
    "license_manager.py",
    "live_update.py",
    "mount_manager.py",
    "network_server.py",
    "security.py",
    "system_restore.py",
}


def test_new_example_inventory_is_complete():
    assert NEW_EXAMPLES <= {path.name for path in EXAMPLES}


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda path: path.name)
def test_example_help_does_not_connect(example):
    completed = subprocess.run(
        [sys.executable, str(example), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr
    assert "Traceback" not in completed.stderr
