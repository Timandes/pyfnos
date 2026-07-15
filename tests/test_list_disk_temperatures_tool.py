import argparse
import importlib.util
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = ROOT / "tools" / "list_disk_temperatures.py"


def load_tool_module():
    module_name = "list_disk_temperatures_tool"
    spec = importlib.util.spec_from_file_location(module_name, TOOL_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    missing = object()
    previous_common = sys.modules.pop("common", missing)
    sys.path.insert(0, str(TOOL_PATH.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(TOOL_PATH.parent))
        if previous_common is missing:
            sys.modules.pop("common", None)
        else:
            sys.modules["common"] = previous_common
    return module


tool = load_tool_module()


def make_args(**overrides):
    values = {
        "user": "admin",
        "password": "password",
        "endpoint": "nas.example.com:5666",
        "code": None,
        "trust_device": False,
        "use_ssl": False,
        "skip_ssl_verify": True,
        "debug": False,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


class FakeStore:
    def __init__(self, disks, smart_responses=None):
        self.disks = disks
        self.smart_responses = smart_responses or {}
        self.smart_calls = []

    async def list_disks(self):
        return {"disk": [{"name": name} for name in self.disks]}

    async def get_disk_smart(self, name):
        self.smart_calls.append(name)
        response = self.smart_responses[name]
        if isinstance(response, Exception):
            raise response
        return response


class FakeResourceMonitor:
    def __init__(self, response):
        self.response = response

    async def disk(self):
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


@pytest.mark.asyncio
async def test_collect_prefers_monitor_then_falls_back_to_nvme_smart():
    store = FakeStore(
        ["sda", "nvme0n1"],
        {
            "nvme0n1": {
                "smart": {
                    "nvme_smart_health_information_log": {"temperature": 42}
                }
            }
        },
    )
    monitor = FakeResourceMonitor(
        {
            "data": {
                "disk": [
                    {"name": "nvme0n1", "temp": 0},
                    {"name": "sda", "temp": 38},
                ]
            }
        }
    )

    results = await tool.collect_disk_temperatures(store, monitor)

    assert results == [
        tool.DiskTemperature(
            name="sda",
            temperature=38,
            source=tool.MONITOR_TEMPERATURE_SOURCE,
        ),
        tool.DiskTemperature(
            name="nvme0n1",
            temperature=42,
            source=tool.NVME_SMART_TEMPERATURE_SOURCE,
            skipped=[
                f"{tool.MONITOR_TEMPERATURE_SOURCE} = 0（值为 0）",
                f"{tool.SMART_TEMPERATURE_SOURCE}（字段不存在）",
            ],
        ),
    ]
    assert store.smart_calls == ["nvme0n1"]


@pytest.mark.asyncio
async def test_missing_monitor_temp_and_zero_smart_current_use_nvme():
    store = FakeStore(
        ["nvme0n1"],
        {
            "nvme0n1": {
                "smart": {
                    "temperature": {"current": 0},
                    "nvme_smart_health_information_log": {"temperature": 36},
                }
            }
        },
    )
    monitor = FakeResourceMonitor(
        {"data": {"disk": [{"name": "nvme0n1"}]}}
    )

    result = (await tool.collect_disk_temperatures(store, monitor))[0]

    assert result == tool.DiskTemperature(
        name="nvme0n1",
        temperature=36,
        source=tool.NVME_SMART_TEMPERATURE_SOURCE,
        skipped=[
            f"{tool.MONITOR_TEMPERATURE_SOURCE}（字段不存在）",
            f"{tool.SMART_TEMPERATURE_SOURCE} = 0（值为 0）",
        ],
    )


@pytest.mark.asyncio
async def test_monitor_failure_falls_back_for_all_disks_and_smart_failure_isolated():
    store = FakeStore(
        ["sda", "sdb"],
        {
            "sda": {"smart": {"temperature": {"current": 31}}},
            "sdb": OSError("device unavailable"),
        },
    )
    monitor = FakeResourceMonitor(TimeoutError("monitor unavailable"))

    results = await tool.collect_disk_temperatures(store, monitor)

    assert results[0] == tool.DiskTemperature(
        name="sda",
        temperature=31,
        source=tool.SMART_TEMPERATURE_SOURCE,
        skipped=[
            "ResourceMonitor.disk()（接口调用失败: "
            "TimeoutError: monitor unavailable）"
        ],
    )
    assert results[1] == tool.DiskTemperature(
        name="sdb",
        skipped=[
            "ResourceMonitor.disk()（接口调用失败: "
            "TimeoutError: monitor unavailable）",
            "Store.get_disk_smart('sdb')（接口调用失败: "
            "OSError: device unavailable）",
        ],
    )
    assert store.smart_calls == ["sda", "sdb"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("value", "reason"),
    [
        (True, "不是数字"),
        ("40", "不是数字"),
        (float("nan"), "不是有限数值"),
        (float("inf"), "不是有限数值"),
        (float("-inf"), "不是有限数值"),
    ],
)
async def test_invalid_monitor_values_are_reported(value, reason):
    store = FakeStore(["sda"], {"sda": {"smart": {}}})
    monitor = FakeResourceMonitor(
        {"data": {"disk": [{"name": "sda", "temp": value}]}}
    )

    result = (await tool.collect_disk_temperatures(store, monitor))[0]

    assert result.temperature is None
    assert reason in result.skipped[0]
    assert result.skipped[1:] == [
        f"{tool.SMART_TEMPERATURE_SOURCE}（字段不存在）",
        f"{tool.NVME_SMART_TEMPERATURE_SOURCE}（字段不存在）",
    ]


@pytest.mark.asyncio
async def test_malformed_monitor_response_is_reported_before_smart_fallback():
    store = FakeStore(
        ["sda"],
        {"sda": {"smart": {"temperature": {"current": -5}}}},
    )
    monitor = FakeResourceMonitor({"data": {"disk": {}}})

    result = (await tool.collect_disk_temperatures(store, monitor))[0]

    assert result == tool.DiskTemperature(
        name="sda",
        temperature=-5,
        source=tool.SMART_TEMPERATURE_SOURCE,
        skipped=[
            "ResourceMonitor.disk().data.disk（字段不存在或不是列表）"
        ],
    )


@pytest.mark.asyncio
async def test_invalid_disk_list_is_fatal():
    class InvalidStore(FakeStore):
        async def list_disks(self):
            return {"disk": [{"name": ""}]}

    with pytest.raises(ValueError, match="无效磁盘名称"):
        await tool.collect_disk_temperatures(
            InvalidStore([]),
            FakeResourceMonitor({"data": {"disk": []}}),
        )


def test_format_includes_source_skips_and_unknown_temperature():
    output = tool.format_disk_temperatures(
        [
            tool.DiskTemperature(
                name="sda",
                temperature=38.0,
                source=tool.MONITOR_TEMPERATURE_SOURCE,
            ),
            tool.DiskTemperature(
                name="sdb",
                skipped=[
                    "ResourceMonitor.disk()（未找到该磁盘）",
                    f"{tool.SMART_TEMPERATURE_SOURCE} = 0（值为 0）",
                ],
            ),
        ]
    )

    assert output == (
        "sda => 38°C\n"
        f"  来源: {tool.MONITOR_TEMPERATURE_SOURCE}\n\n"
        "sdb => 未知\n"
        "  跳过: ResourceMonitor.disk()（未找到该磁盘）\n"
        f"  跳过: {tool.SMART_TEMPERATURE_SOURCE} = 0（值为 0）"
    )


def test_parse_args_exposes_auth_ssl_twofa_and_debug_options():
    args = tool.parse_args(
        [
            "--user",
            "admin",
            "--password",
            "password",
            "-e",
            "nas.example.com:5666",
            "--code",
            "123456",
            "--trust-device",
            "--use-ssl",
            "--skip-ssl-verify",
            "false",
            "--debug",
        ]
    )

    assert args == argparse.Namespace(
        user="admin",
        password="password",
        endpoint="nas.example.com:5666",
        code="123456",
        trust_device=True,
        use_ssl=True,
        skip_ssl_verify=False,
        debug=True,
    )

    incomplete_argv = [
        ["--password", "password", "-e", "nas.example.com:5666"],
        ["--user", "admin", "-e", "nas.example.com:5666"],
    ]
    for argv in incomplete_argv:
        with pytest.raises(SystemExit):
            tool.parse_args(argv)


@pytest.mark.asyncio
async def test_run_partial_unknown_returns_zero_and_always_closes_client(
    monkeypatch,
    capsys,
):
    class FakeClient:
        def __init__(self):
            self.connect_call = None
            self.login_credentials = None
            self.closed = False

        async def connect(self, endpoint, *, use_ssl, skip_ssl_verify):
            self.connect_call = (endpoint, use_ssl, skip_ssl_verify)

        async def login(self, user, password):
            self.login_credentials = (user, password)
            return {"result": "succ", "token": "must-not-be-printed"}

        async def close(self):
            self.closed = True

    client = FakeClient()

    class RuntimeStore(FakeStore):
        def __init__(self, runtime_client):
            assert runtime_client is client
            super().__init__(["sda"], {"sda": {"smart": {}}})

    class RuntimeMonitor(FakeResourceMonitor):
        def __init__(self, runtime_client):
            assert runtime_client is client
            super().__init__(
                {"data": {"disk": [{"name": "sda", "temp": 0}]}}
            )

    monkeypatch.setattr(tool, "FnosClient", lambda: client)
    monkeypatch.setattr(tool, "Store", RuntimeStore)
    monkeypatch.setattr(tool, "ResourceMonitor", RuntimeMonitor)
    args = make_args(use_ssl=True, skip_ssl_verify=False)

    exit_code = await tool.run(args)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == (
        "sda => 未知\n"
        f"  跳过: {tool.MONITOR_TEMPERATURE_SOURCE} = 0（值为 0）\n"
        f"  跳过: {tool.SMART_TEMPERATURE_SOURCE}（字段不存在）\n"
        f"  跳过: {tool.NVME_SMART_TEMPERATURE_SOURCE}（字段不存在）\n"
    )
    assert captured.err == ""
    assert "must-not-be-printed" not in captured.out
    assert client.connect_call == (args.endpoint, True, False)
    assert client.login_credentials == (args.user, args.password)
    assert client.closed is True


@pytest.mark.asyncio
async def test_run_completes_twofa_with_cli_code(monkeypatch, capsys):
    class TwofaClient:
        def __init__(self):
            self.twofa_call = None
            self.closed = False

        async def connect(self, endpoint, *, use_ssl, skip_ssl_verify):
            return None

        async def login(self, user, password):
            return {
                "result": "fail",
                "twofaRequired": True,
                "secureEmail": "a***@example.com",
            }

        async def submit_twofa_code(self, code, *, trust_device):
            self.twofa_call = (code, trust_device)
            return {"result": "succ"}

        async def close(self):
            self.closed = True

    client = TwofaClient()

    class RuntimeStore(FakeStore):
        def __init__(self, runtime_client):
            assert runtime_client is client
            super().__init__(["sda"])

    class RuntimeMonitor(FakeResourceMonitor):
        def __init__(self, runtime_client):
            assert runtime_client is client
            super().__init__(
                {"data": {"disk": [{"name": "sda", "temp": 37}]}}
            )

    monkeypatch.setattr(tool, "FnosClient", lambda: client)
    monkeypatch.setattr(tool, "Store", RuntimeStore)
    monkeypatch.setattr(tool, "ResourceMonitor", RuntimeMonitor)

    exit_code = await tool.run(
        make_args(code="123456", trust_device=True)
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == (
        "账号需要两步验证，安全邮箱: a***@example.com\n"
        "sda => 37°C\n"
        f"  来源: {tool.MONITOR_TEMPERATURE_SOURCE}\n"
    )
    assert captured.err == ""
    assert client.twofa_call == ("123456", True)
    assert client.closed is True


@pytest.mark.asyncio
async def test_run_login_failure_is_fatal_and_does_not_leak_response(
    monkeypatch,
    capsys,
):
    class FailedLoginClient:
        def __init__(self):
            self.closed = False

        async def connect(self, endpoint, *, use_ssl, skip_ssl_verify):
            return None

        async def login(self, user, password):
            return {
                "result": "fail",
                "errmsg": "验证码错误",
                "secret": "must-not-be-printed",
            }

        async def close(self):
            self.closed = True

    client = FailedLoginClient()
    monkeypatch.setattr(tool, "FnosClient", lambda: client)
    args = make_args()

    exit_code = await tool.run(args)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == (
        "错误: 登录或两步验证阶段失败\n"
        "异常类型: RuntimeError\n"
        "异常详情: 验证码错误\n"
        "提示: 使用 --debug 查看完整 traceback\n"
    )
    assert "must-not-be-printed" not in captured.err
    assert client.closed is True


@pytest.mark.asyncio
async def test_run_debug_traceback_redacts_authentication_secrets(
    monkeypatch,
    capsys,
):
    class FailingClient:
        def __init__(self):
            self.closed = False

        async def connect(self, endpoint, *, use_ssl, skip_ssl_verify):
            raise RuntimeError(
                "password=password-raw, code=654321, "
                "token=token-value, longToken=long-value, "
                "accessToken=access-value, secret=secret-value"
            )

        async def close(self):
            self.closed = True

    client = FailingClient()
    monkeypatch.setattr(tool, "FnosClient", lambda: client)
    args = make_args(
        password="password-raw",
        code="654321",
        debug=True,
    )

    exit_code = await tool.run(args)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "错误: 连接阶段失败\n" in captured.err
    assert "异常类型: RuntimeError\n" in captured.err
    assert "Traceback (most recent call last):" in captured.err
    assert "password-raw" not in captured.err
    assert "654321" not in captured.err
    assert "token-value" not in captured.err
    assert "long-value" not in captured.err
    assert "access-value" not in captured.err
    assert "secret-value" not in captured.err
    assert "password=***" in captured.err
    assert "token=***" in captured.err
    assert client.closed is True


@pytest.mark.asyncio
async def test_run_disk_enumeration_failure_reports_collection_stage(
    monkeypatch,
    capsys,
):
    class Client:
        def __init__(self):
            self.closed = False

        async def connect(self, endpoint, *, use_ssl, skip_ssl_verify):
            return None

        async def login(self, user, password):
            return {"result": "succ"}

        async def close(self):
            self.closed = True

    class InvalidStore:
        def __init__(self, client):
            return None

        async def list_disks(self):
            return {"disk": [{"name": ""}]}

    class UnusedMonitor:
        def __init__(self, client):
            return None

    client = Client()
    monkeypatch.setattr(tool, "FnosClient", lambda: client)
    monkeypatch.setattr(tool, "Store", InvalidStore)
    monkeypatch.setattr(tool, "ResourceMonitor", UnusedMonitor)

    exit_code = await tool.run(make_args())

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == (
        "错误: 磁盘枚举与温度获取阶段失败\n"
        "异常类型: ValueError\n"
        "异常详情: Store.list_disks() 返回了无效磁盘名称\n"
        "提示: 使用 --debug 查看完整 traceback\n"
    )
    assert client.closed is True
