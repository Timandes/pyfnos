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
async def test_store_general():
    """测试 Store.general() 方法的集成测试

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_store_general.py -m integration
    或：
        pytest tests/test_store_general.py
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

        # 获取存储通用信息
        general_result = await store.general()

        # 验证响应格式
        assert general_result.get("result") == "succ", "响应结果不是成功"
        assert "array" in general_result, "响应缺少 array 字段"
        assert "block" in general_result, "响应缺少 block 字段"

        # 验证 array 字段
        array_data = general_result["array"]
        assert isinstance(array_data, list), "array 应该是列表"

        # 验证 block 字段
        block_data = general_result["block"]
        assert isinstance(block_data, list), "block 应该是列表"

        # 如果有 array 数据，验证每个存储设备的字段
        for item in array_data:
            assert "name" in item, "存储设备响应缺少 name 字段"
            assert "uuid" in item, "存储设备响应缺少 uuid 字段"
            assert "mountpoint" in item, "存储设备响应缺少 mountpoint 字段"
            assert "frsize" in item, "存储设备响应缺少 frsize 字段"
            assert "fssize" in item, "存储设备响应缺少 fssize 字段"
            assert "level" in item, "存储设备响应缺少 level 字段"
            assert "storId" in item, "存储设备响应缺少 storId 字段"
            assert "md" in item, "存储设备响应缺少 md 字段"

            # 验证字段类型
            assert isinstance(item["name"], str), "name 应该是字符串"
            assert isinstance(item["uuid"], str), "uuid 应该是字符串"
            assert isinstance(item["mountpoint"], str), "mountpoint 应该是字符串"
            assert isinstance(item["frsize"], int), "frsize 应该是整数"
            assert isinstance(item["fssize"], int), "fssize 应该是整数"
            assert isinstance(item["level"], str), "level 应该是字符串"
            assert isinstance(item["storId"], int), "storId 应该是整数"
            assert isinstance(item["md"], list), "md 应该是列表"

            # 验证值的合理性
            assert item["frsize"] >= 0, "frsize 应该是非负数"
            assert item["fssize"] >= 0, "fssize 应该是非负数"
            assert item["storId"] > 0, "storId 应该是正整数"

        # 如果有 block 数据，验证基本结构
        for item in block_data:
            assert "name" in item, "块设备响应缺少 name 字段"
            assert isinstance(item["name"], str), "name 应该是字符串"

    finally:
        # 清理连接
        await client.close()