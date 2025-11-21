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
import logging
from .client import FnosClient

# 创建logger实例
logger = logging.getLogger(__name__)


class Store:
    def __init__(self, client: FnosClient):
        """
        初始化Store类
        
        Args:
            client: FnosClient实例
        """
        self.client = client
    
    async def general(self, timeout: float = 10.0) -> dict:
        """
        请求存储通用信息
        
        Args:
            timeout: 请求超时时间（秒），默认为10.0秒
            
        Returns:
            dict: 服务器返回的结果
        """
        # 使用FnoClient的新方法发送请求并等待响应
        response = await self.client.request_payload_with_response("stor.general", {}, timeout)
        return response
    
    async def calculate_space(self, timeout: float = 10.0) -> dict:
        """
        计算存储空间信息
        
        Args:
            timeout: 请求超时时间（秒），默认为10.0秒
            
        Returns:
            dict: 服务器返回的结果
        """
        # 使用FnoClient的新方法发送请求并等待响应
        response = await self.client.request_payload_with_response("stor.calcSpace", {}, timeout)
        return response
    
    async def list_disks(self, no_hot_spare: bool = True, timeout: float = 10.0) -> dict:
        """
        列出磁盘信息
        
        Args:
            no_hot_spare: 是否排除热备盘，默认为True
            timeout: 请求超时时间（秒），默认为10.0秒
            
        Returns:
            dict: 服务器返回的结果
        """
        # 构造请求参数
        payload = {"noHotSpare": no_hot_spare}
        
        # 使用FnoClient的新方法发送请求并等待响应
        response = await self.client.request_payload_with_response("stor.listDisk", payload, timeout)
        return response
    
    async def get_disk_smart(self, disk: str, timeout: float = 10.0) -> dict:
        """
        获取磁盘SMART信息
        
        Args:
            disk: 磁盘名称（例如："sda"）
            timeout: 请求超时时间（秒），默认为10.0秒
            
        Returns:
            dict: 服务器返回的结果
        """
        payload = {"disk": disk}
        
        response = await self.client.request_payload_with_response("stor.diskSmart", payload, timeout)
        return response
    
    async def get_state(self, name: list[str], uuid: list[str], timeout: float = 10.0) -> dict:
        """
        获取存储状态信息
        
        Args:
            name: 设备名称列表（例如：["dm-1", "dm-0"]）
            uuid: UUID列表（例如：["trim_7cdec818_a061_415b_9307_400e4539235a-0", "trim_13b15f05_d1cb_4fa3_8252_02809cab2410-0"]）
            timeout: 请求超时时间（秒），默认为10.0秒
            
        Returns:
            dict: 服务器返回的结果
        """
        payload = {"name": name, "uuid": uuid}
        
        response = await self.client.request_payload_with_response("stor.state", payload, timeout)
        return response