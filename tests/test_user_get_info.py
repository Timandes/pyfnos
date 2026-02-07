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

from fnos import FnosClient, User


# 集成测试标记，用于区分需要外部依赖的测试
pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_user_get_info():
    """测试 User.getInfo() 方法的集成测试

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_user_get_info.py -m integration
    或：
        pytest tests/test_user_get_info.py
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

        # 创建 User 实例
        user = User(client)

        # 获取用户信息
        get_info_result = await user.getInfo()

        # 验证响应格式
        assert get_info_result.get("result") == "succ", "响应结果不是成功"
        assert "data" in get_info_result, "响应缺少 data 字段"

        # 验证 data 字段
        data = get_info_result["data"]
        assert "uid" in data, "data 响应缺少 uid 字段"
        assert "name" in data, "data 响应缺少 name 字段"
        assert "isAdmin" in data, "data 响应缺少 isAdmin 字段"
        assert "groups" in data, "data 响应缺少 groups 字段"

        # 验证字段类型
        assert isinstance(data["uid"], int), "uid 应该是整数"
        assert isinstance(data["name"], str), "name 应该是字符串"
        assert isinstance(data["isAdmin"], bool), "isAdmin 应该是布尔值"
        assert isinstance(data["groups"], list), "groups 应该是列表"

        # 验证值的合理性
        assert data["uid"] > 0, "uid 应该是正整数"
        assert data["name"], "name 不应该为空"
        assert len(data["groups"]) > 0, "groups 列表不应该为空"

        # 验证 groups 列表中的元素是字符串
        for group in data["groups"]:
            assert isinstance(group, str), f"group '{group}' 应该是字符串"

    finally:
        # 清理连接
        await client.close()