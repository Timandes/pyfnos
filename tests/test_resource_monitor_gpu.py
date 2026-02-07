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
async def test_resmon_gpu():
    """测试 ResourceMonitor.gpu() 方法的集成测试

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_resource_monitor_gpu.py -m integration
    或：
        pytest tests/test_resource_monitor_gpu.py
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

        # 获取 GPU 资源信息
        gpu_result = await resource_monitor.gpu()

        # 验证响应格式
        assert gpu_result.get("result") == "succ", "响应结果不是成功"
        assert "data" in gpu_result, "响应缺少 data 字段"
        assert "gpu" in gpu_result["data"], "响应缺少 gpu 字段"
        assert "num" in gpu_result["data"], "响应缺少 num 字段"

        # 验证 num 字段
        num = gpu_result["data"]["num"]
        assert isinstance(num, int), "num 应该是整数"
        assert num >= 0, "num 应该是非负数"

        # 验证 gpu 列表
        gpu_list = gpu_result["data"]["gpu"]
        assert isinstance(gpu_list, list), "gpu 应该是列表"

        # 如果有 GPU，验证每个 GPU 的字段
        for gpu_item in gpu_list:
            assert "index" in gpu_item, "GPU 响应缺少 index 字段"
            assert "vendor" in gpu_item, "GPU 响应缺少 vendor 字段"
            assert "device" in gpu_item, "GPU 响应缺少 device 字段"
            assert "busy" in gpu_item, "GPU 响应缺少 busy 字段"
            assert "ram" in gpu_item, "GPU 响应缺少 ram 字段"
            assert "temp" in gpu_item, "GPU 响应缺少 temp 字段"

            # 验证字段类型
            assert isinstance(gpu_item["index"], int), "index 应该是整数"
            assert isinstance(gpu_item["vendor"], str), "vendor 应该是字符串"
            assert isinstance(gpu_item["device"], str), "device 应该是字符串"
            assert isinstance(gpu_item["busy"], (int, float)), "busy 应该是数字"
            assert isinstance(gpu_item["ram"], dict), "ram 应该是字典"
            assert isinstance(gpu_item["temp"], (int, float)), "temp 应该是数字"

            # 验证 ram 字段结构
            ram_data = gpu_item["ram"]
            assert "total" in ram_data, "ram 响应缺少 total 字段"
            assert "used" in ram_data, "ram 响应缺少 used 字段"
            assert "free" in ram_data, "ram 响应缺少 free 字段"

            # 验证 ram 字段类型
            assert isinstance(ram_data["total"], int), "ram.total 应该是整数"
            assert isinstance(ram_data["used"], int), "ram.used 应该是整数"
            assert isinstance(ram_data["free"], int), "ram.free 应该是整数"

            # 验证 ram 值的合理性
            assert ram_data["total"] >= 0, "ram.total 应该是非负数"
            assert ram_data["used"] >= 0, "ram.used 应该是非负数"
            assert ram_data["free"] >= 0, "ram.free 应该是非负数"
            assert ram_data["total"] == ram_data["used"] + ram_data["free"], \
                "ram.total 应该等于 ram.used + ram.free"

            # 验证可选字段
            if "vendorId" in gpu_item:
                assert isinstance(gpu_item["vendorId"], int), "vendorId 应该是整数"
            if "deviceId" in gpu_item:
                assert isinstance(gpu_item["deviceId"], int), "deviceId 应该是整数"
            if "subDeviceId" in gpu_item:
                assert isinstance(gpu_item["subDeviceId"], int), "subDeviceId 应该是整数"
            if "engine" in gpu_item:
                assert isinstance(gpu_item["engine"], dict), "engine 应该是字典"

    finally:
        # 清理连接
        await client.close()
