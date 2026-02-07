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

from fnos import FnosClient, EventLogger

# 集成测试标记，用于区分需要外部依赖的测试
pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_eventlogger_common_list():
    """测试 EventLogger.common_list() 方法的集成测试

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_eventlogger_common_list.py -m integration
    或：
        pytest tests/test_eventlogger_common_list.py
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

        # 创建 EventLogger 实例
        event_logger = EventLogger(client)

        # 获取事件日志列表
        event_list_result = await event_logger.common_list()

        # 验证响应格式
        assert event_list_result.get("result") == "succ", "响应结果不是成功"
        assert "data" in event_list_result, "响应缺少 data 字段"

        # 验证 data 字段
        data = event_list_result["data"]
        assert isinstance(data, dict), "data 应该是字典"
        assert "total" in data, "data 缺少 total 字段"
        assert "rows" in data, "data 缺少 rows 字段"

        # 验证字段类型
        assert isinstance(data["total"], int), "total 应该是整数"
        assert isinstance(data["rows"], list), "rows 应该是列表"

        # 如果有事件数据，验证每个事件的字段
        for event in data["rows"]:
            assert "level" in event, "事件缺少 level 字段"
            assert "module" in event, "事件缺少 module 字段"
            assert "id" in event, "事件缺少 id 字段"
            assert "eventtm" in event, "事件缺少 eventtm 字段"
            assert "username" in event, "事件缺少 username 字段"
            assert "content" in event, "事件缺少 content 字段"

            # 验证字段类型
            assert isinstance(event["level"], int), "level 应该是整数"
            assert isinstance(event["module"], int), "module 应该是整数"
            assert isinstance(event["id"], int), "id 应该是整数"
            assert isinstance(event["eventtm"], int), "eventtm 应该是整数"
            assert isinstance(event["username"], str), "username 应该是字符串"
            assert isinstance(event["content"], str), "content 应该是字符串"

            # 验证值的合理性
            assert event["id"] > 0, "id 应该是正整数"
            assert event["eventtm"] > 0, "eventtm 应该是正整数"

    finally:
        # 清理连接
        await client.close()