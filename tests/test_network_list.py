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
async def test_network_list_type_0():
    """测试 Network.list(type=0) 方法的集成测试

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_network_list.py::test_network_list_type_0 -m integration
    或：
        pytest tests/test_network_list.py::test_network_list_type_0
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

        # 获取网络列表信息（type=0）
        list_result = await network.list(type=0)

        # 验证响应格式
        assert list_result.get("result") == "succ", "响应结果不是成功"
        assert "data" in list_result, "响应缺少 data 字段"

        # 验证 data 字段
        data = list_result["data"]
        assert "net" in data, "data 响应缺少 net 字段"
        assert "ifs" in data["net"], "net 响应缺少 ifs 字段"

        # 验证 ifs 是列表
        ifs = data["net"]["ifs"]
        assert isinstance(ifs, list), "ifs 应该是列表"
        assert len(ifs) > 0, "ifs 列表不应该为空"

        # 验证第一个接口的基本字段
        first_if = ifs[0]
        assert "name" in first_if, "网络接口缺少 name 字段"
        assert "index" in first_if, "网络接口缺少 index 字段"
        assert "ifType" in first_if, "网络接口缺少 ifType 字段"
        assert "enable" in first_if, "网络接口缺少 enable 字段"
        assert "running" in first_if, "网络接口缺少 running 字段"
        assert "onlink" in first_if, "网络接口缺少 onlink 字段"
        assert "state" in first_if, "网络接口缺少 state 字段"
        assert "speed" in first_if, "网络接口缺少 speed 字段"
        assert "mtu" in first_if, "网络接口缺少 mtu 字段"
        assert "hwAddr" in first_if, "网络接口缺少 hwAddr 字段"

        # 验证字段类型
        assert isinstance(first_if["name"], str), "name 应该是字符串"
        assert isinstance(first_if["index"], int), "index 应该是整数"
        assert isinstance(first_if["ifType"], int), "ifType 应该是整数"
        assert isinstance(first_if["enable"], bool), "enable 应该是布尔值"
        assert isinstance(first_if["running"], bool), "running 应该是布尔值"
        assert isinstance(first_if["onlink"], bool), "onlink 应该是布尔值"
        assert isinstance(first_if["state"], int), "state 应该是整数"
        assert isinstance(first_if["speed"], int), "speed 应该是整数"
        assert isinstance(first_if["mtu"], int), "mtu 应该是整数"
        assert isinstance(first_if["hwAddr"], str), "hwAddr 应该是字符串"

        # 验证值的合理性
        assert first_if["name"], "name 不应该为空"
        assert first_if["index"] > 0, "index 应该是正整数"
        assert first_if["mtu"] > 0, "mtu 应该是正整数"

        # 验证可选字段
        if "ipv4Addr" in first_if:
            assert isinstance(first_if["ipv4Addr"], str), "ipv4Addr 应该是字符串"

        if "ipv4" in first_if:
            assert isinstance(first_if["ipv4"], list), "ipv4 应该是列表"

        if "ipv6" in first_if:
            assert isinstance(first_if["ipv6"], list), "ipv6 应该是列表"

        if "slaves" in first_if:
            assert isinstance(first_if["slaves"], list), "slaves 应该是列表"

    finally:
        # 清理连接
        await client.close()


@pytest.mark.asyncio
async def test_network_list_type_1():
    """测试 Network.list(type=1) 方法的集成测试

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_network_list.py::test_network_list_type_1 -m integration
    或：
        pytest tests/test_network_list.py::test_network_list_type_1
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

        # 获取网络列表信息（type=1）
        list_result = await network.list(type=1)

        # 验证响应格式
        assert list_result.get("result") == "succ", "响应结果不是成功"
        assert "data" in list_result, "响应缺少 data 字段"

        # 验证 data 字段
        data = list_result["data"]
        assert "net" in data, "data 响应缺少 net 字段"
        assert "ifs" in data["net"], "net 响应缺少 ifs 字段"

        # 验证 ifs 是列表
        ifs = data["net"]["ifs"]
        assert isinstance(ifs, list), "ifs 应该是列表"
        assert len(ifs) > 0, "ifs 列表不应该为空"

    finally:
        # 清理连接
        await client.close()


@pytest.mark.asyncio
async def test_network_list_invalid_type():
    """测试 Network.list() 方法使用无效 type 参数

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_network_list.py::test_network_list_invalid_type -m integration
    或：
        pytest tests/test_network_list.py::test_network_list_invalid_type
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

        # 测试无效的 type 参数
        with pytest.raises(ValueError, match="type参数必须为0或1"):
            await network.list(type=2)

    finally:
        # 清理连接
        await client.close()