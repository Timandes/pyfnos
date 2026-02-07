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

from fnos import FnosClient, SAC


# 集成测试标记，用于区分需要外部依赖的测试
pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_sac_ups_status():
    """测试 SAC.ups_status() 方法的集成测试

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_sac_ups_status.py -m integration
    或：
        pytest tests/test_sac_ups_status.py
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

        # 创建 SAC 实例
        sac = SAC(client)

        # 获取 UPS 状态信息
        ups_status_result = await sac.ups_status()

        # 验证响应格式
        if "result" in ups_status_result:
            assert ups_status_result.get("result") == "succ", "响应结果不是成功"

        assert "data" in ups_status_result, "响应缺少 data 字段"

        # 验证 data 字段
        data = ups_status_result["data"]
        assert "upsEnabled" in data, "data 响应缺少 upsEnabled 字段"
        assert "upsType" in data, "data 响应缺少 upsType 字段"
        assert "upsTypeName" in data, "data 响应缺少 upsTypeName 字段"
        assert "shutdownUpsEnabled" in data, "data 响应缺少 shutdownUpsEnabled 字段"
        assert "currentUps" in data, "data 响应缺少 currentUps 字段"

        # 验证字段类型
        assert isinstance(data["upsEnabled"], bool), "upsEnabled 应该是布尔值"
        assert isinstance(data["upsType"], str), "upsType 应该是字符串"
        assert isinstance(data["upsTypeName"], str), "upsTypeName 应该是字符串"
        assert isinstance(data["shutdownUpsEnabled"], bool), "shutdownUpsEnabled 应该是布尔值"
        assert isinstance(data["currentUps"], dict), "currentUps 应该是字典"

        # 验证 currentUps 字段
        current_ups = data["currentUps"]
        assert "name" in current_ups, "currentUps 响应缺少 name 字段"
        assert "vendor" in current_ups, "currentUps 响应缺少 vendor 字段"
        assert "product" in current_ups, "currentUps 响应缺少 product 字段"
        assert "vendorId" in current_ups, "currentUps 响应缺少 vendorId 字段"
        assert "productId" in current_ups, "currentUps 响应缺少 productId 字段"
        assert "status" in current_ups, "currentUps 响应缺少 status 字段"
        assert "batteryCharge" in current_ups, "currentUps 响应缺少 batteryCharge 字段"
        assert "powerSupplyType" in current_ups, "currentUps 响应缺少 powerSupplyType 字段"
        assert "runtime" in current_ups, "currentUps 响应缺少 runtime 字段"
        assert "shutdownPolicyType" in current_ups, "currentUps 响应缺少 shutdownPolicyType 字段"
        assert "shutdownPolicyOnBattValue" in current_ups, "currentUps 响应缺少 shutdownPolicyOnBattValue 字段"
        assert "shutdownPolicyLowBattValue" in current_ups, "currentUps 响应缺少 shutdownPolicyLowBattValue 字段"
        assert "shutdownPolicyUnit" in current_ups, "currentUps 响应缺少 shutdownPolicyUnit 字段"
        assert "batteryCapacity" in current_ups, "currentUps 响应缺少 batteryCapacity 字段"

        # 验证字段类型
        assert isinstance(current_ups["name"], str), "currentUps.name 应该是字符串"
        assert isinstance(current_ups["vendor"], str), "currentUps.vendor 应该是字符串"
        assert isinstance(current_ups["product"], str), "currentUps.product 应该是字符串"
        assert isinstance(current_ups["vendorId"], str), "currentUps.vendorId 应该是字符串"
        assert isinstance(current_ups["productId"], str), "currentUps.productId 应该是字符串"
        assert isinstance(current_ups["status"], bool), "currentUps.status 应该是布尔值"
        assert isinstance(current_ups["batteryCharge"], str), "currentUps.batteryCharge 应该是字符串"
        assert isinstance(current_ups["powerSupplyType"], str), "currentUps.powerSupplyType 应该是字符串"
        assert isinstance(current_ups["runtime"], str), "currentUps.runtime 应该是字符串"
        assert isinstance(current_ups["shutdownPolicyType"], str), "currentUps.shutdownPolicyType 应该是字符串"
        assert isinstance(current_ups["shutdownPolicyOnBattValue"], int), "currentUps.shutdownPolicyOnBattValue 应该是整数"
        assert isinstance(current_ups["shutdownPolicyLowBattValue"], int), "currentUps.shutdownPolicyLowBattValue 应该是整数"
        assert isinstance(current_ups["shutdownPolicyUnit"], str), "currentUps.shutdownPolicyUnit 应该是字符串"
        assert isinstance(current_ups["batteryCapacity"], str), "currentUps.batteryCapacity 应该是字符串"

    finally:
        # 清理连接
        await client.close()