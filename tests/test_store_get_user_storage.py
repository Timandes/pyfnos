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
async def test_store_get_user_storage():
    """测试 Store.get_user_storage() 方法的集成测试

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_store_get_user_storage.py -m integration
    或：
        pytest tests/test_store_get_user_storage.py
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

        # 获取用户存储信息（所有参数为 True）
        user_storage_result = await store.get_user_storage(
            space_info=True,
            stor_info=True,
            quota_info=True
        )

        # 验证响应格式
        assert user_storage_result.get("result") == "succ", "响应结果不是成功"
        assert "stor" in user_storage_result, "响应缺少 stor 字段"
        assert "uid" in user_storage_result, "响应缺少 uid 字段"

        # 验证字段类型
        assert isinstance(user_storage_result["stor"], list), "stor 应该是列表"
        assert isinstance(user_storage_result["uid"], int), "uid 应该是整数"

        # 如果有存储数据，验证每个存储设备的字段
        for item in user_storage_result["stor"]:
            assert "id" in item, "存储设备缺少 id 字段"
            assert "comment" in item, "存储设备缺少 comment 字段"
            assert "frsize" in item, "存储设备缺少 frsize 字段"
            assert "fssize" in item, "存储设备缺少 fssize 字段"
            assert "level" in item, "存储设备缺少 level 字段"
            assert "fstype" in item, "存储设备缺少 fstype 字段"
            assert "diskType" in item, "存储设备缺少 diskType 字段"
            assert "quotaCurr" in item, "存储设备缺少 quotaCurr 字段"
            assert "quotaMax" in item, "存储设备缺少 quotaMax 字段"

            # 验证字段类型
            assert isinstance(item["id"], int), "id 应该是整数"
            assert isinstance(item["comment"], str), "comment 应该是字符串"
            assert isinstance(item["frsize"], int), "frsize 应该是整数"
            assert isinstance(item["fssize"], int), "fssize 应该是整数"
            assert isinstance(item["level"], str), "level 应该是字符串"
            assert isinstance(item["fstype"], str), "fstype 应该是字符串"
            assert isinstance(item["diskType"], str), "diskType 应该是字符串"
            assert isinstance(item["quotaCurr"], int), "quotaCurr 应该是整数"
            assert isinstance(item["quotaMax"], int), "quotaMax 应该是整数"

            # 验证值的合理性
            assert item["id"] > 0, "id 应该是正整数"
            assert item["frsize"] >= 0, "frsize 应该是非负数"
            assert item["fssize"] >= 0, "fssize 应该是非负数"
            assert item["quotaCurr"] >= 0, "quotaCurr 应该是非负数"

    finally:
        # 清理连接
        await client.close()