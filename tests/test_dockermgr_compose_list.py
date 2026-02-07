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
async def test_dockermgr_list_composes():
    """测试 DockerManager.list_composes() 方法的集成测试

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_dockermgr_compose_list.py -m integration
    或：
        pytest tests/test_dockermgr_compose_list.py
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

        # 获取 Docker Compose 项目列表
        compose_list_result = await docker_mgr.list_composes()

        # 验证响应格式
        assert compose_list_result.get("result") == "succ", "响应结果不是成功"
        assert "rsp" in compose_list_result, "响应缺少 rsp 字段"

        # 验证 rsp 字段
        rsp_data = compose_list_result["rsp"]
        assert isinstance(rsp_data, list), "rsp 应该是列表"

        # 如果没有项目，跳过详细验证
        if len(rsp_data) == 0:
            pytest.skip("没有 Docker Compose 项目")

        # 如果有项目数据，验证每个项目的字段
        for item in rsp_data:
            assert "Created" in item, "项目响应缺少 Created 字段"
            assert "Name" in item, "项目响应缺少 Name 字段"
            assert "ConfigFiles" in item, "项目响应缺少 ConfigFiles 字段"
            assert "Folder" in item, "项目响应缺少 Folder 字段"
            assert "Status" in item, "项目响应缺少 Status 字段"
            assert "Containers" in item, "项目响应缺少 Containers 字段"

            # 验证字段类型
            assert isinstance(item["Created"], int), "Created 应该是整数"
            assert isinstance(item["Name"], str), "Name 应该是字符串"
            assert isinstance(item["ConfigFiles"], str), "ConfigFiles 应该是字符串"
            assert isinstance(item["Folder"], str), "Folder 应该是字符串"
            assert isinstance(item["Status"], str), "Status 应该是字符串"
            assert isinstance(item["Containers"], dict), "Containers 应该是字典"

            # 验证 Containers 字段
            containers = item["Containers"]
            assert "total" in containers, "Containers 缺少 total 字段"
            assert isinstance(containers["total"], int), "total 应该是整数"
            # running 字段可能不存在（如果所有容器都已停止）
            if "running" in containers:
                assert isinstance(containers["running"], int), "running 应该是整数"
            # 其他可选字段
            if "exited" in containers:
                assert isinstance(containers["exited"], int), "exited 应该是整数"

    finally:
        # 清理连接
        await client.close()