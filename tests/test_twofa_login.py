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

import pytest

from fnos import FnosClient, User


pytestmark = pytest.mark.integration

TWOFA_USERNAME = "twofauser"
TWOFA_PASSWORD = "admin"
TWOFA_CODE = "583213"
AUTH_TIMEOUT = 20.0


@pytest.mark.asyncio
async def test_twofa_login_against_mock_server():
    """测试两步验证登录流程的集成测试

    此测试需要：
    1. fnos-mock-server 运行在 127.0.0.1:5666
    2. mock server 配置 FNOS_MOCK_TWOFA_USERS=twofauser
    3. mock server 使用验证码 583213 完成两步验证

    运行方式：
        pytest tests/test_twofa_login.py -m integration
    """
    client = FnosClient()

    try:
        await client.connect("127.0.0.1:5666")
        assert client.connected, "连接失败"

        login_result = await client.login(TWOFA_USERNAME, TWOFA_PASSWORD, timeout=AUTH_TIMEOUT)

        assert login_result.get("result") == "succ", f"登录挑战失败: {login_result}"
        assert login_result.get("twofaRequired") is True
        assert login_result.get("twofaSetupRequired") is False
        assert login_result.get("accessToken"), "两步验证挑战缺少 accessToken"
        secure_email = login_result.get("secureEmail")
        assert isinstance(secure_email, str) and secure_email, "两步验证挑战缺少安全邮箱"
        assert "*" in secure_email, "安全邮箱应该是脱敏后的地址"
        assert client.twofa_pending is not None, "客户端未保存待验证状态"

        final_result = await client.submit_twofa_code(TWOFA_CODE, trust_device=True, timeout=AUTH_TIMEOUT)

        assert final_result.get("result") == "succ", f"两步验证提交失败: {final_result}"
        assert final_result.get("token"), "最终登录响应缺少 token"
        assert final_result.get("secret"), "最终登录响应缺少 secret"
        assert client.token == final_result["token"]
        assert client.get_decrypted_secret() is not None
        assert client.twofa_pending is None, "完成两步验证后不应保留待验证状态"

        user = User(client)
        user_info = await user.getInfo()
        assert user_info.get("result") == "succ", f"登录后接口调用失败: {user_info}"

    finally:
        await client.close()
