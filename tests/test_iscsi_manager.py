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

from fnos import FnosClient, IscsiManager


# 集成测试标记，用于区分需要外部依赖的测试
pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_iscsi_manager_get_config():
    """测试 IscsiManager.get_config() 方法的集成测试

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_iscsi_manager.py -m integration
    或：
        pytest tests/test_iscsi_manager.py
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

        # 创建 IscsiManager 实例
        iscsi = IscsiManager(client)

        # 获取 iSCSI 配置
        result = await iscsi.get_config()

        # 验证响应格式
        assert result.get("result") == "succ", "响应结果不是成功"
        assert "data" in result, "响应缺少 data 字段"

        # 验证 data 字段
        data = result["data"]
        assert "port" in data, "响应缺少 port 字段"
        assert "queueDepth" in data, "响应缺少 queueDepth 字段"
        assert "chap" in data, "响应缺少 chap 字段"
        assert "mutualChap" in data, "响应缺少 mutualChap 字段"

        # 验证字段类型
        assert isinstance(data["port"], int), "port 应该是整数"
        assert isinstance(data["queueDepth"], int), "queueDepth 应该是整数"
        assert isinstance(data["chap"], bool), "chap 应该是布尔值"
        assert isinstance(data["mutualChap"], bool), "mutualChap 应该是布尔值"

    finally:
        # 清理连接
        await client.close()


@pytest.mark.asyncio
async def test_iscsi_manager_list_initiators():
    """测试 IscsiManager.list_initiators() 方法的集成测试"""
    client = FnosClient()

    try:
        await client.connect("127.0.0.1:5666")
        assert client.connected, "连接失败"

        login_result = await client.login("admin", "admin")
        assert login_result.get("result") == "succ", f"登录失败: {login_result}"

        iscsi = IscsiManager(client)

        result = await iscsi.list_initiators()

        assert result.get("result") == "succ", "响应结果不是成功"
        assert "data" in result, "响应缺少 data 字段"

        data = result["data"]
        assert "totalCount" in data, "响应缺少 totalCount 字段"
        assert isinstance(data["totalCount"], int), "totalCount 应该是整数"

    finally:
        await client.close()


@pytest.mark.asyncio
async def test_iscsi_manager_list_luns():
    """测试 IscsiManager.list_luns() 方法的集成测试"""
    client = FnosClient()

    try:
        await client.connect("127.0.0.1:5666")
        assert client.connected, "连接失败"

        login_result = await client.login("admin", "admin")
        assert login_result.get("result") == "succ", f"登录失败: {login_result}"

        iscsi = IscsiManager(client)

        result = await iscsi.list_luns()

        assert result.get("result") == "succ", "响应结果不是成功"
        assert "data" in result, "响应缺少 data 字段"

        data = result["data"]
        assert "luns" in data, "响应缺少 luns 字段"
        assert isinstance(data["luns"], list), "luns 应该是列表"

        # 如果有 LUN 数据，验证每个 LUN 的字段
        for lun in data["luns"]:
            assert "lunName" in lun, "LUN 响应缺少 lunName 字段"
            assert "lunSize" in lun, "LUN 响应缺少 lunSize 字段"
            assert "wwn" in lun, "LUN 响应缺少 wwn 字段"
            assert isinstance(lun["lunSize"], int), "lunSize 应该是整数"
            assert isinstance(lun["lunName"], str), "lunName 应该是字符串"
            assert isinstance(lun["wwn"], str), "wwn 应该是字符串"

    finally:
        await client.close()


@pytest.mark.asyncio
async def test_iscsi_manager_list_lun_usergroups():
    """测试 IscsiManager.list_lun_usergroups() 方法的集成测试"""
    client = FnosClient()

    try:
        await client.connect("127.0.0.1:5666")
        assert client.connected, "连接失败"

        login_result = await client.login("admin", "admin")
        assert login_result.get("result") == "succ", f"登录失败: {login_result}"

        iscsi = IscsiManager(client)

        result = await iscsi.list_lun_usergroups(lun_name="", wwn="")

        assert result.get("result") == "succ", "响应结果不是成功"
        assert "data" in result, "响应缺少 data 字段"

        data = result["data"]
        assert "permState" in data, "响应缺少 permState 字段"
        assert isinstance(data["permState"], int), "permState 应该是整数"

    finally:
        await client.close()


@pytest.mark.asyncio
async def test_iscsi_manager_list_targets():
    """测试 IscsiManager.list_targets() 方法的集成测试"""
    client = FnosClient()

    try:
        await client.connect("127.0.0.1:5666")
        assert client.connected, "连接失败"

        login_result = await client.login("admin", "admin")
        assert login_result.get("result") == "succ", f"登录失败: {login_result}"

        iscsi = IscsiManager(client)

        result = await iscsi.list_targets()

        assert result.get("result") == "succ", "响应结果不是成功"
        assert "data" in result, "响应缺少 data 字段"

        data = result["data"]
        assert "targets" in data, "响应缺少 targets 字段"
        assert isinstance(data["targets"], list), "targets 应该是列表"

        # 如果有 target 数据，验证每个 target 的字段
        for target in data["targets"]:
            assert "targetName" in target, "Target 响应缺少 targetName 字段"
            assert "iqn" in target, "Target 响应缺少 iqn 字段"
            assert isinstance(target["targetName"], str), "targetName 应该是字符串"
            assert isinstance(target["iqn"], str), "iqn 应该是字符串"

    finally:
        await client.close()
