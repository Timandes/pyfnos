# fnOS Disk Temperature Diagnostic Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增 `tools/list_disk_temperatures.py`，按资源监控、常规 SMART、NVMe SMART 的优先级输出每块 fnOS 磁盘的温度、最终来源和每个被跳过候选值的原因。

**Architecture:** 工具以 `Store.list_disks()` 的磁盘名称和顺序为准，通过一个异步编排函数合并 `ResourceMonitor.disk()` 与按需调用的 `Store.get_disk_smart(name)`。温度判断、嵌套字段读取、诊断记录和输出格式化各自保持为小函数；CLI 仅负责参数、连接、登录、退出码和资源清理。

**Tech Stack:** Python 3.11+、`asyncio`、`argparse`、`dataclasses`、现有 `fnos` SDK、pytest、pytest-asyncio。

## Global Constraints

- 不新增第三方依赖，不修改 `fnos` 包的公共 API。
- 新增脚本的精确路径是 `tools/list_disk_temperatures.py`。
- `--user`、`--password`、`-e/--endpoint` 均为必填参数。
- 最终磁盘范围和顺序严格来自 `Store.list_disks()` 的 `disk[].name`。
- 温度优先级固定为 `ResourceMonitor.disk().data.disk[].temp`、`Store.get_disk_smart().smart.temperature.current`、`Store.get_disk_smart().smart.nvme_smart_health_information_log.temperature`。
- 只有有限、非零且非布尔值的 `int`/`float` 才是有效温度；有限非零负数保持有效。
- 只记录实际检查过的候选项；得到有效温度后立即停止更低优先级检查。
- SMART 请求按磁盘顺序串行执行。
- 监控接口或单盘 SMART 失败必须记录原因并尽量继续；连接、登录或磁盘枚举失败返回非零退出码。
- 输出不得包含用户名、密码、token 或 secret。
- Git 提交消息使用英文 Angular/Conventional Commits，禁止 `Co-Authored-By`。

---

## File Structure

- Create: `tools/list_disk_temperatures.py` — 温度提取、回退编排、诊断格式化及 CLI 运行入口。
- Create: `tests/test_list_disk_temperatures_tool.py` — 使用假 API 对象覆盖核心回退链、故障隔离、输出和 CLI 生命周期。
- Reference: `examples/common.py` — 只参考现有参数命名和连接登录方式，不在运行时导入。
- Reference: `fnos/store.py` — `Store.list_disks()` 与 `Store.get_disk_smart()` 的现有接口。
- Reference: `fnos/resource_monitor.py` — `ResourceMonitor.disk()` 的现有接口。
- Reference: `docs/superpowers/specs/2026-07-15-disk-temperature-diagnostic-design.md` — 已批准设计和输出约束。

### Task 1: Core Temperature Fallback Chain

**Files:**
- Create: `tests/test_list_disk_temperatures_tool.py`
- Create: `tools/list_disk_temperatures.py`

**Interfaces:**
- Consumes: `store.list_disks() -> dict`、`store.get_disk_smart(name: str) -> dict`、`resource_monitor.disk() -> dict`。
- Produces: `DiskTemperature`、`collect_disk_temperatures(store: Any, resource_monitor: Any) -> list[DiskTemperature]`、温度来源常量。

- [ ] **Step 1: Write the failing core fallback test**

Create `tests/test_list_disk_temperatures_tool.py` with the module loader, reusable fakes, and the first end-to-end collection test:

```python
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
```

- [ ] **Step 2: Run the core test and verify the expected failure**

Run:

```bash
uv run pytest \
  tests/test_list_disk_temperatures_tool.py::test_collect_prefers_monitor_then_falls_back_to_nvme_smart \
  tests/test_list_disk_temperatures_tool.py::test_missing_monitor_temp_and_zero_smart_current_use_nvme \
  -v
```

Expected: FAIL while loading the module because `tools/list_disk_temperatures.py` does not exist.

- [ ] **Step 3: Implement the minimal core collection pipeline**

