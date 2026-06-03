import argparse
import asyncio
import unittest

from examples.common import login_with_twofa


class TestExampleCommon(unittest.TestCase):
    def test_login_with_twofa_uses_args_code_and_trust_device(self):
        """示例登录helper应使用args中的验证码和信任设备参数"""

        class FakeClient:
            def __init__(self):
                self.submitted_code = None
                self.submitted_trust_device = None

            async def login(self, username, password):
                self.username = username
                self.password = password
                return {
                    "result": "succ",
                    "twofaRequired": True,
                    "twofaSetupRequired": False,
                    "secureEmail": "tim*****@gmail.com",
                    "accessToken": "access-token",
                }

            async def submit_twofa_code(self, code, trust_device=False):
                self.submitted_code = code
                self.submitted_trust_device = trust_device
                return {
                    "result": "succ",
                    "token": "token",
                    "secret": "secret",
                }

        async def run_test():
            client = FakeClient()
            args = argparse.Namespace(
                user="alice",
                password="password",
                code="583213",
                trust_device=True,
            )

            result = await login_with_twofa(client, args)

            self.assertEqual(result["token"], "token")
            self.assertEqual(client.username, "alice")
            self.assertEqual(client.password, "password")
            self.assertEqual(client.submitted_code, "583213")
            self.assertTrue(client.submitted_trust_device)

        asyncio.run(run_test())
