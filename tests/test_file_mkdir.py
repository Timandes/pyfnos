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
async def test_file_mkdir():
    """测试 File.mkdir() 方法的集成测试

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_file_mkdir.py -m integration
    或：
        pytest tests/test_file_mkdir.py
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

        # 创建文件夹
        mkdir_result = await file_obj.mkdir(test_path)

        # 验证响应格式
        assert mkdir_result.get("result") == "succ", "响应结果不是成功"

        # 清理：删除刚创建的文件夹
        remove_result = await file_obj.remove([test_path], move_to_trashbin=False)

    finally:
        # 清理连接
        await client.close()


@pytest.mark.asyncio
async def test_file_mkdir_empty_path():
    """测试 File.mkdir() 方法使用空路径参数

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_file_mkdir.py::test_file_mkdir_empty_path -m integration
    或：
        pytest tests/test_file_mkdir.py::test_file_mkdir_empty_path
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

        # 测试空路径参数
        with pytest.raises(ValueError, match="path参数不能为空"):
            await file_obj.mkdir("")

    finally:
        # 清理连接
        await client.close()