Create `tools/list_disk_temperatures.py` with the following initial implementation:

```python
# Copyright 2025 Timandes White
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from dataclasses import dataclass, field
import math
from typing import Any


MONITOR_TEMPERATURE_SOURCE = "ResourceMonitor.disk().data.disk[].temp"
SMART_TEMPERATURE_SOURCE = (
    "Store.get_disk_smart().smart.temperature.current"
)
NVME_SMART_TEMPERATURE_SOURCE = (
    "Store.get_disk_smart().smart."
    "nvme_smart_health_information_log.temperature"
)
MISSING = object()


@dataclass
class DiskTemperature:
    name: str
    temperature: int | float | None = None
    source: str | None = None
    skipped: list[str] = field(default_factory=list)


def _get_nested(mapping: object, *keys: str) -> object:
    current = mapping
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return MISSING
        current = current[key]
    return current


def _temperature_problem(value: object) -> str | None:
    if value is MISSING:
        return "字段不存在"
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return "不是数字"
    if not math.isfinite(value):
        return "不是有限数值"
    if value == 0:
        return "值为 0"
    return None


def _skip_message(source: str, value: object, reason: str) -> str:
    if value is MISSING:
        return f"{source}（{reason}）"
    return f"{source} = {value!r}（{reason}）"


def _try_temperature(
    result: DiskTemperature,
    source: str,
    value: object,
) -> bool:
    problem = _temperature_problem(value)
    if problem is not None:
        result.skipped.append(_skip_message(source, value, problem))
        return False
    result.temperature = value
    result.source = source
    return True


def _disk_names(response: object) -> list[str]:
    disks = _get_nested(response, "disk")
    if not isinstance(disks, list):
        raise ValueError("Store.list_disks() 响应缺少 disk 列表")

    names = []
    for disk in disks:
        if not isinstance(disk, dict):
            raise ValueError("Store.list_disks() 返回了无效磁盘项")
        name = disk.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError("Store.list_disks() 返回了无效磁盘名称")
        names.append(name)
    return names


def _monitor_temperatures(response: object) -> dict[str, object]:
    disks = _get_nested(response, "data", "disk")
    if not isinstance(disks, list):
        return {}

    temperatures = {}
    for disk in disks:
        if not isinstance(disk, dict):
            continue
        name = disk.get("name")
        if isinstance(name, str) and name and name not in temperatures:
            temperatures[name] = disk.get("temp", MISSING)
    return temperatures


async def collect_disk_temperatures(
    store: Any,
    resource_monitor: Any,
) -> list[DiskTemperature]:
    names = _disk_names(await store.list_disks())
    monitor_temperatures = _monitor_temperatures(await resource_monitor.disk())
    results = []

    for name in names:
        result = DiskTemperature(name=name)
        if name not in monitor_temperatures:
            result.skipped.append(
                "ResourceMonitor.disk()（未找到该磁盘）"
            )
        elif _try_temperature(
            result,
            MONITOR_TEMPERATURE_SOURCE,
            monitor_temperatures[name],
        ):
            results.append(result)
            continue

        smart = await store.get_disk_smart(name)
        current = _get_nested(smart, "smart", "temperature", "current")
        if _try_temperature(result, SMART_TEMPERATURE_SOURCE, current):
            results.append(result)
            continue

        nvme = _get_nested(
            smart,
            "smart",
            "nvme_smart_health_information_log",
            "temperature",
        )
        _try_temperature(result, NVME_SMART_TEMPERATURE_SOURCE, nvme)
        results.append(result)

    return results
```

- [ ] **Step 4: Run the core test and verify it passes**

Run:

```bash
uv run pytest \
  tests/test_list_disk_temperatures_tool.py::test_collect_prefers_monitor_then_falls_back_to_nvme_smart \
  tests/test_list_disk_temperatures_tool.py::test_missing_monitor_temp_and_zero_smart_current_use_nvme \
  -v
```

Expected: both tests PASS; monitor list ordering does not affect Store ordering, and `store.smart_calls` contains only disks whose monitor temperature is missing or zero.

