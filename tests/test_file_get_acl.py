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
async def test_file_get_acl():
    """测试 File.get_acl() 方法的集成测试

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_file_get_acl.py -m integration
    或：
        pytest tests/test_file_get_acl.py
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

        # 获取文件 ACL 信息
        get_acl_result = await file_obj.get_acl(["vol2/@team/data", "vol2/@team/files"])

        # 验证响应格式
        assert get_acl_result.get("result") == "succ", "响应结果不是成功"
        assert "data" in get_acl_result, "响应缺少 data 字段"

        # 验证 data 字段
        data = get_acl_result["data"]
        assert isinstance(data, list), "data 应该是列表"

        # 如果有 ACL 数据，验证每个文件 ACL 的字段
        for acl_item in data:
            assert "defaultPermset" in acl_item, "ACL 缺少 defaultPermset 字段"
            assert "permset" in acl_item, "ACL 缺少 permset 字段"

            # 验证字段类型
            assert isinstance(acl_item["defaultPermset"], list), "defaultPermset 应该是列表"
            assert isinstance(acl_item["permset"], list), "permset 应该是列表"

            # 验证 permset 字段
            for perm_item in acl_item["permset"]:
                # 验证至少有一个权限字段存在
                assert len(perm_item) >= 1, "权限项应该至少有一个键值对"

                # 验证键的类型和值
                for key, value in perm_item.items():
                    # 验证键的有效性
                    if key in ["owner", "group", "other"]:
                        # 这些键的值应该是权限值
                        assert isinstance(value, int), f"{key} 的值应该是整数"
                    elif key in ["uid", "gid"]:
                        # 这些键表示用户/组ID，应该搭配 perm 字段
                        assert isinstance(value, int), f"{key} 的值应该是整数"
                        assert "perm" in perm_item, f"存在 {key} 但缺少 perm 字段"
                    elif key == "perm":
                        # perm 是权限值，应该搭配 uid 或 gid
                        assert isinstance(value, int), "perm 的值应该是整数"
                        assert any(k in ["uid", "gid"] for k in perm_item.keys()), "存在 perm 但缺少 uid 或 gid 字段"
                    else:
                        assert False, f"无效的权限键: {key}"

    finally:
        # 清理连接
        await client.close()