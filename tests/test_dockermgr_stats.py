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

from fnos import FnosClient, DockerManager

# 集成测试标记，用于区分需要外部依赖的测试
pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_dockermgr_stats():
    """测试 DockerManager.stats() 方法的集成测试

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_dockermgr_stats.py -m integration
    或：
        pytest tests/test_dockermgr_stats.py
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

        # 创建 DockerManager 实例
        docker_mgr = DockerManager(client)

        # 获取容器统计信息
        stats_result = await docker_mgr.stats()

        # 验证响应格式
        assert stats_result.get("result") == "succ", "响应结果不是成功"
        assert "rsp" in stats_result, "响应缺少 rsp 字段"

        # 验证 rsp 字段
        rsp_data = stats_result["rsp"]
        assert isinstance(rsp_data, dict), "rsp 应该是字典"

        # 如果有统计数据，验证每个容器的统计字段
        for container_id, stats in rsp_data.items():
            assert isinstance(container_id, str), "容器ID应该是字符串"
            assert "cpuUsage" in stats, f"容器 {container_id} 缺少 cpuUsage 字段"
            assert "usedMem" in stats, f"容器 {container_id} 缺少 usedMem 字段"
            assert "networkRx" in stats, f"容器 {container_id} 缺少 networkRx 字段"
            assert "networkTx" in stats, f"容器 {container_id} 缺少 networkTx 字段"

            # 验证字段类型
            assert isinstance(stats["cpuUsage"], (int, float)), "cpuUsage 应该是数字"
            assert isinstance(stats["usedMem"], int), "usedMem 应该是整数"
            assert isinstance(stats["networkRx"], int), "networkRx 应该是整数"
            assert isinstance(stats["networkTx"], int), "networkTx 应该是整数"

            # 验证值的合理性
            assert stats["cpuUsage"] >= 0, "cpuUsage 应该是非负数"
            assert stats["usedMem"] >= 0, "usedMem 应该是非负数"
            assert stats["networkRx"] >= 0, "networkRx 应该是非负数"
            assert stats["networkTx"] >= 0, "networkTx 应该是非负数"

    finally:
        # 清理连接
        await client.close()