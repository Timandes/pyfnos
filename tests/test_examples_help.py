import importlib.util
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
EXAMPLES_REQUIRING_CONNECTION_CLEANUP = {
    "resource_monitor.py",
    "sac.py",
    "store.py",
    "system_info.py",
}


class FailingConnectionClient:
    def __init__(self):
        self.closed = False

    def on_message(self, _handler):
        pass

    async def close(self):
        self.closed = True


def load_example(path: Path):
    spec = importlib.util.spec_from_file_location(f"example_{path.stem}", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "example_name",
    sorted(EXAMPLES_REQUIRING_CONNECTION_CLEANUP),
)
async def test_extended_example_closes_client_when_connection_fails(
    example_name,
    monkeypatch,
):
    monkeypatch.syspath_prepend(str(ROOT / "examples"))
    module = load_example(ROOT / "examples" / example_name)
    client = FailingConnectionClient()

    async def fail_connection(_client, _args):
        raise RuntimeError("connection failed")

    monkeypatch.setattr(module, "FnosClient", lambda: client)
    monkeypatch.setattr(module, "connect_client", fail_connection)
    monkeypatch.setattr(
        sys,
        "argv",
        [example_name, "--user", "admin", "--password", "admin"],
    )

    with pytest.raises(RuntimeError, match="connection failed"):
        await module.main()

    assert client.closed
