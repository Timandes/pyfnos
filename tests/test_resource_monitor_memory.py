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

from fnos import FnosClient, ResourceMonitor


# 集成测试标记，用于区分需要外部依赖的测试
pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_resmon_memory():
    """测试 ResourceMonitor.memory() 方法的集成测试

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_resource_monitor_memory.py -m integration
    或：
        pytest tests/test_resource_monitor_memory.py
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

        # 创建 ResourceMonitor 实例
        resource_monitor = ResourceMonitor(client)

        # 获取内存资源信息
        memory_result = await resource_monitor.memory()

        # 验证响应格式
        assert memory_result.get("result") == "succ", "响应结果不是成功"
        assert "data" in memory_result, "响应缺少 data 字段"
        assert "mem" in memory_result["data"], "响应缺少 mem 字段"
        assert "swap" in memory_result["data"], "响应缺少 swap 字段"

        # 验证 mem 字段结构
        mem_data = memory_result["data"]["mem"]
        assert "reserved" in mem_data, "mem 响应缺少 reserved 字段"
        assert "total" in mem_data, "mem 响应缺少 total 字段"
        assert "free" in mem_data, "mem 响应缺少 free 字段"
        assert "used" in mem_data, "mem 响应缺少 used 字段"
        assert "available" in mem_data, "mem 响应缺少 available 字段"
        assert "cached" in mem_data, "mem 响应缺少 cached 字段"
        assert "buffers" in mem_data, "mem 响应缺少 buffers 字段"

        # 验证 swap 字段结构
        swap_data = memory_result["data"]["swap"]
        assert "total" in swap_data, "swap 响应缺少 total 字段"
        assert "free" in swap_data, "swap 响应缺少 free 字段"
        assert "used" in swap_data, "swap 响应缺少 used 字段"

        # 验证 mem 字段类型
        assert isinstance(mem_data["reserved"], int), "mem.reserved 应该是整数"
        assert isinstance(mem_data["total"], int), "mem.total 应该是整数"
        assert isinstance(mem_data["free"], int), "mem.free 应该是整数"
        assert isinstance(mem_data["used"], int), "mem.used 应该是整数"
        assert isinstance(mem_data["available"], int), "mem.available 应该是整数"
        assert isinstance(mem_data["cached"], int), "mem.cached 应该是整数"
        assert isinstance(mem_data["buffers"], int), "mem.buffers 应该是整数"

        # 验证 swap 字段类型
        assert isinstance(swap_data["total"], int), "swap.total 应该是整数"
        assert isinstance(swap_data["free"], int), "swap.free 应该是整数"
        assert isinstance(swap_data["used"], int), "swap.used 应该是整数"

        # 验证内存值的合理性（应该都是非负数）
        assert mem_data["reserved"] >= 0, "mem.reserved 应该是非负数"
        assert mem_data["total"] >= 0, "mem.total 应该是非负数"
        assert mem_data["free"] >= 0, "mem.free 应该是非负数"
        assert mem_data["used"] >= 0, "mem.used 应该是非负数"
        assert mem_data["available"] >= 0, "mem.available 应该是非负数"
        assert mem_data["cached"] >= 0, "mem.cached 应该是非负数"
        assert mem_data["buffers"] >= 0, "mem.buffers 应该是非负数"

        # 验证 swap 值的合理性（应该都是非负数）
        assert swap_data["total"] >= 0, "swap.total 应该是非负数"
        assert swap_data["free"] >= 0, "swap.free 应该是非负数"
        assert swap_data["used"] >= 0, "swap.used 应该是非负数"

        # 验证内存关系：total >= used, total >= free
        assert mem_data["total"] >= mem_data["used"], "total 应该大于等于 used"
        assert mem_data["total"] >= mem_data["free"], "total 应该大于等于 free"

        # 验证 swap 关系：total = free + used
        assert swap_data["total"] == swap_data["free"] + swap_data["used"], \
            "swap.total 应该等于 swap.free + swap.used"

    finally:
        # 清理连接
        await client.close()