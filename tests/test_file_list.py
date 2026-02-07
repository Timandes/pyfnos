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

from fnos import FnosClient, File


# 集成测试标记，用于区分需要外部依赖的测试
pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_file_list_default():
    """测试 File.list() 方法（默认路径）的集成测试

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_file_list.py::test_file_list_default -m integration
    或：
        pytest tests/test_file_list.py::test_file_list_default
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

        # 创建 File 实例
        file_obj = File(client)

        # 获取文件列表（默认路径）
        list_result = await file_obj.list()

        # 验证响应格式
        assert "files" in list_result, "响应缺少 files 字段"

        # 验证 files 字段
        files = list_result["files"]
        assert isinstance(files, list), "files 应该是列表"

        # 验证可选字段
        if len(files) > 0:
            first_file = files[0]
            assert "name" in first_file, "文件对象缺少 name 字段"
            assert "uid" in first_file, "文件对象缺少 uid 字段"
            assert "mtim" in first_file, "文件对象缺少 mtim 字段"
            assert "btim" in first_file, "文件对象缺少 btim 字段"

            # 验证字段类型
            assert isinstance(first_file["name"], str), "name 应该是字符串"
            assert isinstance(first_file["uid"], int), "uid 应该是整数"
            assert isinstance(first_file["mtim"], int), "mtim 应该是整数"
            assert isinstance(first_file["btim"], int), "btim 应该是整数"

            # 验证值的合理性
            assert first_file["name"], "name 不应该为空"
            assert first_file["uid"] >= 0, "uid 应该是非负数"
            assert first_file["mtim"] > 0, "mtim 应该是正整数"
            assert first_file["btim"] > 0, "btim 应该是正整数"

            # 验证可选字段
            if "dir" in first_file:
                assert isinstance(first_file["dir"], int), "dir 应该是整数"

            if "size" in first_file:
                assert isinstance(first_file["size"], int), "size 应该是整数"
                assert first_file["size"] >= 0, "size 应该是非负数"

            if "v" in first_file:
                assert isinstance(first_file["v"], int), "v 应该是整数"
                assert first_file["v"] > 0, "v 应该是正整数"

    finally:
        # 清理连接
        await client.close()


@pytest.mark.asyncio
async def test_file_list_with_path():
    """测试 File.list(path) 方法（指定路径）的集成测试

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_file_list.py::test_file_list_with_path -m integration
    或：
        pytest tests/test_file_list.py::test_file_list_with_path
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

        # 创建 File 实例
        file_obj = File(client)

        # 先获取默认路径的文件列表
        default_list_result = await file_obj.list()

        # 如果有文件夹，测试指定路径
        if "files" in default_list_result and len(default_list_result["files"]) > 0:
            for file_item in default_list_result["files"]:
                if "dir" in file_item:
                    # 找到第一个文件夹
                    test_path = f"vol{file_item.get('v', 1)}/1000/{file_item['name']}"
                    list_path_result = await file_obj.list(test_path)

                    # 验证响应格式
                    assert "files" in list_path_result, "响应缺少 files 字段"
                    assert isinstance(list_path_result["files"], list), "files 应该是列表"
                    break
        else:
            pytest.skip("没有找到文件夹进行指定路径测试")

    finally:
        # 清理连接
        await client.close()