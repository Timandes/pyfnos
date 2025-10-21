import websocket
import json
import time
import threading
import uuid
import base64
import random
import hashlib
import hmac
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

class FnosClient:
    def __init__(self):
        self.ws = None
        self.public_key = None
        self.host_name = None
        self.session_id = None
        self.connected = False
        self.heartbeat_thread = None
        self.stop_heartbeat = False
        self.login_response = None
        self.login_event = threading.Event()
        self.decrypted_secret = None
        self.aes_key = None
        self.iv = None
        self.pending_requests = {}  # 用于存储待处理的请求
        self.on_message_callback = None  # 外部消息回调函数
        
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
    
    def connect(self):
        """连接到WebSocket服务器"""
        try:
            print("正在连接到WebSocket服务器...")
            # 创建WebSocket连接
            self.ws = websocket.WebSocketApp(
                "ws://nas-9.timandes.net:5666/websocket?type=main",
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                on_open=self._on_open
            )
            
            # 启动WebSocket连接（设置超时）
            self.ws.run_forever()
            
        except Exception as e:
            print(f"连接失败: {e}")
            self.connected = False
        
    def _send_message(self, message):
        """发送消息到服务器"""
        if self.ws and self.connected:
            self.ws.send(json.dumps(message))
            
    def _on_message(self, ws, message):
        """处理接收到的消息"""
        # 首先调用外部回调函数（如果存在）
        if self.on_message_callback:
            try:
                self.on_message_callback(message)
            except Exception as e:
                print(f"外部消息回调函数出错: {e}")
        
        try:
            data = json.loads(message)
            if "pub" in data and "reqid" in data:
                # 这是第一个请求的响应（获取RSA公钥）
                self.public_key = data["pub"]
                self.session_id = data["si"]
                print(f"已获取RSA公钥: {data['pub']}")
                print(f"会话ID: {data['si']}")
                # 发送第二个请求
                self._send_second_request()
            elif "data" in data and "hostName" in data["data"]:
                # 这是第二个请求的响应（获取主机名）
                self.host_name = data["data"]["hostName"]
                print(f"主机名: {self.host_name}")
                print(f"Trim版本: {data['data']['trimVersion']}")
                # 启动心跳机制
                self._start_heartbeat()
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
                self.login_event.set()
                print("登录成功")
            elif "result" in data and data["result"] == "fail":
                # 登录失败
                self.login_response = data
                self.login_event.set()
                print(f"登录失败: {data.get('msg', '未知错误')}")
            else:
                # 检查是否有待处理的请求在等待这个响应
                # 这里我们简单地将所有其他消息视为请求响应
                # 在实际应用中，可能需要更复杂的匹配机制
                for req_id, req_data in list(self.pending_requests.items()):
                    req_data['response'] = message
                    req_data['event'].set()
                    break
                print(f"收到未知消息: {message}")
        except json.JSONDecodeError:
            # 如果不是JSON格式，检查是否有待处理的请求在等待这个响应
            for req_id, req_data in list(self.pending_requests.items()):
                req_data['response'] = message
                req_data['event'].set()
                break
            print(f"无法解析消息: {message}")
        
    def _on_error(self, ws, error):
        """处理错误"""
        print(f"WebSocket错误: {error}")
        
    def _on_close(self, ws, close_status_code, close_msg):
        """处理连接关闭"""
        print("WebSocket连接已关闭")
        self.connected = False
        self.stop_heartbeat = True
        
    def _on_open(self, ws):
        """处理连接打开"""
        print("WebSocket连接已建立")
        self.connected = True
        # 发送第一个请求获取RSA公钥
        self._send_first_request()
        
    def _send_first_request(self):
        """发送第一个请求获取RSA公钥"""
        reqid = self._generate_reqid()
        message = {
            "reqid": reqid,
            "req": "util.crypto.getRSAPub"
        }
        self._send_message(message)
        
    def _send_second_request(self):
        """发送第二个请求获取主机名"""
        reqid = self._generate_reqid()
        message = {
            "reqid": reqid,
            "req": "appcgi.sysinfo.getHostName"
        }
        self._send_message(message)
        
    def _start_heartbeat(self):
        """启动心跳机制"""
        def heartbeat_worker():
            while not self.stop_heartbeat:
                time.sleep(30)  # 每30秒发送一次
                if self.connected:
                    message = {
                        "req": "ping"
                    }
                    self._send_message(message)
                    print("已发送心跳请求")
        
        # 启动心跳线程
        self.heartbeat_thread = threading.Thread(target=heartbeat_worker, daemon=True)
        self.heartbeat_thread.start()
    
    def login(self, username, password):
        """用户登录方法"""
        if not self.connected:
            raise Exception("未连接到服务器")
        
        if not self.public_key or not self.session_id:
            raise Exception("未获取到公钥或会话ID")
        
        # 加密登录数据
        encrypted_data = self._encrypt_login_data(username, password)
        print(f"Sending login request: {encrypted_data}")
        
        # 发送登录请求并等待响应
        self.login_event.clear()
        self._send_message(encrypted_data)
        
        # 等待登录响应（最多等待10秒）
        if self.login_event.wait(10):
            return self.login_response
        else:
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
    
    def request(self, e):
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
        self.ws.send(request_data)
        print(f"已发送请求: {request_data}")
    
    def request_payload(self, req: str, payload: dict):
        """以payload为主体，添加req和reqid后发送请求"""
        # 将req以key=req放进去
        payload_data = payload.copy()  # 创建副本避免修改原始数据
        payload_data["req"] = req
        
        # 生成请求ID以key="reqid"放进去
        payload_data["reqid"] = self._generate_reqid()
        
        # JSON序列化之后访问request()方法完成发送
        json_data = json.dumps(payload_data, separators=(',', ':'))
        self.request(json_data)