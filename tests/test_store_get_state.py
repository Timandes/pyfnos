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
async def test_store_get_state():
    """测试 Store.get_state() 方法的集成测试

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_store_get_state.py -m integration
    或：
        pytest tests/test_store_get_state.py
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

        # 先获取存储通用信息，获取可用的设备名称和 UUID
        general_result = await store.general()
        assert general_result.get("result") == "succ", "获取存储通用信息失败"

        array_data = general_result.get("array", [])
        if not array_data:
            pytest.skip("系统中没有可用的存储设备")

        # 提取第一个设备的名称和 UUID
        first_device = array_data[0]
        device_name = first_device["name"]
        device_uuid = first_device["uuid"]

        # 获取存储状态信息
        state_result = await store.get_state([device_name], [device_uuid])

        # 验证响应格式
        assert state_result.get("result") == "succ", "响应结果不是成功"
        assert "state" in state_result, "响应缺少 state 字段"

        # 验证 state 字段
        state_list = state_result["state"]
        assert isinstance(state_list, list), "state 应该是列表"

        # 验证每个存储状态的字段
        for state_item in state_list:
            assert "name" in state_item, "存储状态响应缺少 name 字段"
            assert "uuid" in state_item, "存储状态响应缺少 uuid 字段"
            assert "frsize" in state_item, "存储状态响应缺少 frsize 字段"
            assert "fssize" in state_item, "存储状态响应缺少 fssize 字段"
            assert "level" in state_item, "存储状态响应缺少 level 字段"
            assert "storId" in state_item, "存储状态响应缺少 storId 字段"
            assert "md" in state_item, "存储状态响应缺少 md 字段"

            # 验证字段类型
            assert isinstance(state_item["name"], str), "name 应该是字符串"
            assert isinstance(state_item["uuid"], str), "uuid 应该是字符串"
            assert isinstance(state_item["frsize"], int), "frsize 应该是整数"
            assert isinstance(state_item["fssize"], int), "fssize 应该是整数"
            assert isinstance(state_item["level"], str), "level 应该是字符串"
            assert isinstance(state_item["storId"], int), "storId 应该是整数"
            assert isinstance(state_item["md"], list), "md 应该是列表"

            # 验证值的合理性
            assert state_item["frsize"] >= 0, "frsize 应该是非负数"
            assert state_item["fssize"] >= 0, "fssize 应该是非负数"
            assert state_item["storId"] > 0, "storId 应该是正整数"

            # 验证 md 字段
            md_list = state_item["md"]
            for md_item in md_list:
                assert "name" in md_item, "md 响应缺少 name 字段"
                assert "uuid" in md_item, "md 响应缺少 uuid 字段"
                assert "raidDisks" in md_item, "md 响应缺少 raidDisks 字段"
                assert "level" in md_item, "md 响应缺少 level 字段"
                assert "arrayState" in md_item, "md 响应缺少 arrayState 字段"
                assert "syncAction" in md_item, "md 响应缺少 syncAction 字段"

                # 验证 md 字段类型
                assert isinstance(md_item["name"], str), "md.name 应该是字符串"
                assert isinstance(md_item["uuid"], str), "md.uuid 应该是字符串"
                assert isinstance(md_item["raidDisks"], int), "md.raidDisks 应该是整数"
                assert isinstance(md_item["level"], str), "md.level 应该是字符串"
                assert isinstance(md_item["arrayState"], str), "md.arrayState 应该是字符串"
                assert isinstance(md_item["syncAction"], str), "md.syncAction 应该是字符串"

                # 验证值的合理性
                assert md_item["raidDisks"] > 0, "md.raidDisks 应该是正整数"

                # 验证可选的 disk 字段
                if "disk" in md_item:
                    disk_list = md_item["disk"]
                    assert isinstance(disk_list, list), "md.disk 应该是列表"
                    for disk in disk_list:
                        assert "name" in disk, "disk 响应缺少 name 字段"
                        assert "arrState" in disk, "disk 响应缺少 arrState 字段"
                        assert isinstance(disk["name"], str), "disk.name 应该是字符串"
                        assert isinstance(disk["arrState"], str), "disk.arrState 应该是字符串"

    finally:
        # 清理连接
        await client.close()