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

from ._validation import require_non_empty_string, require_non_negative_int
from .client import FnosClient

# 创建logger实例
logger = logging.getLogger(__name__)


class User:
    def __init__(self, client: FnosClient):
        """
        初始化User类
        
        Args:
            client: FnosClient实例
        """
        self.client = client
    
    async def listUserGroups(self, timeout: float = 10.0) -> dict:
        """
        请求用户和组列表信息
        
        Args:
            timeout: 请求超时时间（秒），默认为10.0秒
            
        Returns:
            dict: 服务器返回的结果
        """
        payload = {
            "users": True,
            "groups": True
        }
        # 使用FnoClient的新方法发送请求并等待响应
        response = await self.client.request_payload_with_response("user.listUG", payload, timeout)
        return response
    
    async def groupUsers(self, timeout: float = 10.0) -> dict:
        """
        请求用户分组信息
        
        Args:
            timeout: 请求超时时间（秒），默认为10.0秒
            
        Returns:
            dict: 服务器返回的结果
        """
        payload = {}
        # 使用FnoClient的新方法发送请求并等待响应
        response = await self.client.request_payload_with_response("user.groupUsers", payload, timeout)
        return response
    
    async def getInfo(self, timeout: float = 10.0) -> dict:
        """
        获取用户信息
        
        Args:
            timeout: 请求超时时间（秒），默认为10.0秒
            
        Returns:
            dict: 服务器返回的结果
        """
        payload = {}
        # 使用FnoClient的新方法发送请求并等待响应
        response = await self.client.request_payload_with_response("user.info", payload, timeout)
        return response
    
    async def isAdmin(self, timeout: float = 10.0) -> dict:
        """
        检查当前用户是否为管理员
        
        Args:
            timeout: 请求超时时间（秒），默认为10.0秒
            
        Returns:
            dict: 服务器返回的结果
        """
        payload = {}
        # 使用FnoClient的新方法发送请求并等待响应
        response = await self.client.request_payload_with_response("user.isAdmin", payload, timeout)
        return response

    async def list_tokens(self, timeout: float = 10.0) -> dict:
        """获取当前账号的登录令牌列表。"""
        return await self.client.request_payload_with_response(
            "appcgi.accountsrv.v1.token.list", {"data": {}}, timeout
        )

    async def get_my_twofa_config(self, timeout: float = 10.0) -> dict:
        """获取当前用户的两步验证配置。"""
        return await self.client.request_payload_with_response(
            "appcgi.tfa.security.v1.me.getConfig", {}, timeout
        )

    async def get_global_twofa_config(self, timeout: float = 10.0) -> dict:
        """获取系统级两步验证配置。"""
        return await self.client.request_payload_with_response(
            "appcgi.tfa.security.v1.twofa.getConfig", {}, timeout
        )

    async def get_user_twofa_config(self, uid: int, timeout: float = 10.0) -> dict:
        """获取指定用户的两步验证配置。"""
        require_non_negative_int("uid", uid)
        return await self.client.request_payload_with_response(
            "appcgi.tfa.security.v1.user.getTwofaConfig",
            {"data": {"uid": uid}},
            timeout,
        )

    async def get_active_state(self, timeout: float = 10.0) -> dict:
        """获取当前用户活跃状态。"""
        return await self.client.request_payload_with_response(
            "user.active", {}, timeout
        )

    async def get_group_info(self, group: str, timeout: float = 10.0) -> dict:
        """获取指定用户组详情。"""
        require_non_empty_string("group", group)
        return await self.client.request_payload_with_response(
            "user.groupInfo", {"group": group}, timeout
        )

    async def list_groups(self, timeout: float = 10.0) -> dict:
        """获取用户组列表。"""
        return await self.client.request_payload_with_response(
            "user.groupList", {}, timeout
        )

    async def list_login_devices(self, timeout: float = 10.0) -> dict:
        """获取登录设备列表。"""
        return await self.client.request_payload_with_response(
            "user.listLoginDevice", {}, timeout
        )

    async def get_preference(self, name: str, timeout: float = 10.0) -> dict:
        """获取指定用户偏好。"""
        require_non_empty_string("name", name)
        return await self.client.request_payload_with_response(
            "usrdat.get", {"name": name}, timeout
        )
