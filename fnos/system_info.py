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


class SystemInfo:
    def __init__(self, client: FnosClient):
        """
        初始化SystemInfo类
        
        Args:
            client: FnosClient实例
        """
        self.client = client
    
    async def get_host_name(self, timeout: float = 10.0) -> dict:
        """
        请求主机名信息
        
        Args:
            timeout: 请求超时时间（秒），默认为10.0秒
            
        Returns:
            dict: 服务器返回的结果
        """
        # 使用FnoClient的新方法发送请求并等待响应
        response = await self.client.request_payload_with_response("appcgi.sysinfo.getHostName", {}, timeout)
        return response
    
    async def get_trim_version(self, timeout: float = 10.0) -> dict:
        """
        请求Trim版本信息
        
        Args:
            timeout: 请求超时时间（秒），默认为10.0秒
            
        Returns:
            dict: 服务器返回的结果
        """
        # 使用FnoClient的新方法发送请求并等待响应
        response = await self.client.request_payload_with_response("appcgi.sysinfo.getTrimVersion", {}, timeout)
        return response
    
    async def get_machine_id(self, timeout: float = 10.0) -> dict:
        """
        请求机器ID信息
        
        Args:
            timeout: 请求超时时间（秒），默认为10.0秒
            
        Returns:
            dict: 服务器返回的结果
        """
        # 使用FnoClient的新方法发送请求并等待响应
        response = await self.client.request_payload_with_response("appcgi.sysinfo.getMachineId", {}, timeout)
        return response
    
    async def get_hardware_info(self, timeout: float = 10.0) -> dict:
        """
        请求硬件信息
        
        Args:
            timeout: 请求超时时间（秒），默认为10.0秒
            
        Returns:
            dict: 服务器返回的结果
        """
        # 使用FnoClient的新方法发送请求并等待响应
        response = await self.client.request_payload_with_response("appcgi.sysinfo.getHardwareInfo", {}, timeout)
        return response
    
    async def get_uptime(self, timeout: float = 10.0) -> dict:
        """
        请求系统运行时间信息
        
        Args:
            timeout: 请求超时时间（秒），默认为10.0秒
            
        Returns:
            dict: 服务器返回的结果
        """
        # 使用FnoClient的新方法发送请求并等待响应
        response = await self.client.request_payload_with_response("appcgi.sysinfo.getUptime", {}, timeout)
        return response