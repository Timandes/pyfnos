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
NEW_EXAMPLE_HELP = {
    "backup_manager.py": {
        "description": "fnOS 备份任务查询示例",
        "domain_help": (
            "--direction {0,1}",
            "备份任务方向：0=上传，1=下载（默认：0）",
        ),
    },
    "download_center.py": {
        "description": "fnOS 下载中心查询示例",
        "domain_help": (
            "--state-filter STATE_FILTER",
            "下载任务状态位掩码（默认：65535）",
            "--init-flag {true,false}",
            "下载任务初始化标志（默认：true）",
        ),
    },
    "ip_blocker.py": {
        "description": "fnOS IP 阻止规则查询示例",
        "domain_help": (),
    },
    "license_manager.py": {
        "description": "fnOS 软件许可查询示例",
        "domain_help": (
            "--page PAGE",
            "软件许可页码（默认：1）",
            "--page-size PAGE_SIZE",
            "软件许可每页数量（默认：200）",
        ),
    },
    "live_update.py": {
        "description": "fnOS 在线更新状态查询示例",
        "domain_help": (),
    },
    "mount_manager.py": {
        "description": "fnOS 挂载管理查询示例",
        "domain_help": (),
    },
    "network_server.py": {
        "description": "fnOS 网络服务查询示例",
        "domain_help": (
            "--page PAGE",
            "DDNS 记录页码（默认：1）",
            "--page-size PAGE_SIZE",
            "DDNS 记录每页数量（默认：200）",
        ),
    },
    "security.py": {
        "description": "fnOS 安全状态查询示例",
        "domain_help": (),
    },
    "system_restore.py": {
        "description": "fnOS 系统恢复信息查询示例",
        "domain_help": (),
    },
}
NEW_EXAMPLE_COMMANDS = {
    "backup_manager.py": "--direction 0",
    "download_center.py": "--state-filter 65535 --init-flag true",
    "ip_blocker.py": "",
    "license_manager.py": "--page 1 --page-size 200",
    "live_update.py": "",
    "mount_manager.py": "",
    "network_server.py": "--page 1 --page-size 200",
    "security.py": "",
    "system_restore.py": "",
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


def test_readme_documents_new_example_commands():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    for example_name, domain_args in NEW_EXAMPLE_COMMANDS.items():
        command = (
            f"uv run examples/{example_name} "
            "--user myuser --password mypassword -e my-server.com:5666"
        )
        if domain_args:
            command = f"{command} {domain_args}"
        assert command in readme

    assert "`--direction`" in readme
    assert "`--state-filter`" in readme
    assert "`--init-flag`" in readme
    assert "`--page`" in readme
    assert "`--page-size`" in readme


def configure_successful_example(module, monkeypatch):
    client = FailingConnectionClient()

    async def succeed(_client, _args):
        return {"result": "succ"}

    monkeypatch.setattr(module, "FnosClient", lambda: client)
    monkeypatch.setattr(module, "connect_client", succeed)
    monkeypatch.setattr(module, "login_with_twofa", succeed)
    return client


@pytest.mark.asyncio
async def test_backup_manager_cli_passes_direction(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "examples"))
    module = load_example(ROOT / "examples" / "backup_manager.py")
    configure_successful_example(module, monkeypatch)
    calls = []

    class RecordingBackupManager:
        def __init__(self, _client):
            pass

        async def list_tasks(self, direction):
            calls.append(direction)
            return {}

    monkeypatch.setattr(module, "BackupManager", RecordingBackupManager)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "backup_manager.py",
            "--user",
            "admin",
            "--password",
            "admin",
            "--direction",
            "1",
        ],
    )

    await module.main()

    assert calls == [1]


@pytest.mark.asyncio
async def test_download_center_cli_passes_task_filters(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "examples"))
    module = load_example(ROOT / "examples" / "download_center.py")
    configure_successful_example(module, monkeypatch)
    calls = []

    class RecordingDownloadCenter:
        def __init__(self, _client):
            pass

        async def get_default_save_directory(self):
            return {}

        async def get_statistics(self):
            return {}

        async def query_tasks(self, *, state_filter, init_flag):
            calls.append((state_filter, init_flag))
            return {}

    monkeypatch.setattr(module, "DownloadCenter", RecordingDownloadCenter)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "download_center.py",
            "--user",
            "admin",
            "--password",
            "admin",
            "--state-filter",
            "16",
            "--init-flag",
            "false",
        ],
    )

    await module.main()

    assert calls == [(16, False)]


