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
    spec.loader.exec_module(module)
    return module


tool = load_tool_module()


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
        skipped=["ResourceMonitor.disk()（接口调用失败: TimeoutError）"],
    )
    assert results[1] == tool.DiskTemperature(
        name="sdb",
        skipped=[
            "ResourceMonitor.disk()（接口调用失败: TimeoutError）",
            "Store.get_disk_smart('sdb')（接口调用失败: OSError）",
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
