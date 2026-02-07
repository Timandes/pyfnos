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

from fnos import FnosClient, Notify

# 集成测试标记，用于区分需要外部依赖的测试
pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_notify_unread_total():
    """测试 Notify.unread_total() 方法的集成测试

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_notify_unread_total.py -m integration
    或：
        pytest tests/test_notify_unread_total.py
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

        # 创建 Notify 实例
        notify = Notify(client)

        # 获取未读通知总数
        unread_total_result = await notify.unread_total()

        # 验证响应格式
        assert unread_total_result.get("result") == "succ", "响应结果不是成功"
        assert "unreadTotal" in unread_total_result, "响应缺少 unreadTotal 字段"

        # 验证字段类型
        unread_total = unread_total_result["unreadTotal"]
        assert isinstance(unread_total, int), "unreadTotal 应该是整数"

        # 验证值的合理性
        assert unread_total >= 0, "unreadTotal 应该是非负数"

    finally:
        # 清理连接
        await client.close()