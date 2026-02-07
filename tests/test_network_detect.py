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

from fnos import FnosClient, Network


# 集成测试标记，用于区分需要外部依赖的测试
pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_network_detect():
    """测试 Network.detect() 方法的集成测试

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录
    3. 系统中存在网络接口

    运行方式：
        pytest tests/test_network_detect.py -m integration
    或：
        pytest tests/test_network_detect.py
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

        # 创建 Network 实例
        network = Network(client)

        # 获取网络列表，找到一个存在的网络接口
        list_result = await network.list(type=0)

        # 找到第一个网络接口
        if "data" in list_result and "net" in list_result["data"]:
            if_name = list_result["data"]["net"]["ifs"][0]["name"]

            # 检测网络接口
            detect_result = await network.detect(if_name)

            # 验证响应格式
            assert detect_result.get("result") == "succ", "响应结果不是成功"
            assert "data" in detect_result, "响应缺少 data 字段"

            # 验证 data 字段
            data = detect_result["data"]
            assert "ifs" in data, "data 响应缺少 ifs 字段"

            # 验证 ifs 字段
            ifs = data["ifs"]
            assert "ipv4Lan" in ifs, "ifs 响应缺少 ipv4Lan 字段"
            assert "ipv4Wan" in ifs, "ifs 响应缺少 ipv4Wan 字段"
            assert "ipv6Lan" in ifs, "ifs 响应缺少 ipv6Lan 字段"
            assert "ipv6Wan" in ifs, "ifs 响应缺少 ipv6Wan 字段"

            # 验证字段类型
            assert isinstance(ifs["ipv4Lan"], int), "ipv4Lan 应该是整数"
            assert isinstance(ifs["ipv4Wan"], int), "ipv4Wan 应该是整数"
            assert isinstance(ifs["ipv6Lan"], int), "ipv6Lan 应该是整数"
            assert isinstance(ifs["ipv6Wan"], int), "ipv6Wan 应该是整数"

            # 验证值的合理性（0 或 1）
            assert ifs["ipv4Lan"] in [0, 1], "ipv4Lan 应该是 0 或 1"
            assert ifs["ipv4Wan"] in [0, 1], "ipv4Wan 应该是 0 或 1"
            assert ifs["ipv6Lan"] in [0, 1], "ipv6Lan 应该是 0 或 1"
            assert ifs["ipv6Wan"] in [0, 1], "ipv6Wan 应该是 0 或 1"
        else:
            pytest.skip("没有找到网络接口")

    finally:
        # 清理连接
        await client.close()