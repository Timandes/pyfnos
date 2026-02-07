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
import time

from fnos import FnosClient, File


# 集成测试标记，用于区分需要外部依赖的测试
pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_file_remove_without_trashbin():
    """测试 File.remove() 方法（不移到回收站）的集成测试

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_file_remove.py::test_file_remove_without_trashbin -m integration
    或：
        pytest tests/test_file_remove.py::test_file_remove_without_trashbin
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

        # 创建一个测试文件夹
        test_timestamp = int(time.time())
        test_dir_name = f"test_dir_{test_timestamp}"
        test_path = f"vol1/1000/{test_dir_name}"

        # 先创建文件夹
        mkdir_result = await file_obj.mkdir(test_path)
        assert mkdir_result.get("result") == "succ", "创建文件夹失败"

        # 删除文件夹（不移到回收站）
        remove_result = await file_obj.remove([test_path], move_to_trashbin=False)

        # 验证响应格式
        assert "taskId" in remove_result, "响应缺少 taskId 字段"

        # 验证字段类型
        assert isinstance(remove_result["taskId"], str), "taskId 应该是字符串"
        assert remove_result["taskId"], "taskId 不应该为空"

    finally:
        # 清理连接
        await client.close()


@pytest.mark.asyncio
async def test_file_remove_with_trashbin():
    """测试 File.remove() 方法（移到回收站）的集成测试

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_file_remove.py::test_file_remove_with_trashbin -m integration
    或：
        pytest tests/test_file_remove.py::test_file_remove_with_trashbin
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

        # 创建一个测试文件夹
        test_timestamp = int(time.time())
        test_dir_name = f"test_dir_{test_timestamp}"
        test_path = f"vol1/1000/{test_dir_name}"

        # 先创建文件夹
        mkdir_result = await file_obj.mkdir(test_path)
        assert mkdir_result.get("result") == "succ", "创建文件夹失败"

        # 删除文件夹（移到回收站）
        remove_result = await file_obj.remove([test_path], move_to_trashbin=True)

        # 验证响应格式
        assert "taskId" in remove_result, "响应缺少 taskId 字段"

        # 验证字段类型
        assert isinstance(remove_result["taskId"], str), "taskId 应该是字符串"
        assert remove_result["taskId"], "taskId 不应该为空"

    finally:
        # 清理连接
        await client.close()


@pytest.mark.asyncio
async def test_file_remove_empty_files():
    """测试 File.remove() 方法使用空文件列表参数

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_file_remove.py::test_file_remove_empty_files -m integration
    或：
        pytest tests/test_file_remove.py::test_file_remove_empty_files
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

        # 测试空文件列表参数
        with pytest.raises(ValueError, match="files参数必须是非空列表"):
            await file_obj.remove([])

    finally:
        # 清理连接
        await client.close()


@pytest.mark.asyncio
async def test_file_remove_invalid_files_type():
    """测试 File.remove() 方法使用无效的 files 参数类型

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_file_remove.py::test_file_remove_invalid_files_type -m integration
    或：
        pytest tests/test_file_remove.py::test_file_remove_invalid_files_type
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

        # 测试无效的 files 参数类型
        with pytest.raises(ValueError, match="files参数必须是非空列表"):
            await file_obj.remove("not_a_list")

    finally:
        # 清理连接
        await client.close()