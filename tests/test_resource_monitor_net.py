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
async def test_resmon_net():
    """测试 ResourceMonitor.net() 方法的集成测试

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_resource_monitor_net.py -m integration
    或：
        pytest tests/test_resource_monitor_net.py
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

        # 获取网络资源信息
        net_result = await resource_monitor.net()

        # 验证响应格式
        assert net_result.get("result") == "succ", "响应结果不是成功"
        assert "data" in net_result, "响应缺少 data 字段"
        assert "ifs" in net_result["data"], "响应缺少 ifs 字段"

        # 验证 ifs 列表
        ifs_list = net_result["data"]["ifs"]
        assert isinstance(ifs_list, list), "ifs 应该是列表"

        # 如果有网络接口，验证每个接口的字段
        for iface in ifs_list:
            assert "name" in iface, "网络接口响应缺少 name 字段"
            assert "index" in iface, "网络接口响应缺少 index 字段"
            assert "ifType" in iface, "网络接口响应缺少 ifType 字段"
            assert "receive" in iface, "网络接口响应缺少 receive 字段"
            assert "transmit" in iface, "网络接口响应缺少 transmit 字段"

            # 验证字段类型
            assert isinstance(iface["name"], str), "name 应该是字符串"
            assert isinstance(iface["index"], int), "index 应该是整数"
            assert isinstance(iface["ifType"], int), "ifType 应该是整数"
            assert isinstance(iface["receive"], (int, float)), "receive 应该是数字"
            assert isinstance(iface["transmit"], (int, float)), "transmit 应该是数字"

            # 验证值的合理性
            assert iface["receive"] >= 0, "receive 应该是非负数"
            assert iface["transmit"] >= 0, "transmit 应该是非负数"

            # 验证可选字段
            if "bond" in iface:
                assert isinstance(iface["bond"], bool), "bond 应该是布尔值"

    finally:
        # 清理连接
        await client.close()