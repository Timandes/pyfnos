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
SMART_TEMPERATURE_SOURCE = "Store.get_disk_smart().smart.temperature.current"
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
            result.skipped.append("ResourceMonitor.disk()（未找到该磁盘）")
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
