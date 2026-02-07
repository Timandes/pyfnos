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