- [ ] **Step 5: Commit the core collection pipeline**

```bash
git add tools/list_disk_temperatures.py tests/test_list_disk_temperatures_tool.py
git commit -m "feat: add disk temperature collection"
```

### Task 2: Failure Isolation and Invalid Temperature Diagnostics

**Files:**
- Modify: `tests/test_list_disk_temperatures_tool.py`
- Modify: `tools/list_disk_temperatures.py`

**Interfaces:**
- Consumes: Task 1's `DiskTemperature` and `collect_disk_temperatures()`.
- Produces: monitor-wide fallback, per-disk SMART isolation, malformed response diagnostics, and safe exception summaries.

- [ ] **Step 1: Write failing failure-isolation and invalid-value tests**

Append these tests to `tests/test_list_disk_temperatures_tool.py`:

```python
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
```

- [ ] **Step 2: Run the new tests and verify the expected failures**

Run:

```bash
uv run pytest \
  tests/test_list_disk_temperatures_tool.py::test_monitor_failure_falls_back_for_all_disks_and_smart_failure_isolated \
  tests/test_list_disk_temperatures_tool.py::test_invalid_monitor_values_are_reported \
  tests/test_list_disk_temperatures_tool.py::test_malformed_monitor_response_is_reported_before_smart_fallback \
  tests/test_list_disk_temperatures_tool.py::test_invalid_disk_list_is_fatal \
  -v
```

Expected: monitor-failure and malformed-response tests FAIL because Task 1 does not catch those failures or distinguish malformed responses; parameterized invalid-value cases already pass and protect existing behavior.

- [ ] **Step 3: Add safe exception summaries and isolate fallback failures**

Add this helper after `_skip_message()` in `tools/list_disk_temperatures.py`:

```python
def _exception_summary(error: Exception) -> str:
    return type(error).__name__
```

Replace `_monitor_temperatures()` with a parser that reports malformed response structure:

```python
def _monitor_temperatures(
    response: object,
) -> tuple[dict[str, object], str | None]:
    disks = _get_nested(response, "data", "disk")
    if not isinstance(disks, list):
        return (
            {},
            "ResourceMonitor.disk().data.disk（字段不存在或不是列表）",
        )

    temperatures = {}
    for disk in disks:
        if not isinstance(disk, dict):
            continue
        name = disk.get("name")
        if isinstance(name, str) and name and name not in temperatures:
            temperatures[name] = disk.get("temp", MISSING)
    return temperatures, None
```

Replace `collect_disk_temperatures()` with the failure-isolating implementation:

```python
async def collect_disk_temperatures(
    store: Any,
    resource_monitor: Any,
) -> list[DiskTemperature]:
    names = _disk_names(await store.list_disks())

    try:
        monitor_response = await resource_monitor.disk()
    except Exception as error:
        monitor_temperatures = {}
        monitor_problem = (
            "ResourceMonitor.disk()（接口调用失败: "
            f"{_exception_summary(error)}）"
        )
    else:
        monitor_temperatures, monitor_problem = _monitor_temperatures(
            monitor_response
        )

    results = []
    for name in names:
        result = DiskTemperature(name=name)
        if monitor_problem is not None:
            result.skipped.append(monitor_problem)
        elif name not in monitor_temperatures:
            result.skipped.append(
                "ResourceMonitor.disk()（未找到该磁盘）"
            )
        elif _try_temperature(
            result,
            MONITOR_TEMPERATURE_SOURCE,
            monitor_temperatures[name],
        ):
            results.append(result)
            continue

        try:
            smart = await store.get_disk_smart(name)
        except Exception as error:
            result.skipped.append(
                f"Store.get_disk_smart({name!r})（接口调用失败: "
                f"{_exception_summary(error)}）"
            )
            results.append(result)
            continue

        current = _get_nested(smart, "smart", "temperature", "current")
        if _try_temperature(result, SMART_TEMPERATURE_SOURCE, current):
            results.append(result)
            continue

        nvme = _get_nested(
            smart,
            "smart",
            "nvme_smart_health_information_log",
            "temperature",
        )
        _try_temperature(result, NVME_SMART_TEMPERATURE_SOURCE, nvme)
        results.append(result)

    return results
```

