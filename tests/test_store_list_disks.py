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
async def test_store_list_disks_default():
    """测试 Store.list_disks() 方法的集成测试（默认参数，排除热备盘）

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_store_list_disks.py::test_store_list_disks_default -m integration
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

        # 获取磁盘列表（默认参数，排除热备盘）
        disks_result = await store.list_disks()

        # 验证响应格式（服务器可能不返回 result 字段）
        if "result" in disks_result:
            assert disks_result["result"] == "succ", f"响应结果不是成功: {disks_result}"
        assert "disk" in disks_result, "响应缺少 disk 字段"

        # 验证 disk 字段
        disk_list = disks_result["disk"]
        assert isinstance(disk_list, list), "disk 应该是列表"

        # 如果有磁盘数据，验证每个磁盘的字段
        for disk in disk_list:
            assert "name" in disk, "磁盘响应缺少 name 字段"
            assert "size" in disk, "磁盘响应缺少 size 字段"
            assert "modelName" in disk, "磁盘响应缺少 modelName 字段"
            assert "serialNumber" in disk, "磁盘响应缺少 serialNumber 字段"
            assert "type" in disk, "磁盘响应缺少 type 字段"
            assert "protocol" in disk, "磁盘响应缺少 protocol 字段"
            assert "firmwareVersion" in disk, "磁盘响应缺少 firmwareVersion 字段"
            assert "logicalBlockSize" in disk, "磁盘响应缺少 logicalBlockSize 字段"
            assert "diskGroup" in disk, "磁盘响应缺少 diskGroup 字段"
            assert "diskGroupEx" in disk, "磁盘响应缺少 diskGroupEx 字段"

            # 验证字段类型
            assert isinstance(disk["name"], str), "name 应该是字符串"
            assert isinstance(disk["size"], int), "size 应该是整数"
            assert isinstance(disk["modelName"], str), "modelName 应该是字符串"
            assert isinstance(disk["serialNumber"], str), "serialNumber 应该是字符串"
            assert isinstance(disk["type"], str), "type 应该是字符串"
            assert isinstance(disk["protocol"], str), "protocol 应该是字符串"
            assert isinstance(disk["firmwareVersion"], str), "firmwareVersion 应该是字符串"
            assert isinstance(disk["logicalBlockSize"], int), "logicalBlockSize 应该是整数"
            assert isinstance(disk["diskGroup"], str), "diskGroup 应该是字符串"
            assert isinstance(disk["diskGroupEx"], str), "diskGroupEx 应该是字符串"

            # 验证值的合理性
            assert disk["size"] > 0, "size 应该是正整数"
            assert disk["logicalBlockSize"] > 0, "logicalBlockSize 应该是正整数"

            # 验证可选字段
            if "storage" in disk:
                assert isinstance(disk["storage"], list), "storage 应该是列表"

    finally:
        # 清理连接
        await client.close()


@pytest.mark.asyncio
async def test_store_list_disks_with_hot_spare():
    """测试 Store.list_disks() 方法的集成测试（包含热备盘）

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_store_list_disks.py::test_store_list_disks_with_hot_spare -m integration
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

        # 获取磁盘列表（包含热备盘）
        disks_result = await store.list_disks(no_hot_spare=False)

        # 验证响应格式（服务器可能不返回 result 字段）
        if "result" in disks_result:
            assert disks_result["result"] == "succ", f"响应结果不是成功: {disks_result}"
        assert "disk" in disks_result, "响应缺少 disk 字段"

        # 验证 disk 字段
        disk_list = disks_result["disk"]
        assert isinstance(disk_list, list), "disk 应该是列表"

    finally:
        # 清理连接
        await client.close()