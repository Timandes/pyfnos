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
async def test_dockermgr_system_setting_get():
    """测试 DockerManager.system_setting_get() 方法的集成测试

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_dockermgr_system_setting_get.py -m integration
    或：
        pytest tests/test_dockermgr_system_setting_get.py
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

        # 获取 Docker 系统设置
        system_setting_result = await docker_mgr.system_setting_get()

        # 验证响应格式
        assert system_setting_result.get("result") == "succ", "响应结果不是成功"
        assert "rsp" in system_setting_result, "响应缺少 rsp 字段"

        # 验证 rsp 字段
        rsp_data = system_setting_result["rsp"]
        assert isinstance(rsp_data, dict), "rsp 应该是字典"

        # 验证必须存在的字段
        assert "dataRoot" in rsp_data, "系统设置缺少 dataRoot 字段"
        assert "currentMirror" in rsp_data, "系统设置缺少 currentMirror 字段"
        assert "mirrorsV2" in rsp_data, "系统设置缺少 mirrorsV2 字段"
        assert "mirrors" in rsp_data, "系统设置缺少 mirrors 字段"
        assert "autoBoot" in rsp_data, "系统设置缺少 autoBoot 字段"
        assert "status" in rsp_data, "系统设置缺少 status 字段"

        # 验证字段类型
        assert isinstance(rsp_data["dataRoot"], int), "dataRoot 应该是整数"
        assert isinstance(rsp_data["currentMirror"], str), "currentMirror 应该是字符串"
        assert isinstance(rsp_data["mirrorsV2"], list), "mirrorsV2 应该是列表"
        assert isinstance(rsp_data["mirrors"], dict), "mirrors 应该是字典"
        assert isinstance(rsp_data["autoBoot"], bool), "autoBoot 应该是布尔值"
        assert isinstance(rsp_data["status"], bool), "status 应该是布尔值"

        # 验证 mirrorsV2 字段
        for mirror in rsp_data["mirrorsV2"]:
            assert "res" in mirror, "镜像源缺少 res 字段"
            assert "url" in mirror, "镜像源缺少 url 字段"
            assert "name" in mirror, "镜像源缺少 name 字段"
            assert isinstance(mirror["res"], bool), "res 应该是布尔值"
            assert isinstance(mirror["url"], str), "url 应该是字符串"
            assert isinstance(mirror["name"], str), "name 应该是字符串"

    finally:
        # 清理连接
        await client.close()