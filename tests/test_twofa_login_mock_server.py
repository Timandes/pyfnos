"""Two-factor login integration tests backed by fnos-mock-server."""

import pytest

from fnos import FnosClient


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_twofa_login_with_mock_server(fnos_twofa_mock_endpoint):
    """已绑定2FA账号应先返回challenge，提交验证码后完成登录"""
    client = FnosClient()

    try:
        await client.connect(fnos_twofa_mock_endpoint)

        result = await client.login("admin", "admin")
        assert result["result"] == "succ"
        assert result["twofaRequired"] is True
        assert result["twofaSetupRequired"] is False
        assert result["accessToken"]
        assert result["secureEmail"] == "tim*****@gmail.com"

        final_result = await client.submit_twofa_code("583213", trust_device=True)
        assert final_result["result"] == "succ"
        assert "token" in final_result
        assert "secret" in final_result
        assert client.token == final_result["token"]
        assert client.decrypted_secret is not None
        assert client.twofa_pending is None

        user_info = await client.request_payload_with_response("user.info", {})
        assert user_info["result"] == "succ"
    finally:
        await client.close()
