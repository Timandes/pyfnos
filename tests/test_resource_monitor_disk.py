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
async def test_resmon_disk():
    """测试 ResourceMonitor.disk() 方法的集成测试

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_resource_monitor_disk.py -m integration
    或：
        pytest tests/test_resource_monitor_disk.py
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

        # 获取磁盘资源信息
        disk_result = await resource_monitor.disk()

        # 验证响应格式
        assert disk_result.get("result") == "succ", "响应结果不是成功"
        assert "data" in disk_result, "响应缺少 data 字段"
        assert "disk" in disk_result["data"], "响应缺少 disk 字段"
        assert "num" in disk_result["data"], "响应缺少 num 字段"

        # 验证 num 字段
        num = disk_result["data"]["num"]
        assert isinstance(num, int), "num 应该是整数"
        assert num >= 0, "num 应该是非负数"

        # 验证 disk 列表
        disk_list = disk_result["data"]["disk"]
        assert isinstance(disk_list, list), "disk 应该是列表"
        assert len(disk_list) == num, f"disk 列表长度 {len(disk_list)} 应该等于 num {num}"

        # 如果有磁盘，验证每个磁盘的字段
        for disk_item in disk_list:
            assert "name" in disk_item, "磁盘响应缺少 name 字段"
            assert "temp" in disk_item, "磁盘响应缺少 temp 字段"
            assert "standby" in disk_item, "磁盘响应缺少 standby 字段"
            assert "busy" in disk_item, "磁盘响应缺少 busy 字段"
            assert "read" in disk_item, "磁盘响应缺少 read 字段"
            assert "write" in disk_item, "磁盘响应缺少 write 字段"

            # 验证字段类型
            assert isinstance(disk_item["name"], str), "name 应该是字符串"
            assert isinstance(disk_item["temp"], (int, float)), "temp 应该是数字"
            assert isinstance(disk_item["standby"], bool), "standby 应该是布尔值"
            assert isinstance(disk_item["busy"], (int, float)), "busy 应该是数字"
            assert isinstance(disk_item["read"], (int, float)), "read 应该是数字"
            assert isinstance(disk_item["write"], (int, float)), "write 应该是数字"

            # 验证值的合理性
            assert disk_item["name"], "name 不应该为空"
            assert disk_item["temp"] >= 0, "temp 应该是非负数"
            assert disk_item["busy"] >= 0, "busy 应该是非负数"
            assert disk_item["read"] >= 0, "read 应该是非负数"
            assert disk_item["write"] >= 0, "write 应该是非负数"

            # 温度通常在 0-100 摄氏度之间（但也可能更高）
            assert disk_item["temp"] >= 0, "temp 应该是非负数"

    finally:
        # 清理连接
        await client.close()