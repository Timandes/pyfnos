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

from fnos import FnosClient, SystemInfo


# 集成测试标记，用于区分需要外部依赖的测试
pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_system_info_get_trim_version():
    """测试 SystemInfo.get_trim_version() 方法的集成测试

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_system_info_get_trim_version.py -m integration
    或：
        pytest tests/test_system_info_get_trim_version.py
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

        # 创建 SystemInfo 实例
        system_info = SystemInfo(client)

        # 获取 Trim 版本信息
        trim_version_result = await system_info.get_trim_version()

        # 验证响应格式
        assert trim_version_result.get("result") == "succ", "响应结果不是成功"
        assert "data" in trim_version_result, "响应缺少 data 字段"

        # 验证 data 字段
        data = trim_version_result["data"]
        assert "trimVersion" in data, "data 响应缺少 trimVersion 字段"

        # 验证字段类型
        assert isinstance(data["trimVersion"], str), "trimVersion 应该是字符串"

        # 验证值的合理性
        assert data["trimVersion"], "trimVersion 不应该为空"

    finally:
        # 清理连接
        await client.close()