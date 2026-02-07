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


class EventLogger:
    def __init__(self, client: FnosClient):
        """
        初始化EventLogger类
        
        Args:
            client: FnosClient实例
        """
        self.client = client
    
    async def common_list(self, timeout: float = 10.0) -> dict:
        """
        获取事件日志列表
        
        Args:
            timeout: 请求超时时间（秒），默认为10.0秒
            
        Returns:
            dict: 包含事件日志列表的服务器返回结果
            示例:
            {
              "data": {
                "total": 991545,
                "rows": [
                  {
                    "level": 0,
                    "module": 1,
                    "id": 1535601,
                    "eventtm": 1770444495,
                    "username": "SystemMonitor",
                    "content": "SystemMonitor登录成功 IP:172.21.0.2"
                  }
                ]
              },
              "reqid": "reqid",
              "result": "succ",
              "rev": "0.1",
              "req": "appcgi.eventlogger.common.list"
            }
        """
        response = await self.client.request_payload_with_response("appcgi.eventlogger.common.list", {}, timeout)
        return response