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