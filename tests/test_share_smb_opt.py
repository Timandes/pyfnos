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

from fnos import FnosClient, Share

# 集成测试标记，用于区分需要外部依赖的测试
pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_share_smb_opt():
    """测试 Share.smb_opt() 方法的集成测试

    此测试需要：
    1. fnOS 服务运行在 127.0.0.1:5666
    2. 使用 admin/admin 账户可以登录

    运行方式：
        pytest tests/test_share_smb_opt.py -m integration
    或：
        pytest tests/test_share_smb_opt.py
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

        # 创建 Share 实例
        share = Share(client)

        # 获取 SMB 配置信息
        smb_opt_result = await share.smb_opt()

        # 验证响应格式
        assert smb_opt_result.get("result") == "succ", "响应结果不是成功"
        assert "data" in smb_opt_result, "响应缺少 data 字段"

        # 验证 data 字段
        data = smb_opt_result["data"]
        assert isinstance(data, dict), "data 应该是字典"

        # 验证必须存在的字段
        assert "smbEnable" in data, "SMB配置缺少 smbEnable 字段"
        assert "wsddEnable" in data, "SMB配置缺少 wsddEnable 字段"
        assert "mode" in data, "SMB配置缺少 mode 字段"
        assert "ipv4Addr" in data, "SMB配置缺少 ipv4Addr 字段"
        assert "svcPort" in data, "SMB配置缺少 svcPort 字段"
        assert "mount" in data, "SMB配置缺少 mount 字段"
        assert "option" in data, "SMB配置缺少 option 字段"
        assert "timeMachine" in data, "SMB配置缺少 timeMachine 字段"

        # 验证字段类型
        assert isinstance(data["smbEnable"], bool), "smbEnable 应该是布尔值"
        assert isinstance(data["wsddEnable"], bool), "wsddEnable 应该是布尔值"
        assert isinstance(data["mode"], int), "mode 应该是整数"
        assert isinstance(data["ipv4Addr"], str), "ipv4Addr 应该是字符串"
        assert isinstance(data["svcPort"], int), "svcPort 应该是整数"
        assert isinstance(data["mount"], str), "mount 应该是字符串"
        assert isinstance(data["option"], dict), "option 应该是字典"
        assert isinstance(data["timeMachine"], dict), "timeMachine 应该是字典"

        # 验证 option 字段
        option = data["option"]
        assert "workGroup" in option, "option 缺少 workGroup 字段"
        assert "oplocks" in option, "option 缺少 oplocks 字段"
        assert "ntlmv1" in option, "option 缺少 ntlmv1 字段"
        assert "serverSigning" in option, "option 缺少 serverSigning 字段"
        assert "transportEncryption" in option, "option 缺少 transportEncryption 字段"
        assert "supportSmb1" in option, "option 缺少 supportSmb1 字段"
        assert "enableFruit" in option, "option 缺少 enableFruit 字段"
        assert "enableDirSort" in option, "option 缺少 enableDirSort 字段"
        assert "enableVoteFile" in option, "option 缺少 enableVoteFile 字段"
        assert "voteFiles" in option, "option 缺少 voteFiles 字段"
        assert "deleteVoteFiles" in option, "option 缺少 deleteVoteFiles 字段"
        assert "wildcardSearchCache" in option, "option 缺少 wildcardSearchCache 字段"
        assert "winsIP" in option, "option 缺少 winsIP 字段"
        assert "disableMultiConn" in option, "option 缺少 disableMultiConn 字段"
        assert "enableMultiChannel" in option, "option 缺少 enableMultiChannel 字段"
        assert "aioWrite" in option, "option 缺少 aioWrite 字段"

        # 验证 timeMachine 字段
        time_machine = data["timeMachine"]
        assert "enable" in time_machine, "timeMachine 缺少 enable 字段"
        assert "vol" in time_machine, "timeMachine 缺少 vol 字段"
        assert "quota" in time_machine, "timeMachine 缺少 quota 字段"
        assert "folder" in time_machine, "timeMachine 缺少 folder 字段"
        assert "status" in time_machine, "timeMachine 缺少 status 字段"

        assert isinstance(time_machine["enable"], bool), "enable 应该是布尔值"
        assert isinstance(time_machine["vol"], int), "vol 应该是整数"
        assert isinstance(time_machine["quota"], int), "quota 应该是整数"
        assert isinstance(time_machine["folder"], str), "folder 应该是字符串"
        assert isinstance(time_machine["status"], int), "status 应该是整数"

    finally:
        # 清理连接
        await client.close()