@pytest.mark.asyncio
async def test_license_manager_cli_passes_pagination(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "examples"))
    module = load_example(ROOT / "examples" / "license_manager.py")
    configure_successful_example(module, monkeypatch)
    calls = []

    class RecordingLicenseManager:
        def __init__(self, _client):
            pass

        async def list(self, page, page_size):
            calls.append((page, page_size))
            return {}

    monkeypatch.setattr(module, "LicenseManager", RecordingLicenseManager)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "license_manager.py",
            "--user",
            "admin",
            "--password",
            "admin",
            "--page",
            "2",
            "--page-size",
            "50",
        ],
    )

    await module.main()

    assert calls == [(2, 50)]


@pytest.mark.asyncio
async def test_network_server_cli_passes_ddns_pagination(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "examples"))
    module = load_example(ROOT / "examples" / "network_server.py")
    configure_successful_example(module, monkeypatch)
    calls = []

    class RecordingNetworkServer:
        def __init__(self, _client):
            pass

        async def list_certificates(self):
            return {}

        async def get_connection_config(self):
            return {}

        async def get_connection_status(self):
            return {}

        async def list_ddns_providers(self):
            return {}

        async def list_ddns_records(self, page, page_size):
            calls.append((page, page_size))
            return {}

    monkeypatch.setattr(module, "NetworkServer", RecordingNetworkServer)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "network_server.py",
            "--user",
            "admin",
            "--password",
            "admin",
            "--page",
            "3",
            "--page-size",
            "25",
        ],
    )

    await module.main()

    assert calls == [(3, 25)]


@pytest.mark.parametrize(
    ("example_name", "contract"),
    sorted(NEW_EXAMPLE_HELP.items()),
    ids=lambda value: value if isinstance(value, str) else None,
)
def test_new_example_help_is_complete(example_name, contract):
    completed = subprocess.run(
        [sys.executable, str(ROOT / "examples" / example_name), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert completed.returncode == 0, completed.stderr
    expected = (
        "usage:",
        contract["description"],
        "--user USER",
        "--password PASSWORD",
        "--endpoint ENDPOINT",
        "--code CODE",
        "--trust-device",
        "--use-ssl",
        "--skip-ssl-verify SKIP_SSL_VERIFY",
        *contract["domain_help"],
    )
    for fragment in expected:
        assert fragment in completed.stdout, (example_name, fragment)


@pytest.mark.parametrize("value", ("true", "false"))
def test_download_center_init_flag_accepts_boolean_values(value):
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "download_center.py"),
            "--init-flag",
            value,
            "--help",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert completed.returncode == 0, completed.stderr
    assert "Traceback" not in completed.stderr


def test_download_center_init_flag_rejects_invalid_value():
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "download_center.py"),
            "--user",
            "admin",
            "--password",
            "admin",
            "--init-flag",
            "invalid",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert completed.returncode == 2
    assert "必须是 true 或 false" in completed.stderr


@pytest.mark.parametrize("example_name", sorted(NEW_EXAMPLES))
def test_new_example_has_module_documentation(example_name, monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "examples"))
    module = load_example(ROOT / "examples" / example_name)

    assert module.__doc__
    assert "示例" in module.__doc__


@pytest.mark.asyncio
@pytest.mark.parametrize("example_name", sorted(NEW_EXAMPLES))
async def test_new_example_reports_connection_failure_and_closes(
    example_name,
    monkeypatch,
    capsys,
):
    monkeypatch.syspath_prepend(str(ROOT / "examples"))
    module = load_example(ROOT / "examples" / example_name)
    client = FailingConnectionClient()

    async def fail_connection(_client, _args):
        raise RuntimeError("connection failed")

    monkeypatch.setattr(module, "FnosClient", lambda: client)
    monkeypatch.setattr(module, "connect_and_login", fail_connection, raising=False)
    monkeypatch.setattr(module, "connect_client", fail_connection, raising=False)
    monkeypatch.setattr(
        sys,
        "argv",
        [example_name, "--user", "admin", "--password", "admin"],
    )

    await module.main()

    output = capsys.readouterr().out
    assert "正在连接到服务器" in output
    assert "发生错误: connection failed" in output
    assert "连接已关闭" in output
    assert client.closed


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
