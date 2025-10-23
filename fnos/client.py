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
import json
import time
import uuid
import base64
import random
import hashlib
import hmac
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
import websockets

class FnosClient:
    def __init__(self):
        self.ws = None
        self.public_key = None
        self.host_name = None
        self.session_id = None
        self.connected = False
        self.heartbeat_task = None
        self.stop_heartbeat = False
        self.login_response = None
        self.login_future = None
        self.decrypted_secret = None
        self.aes_key = None
        self.iv = None
        self.pending_requests = {}  # 用于存储待处理的请求
        self.on_message_callback = None  # 外部消息回调函数
        self.message_queue = asyncio.Queue()
        
    def _generate_reqid(self):
        """生成唯一的reqid"""
        # 使用时间戳和随机数来确保唯一性
        timestamp = int(time.time() * 1000000)  # 微秒级时间戳
        random_part = uuid.uuid4().hex[:16]  # 16位随机字符串
        # 格式化为指定格式: timestamp(16位) + random_part(16位)
        reqid = f"{timestamp:016x}"[:16] + random_part[:16]
        return reqid
    
    def _generate_did(self):
        """生成设备ID"""
        t = base64.b32encode(str(int(time.time() * 1000)).encode()).decode()
        e = base64.b32encode(str(random.random()).encode()).decode()[:15]
        n = base64.b32encode(str(random.random()).encode()).decode()[:15]
        return f"{t}-{e}-{n}".lower().replace('=', '')
    
    def _encrypt_login_data(self, username, password):
        """加密登录数据"""
        # 生成随机AES密钥
        self.aes_key = get_random_bytes(32)  # 256位密钥
        
        # 使用RSA公钥加密AES密钥
        rsa_key = RSA.import_key(self.public_key)
        rsa_cipher = PKCS1_v1_5.new(rsa_key)
        encrypted_aes_key = rsa_cipher.encrypt(self.aes_key)
        
        # 构造登录数据
        login_data = {
            "reqid": self._generate_reqid(),
            "user": username,
            "password": password,
            "stay": True,
            "deviceType": "Browser",
            "deviceName": "Mac OS-Safari",
            "did": self._generate_did(),
            "req": "user.login",
            "si": self.session_id
        }
        
        # 使用AES密钥加密登录数据
        json_data = json.dumps(login_data, separators=(',', ':'))
        padded_data = pad(json_data.encode('utf-8'), AES.block_size)
        
        # 生成随机IV并加密
        self.iv = get_random_bytes(16)
        aes_cipher = AES.new(self.aes_key, AES.MODE_CBC, self.iv)
        encrypted_data = aes_cipher.encrypt(padded_data)
        
        # 构造返回数据
        return {
            "req": "encrypted",
            "iv": base64.b64encode(self.iv).decode('utf-8'),
            "rsa": base64.b64encode(encrypted_aes_key).decode('utf-8'),
            "aes": base64.b64encode(encrypted_data).decode('utf-8')
        }
    
    def _decrypt_secret(self, encrypted_secret, aes_key, iv):
        """解密secret字段"""
        try:
            # 解码base64
            encrypted_data = base64.b64decode(encrypted_secret)
            iv_bytes = base64.b64decode(iv)
            key_bytes = base64.b64decode(aes_key)
            
            # 使用AES解密
            cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
            decrypted_data = cipher.decrypt(encrypted_data)
            
            # 移除填充
            from Crypto.Util.Padding import unpad
            unpadded_data = unpad(decrypted_data, AES.block_size)
            
            return unpadded_data.decode('utf-8')
        except Exception as e:
            print(f"解密secret失败: {e}")
            return None
    
    def _decrypt_login_secret(self, encrypted_secret):
        """解密登录响应中的secret字段"""
        try:
            # 使用登录时生成的AES密钥和IV解密
            aes_cipher = AES.new(self.aes_key, AES.MODE_CBC, self.iv)
            raw_secret = base64.b64decode(encrypted_secret)
            raw_decrypted_secret = aes_cipher.decrypt(raw_secret)
            
            # 移除PKCS#7填充
            unpadded_data = unpad(raw_decrypted_secret, AES.block_size)
            
            return base64.b64encode(unpadded_data).decode('utf-8')
        except Exception as e:
            print(f"解密登录secret失败: {e}")
            return None
    
    async def connect(self, endpoint):
        """连接到WebSocket服务器"""
        try:
            print("正在连接到WebSocket服务器...")
            # 创建WebSocket连接
            self.ws = await websockets.connect(f"ws://{endpoint}/websocket?type=main")
            print("websockets.connect returned")

            print("Creating async message handler...")
            # 启动消息处理任务
            self.message_task = asyncio.create_task(self._message_handler())
            print("Async message handler task created")
            
            print("Sending first request...")
            # 发送第一个请求获取RSA公钥
            await self._send_first_request()
            print("First request sent")
            
            # 注意：self.connected 将在收到公钥响应后设置为True
            # 在 _process_message 方法中处理
            
        except Exception as e:
            print(f"连接失败: {e}")
            self.connected = False
    
    async def _send_message(self, message):
        """发送消息到服务器"""
        if self.ws:  # 只需要检查WebSocket连接存在，不需要等待连接完全建立
            message_json = json.dumps(message)
            print(f"Sending message: {message_json}")
            await self.ws.send(message_json)
            
    async def _message_handler(self):
        """处理接收到的消息"""
        try:
            async for message in self.ws:
                # 首先调用外部回调函数（如果存在）
                if self.on_message_callback:
                    try:
                        self.on_message_callback(message)
                    except Exception as e:
                        print(f"外部消息回调函数出错: {e}")
                
                await self._process_message(message)
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket连接已关闭")
            self.connected = False
            self.stop_heartbeat = True
        except Exception as e:
            print(f"消息处理错误: {e}")
            
    async def _process_message(self, message):
        """处理接收到的消息"""
        try:
            data = json.loads(message)
            if "pub" in data and "reqid" in data:
                # 这是第一个请求的响应（获取RSA公钥）
                self.public_key = data["pub"]
                self.session_id = data["si"]
                print(f"已获取RSA公钥: {data['pub']}")
                print(f"会话ID: {data['si']}")
                # 设置连接状态为已连接
                self.connected = True
                print("WebSocket连接已建立")
                # 发送第二个请求
                await self._send_second_request()
            elif "data" in data and "hostName" in data:
                # 这是第二个请求的响应（获取主机名）
                self.host_name = data["data"]["hostName"]
                print(f"主机名: {self.host_name}")
                print(f"Trim版本: {data['data']['trimVersion']}")
                # 启动心跳机制
                await self._start_heartbeat()
            elif "res" in data and data["res"] == "pong":
                # 这是心跳响应
                print("收到心跳响应: pong")
            elif "uid" in data and "result" in data and data["result"] == "succ":
                # 这是登录响应
                self.login_response = data
                # 解密secret字段并保存
                if "secret" in data:
                    self.decrypted_secret = self._decrypt_login_secret(data["secret"])
                    print(f"服务器返回的secret: {self.decrypted_secret}")
                if self.login_future and not self.login_future.done():
                    self.login_future.set_result(self.login_response)
                print("登录成功")
            elif "result" in data and data["result"] == "fail":
                # 登录失败
                self.login_response = data
                if self.login_future and not self.login_future.done():
                    self.login_future.set_result(self.login_response)
                print(f"登录失败: {data.get('msg', '未知错误')}")
            else:
                # 检查消息中是否包含reqid，这可能是待处理请求的响应
                if "reqid" in data:
                    reqid = data["reqid"]
                    if reqid in self.pending_requests:
                        req_data = self.pending_requests[reqid]
                        # 从待处理请求中移除
                        del self.pending_requests[reqid]
                        # 设置响应结果
                        if not req_data['future'].done():
                            req_data['future'].set_result(data)
                        print(f"收到待处理请求的响应: {reqid}")
                    else:
                        print(f"收到未知请求ID的响应: {reqid}")
                else:
                    # 检查是否有待处理的请求在等待这个响应
                    # 这里我们简单地将所有其他消息视为请求响应
                    # 在实际应用中，可能需要更复杂的匹配机制
                    for req_id, req_data in list(self.pending_requests.items()):
                        req_data['response'] = message
                        if not req_data['future'].done():
                            req_data['future'].set_result(message)
                        break
                    print(f"收到未知消息: {message}")
        except json.JSONDecodeError:
            # 如果不是JSON格式，检查是否有待处理的请求在等待这个响应
            for req_id, req_data in list(self.pending_requests.items()):
                req_data['response'] = message
                if not req_data['future'].done():
                    req_data['future'].set_result(message)
                break
            print(f"无法解析消息: {message}")
        
    async def _send_first_request(self):
        """发送第一个请求获取RSA公钥"""
        reqid = self._generate_reqid()
        message = {
            "reqid": reqid,
            "req": "util.crypto.getRSAPub"
        }
        await self._send_message(message)
        
    async def _send_second_request(self):
        """发送第二个请求获取主机名"""
        reqid = self._generate_reqid()
        message = {
            "reqid": reqid,
            "req": "appcgi.sysinfo.getHostName"
        }
        await self._send_message(message)
        
    async def _start_heartbeat(self):
        """启动心跳机制"""
        async def heartbeat_worker():
            while not self.stop_heartbeat:
                await asyncio.sleep(30)  # 每30秒发送一次
                if self.connected:
                    message = {
                        "req": "ping"
                    }
                    await self._send_message(message)
                    print("已发送心跳请求")
        
        # 启动心跳任务
        self.heartbeat_task = asyncio.create_task(heartbeat_worker())
    
    async def login(self, username, password):
        """用户登录方法"""
        if not self.connected:
            raise Exception("未连接到服务器")
        
        if not self.public_key or not self.session_id:
            raise Exception("未获取到公钥或会话ID")
        
        # 加密登录数据
        encrypted_data = self._encrypt_login_data(username, password)
        print(f"Sending login request: {encrypted_data}")
        
        # 发送登录请求并等待响应
        self.login_future = asyncio.Future()
        await self._send_message(encrypted_data)
        
        # 等待登录响应（最多等待10秒）
        try:
            await asyncio.wait_for(self.login_future, timeout=10)
            return self.login_response
        except asyncio.TimeoutError:
            raise Exception("登录超时")
    
    def get_decrypted_secret(self):
        """获取解密后的secret"""
        return self.decrypted_secret
    
    def on_message(self, callback):
        """设置消息回调函数"""
        self.on_message_callback = callback
    
    def _iz(self, data):
        """实现HMAC-SHA256加密函数"""
        if not self.decrypted_secret:
            raise Exception("未获取到secret")
        
        # 解码base64格式的secret
        key = base64.b64decode(self.decrypted_secret)
        
        # 计算HMAC-SHA256
        hmac_result = hmac.new(key, data.encode('utf-8'), hashlib.sha256).digest()
        
        # 返回base64编码的结果
        return base64.b64encode(hmac_result).decode('utf-8')
    
    async def request(self, e):
        """发送请求"""
        if not self.connected:
            raise Exception("未连接到服务器")
        
        if not self.decrypted_secret:
            raise Exception("未获取到secret")
        
        # 计算iz(e) + e
        print(f"Sending msg: {e}")
        iz_result = self._iz(e)
        print(f"Calculated iz-result: {iz_result}")
        request_data = iz_result + e
        print(f"Sending msg to channel: {request_data}")
        
        # 发送数据
        await self.ws.send(request_data)
        print(f"已发送请求: {request_data}")
    
    async def request_payload(self, req: str, payload: dict):
        """以payload为主体，添加req和reqid后发送请求"""
        # 将req以key=req放进去
        payload_data = payload.copy()  # 创建副本避免修改原始数据
        payload_data["req"] = req
        
        # 生成请求ID以key="reqid"放进去
        reqid = self._generate_reqid()
        payload_data["reqid"] = reqid
        
        # JSON序列化之后访问request()方法完成发送
        json_data = json.dumps(payload_data, separators=(',', ':'))
        await self.request(json_data)
        
        return reqid

    async def request_payload_with_response(self, req: str, payload: dict, timeout: float = 10.0):
        """以payload为主体，添加req和reqid后发送请求，并返回响应"""
        # 创建一个Future对象来等待响应
        future = asyncio.Future()
        
        # 将请求添加到待处理请求列表
        reqid = self._generate_reqid()
        self.pending_requests[reqid] = {
            'future': future,
            'req': req,
            'payload': payload
        }
        
        # 构造请求数据
        payload_data = payload.copy()  # 创建副本避免修改原始数据
        payload_data["req"] = req
        payload_data["reqid"] = reqid
        
        # JSON序列化之后访问request()方法完成发送
        json_data = json.dumps(payload_data, separators=(',', ':'))
        await self.request(json_data)
        
        # 等待响应（最多等待指定的超时时间）
        try:
            response = await asyncio.wait_for(future, timeout=timeout)
            return response
        except asyncio.TimeoutError:
            raise Exception(f"请求 {req} 超时")
    
    async def close(self):
        """关闭WebSocket连接"""
        if self.ws:
            await self.ws.close()
            self.connected = False
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        if hasattr(self, 'message_task'):
            self.message_task.cancel()