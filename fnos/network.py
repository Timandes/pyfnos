# Copyright 2025 Timandes White
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# you may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import asyncio
import logging
from .client import FnosClient

# 创建logger实例
logger = logging.getLogger(__name__)


class Network:
    def __init__(self, client: FnosClient):
        """
        初始化Network类
        
        Args:
            client: FnosClient实例
        """
        self.client = client
    
    async def list(self, type: int = 0, timeout: float = 10.0) -> dict:
        """
        列出网络信息
        
        Args:
            type: 网络类型，可选值为0和1，默认为0
            timeout: 请求超时时间（秒），默认为10.0秒
            
        Returns:
            dict: 服务器返回的结果
        """
        # 验证type参数
        if type not in [0, 1]:
            raise ValueError("type参数必须为0或1")
        
        # 构造请求参数
        payload = {"type": type}
        
        # 使用FnoClient的新方法发送请求并等待响应
        response = await self.client.request_payload_with_response("appcgi.network.net.list", payload, timeout)
        return response
    
    async def detect(self, if_name: str, timeout: float = 10.0) -> dict:
        """
        检测网络接口
        
        Args:
            if_name: 网络接口名称
            timeout: 请求超时时间（秒），默认为10.0秒
            
        Returns:
            dict: 服务器返回的结果
        """
        # 构造请求参数
        payload = {"ifName": if_name}
        
        # 使用FnoClient的新方法发送请求并等待响应
        response = await self.client.request_payload_with_response("appcgi.network.net.detect", payload, timeout)
        return response