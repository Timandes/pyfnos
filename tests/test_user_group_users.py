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
async def test_user_group_users():
    """测试 User.groupUsers() 方法的集成测试

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_user_group_users.py -m integration
    或：
        pytest tests/test_user_group_users.py
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

        # 获取用户分组信息
        group_users_result = await user.groupUsers()

        # 验证响应格式
        assert group_users_result.get("result") == "succ", "响应结果不是成功"
        assert "groups" in group_users_result, "响应缺少 groups 字段"

        # 验证 groups 字段
        groups = group_users_result["groups"]
        assert isinstance(groups, list), "groups 应该是列表"
        assert len(groups) > 0, "groups 列表不应该为空"

        # 验证第一个组的基本字段
        first_group = groups[0]
        assert "group" in first_group, "组对象缺少 group 字段"
        assert "gid" in first_group, "组对象缺少 gid 字段"
        assert isinstance(first_group["group"], str), "group 应该是字符串"
        assert isinstance(first_group["gid"], int), "gid 应该是整数"
        assert first_group["group"], "group 不应该为空"
        assert first_group["gid"] > 0, "gid 应该是正整数"

        # 验证可选字段
        if "users" in first_group:
            users_list = first_group["users"]
            assert isinstance(users_list, list), "users 应该是列表"
            for uid in users_list:
                assert isinstance(uid, int), f"uid '{uid}' 应该是整数"
                assert uid >= 0, f"uid '{uid}' 应该是非负数"

    finally:
        # 清理连接
        await client.close()