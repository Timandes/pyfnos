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
async def test_store_calculate_space():
    """测试 Store.calculate_space() 方法的集成测试

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_store_calculate_space.py -m integration
    或：
        pytest tests/test_store_calculate_space.py
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

        # 计算存储空间
        calc_space_result = await store.calculate_space()

        # 验证响应格式
        assert calc_space_result.get("result") == "succ", "响应结果不是成功"
        assert "fssizeSys" in calc_space_result, "响应缺少 fssizeSys 字段"
        assert "frsizeSys" in calc_space_result, "响应缺少 frsizeSys 字段"
        assert "sysDiskType" in calc_space_result, "响应缺少 sysDiskType 字段"
        assert "storTotal" in calc_space_result, "响应缺少 storTotal 字段"
        assert "fssizeStor" in calc_space_result, "响应缺少 fssizeStor 字段"
        assert "frsizeStor" in calc_space_result, "响应缺少 frsizeStor 字段"
        assert "HDD" in calc_space_result, "响应缺少 HDD 字段"
        assert "SSD" in calc_space_result, "响应缺少 SSD 字段"
        assert "USB" in calc_space_result, "响应缺少 USB 字段"

        # 验证字段类型
        assert isinstance(calc_space_result["fssizeSys"], int), "fssizeSys 应该是整数"
        assert isinstance(calc_space_result["frsizeSys"], int), "frsizeSys 应该是整数"
        assert isinstance(calc_space_result["sysDiskType"], str), "sysDiskType 应该是字符串"
        assert isinstance(calc_space_result["storTotal"], int), "storTotal 应该是整数"
        assert isinstance(calc_space_result["fssizeStor"], int), "fssizeStor 应该是整数"
        assert isinstance(calc_space_result["frsizeStor"], int), "frsizeStor 应该是整数"
        assert isinstance(calc_space_result["HDD"], int), "HDD 应该是整数"
        assert isinstance(calc_space_result["SSD"], int), "SSD 应该是整数"
        assert isinstance(calc_space_result["USB"], int), "USB 应该是整数"

        # 验证值的合理性
        assert calc_space_result["fssizeSys"] >= 0, "fssizeSys 应该是非负数"
        assert calc_space_result["frsizeSys"] >= 0, "frsizeSys 应该是非负数"
        assert calc_space_result["frsizeSys"] <= calc_space_result["fssizeSys"], \
            "frsizeSys 不应该大于 fssizeSys"
        assert calc_space_result["storTotal"] >= 0, "storTotal 应该是非负数"
        assert calc_space_result["fssizeStor"] >= 0, "fssizeStor 应该是非负数"
        assert calc_space_result["frsizeStor"] >= 0, "frsizeStor 应该是非负数"
        assert calc_space_result["frsizeStor"] <= calc_space_result["fssizeStor"], \
            "frsizeStor 不应该大于 fssizeStor"
        assert calc_space_result["HDD"] >= 0, "HDD 应该是非负数"
        assert calc_space_result["SSD"] >= 0, "SSD 应该是非负数"
        assert calc_space_result["USB"] >= 0, "USB 应该是非负数"

        # 验证磁盘数量关系
        assert calc_space_result["HDD"] + calc_space_result["SSD"] + calc_space_result["USB"] >= \
            calc_space_result["storTotal"], "磁盘总数应该大于等于存储设备数"

        # 验证 sysDiskType 是有效值
        valid_disk_types = ["SSD", "HDD", "USB", "NVMe", "SATA", "SAS"]
        assert calc_space_result["sysDiskType"] in valid_disk_types, \
            f"sysDiskType 应该是有效值，当前值: {calc_space_result['sysDiskType']}"

    finally:
        # 清理连接
        await client.close()