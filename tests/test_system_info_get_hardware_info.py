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
async def test_system_info_get_hardware_info():
    """测试 SystemInfo.get_hardware_info() 方法的集成测试

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_system_info_get_hardware_info.py -m integration
    或：
        pytest tests/test_system_info_get_hardware_info.py
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

        # 获取硬件信息
        hardware_info_result = await system_info.get_hardware_info()

        # 验证响应格式
        assert hardware_info_result.get("result") == "succ", "响应结果不是成功"
        assert "data" in hardware_info_result, "响应缺少 data 字段"

        # 验证 data 字段
        data = hardware_info_result["data"]
        assert "cpu" in data, "data 响应缺少 cpu 字段"
        assert "mem" in data, "data 响应缺少 mem 字段"
        assert "bios" in data, "data 响应缺少 bios 字段"
        assert "sysdisk" in data, "data 响应缺少 sysdisk 字段"

        # 验证 cpu 字段
        cpu = data["cpu"]
        assert "name" in cpu, "cpu 响应缺少 name 字段"
        assert "num" in cpu, "cpu 响应缺少 num 字段"
        assert "core" in cpu, "cpu 响应缺少 core 字段"
        assert "thread" in cpu, "cpu 响应缺少 thread 字段"
        assert isinstance(cpu["name"], str), "cpu.name 应该是字符串"
        assert isinstance(cpu["num"], int), "cpu.num 应该是整数"
        assert isinstance(cpu["core"], int), "cpu.core 应该是整数"
        assert isinstance(cpu["thread"], int), "cpu.thread 应该是整数"
        assert cpu["num"] > 0, "cpu.num 应该是正整数"
        assert cpu["core"] > 0, "cpu.core 应该是正整数"
        assert cpu["thread"] > 0, "cpu.thread 应该是正整数"

        # 验证 mem 字段
        mem = data["mem"]
        assert "num" in mem, "mem 响应缺少 num 字段"
        assert "total" in mem, "mem 响应缺少 total 字段"
        assert "frequency" in mem, "mem 响应缺少 frequency 字段"
        assert "type" in mem, "mem 响应缺少 type 字段"
        assert "vendor" in mem, "mem 响应缺少 vendor 字段"
        assert isinstance(mem["num"], int), "mem.num 应该是整数"
        assert isinstance(mem["total"], int), "mem.total 应该是整数"
        assert isinstance(mem["frequency"], int), "mem.frequency 应该是整数"
        assert isinstance(mem["type"], str), "mem.type 应该是字符串"
        assert isinstance(mem["vendor"], str), "mem.vendor 应该是字符串"
        assert mem["num"] > 0, "mem.num 应该是正整数"
        assert mem["total"] > 0, "mem.total 应该是正整数"

        # 验证 bios 字段
        bios = data["bios"]
        assert "vendor" in bios, "bios 响应缺少 vendor 字段"
        assert "version" in bios, "bios 响应缺少 version 字段"
        assert "baseboard" in bios, "bios 响应缺少 baseboard 字段"
        assert "system" in bios, "bios 响应缺少 system 字段"
        assert isinstance(bios["vendor"], str), "bios.vendor 应该是字符串"
        assert isinstance(bios["version"], str), "bios.version 应该是字符串"

        # 验证 sysdisk 字段
        sysdisk = data["sysdisk"]
        assert "size" in sysdisk, "sysdisk 响应缺少 size 字段"
        assert "model" in sysdisk, "sysdisk 响应缺少 model 字段"
        assert "protocol" in sysdisk, "sysdisk 响应缺少 protocol 字段"
        assert "serialNumber" in sysdisk, "sysdisk 响应缺少 serialNumber 字段"
        assert isinstance(sysdisk["size"], int), "sysdisk.size 应该是整数"
        assert isinstance(sysdisk["model"], str), "sysdisk.model 应该是字符串"
        assert isinstance(sysdisk["protocol"], str), "sysdisk.protocol 应该是字符串"
        assert isinstance(sysdisk["serialNumber"], str), "sysdisk.serialNumber 应该是字符串"
        assert sysdisk["size"] >= 0, "sysdisk.size 应该是非负数"

        # 验证可选字段
        if "gpu" in data:
            gpu_list = data["gpu"]
            assert isinstance(gpu_list, list), "gpu 应该是列表"

        if "vm" in data:
            vm = data["vm"]
            assert isinstance(vm, dict), "vm 应该是字典"
            if "available" in vm:
                assert isinstance(vm["available"], int), "vm.available 应该是整数"
            if "iommu" in vm:
                assert isinstance(vm["iommu"], int), "vm.iommu 应该是整数"
            if "sriov" in vm:
                assert isinstance(vm["sriov"], int), "vm.sriov 应该是整数"

    finally:
        # 清理连接
        await client.close()