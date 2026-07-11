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

import logging

from ._validation import require_positive_int
from .client import FnosClient

# 创建logger实例
logger = logging.getLogger(__name__)


class Share:
    def __init__(self, client: FnosClient):
        """
        初始化Share类
        
        Args:
            client: FnosClient实例
        """
        self.client = client
    
    async def smb_opt(self, timeout: float = 10.0) -> dict:
        """
        获取SMB共享配置信息
        
        Args:
            timeout: 请求超时时间（秒），默认为10.0秒
            
        Returns:
            dict: 包含SMB配置信息的服务器返回结果
            示例:
            {
              "data": {
                "smbEnable": true,
                "wsddEnable": true,
                "mode": 2,
                "ipv4Addr": "192.168.31.118",
                "svcPort": 445,
                "mount": "NAS-9",
                "option": {
                  "workGroup": "",
                  "oplocks": true,
                  "ntlmv1": false,
                  "serverSigning": 1,
                  "transportEncryption": 1,
                  "supportSmb1": false,
                  "enableFruit": false,
                  "enableDirSort": false,
                  "enableVoteFile": true,
                  "voteFiles": "/._*/.DS_Store/",
                  "deleteVoteFiles": false,
                  "wildcardSearchCache": false,
                  "winsIP": "",
                  "disableMultiConn": false,
                  "enableMultiChannel": true,
                  "aioWrite": 2
                },
                "timeMachine": {
                  "enable": false,
                  "vol": 0,
                  "quota": 10737418240,
                  "folder": "",
                  "status": -1
                }
              },
              "reqid": "reqid",
              "result": "succ",
              "rev": "0.1",
              "req": "appcgi.share.smb.opt"
            }
        """
        response = await self.client.request_payload_with_response("appcgi.share.smb.opt", {}, timeout)
        return response

    async def dlna_options(self, timeout: float = 10.0) -> dict:
        """获取 DLNA 服务配置。"""
        return await self.client.request_payload_with_response(
            "appcgi.share.dlna.opt", {}, timeout
        )

    async def dlna_share_options(self, timeout: float = 10.0) -> dict:
        """获取 DLNA 共享配置。"""
        return await self.client.request_payload_with_response(
            "appcgi.share.dlna.share.opt", {}, timeout
        )

    async def ftp_options(self, timeout: float = 10.0) -> dict:
        """获取 FTP 服务配置。"""
        return await self.client.request_payload_with_response(
            "appcgi.share.ftp.opt", {}, timeout
        )

    async def ftp_share_options(self, timeout: float = 10.0) -> dict:
        """获取 FTP 共享配置。"""
        return await self.client.request_payload_with_response(
            "appcgi.share.ftp.share.opt", {}, timeout
        )

    async def nfs_options(self, timeout: float = 10.0) -> dict:
        """获取 NFS 服务配置。"""
        return await self.client.request_payload_with_response(
            "appcgi.share.nfs.opt", {}, timeout
        )

    async def nfs_share_options(self, timeout: float = 10.0) -> dict:
        """获取 NFS 共享配置。"""
        return await self.client.request_payload_with_response(
            "appcgi.share.nfs.share.opt", {}, timeout
        )

    async def smb_share_options(self, timeout: float = 10.0) -> dict:
        """获取 SMB 共享配置。"""
        return await self.client.request_payload_with_response(
            "appcgi.share.smb.share.opt", {}, timeout
        )

    async def webdav_options(self, timeout: float = 10.0) -> dict:
        """获取 WebDAV 服务配置。"""
        return await self.client.request_payload_with_response(
            "appcgi.share.webdav.opt", {}, timeout
        )

    async def webdav_share_options(self, timeout: float = 10.0) -> dict:
        """获取 WebDAV 共享配置。"""
        return await self.client.request_payload_with_response(
            "appcgi.share.webdav.share.opt", {}, timeout
        )

    async def get_link_defaults(self, timeout: float = 10.0) -> dict:
        """获取分享链接默认配置。"""
        return await self.client.request_payload_with_response(
            "appcgi.sharesvr.share.link.default.get", {}, timeout
        )

    async def get_default_link(self, timeout: float = 10.0) -> dict:
        """获取默认分享链接。"""
        return await self.client.request_payload_with_response(
            "appcgi.sharesvr.share.link.default", {}, timeout
        )

    async def list_links(
        self,
        is_admin: bool = False,
        keyword: str = "",
        page: int = 1,
        page_size: int = 100,
        sort_column: str = "createdTime",
        sort_type: str = "DESC",
        timeout: float = 10.0,
    ) -> dict:
        """分页查询分享链接。"""
        require_positive_int("page", page)
        require_positive_int("page_size", page_size)
        payload = {
            "data": {
                "isAdmin": is_admin,
                "keyword": keyword,
                "page": page,
                "pageSize": page_size,
                "sortColumn": sort_column,
                "sortType": sort_type,
            }
        }
        return await self.client.request_payload_with_response(
            "appcgi.sharesvr.share.link.list", payload, timeout
        )

    async def get_link_permission(self, timeout: float = 10.0) -> dict:
        """获取分享链接权限配置。"""
        return await self.client.request_payload_with_response(
            "appcgi.sharesvr.share.permission.get", {}, timeout
        )
