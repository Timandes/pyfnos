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


class Notify:
    def __init__(self, client: FnosClient):
        """
        初始化Notify类
        
        Args:
            client: FnosClient实例
        """
        self.client = client
    
    async def unread_total(self, timeout: float = 10.0) -> dict:
        """
        获取未读通知总数
        
        Args:
            timeout: 请求超时时间（秒），默认为10.0秒
            
        Returns:
            dict: 包含未读通知总数的服务器返回结果
            示例:
            {
              "unreadTotal": 21,
              "result": "succ",
              "reqid": "reqid"
            }
        """
        response = await self.client.request_payload_with_response("notify.unreadTotal", {}, timeout)
        return response