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
import logging
from .client import FnosClient

# 创建logger实例
logger = logging.getLogger(__name__)


class IscsiManager:
    def __init__(self, client: FnosClient):
        """
        初始化IscsiManager类

        Args:
            client: FnosClient实例
        """
        self.client = client

    async def get_config(self, timeout: float = 10.0) -> dict:
        """
        获取 iSCSI 配置信息

        Args:
            timeout: 请求超时时间（秒），默认为10.0秒

        Returns:
            dict: 服务器返回的结果
        """
        response = await self.client.request_payload_with_response(
            "appcgi.iscsimgr.iscsi.config.get", {}, timeout
        )
        return response

    async def list_initiators(self, timeout: float = 10.0) -> dict:
        """
        获取 iSCSI Initiator 列表

        Args:
            timeout: 请求超时时间（秒），默认为10.0秒

        Returns:
            dict: 服务器返回的结果
        """
        response = await self.client.request_payload_with_response(
            "appcgi.iscsimgr.iscsi.initiator.list", {}, timeout
        )
        return response

    async def list_luns(self, timeout: float = 10.0) -> dict:
        """
        获取 iSCSI LUN 列表

        Args:
            timeout: 请求超时时间（秒），默认为10.0秒

        Returns:
            dict: 服务器返回的结果
        """
        response = await self.client.request_payload_with_response(
            "appcgi.iscsimgr.iscsi.lun.list", {}, timeout
        )
        return response

    async def list_lun_usergroups(
        self, lun_name: str = "", wwn: str = "", timeout: float = 10.0
    ) -> dict:
        """
        获取 iSCSI LUN 用户组列表

        Args:
            lun_name: LUN 名称，默认为空字符串（查询所有）
            wwn: WWN，默认为空字符串（查询所有）
            timeout: 请求超时时间（秒），默认为10.0秒

        Returns:
            dict: 服务器返回的结果
        """
        payload = {"lunName": lun_name, "wwn": wwn}
        response = await self.client.request_payload_with_response(
            "appcgi.iscsimgr.iscsi.lun.usergroup.list", payload, timeout
        )
        return response

    async def list_targets(self, timeout: float = 10.0) -> dict:
        """
        获取 iSCSI Target 列表

        Args:
            timeout: 请求超时时间（秒），默认为10.0秒

        Returns:
            dict: 服务器返回的结果
        """
        response = await self.client.request_payload_with_response(
            "appcgi.iscsimgr.iscsi.target.list", {}, timeout
        )
        return response
