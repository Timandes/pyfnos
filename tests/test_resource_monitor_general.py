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
async def test_resmon_general_default():
    """测试 ResourceMonitor.general() 方法的集成测试（默认参数）

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_resource_monitor_general.py -m integration
    或：
        pytest tests/test_resource_monitor_general.py
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

        # 获取通用资源信息（使用默认参数）
        general_result = await resource_monitor.general()

        # 验证响应格式
        assert general_result.get("result") == "succ", "响应结果不是成功"
        assert "data" in general_result, "响应缺少 data 字段"
        assert "item" in general_result["data"], "响应缺少 item 字段"

        # 验证 item 字段
        item_data = general_result["data"]["item"]
        assert isinstance(item_data, dict), "item 应该是字典"

        # 验证默认返回的字段
        assert "storeSpeed" in item_data, "item 响应缺少 storeSpeed 字段"
        assert "netSpeed" in item_data, "item 响应缺少 netSpeed 字段"
        assert "cpuBusy" in item_data, "item 响应缺少 cpuBusy 字段"
        assert "memPercent" in item_data, "item 响应缺少 memPercent 字段"

        # 验证 storeSpeed 字段结构
        store_speed = item_data["storeSpeed"]
        assert "read" in store_speed, "storeSpeed 响应缺少 read 字段"
        assert "write" in store_speed, "storeSpeed 响应缺少 write 字段"
        assert isinstance(store_speed["read"], (int, float)), "storeSpeed.read 应该是数字"
        assert isinstance(store_speed["write"], (int, float)), "storeSpeed.write 应该是数字"
        assert store_speed["read"] >= 0, "storeSpeed.read 应该是非负数"
        assert store_speed["write"] >= 0, "storeSpeed.write 应该是非负数"

        # 验证 netSpeed 字段结构
        net_speed = item_data["netSpeed"]
        assert "transmit" in net_speed, "netSpeed 响应缺少 transmit 字段"
        assert "receive" in net_speed, "netSpeed 响应缺少 receive 字段"
        assert isinstance(net_speed["transmit"], (int, float)), "netSpeed.transmit 应该是数字"
        assert isinstance(net_speed["receive"], (int, float)), "netSpeed.receive 应该是数字"
        assert net_speed["transmit"] >= 0, "netSpeed.transmit 应该是非负数"
        assert net_speed["receive"] >= 0, "netSpeed.receive 应该是非负数"

        # 验证 cpuBusy 字段
        cpu_busy = item_data["cpuBusy"]
        assert isinstance(cpu_busy, (int, float)), "cpuBusy 应该是数字"
        assert 0 <= cpu_busy <= 100, "cpuBusy 应该在 0-100 之间"

        # 验证 memPercent 字段
        mem_percent = item_data["memPercent"]
        assert isinstance(mem_percent, (int, float)), "memPercent 应该是数字"
        assert 0 <= mem_percent <= 100, "memPercent 应该在 0-100 之间"

    finally:
        # 清理连接
        await client.close()


@pytest.mark.asyncio
async def test_resmon_general_custom_items():
    """测试 ResourceMonitor.general() 方法的集成测试（自定义 items 参数）

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_resource_monitor_general.py::test_resmon_general_custom_items -m integration
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

        # 获取通用资源信息（自定义 items）
        custom_items = ["cpuBusy", "memPercent"]
        general_result = await resource_monitor.general(items=custom_items)

        # 验证响应格式
        assert general_result.get("result") == "succ", "响应结果不是成功"
        assert "data" in general_result, "响应缺少 data 字段"
        assert "item" in general_result["data"], "响应缺少 item 字段"

        # 验证 item 字段
        item_data = general_result["data"]["item"]
        assert isinstance(item_data, dict), "item 应该是字典"

        # 验证只返回了请求的字段
        assert "cpuBusy" in item_data, "item 响应缺少 cpuBusy 字段"
        assert "memPercent" in item_data, "item 响应缺少 memPercent 字段"

        # 验证 cpuBusy 字段
        cpu_busy = item_data["cpuBusy"]
        assert isinstance(cpu_busy, (int, float)), "cpuBusy 应该是数字"
        assert 0 <= cpu_busy <= 100, "cpuBusy 应该在 0-100 之间"

        # 验证 memPercent 字段
        mem_percent = item_data["memPercent"]
        assert isinstance(mem_percent, (int, float)), "memPercent 应该是数字"
        assert 0 <= mem_percent <= 100, "memPercent 应该在 0-100 之间"

    finally:
        # 清理连接
        await client.close()