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

import argparse
import asyncio
from dataclasses import dataclass, field
import math
import re
import sys
import traceback
from typing import Any

from common import add_auth_arguments, connect_client, login_with_twofa
from fnos import FnosClient, ResourceMonitor, Store


MONITOR_TEMPERATURE_SOURCE = "ResourceMonitor.disk().data.disk[].temp"
SMART_TEMPERATURE_SOURCE = "Store.get_disk_smart().smart.temperature.current"
NVME_SMART_TEMPERATURE_SOURCE = (
    "Store.get_disk_smart().smart."
    "nvme_smart_health_information_log.temperature"
)
MISSING = object()
AUTH_VALUE_PATTERN = re.compile(
    r"""
    (?P<prefix>
        ["']?(?:accessToken|longToken|token|secret|password)["']?
        \s*[:=]\s*
    )
    (?P<value>
        "(?:\\.|[^"\\])*"
        |
        '(?:\\.|[^'\\])*'
        |
        [^,\s}\]]+
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


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


def _redact(text: str, sensitive_values: tuple[object, ...] = ()) -> str:
    redacted = text
    for value in sensitive_values:
        if value is not None and str(value):
            redacted = redacted.replace(str(value), "***")

    def replace_auth_value(match: re.Match[str]) -> str:
        value = match.group("value")
        if value[:1] in {'"', "'"} and value[-1:] == value[:1]:
            replacement = f"{value[0]}***{value[-1]}"
        else:
            replacement = "***"
        return f"{match.group('prefix')}{replacement}"

    return AUTH_VALUE_PATTERN.sub(replace_auth_value, redacted)


def _exception_parts(
    error: Exception,
    sensitive_values: tuple[object, ...] = (),
) -> tuple[str, str]:
    detail = str(error).strip() or "无详细信息"
    return type(error).__name__, _redact(detail, sensitive_values)


def _exception_summary(
    error: Exception,
    sensitive_values: tuple[object, ...] = (),
) -> str:
    exception_type, detail = _exception_parts(error, sensitive_values)
    return f"{exception_type}: {detail}"


def _print_failure(
    stage: str,
    error: Exception,
    args: argparse.Namespace,
) -> None:
    auth_sensitive_values = getattr(args, "_auth_sensitive_values", ())
    sensitive_values = (
        getattr(args, "password", None),
        getattr(args, "code", None),
        *auth_sensitive_values,
    )
    try:
        exception_type, detail = _exception_parts(error, sensitive_values)
        print(f"错误: {stage}阶段失败", file=sys.stderr)
        print(f"异常类型: {exception_type}", file=sys.stderr)
        print(f"异常详情: {detail}", file=sys.stderr)

        if getattr(args, "debug", False):
            formatted = "".join(
                traceback.format_exception(
                    type(error),
                    error,
                    error.__traceback__,
                )
            )
            print(
                _redact(formatted, sensitive_values),
                file=sys.stderr,
                end="",
            )
        else:
            print(
                "提示: 使用 --debug 查看完整 traceback",
                file=sys.stderr,
            )
    finally:
        if hasattr(args, "_auth_sensitive_values"):
            del args._auth_sensitive_values


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
            result.skipped.append("ResourceMonitor.disk()（未找到该磁盘）")
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
    add_auth_arguments(parser)
    parser.add_argument(
        "--debug",
        action="store_true",
        help="输出已脱敏的完整 traceback",
    )
    return parser.parse_args(argv)


async def run(args: argparse.Namespace) -> int:
    client = FnosClient()
    stage = "连接"
    try:
        await connect_client(client, args)

        stage = "登录或两步验证"
        await login_with_twofa(client, args)

        stage = "磁盘枚举与温度获取"
        results = await collect_disk_temperatures(
            Store(client),
            ResourceMonitor(client),
        )
        print(format_disk_temperatures(results))
        return 0
    except Exception as error:
        _print_failure(stage, error, args)
        return 1
    finally:
        await client.close()


def main(argv: list[str] | None = None) -> int:
    return asyncio.run(run(parse_args(argv)))


if __name__ == "__main__":
    raise SystemExit(main())
