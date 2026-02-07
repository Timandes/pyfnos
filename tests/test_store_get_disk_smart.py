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

from fnos import FnosClient, Store


# 集成测试标记，用于区分需要外部依赖的测试
pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_store_get_disk_smart():
    """测试 Store.get_disk_smart() 方法的集成测试

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录
    3. 系统中存在磁盘（如 sda, nvme0n1 等）

    运行方式：
        pytest tests/test_store_get_disk_smart.py -m integration
    或：
        pytest tests/test_store_get_disk_smart.py
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

        # 创建 Store 实例
        store = Store(client)

        # 先获取磁盘列表，找到一个存在的磁盘
        disks_result = await store.list_disks()
        # 服务器可能不返回 result 字段，只检查是否有 disk 字段
        assert "disk" in disks_result, "响应缺少 disk 字段"

        disk_list = disks_result.get("disk", [])
        if not disk_list:
            pytest.skip("系统中没有可用的磁盘")

        # 使用第一个磁盘进行 SMART 测试
        disk_name = disk_list[0]["name"]

        # 获取磁盘 SMART 信息
        smart_result = await store.get_disk_smart(disk_name)

        # 验证响应格式
        assert smart_result.get("result") == "succ", f"响应结果不是成功: {smart_result}"
        assert "smart" in smart_result, "响应缺少 smart 字段"

        # 验证 smart 字段
        smart_data = smart_result["smart"]
        assert isinstance(smart_data, dict), "smart 应该是字典"

        # 验证 SMART 数据的必需字段
        assert "smartctl" in smart_data, "smart 响应缺少 smartctl 字段"
        assert "device" in smart_data, "smart 响应缺少 device 字段"
        assert "model_name" in smart_data, "smart 响应缺少 model_name 字段"
        assert "serial_number" in smart_data, "smart 响应缺少 serial_number 字段"
        assert "firmware_version" in smart_data, "smart 响应缺少 firmware_version 字段"
        assert "smart_support" in smart_data, "smart 响应缺少 smart_support 字段"
        assert "smart_status" in smart_data, "smart 响应缺少 smart_status 字段"

        # 验证 smartctl 字段
        smartctl_data = smart_data["smartctl"]
        assert isinstance(smartctl_data, dict), "smartctl 应该是字典"
        assert "version" in smartctl_data, "smartctl 响应缺少 version 字段"
        assert isinstance(smartctl_data["version"], list), "version 应该是列表"

        # 验证 device 字段
        device_data = smart_data["device"]
        assert isinstance(device_data, dict), "device 应该是字典"
        assert "name" in device_data, "device 响应缺少 name 字段"
        assert "type" in device_data, "device 响应缺少 type 字段"
        assert isinstance(device_data["name"], str), "device.name 应该是字符串"
        assert isinstance(device_data["type"], str), "device.type 应该是字符串"

        # 验证基本字段类型
        assert isinstance(smart_data["model_name"], str), "model_name 应该是字符串"
        assert isinstance(smart_data["serial_number"], str), "serial_number 应该是字符串"
        assert isinstance(smart_data["firmware_version"], str), "firmware_version 应该是字符串"

        # 验证 smart_support 字段
        smart_support_data = smart_data["smart_support"]
        assert isinstance(smart_support_data, dict), "smart_support 应该是字典"
        assert "available" in smart_support_data, "smart_support 响应缺少 available 字段"
        assert "enabled" in smart_support_data, "smart_support 响应缺少 enabled 字段"
        assert isinstance(smart_support_data["available"], bool), "available 应该是布尔值"
        assert isinstance(smart_support_data["enabled"], bool), "enabled 应该是布尔值"

        # 验证 smart_status 字段
        smart_status_data = smart_data["smart_status"]
        assert isinstance(smart_status_data, dict), "smart_status 应该是字典"
        assert "passed" in smart_status_data, "smart_status 响应缺少 passed 字段"
        assert isinstance(smart_status_data["passed"], bool), "passed 应该是布尔值"

        # 验证可选字段
        if "temperature" in smart_data:
            temp_data = smart_data["temperature"]
            assert isinstance(temp_data, dict), "temperature 应该是字典"
            if "current" in temp_data:
                assert isinstance(temp_data["current"], (int, float)), "temperature.current 应该是数字"
                assert temp_data["current"] >= 0, "temperature.current 应该是非负数"

    finally:
        # 清理连接
        await client.close()