- [ ] **Step 4: Run all core tests and verify they pass**

Run:

```bash
uv run pytest tests/test_list_disk_temperatures_tool.py -v
```

Expected: all Task 1 and Task 2 tests PASS; monitor and per-disk SMART exceptions do not escape.

- [ ] **Step 5: Commit failure isolation**

```bash
git add tools/list_disk_temperatures.py tests/test_list_disk_temperatures_tool.py
git commit -m "fix: isolate disk temperature fallback failures"
```

### Task 3: Human-Readable Output and CLI Lifecycle

**Files:**
- Modify: `tests/test_list_disk_temperatures_tool.py`
- Modify: `tools/list_disk_temperatures.py`

**Interfaces:**
- Consumes: Task 2's `collect_disk_temperatures()` and `DiskTemperature`.
- Produces: `format_disk_temperatures(results: list[DiskTemperature]) -> str`、`parse_args(argv: list[str] | None = None) -> argparse.Namespace`、`run(args: argparse.Namespace) -> int`、`main(argv: list[str] | None = None) -> int`。

- [ ] **Step 1: Write failing formatter and CLI lifecycle tests**

Append these imports near the top of `tests/test_list_disk_temperatures_tool.py`:

```python
import argparse
```

Append these tests:

```python
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


def test_parse_args_requires_credentials_and_endpoint():
    args = tool.parse_args(
        [
            "--user",
            "admin",
            "--password",
            "password",
            "-e",
            "nas.example.com:5666",
        ]
    )

    assert args == argparse.Namespace(
        user="admin",
        password="password",
        endpoint="nas.example.com:5666",
    )

    incomplete_argv = [
        ["--password", "password", "-e", "nas.example.com:5666"],
        ["--user", "admin", "-e", "nas.example.com:5666"],
        ["--user", "admin", "--password", "password"],
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
            self.connected_endpoint = None
            self.login_credentials = None
            self.closed = False

        async def connect(self, endpoint):
            self.connected_endpoint = endpoint

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
    args = argparse.Namespace(
        user="admin",
        password="password",
        endpoint="nas.example.com:5666",
    )

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
    assert client.connected_endpoint == args.endpoint
    assert client.login_credentials == (args.user, args.password)
    assert client.closed is True


@pytest.mark.asyncio
async def test_run_login_failure_is_fatal_and_does_not_leak_response(
    monkeypatch,
    capsys,
):
    class FailedLoginClient:
        def __init__(self):
            self.closed = False

        async def connect(self, endpoint):
            return None

        async def login(self, user, password):
            return {
                "result": "fail",
                "msg": "bad password",
                "secret": "must-not-be-printed",
            }

        async def close(self):
            self.closed = True

    client = FailedLoginClient()
    monkeypatch.setattr(tool, "FnosClient", lambda: client)
    args = argparse.Namespace(
        user="admin",
        password="password",
        endpoint="nas.example.com:5666",
    )

    exit_code = await tool.run(args)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == "错误: 登录失败\n"
    assert "must-not-be-printed" not in captured.err
    assert client.closed is True


@pytest.mark.asyncio
async def test_run_unexpected_failure_reports_only_exception_type(
    monkeypatch,
    capsys,
):
    class FailingClient:
        def __init__(self):
            self.closed = False

        async def connect(self, endpoint):
            raise RuntimeError("secret diagnostic details")

        async def close(self):
            self.closed = True

    client = FailingClient()
    monkeypatch.setattr(tool, "FnosClient", lambda: client)
    args = argparse.Namespace(
        user="admin",
        password="password",
        endpoint="nas.example.com:5666",
    )

    exit_code = await tool.run(args)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == "错误: 磁盘温度诊断失败（RuntimeError）\n"
    assert "secret diagnostic details" not in captured.err
    assert client.closed is True
```

