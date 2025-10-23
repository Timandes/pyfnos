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

import json
import asyncio
from .client import FnosClient


class ResourceMonitor:
    def __init__(self, client: FnosClient):
        """
        初始化ResourceMonitor类
        
        Args:
            client: FnosClient实例
        """
        self.client = client
    
    async def cpu(self, timeout: float = 10.0) -> dict:
        """
        请求CPU资源监控信息
        
        Args:
            timeout: 请求超时时间（秒），默认为10.0秒
            
        Returns:
            dict: 服务器返回的结果
        """
        # 使用FnoClient的新方法发送请求并等待响应
        response = await self.client.request_payload_with_response("appcgi.resmon.cpu", {}, timeout)
        return response
    
    async def gpu(self, timeout: float = 10.0) -> dict:
        """
        请求GPU资源监控信息
        
        Args:
            timeout: 请求超时时间（秒），默认为10.0秒
            
        Returns:
            dict: 服务器返回的结果
        """
        # 使用FnoClient的新方法发送请求并等待响应
        response = await self.client.request_payload_with_response("appcgi.resmon.gpu", {}, timeout)
        return response
    
    async def memory(self, timeout: float = 10.0) -> dict:
        """
        请求内存资源监控信息
        
        Args:
            timeout: 请求超时时间（秒），默认为10.0秒
            
        Returns:
            dict: 服务器返回的结果
        """
        # 使用FnoClient的新方法发送请求并等待响应
        response = await self.client.request_payload_with_response("appcgi.resmon.mem", {}, timeout)
        return response