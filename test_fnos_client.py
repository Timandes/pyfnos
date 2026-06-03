import unittest
import base64
import hashlib
import hmac
import threading
from Crypto.Random import get_random_bytes
from fnos import FnosClient

class TestFnosClient(unittest.TestCase):
    def test_reqid_generation(self):
        """测试reqid生成机制"""
        client = FnosClient()
        reqid1 = client._generate_reqid()
        reqid2 = client._generate_reqid()

        # 检查reqid是否为字符串
        self.assertIsInstance(reqid1, str)
        self.assertIsInstance(reqid2, str)

        # 检查reqid长度是否正确（25位：13位时间戳 + 12位随机字符串）
        self.assertEqual(len(reqid1), 25)
        self.assertEqual(len(reqid2), 25)

        # 检查两次生成的reqid是否不同
        self.assertNotEqual(reqid1, reqid2)
    
    def test_did_generation(self):
        """测试设备ID生成机制"""
        client = FnosClient()
        did1 = client._generate_did()
        did2 = client._generate_did()
        
        # 检查did是否为字符串
        self.assertIsInstance(did1, str)
        self.assertIsInstance(did2, str)
        
        # 检查两次生成的did是否不同
        self.assertNotEqual(did1, did2)
        
        # 检查格式是否正确（包含两个连字符）
        self.assertEqual(did1.count('-'), 2)
        self.assertEqual(did2.count('-'), 2)
    
    def test_iz_function(self):
        """测试iz函数"""
        client = FnosClient()
        # 设置一个测试用的secret
        test_secret = base64.b64encode(b"test_secret_key").decode('utf-8')
        client.decrypted_secret = test_secret
        
        # 测试iz函数
        result = client._iz("test_data")
        
        # 验证结果是base64编码的字符串
        self.assertIsInstance(result, str)
        
        # 验证结果不是空的
        self.assertNotEqual(result, "")
        
        # 验证结果是base64格式
        try:
            base64.b64decode(result)
        except Exception:
            self.fail("iz函数返回的不是有效的base64字符串")
    
    def test_iz_function_calibration(self):
        """校准测试iz函数：特定输入输出验证"""
        client = FnosClient()
        # 设置指定的secret值
        client.decrypted_secret = "J3sfIMwxGV+SxHpaQFiZbw=="
        
        # 设置指定的输入数据
        test_data = '{"reqid":"68f6d99868f6d996000000020004","req":"user.info"}'
        
        # 调用iz函数
        result = client._iz(test_data)
        
        # 验证结果是否与预期相符
        expected_result = "tktNU6xPp/h/RNu3xtIAXg5m0YFVM17nZvT/x6uc2ek="
        self.assertEqual(result, expected_result, 
                         f"iz函数结果不匹配。期望: {expected_result}, 实际: {result}")
    
    def test_on_message_callback(self):
        """测试on_message回调功能"""
        client = FnosClient()
        
        # 验证on_message方法存在
        self.assertTrue(hasattr(client, 'on_message'))
        self.assertTrue(callable(getattr(client, 'on_message')))
        
        # 验证可以设置回调函数
        def test_callback(message):
            pass
        
        client.on_message(test_callback)
        self.assertEqual(client.on_message_callback, test_callback)
    
    def test_request_method_signature(self):
        """测试request方法的签名"""
        client = FnosClient()
        # 设置一个测试用的secret
        test_secret = base64.b64encode(b"test_secret_key").decode('utf-8')
        client.decrypted_secret = test_secret
        
        # 验证方法存在且可调用
        self.assertTrue(hasattr(client, 'request'))
        self.assertTrue(callable(getattr(client, 'request')))
    
    def test_decrypt_login_secret(self):
        """测试_decrypt_login_secret方法"""
        client = FnosClient()

        # 设置测试用的AES密钥和IV（模拟登录时生成的）
        from Crypto.Cipher import AES
        from Crypto.Random import get_random_bytes

        # 生成测试用的密钥和IV
        client.aes_key = base64.b64decode("OWlTcnVncnNxdDNRcWV0TjNaNWJRajJ3U3loOGRvS1g=")#get_random_bytes(32)  # 256位密钥
        client.iv = base64.b64decode("Spsb/LIwxCGz5aEbR5lbBQ==")#get_random_bytes(16)

        # 设置指定的输入数据
        test_data = 'AEslF1tKUjAMjeQNx+dffr2BwCn9oYjzYgWn9FZysyA='

        # 调用iz函数
        result = client._decrypt_login_secret(test_data)

        # 验证结果是否与预期相符
        expected_result = "WyYXbAbR4gnL3DgXdiwJbw=="
        self.assertEqual(result, expected_result,
                         f"iz函数结果不匹配。期望: {expected_result}, 实际: {result}")

    def test_final_login_success_accepts_token_and_secret_without_long_token(self):
        """最终登录成功不应依赖longToken字段"""
        client = FnosClient()

        response = {
            "uid": 1001,
            "admin": True,
            "secret": "encrypted-secret",
            "token": "short-token",
            "result": "succ",
            "reqid": "6a1ee1ca00000000000000000004",
        }

        self.assertTrue(client._is_final_login_success(response))

    def test_twofa_challenge_detection_for_bound_untrusted_device(self):
        """已绑定2FA且当前设备不可信时应该识别为验证码挑战"""
        client = FnosClient()

        response = {
            "isTwofaEnforced": True,
            "isBindTwofaSecret": True,
            "isBindSecureEmail": True,
            "secureEmail": "tim*****@gmail.com",
            "isTrustedDevice": False,
            "accessToken": "tNSYygumSut0IDJCypvre5YQsOJeYQir",
            "result": "succ",
            "reqid": "6a1ee1b700000000000000000003",
        }

        self.assertTrue(client._is_twofa_challenge(response))
        self.assertFalse(client._is_twofa_setup_challenge(response))

    def test_twofa_setup_detection_for_enforced_unbound_account(self):
        """强制2FA但未绑定TOTP时应该识别为setup挑战"""
        client = FnosClient()

        response = {
            "isTwofaEnforced": True,
            "isBindTwofaSecret": False,
            "isBindSecureEmail": False,
            "isTrustedDevice": False,
            "accessToken": "setup-access-token",
            "twofaSecret": "secret-for-qr",
            "otpauth": "otpauth://totp/fnOS",
            "result": "succ",
            "reqid": "setup-reqid",
        }

        self.assertFalse(client._is_twofa_challenge(response))
        self.assertTrue(client._is_twofa_setup_challenge(response))

    def test_handle_final_login_success_stores_optional_long_token(self):
        """最终登录响应应保存token并允许longToken缺失"""
        client = FnosClient()
        client._decrypt_login_secret = lambda encrypted_secret: "decrypted-secret"

        response = {
            "uid": 1001,
            "secret": "encrypted-secret",
            "token": "short-token",
            "result": "succ",
            "reqid": "final-reqid",
        }

        result = client._handle_final_login_success(response)

        self.assertEqual(result, response)
        self.assertEqual(client.decrypted_secret, "decrypted-secret")
        self.assertEqual(client.token, "short-token")
        self.assertIsNone(client.long_token)
        self.assertIsNone(client.twofa_pending)

    def test_encrypt_login_data_uses_configurable_device_context(self):
        """login payload应接受stay/deviceType/deviceName参数并委托通用加密方法"""
        client = FnosClient()
        client.session_id = "session-123"
        client._generate_reqid = lambda: "login-reqid"
        client._generate_did = lambda: "device-id"
        captured_payload = {}

        def fake_encrypt_auth_data(payload):
            captured_payload.update(payload)
            return {"req": "encrypted", "payload": payload}

        client._encrypt_auth_data = fake_encrypt_auth_data

        encrypted = client._encrypt_login_data(
            "alice",
            "password",
            stay=False,
            device_type="CLI",
            device_name="pytest-device",
        )

        self.assertEqual(encrypted["req"], "encrypted")
        self.assertEqual(client.login_reqid, "login-reqid")
        self.assertEqual(captured_payload["req"], "user.login")
        self.assertEqual(captured_payload["reqid"], "login-reqid")
        self.assertEqual(captured_payload["user"], "alice")
        self.assertEqual(captured_payload["password"], "password")
        self.assertFalse(captured_payload["stay"])
        self.assertEqual(captured_payload["deviceType"], "CLI")
        self.assertEqual(captured_payload["deviceName"], "pytest-device")
        self.assertEqual(captured_payload["did"], "device-id")
        self.assertEqual(captured_payload["si"], "session-123")

    def test_process_message_routes_twofa_challenge_to_login_future(self):
        """2FA challenge响应应完成login_future并保存pending上下文"""
        import asyncio
        import json

        async def run_test():
            client = FnosClient()
            future = asyncio.Future()
            client.login_future = future
            client.login_reqid = "login-reqid"

            response = {
                "isTwofaEnforced": True,
                "isBindTwofaSecret": True,
                "isBindSecureEmail": True,
                "secureEmail": "tim*****@gmail.com",
                "isTrustedDevice": False,
                "accessToken": "access-token",
                "result": "succ",
                "reqid": "login-reqid",
            }

            await client._process_message(json.dumps(response))

            self.assertTrue(future.done())
            result = future.result()
            self.assertTrue(result["twofaRequired"])
            self.assertFalse(result["twofaSetupRequired"])
            self.assertEqual(client.twofa_pending["accessToken"], "access-token")

        asyncio.run(run_test())

    def test_process_message_routes_twofa_setup_challenge_to_login_future(self):
        """强制但未绑定2FA响应应完成login_future并标记setup required"""
        import asyncio
        import json

        async def run_test():
            client = FnosClient()
            future = asyncio.Future()
            client.login_future = future
            client.login_reqid = "setup-reqid"

            response = {
                "isTwofaEnforced": True,
                "isBindTwofaSecret": False,
                "isBindSecureEmail": False,
                "isTrustedDevice": False,
                "accessToken": "setup-access-token",
                "twofaSecret": "secret-for-qr",
                "otpauth": "otpauth://totp/fnOS",
                "result": "succ",
                "reqid": "setup-reqid",
            }

            await client._process_message(json.dumps(response))

            self.assertTrue(future.done())
            result = future.result()
            self.assertFalse(result["twofaRequired"])
            self.assertTrue(result["twofaSetupRequired"])
            self.assertEqual(client.twofa_pending["accessToken"], "setup-access-token")

        asyncio.run(run_test())

    def test_process_message_accepts_final_login_without_long_token(self):
        """最终登录响应没有longToken时也应完成login_future"""
        import asyncio
        import json

        async def run_test():
            client = FnosClient()
            client._decrypt_login_secret = lambda encrypted_secret: "decrypted-secret"
            future = asyncio.Future()
            client.login_future = future

            response = {
                "uid": 1001,
                "secret": "encrypted-secret",
                "token": "short-token",
                "result": "succ",
                "reqid": "final-reqid",
            }

            await client._process_message(json.dumps(response))

            self.assertTrue(future.done())
            self.assertEqual(future.result(), response)
            self.assertEqual(client.decrypted_secret, "decrypted-secret")
            self.assertEqual(client.token, "short-token")
            self.assertIsNone(client.long_token)

        asyncio.run(run_test())

    def test_process_message_routes_successful_twofa_response_to_twofa_future(self):
        """2FA成功响应应完成twofa_future并保存登录凭据"""
        import asyncio
        import json

        async def run_test():
            client = FnosClient()
            client._decrypt_login_secret = lambda encrypted_secret: "decrypted-secret"
            future = asyncio.Future()
            client.twofa_future = future
            client.twofa_reqid = "twofa-reqid"
            client.twofa_pending = {"accessToken": "access-token"}

            response = {
                "uid": 1001,
                "admin": True,
                "secret": "encrypted-secret",
                "token": "short-token",
                "result": "succ",
                "reqid": "twofa-reqid",
            }

            await client._process_message(json.dumps(response))

            self.assertTrue(future.done())
            self.assertEqual(future.result(), response)
            self.assertEqual(client.decrypted_secret, "decrypted-secret")
            self.assertEqual(client.token, "short-token")
            self.assertIsNone(client.twofa_pending)

        asyncio.run(run_test())

    def test_submit_twofa_code_requires_pending_challenge(self):
        """没有pending 2FA上下文时不能提交验证码"""
        import asyncio

        async def run_test():
            client = FnosClient()
            client.connected = True
            client.public_key = "public-key"
            client.session_id = "session-id"

            with self.assertRaises(Exception) as context:
                await client.submit_twofa_code("583213")

            self.assertIn("没有待完成的两步验证登录", str(context.exception))

        asyncio.run(run_test())

    def test_submit_twofa_code_rejects_non_six_digit_code(self):
        """验证码必须是6位数字"""
        import asyncio

        async def run_test():
            client = FnosClient()
            client.connected = True
            client.public_key = "public-key"
            client.session_id = "session-id"
            client.twofa_pending = {"accessToken": "access-token"}

            with self.assertRaises(ValueError) as context:
                await client.submit_twofa_code("abc123")

            self.assertIn("两步验证码必须是6位数字", str(context.exception))

        asyncio.run(run_test())

    def test_submit_twofa_code_builds_login_verify_payload(self):
        """submit_twofa_code应发送user.2fa.loginVerify payload"""
        import asyncio

        async def run_test():
            client = FnosClient()
            client.connected = True
            client.public_key = "public-key"
            client.session_id = "session-id"
            client.twofa_pending = {
                "accessToken": "access-token",
                "username": "alice",
                "stay": False,
                "deviceType": "CLI",
                "deviceName": "pytest-device",
            }
            client._generate_reqid = lambda: "twofa-reqid"
            client._generate_did = lambda: "device-id"
            captured_payload = {}
            sent_message = {}

            def fake_encrypt_auth_data(payload):
                captured_payload.update(payload)
                return {"req": "encrypted", "payload": payload}

            async def fake_send_message(message):
                sent_message.update(message)
                client.twofa_future.set_result({
                    "result": "fail",
                    "errno": 135168,
                    "reqid": "twofa-reqid",
                })

            client._encrypt_auth_data = fake_encrypt_auth_data
            client._send_message = fake_send_message

            response = await client.submit_twofa_code("583213", trust_device=True)

            self.assertEqual(response["errno"], 135168)
            self.assertEqual(sent_message["req"], "encrypted")
            self.assertEqual(captured_payload["req"], "user.2fa.loginVerify")
            self.assertEqual(captured_payload["reqid"], "twofa-reqid")
            self.assertEqual(captured_payload["code"], "583213")
            self.assertTrue(captured_payload["isTrustedDevice"])
            self.assertEqual(captured_payload["accessToken"], "access-token")
            self.assertEqual(captured_payload["stay"], 0)
            self.assertEqual(captured_payload["deviceName"], "pytest-device")
            self.assertEqual(captured_payload["deviceType"], "CLI")
            self.assertEqual(captured_payload["did"], "device-id")
            self.assertEqual(captured_payload["si"], "session-id")
            self.assertIsNone(client.twofa_reqid)
            self.assertIsNone(client.twofa_future)

        asyncio.run(run_test())

    def test_gethostname_response_routes_to_correct_future(self):
        """测试getHostName响应应该正确传递给对应的future"""
        import asyncio

        async def run_test():
            client = FnosClient()

            # 创建一个Future来等待getHostName响应
            future = asyncio.Future()

            # 模拟添加一个待处理的getHostName请求
            test_reqid = "123456789012345678901234567"
            client.pending_requests[test_reqid] = {
                'future': future,
                'req': 'appcgi.sysinfo.getHostName',
                'payload': {}
            }

            # 模拟收到一个getHostName响应
            response = {
                "reqid": test_reqid,
                "req": "appcgi.sysinfo.getHostName",
                "result": "succ",
                "data": {
                    "hostName": "test-host",
                    "trimVersion": "1.0.0"
                }
            }

            # 处理消息
            import json
            await client._process_message(json.dumps(response))

            # 验证future被正确设置
            self.assertTrue(future.done(), "Future应该被设置为完成状态")

            # 验证响应内容正确
            result = future.result()
            self.assertEqual(result["data"]["hostName"], "test-host")
            self.assertEqual(result["reqid"], test_reqid)

            # 验证pending_requests中的请求被移除
            self.assertNotIn(test_reqid, client.pending_requests)

        # 运行异步测试
        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
