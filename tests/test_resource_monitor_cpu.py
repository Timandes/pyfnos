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

import asyncio
import pytest

from fnos import FnosClient, ResourceMonitor


# 集成测试标记，用于区分需要外部依赖的测试
pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_resmon_cpu():
    """测试 ResourceMonitor.cpu() 方法的集成测试

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_resource_monitor_cpu.py -m integration
    或：
        pytest tests/test_resource_monitor_cpu.py
    """
    # 创建客户端
    client = FnosClient()

    try:
        # 连接到 fnOS 服务
        await client.connect("127.0.0.1:5666")
        assert client.connected, "连接失败"

        # 登录
        login_result = await client.login("admin", "admin")
        assert login_result.get("result") == "succ", f"登录失败: {login_result}"

        # 创建 ResourceMonitor 实例
        resource_monitor = ResourceMonitor(client)

        # 获取 CPU 资源信息
        cpu_result = await resource_monitor.cpu()

        # 验证响应格式
        assert cpu_result.get("result") == "succ", "响应结果不是成功"
        assert "data" in cpu_result, "响应缺少 data 字段"
        assert "cpu" in cpu_result["data"], "响应缺少 cpu 字段"

        cpu_data = cpu_result["data"]["cpu"]

        # 验证 CPU 必需字段
        assert "name" in cpu_data, "CPU 响应缺少 name 字段"
        assert "num" in cpu_data, "CPU 响应缺少 num 字段"
        assert "core" in cpu_data, "CPU 响应缺少 core 字段"
        assert "thread" in cpu_data, "CPU 响应缺少 thread 字段"
        assert "maxFreq" in cpu_data, "CPU 响应缺少 maxFreq 字段"
        assert "temp" in cpu_data, "CPU 响应缺少 temp 字段"
        assert "busy" in cpu_data, "CPU 响应缺少 busy 字段"
        assert "loadavg" in cpu_data, "CPU 响应缺少 loadavg 字段"

        # 验证 busy 字段结构
        busy_data = cpu_data["busy"]
        assert "all" in busy_data, "busy 响应缺少 all 字段"
        assert "user" in busy_data, "busy 响应缺少 user 字段"
        assert "system" in busy_data, "busy 响应缺少 system 字段"
        assert "iowait" in busy_data, "busy 响应缺少 iowait 字段"
        assert "other" in busy_data, "busy 响应缺少 other 字段"

        # 验证 loadavg 字段结构
        loadavg_data = cpu_data["loadavg"]
        assert "avg1min" in loadavg_data, "loadavg 响应缺少 avg1min 字段"
        assert "avg5min" in loadavg_data, "loadavg 响应缺少 avg5min 字段"
        assert "avg15min" in loadavg_data, "loadavg 响应缺少 avg15min 字段"

        # 验证字段类型
        assert isinstance(cpu_data["name"], str), "name 应该是字符串"
        assert isinstance(cpu_data["num"], int), "num 应该是整数"
        assert isinstance(cpu_data["core"], int), "core 应该是整数"
        assert isinstance(cpu_data["thread"], int), "thread 应该是整数"
        assert isinstance(cpu_data["maxFreq"], (int, float)), "maxFreq 应该是数字"
        assert isinstance(cpu_data["temp"], list), "temp 应该是列表"

        # 验证 busy 字段类型
        assert isinstance(busy_data["all"], (int, float)), "busy.all 应该是数字"
        assert isinstance(busy_data["user"], (int, float)), "busy.user 应该是数字"
        assert isinstance(busy_data["system"], (int, float)), "busy.system 应该是数字"
        assert isinstance(busy_data["iowait"], (int, float)), "busy.iowait 应该是数字"
        assert isinstance(busy_data["other"], (int, float)), "busy.other 应该是数字"

        # 验证 loadavg 字段类型
        assert isinstance(loadavg_data["avg1min"], (int, float)), "loadavg.avg1min 应该是数字"
        assert isinstance(loadavg_data["avg5min"], (int, float)), "loadavg.avg5min 应该是数字"
        assert isinstance(loadavg_data["avg15min"], (int, float)), "loadavg.avg15min 应该是数字"

    finally:
        # 清理连接
        await client.close()