- [ ] **Step 2: Run formatter and lifecycle tests and verify they fail**

Run:

```bash
uv run pytest \
  tests/test_list_disk_temperatures_tool.py::test_format_includes_source_skips_and_unknown_temperature \
  tests/test_list_disk_temperatures_tool.py::test_parse_args_requires_credentials_and_endpoint \
  tests/test_list_disk_temperatures_tool.py::test_run_partial_unknown_returns_zero_and_always_closes_client \
  tests/test_list_disk_temperatures_tool.py::test_run_login_failure_is_fatal_and_does_not_leak_response \
  tests/test_list_disk_temperatures_tool.py::test_run_unexpected_failure_reports_only_exception_type \
  -v
```

Expected: FAIL because formatter, argument parser, runtime imports, and `run()` do not exist.

- [ ] **Step 3: Add formatting, CLI parsing, runtime lifecycle, and executable entry point**

Add these imports below the license header in `tools/list_disk_temperatures.py`:

```python
import argparse
import asyncio
from dataclasses import dataclass, field
import math
import sys
from typing import Any

from fnos import FnosClient, ResourceMonitor, Store
```

Replace the existing import block rather than duplicating `dataclasses`, `math`, or `typing` imports.

Append the following functions after `collect_disk_temperatures()`:

```python
def _format_temperature(value: int | float) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def format_disk_temperatures(results: list[DiskTemperature]) -> str:
    blocks = []
    for result in results:
        if result.temperature is None:
            heading = f"{result.name} => 未知"
        else:
            heading = (
                f"{result.name} => "
                f"{_format_temperature(result.temperature)}°C"
            )

        lines = [heading]
        if result.source is not None:
            lines.append(f"  来源: {result.source}")
        lines.extend(f"  跳过: {message}" for message in result.skipped)
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="fnOS 磁盘温度诊断工具")
    parser.add_argument("--user", required=True, help="用户名")
    parser.add_argument("--password", required=True, help="密码")
    parser.add_argument(
        "-e",
        "--endpoint",
        required=True,
        help="fnOS 服务器地址，例如 nas.example.com:5666",
    )
    return parser.parse_args(argv)


async def run(args: argparse.Namespace) -> int:
    client = FnosClient()
    try:
        await client.connect(args.endpoint)
        login_result = await client.login(args.user, args.password)
        if (
            not isinstance(login_result, dict)
            or login_result.get("result") != "succ"
        ):
            print("错误: 登录失败", file=sys.stderr)
            return 1

        results = await collect_disk_temperatures(
            Store(client),
            ResourceMonitor(client),
        )
        print(format_disk_temperatures(results))
        return 0
    except Exception as error:
        print(
            "错误: 磁盘温度诊断失败"
            f"（{_exception_summary(error)}）",
            file=sys.stderr,
        )
        return 1
    finally:
        await client.close()


def main(argv: list[str] | None = None) -> int:
    return asyncio.run(run(parse_args(argv)))


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the complete tool test file and CLI help**

Run:

```bash
uv run pytest tests/test_list_disk_temperatures_tool.py -v
uv run python tools/list_disk_temperatures.py --help
```

Expected: all tool tests PASS; help exits `0` and lists required `--user`, `--password`, and `-e ENDPOINT, --endpoint ENDPOINT`.

- [ ] **Step 5: Run repository verification**

Run:

```bash
uv run pytest -m "not integration"
git diff --check
```

Expected: all non-integration tests PASS and `git diff --check` produces no output.

- [ ] **Step 6: Review the final diff against the approved design**

Run:

```bash
git diff -- tools/list_disk_temperatures.py tests/test_list_disk_temperatures_tool.py
git status --short
```

Expected: only the new tool and its test file are uncommitted; source labels, skip reasons, SMART priority, required CLI parameters, serial behavior, and cleanup match the approved design.

- [ ] **Step 7: Commit the CLI and final verification changes**

```bash
git add tools/list_disk_temperatures.py tests/test_list_disk_temperatures_tool.py
git commit -m "feat: add disk temperature diagnostic tool"
```
