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
async def test_dockermgr_list_containers():
    """测试 DockerManager.list_containers() 方法的集成测试

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_dockermgr_container_list.py -m integration
    或：
        pytest tests/test_dockermgr_container_list.py
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

        # 获取容器列表（包含所有容器）
        container_list_result = await docker_mgr.list_containers(all=True)

        # 验证响应格式
        assert container_list_result.get("result") == "succ", "响应结果不是成功"
        assert "rsp" in container_list_result, "响应缺少 rsp 字段"

        # 验证 rsp 字段
        rsp_data = container_list_result["rsp"]
        assert isinstance(rsp_data, list), "rsp 应该是列表"

        # 如果有容器数据，验证每个容器的字段
        for item in rsp_data:
            assert "Id" in item, "容器响应缺少 Id 字段"
            assert "Command" in item, "容器响应缺少 Command 字段"
            assert "Created" in item, "容器响应缺少 Created 字段"
            assert "HostConfig" in item, "容器响应缺少 HostConfig 字段"
            assert "Image" in item, "容器响应缺少 Image 字段"
            assert "ImageID" in item, "容器响应缺少 ImageID 字段"
            assert "Names" in item, "容器响应缺少 Names 字段"
            assert "State" in item, "容器响应缺少 State 字段"
            assert "Status" in item, "容器响应缺少 Status 字段"
            assert "Project" in item, "容器响应缺少 Project 字段"
            assert "Icon" in item, "容器响应缺少 Icon 字段"

            # 验证字段类型
            assert isinstance(item["Id"], str), "Id 应该是字符串"
            assert isinstance(item["Command"], str), "Command 应该是字符串"
            assert isinstance(item["Created"], int), "Created 应该是整数"
            assert isinstance(item["HostConfig"], dict), "HostConfig 应该是字典"
            assert isinstance(item["Image"], str), "Image 应该是字符串"
            assert isinstance(item["ImageID"], str), "ImageID 应该是字符串"
            assert isinstance(item["Names"], list), "Names 应该是列表"
            assert isinstance(item["State"], str), "State 应该是字符串"
            assert isinstance(item["Status"], str), "Status 应该是字符串"
            assert isinstance(item["Project"], str), "Project 应该是字符串"
            assert isinstance(item["Icon"], str), "Icon 应该是字符串"

            # 验证可选的 Ports 字段
            if "Ports" in item:
                assert isinstance(item["Ports"], list), "Ports 应该是列表"

    finally:
        # 清理连接
        await client.close()