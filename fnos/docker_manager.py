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


class DockerManager:
    def __init__(self, client: FnosClient):
        """
        初始化DockerManager类
        
        Args:
            client: FnosClient实例
        """
        self.client = client
    
    async def compose_list(self, timeout: float = 10.0) -> dict:
        """
        获取Docker Compose项目列表
        
        Args:
            timeout: 请求超时时间（秒），默认为10.0秒
            
        Returns:
            dict: 包含Docker Compose项目列表的服务器返回结果
            示例:
            {
              "reqid": "reqid",
              "result": "succ",
              "rsp": [
                {
                  "Created": 1770072414898,
                  "Name": "fnos-prometheus-exporter",
                  "ConfigFiles": "home/timandes/home-lab/nas-9/fnos-prometheus-exporter/docker-compose.yml",
                  "Folder": "home/timandes/home-lab/nas-9/fnos-prometheus-exporter",
                  "Status": "ready",
                  "Containers": {
                    "running": 1,
                    "total": 1
                  }
                }
              ]
            }
        """
        response = await self.client.request_payload_with_response("appcgi.dockermgr.composeList", {}, timeout)
        return response
    
    async def container_list(self, all: bool = True, timeout: float = 10.0) -> dict:
        """
        获取容器列表
        
        Args:
            all: 是否返回所有容器（包括停止的），默认为True
            timeout: 请求超时时间（秒），默认为10.0秒
            
        Returns:
            dict: 包含容器列表的服务器返回结果
            示例:
            {
              "reqid": "reqid",
              "result": "succ",
              "rsp": [
                {
                  "Id": "container-id",
                  "Command": "/image/scripts/start",
                  "Created": 1769313591,
                  "HostConfig": {
                    "NetworkMode": "network-mode"
                  },
                  "Image": "image-name",
                  "ImageID": "sha256:image-id",
                  "Names": ["/container-name"],
                  "State": "running",
                  "Status": "Up 5 days",
                  "Project": "project-name",
                  "Icon": "",
                  "Ports": [
                    {
                      "PublicPort": 8080,
                      "PrivatePort": 80,
                      "Type": "tcp",
                      "IP": "0.0.0.0"
                    }
                  ]
                }
              ]
            }
        """
        payload = {"all": all}
        response = await self.client.request_payload_with_response("appcgi.dockermgr.containerList", payload, timeout)
        return response
    
    async def stats(self, timeout: float = 10.0) -> dict:
        """
        获取容器统计信息
        
        Args:
            timeout: 请求超时时间（秒），默认为10.0秒
            
        Returns:
            dict: 包含容器统计信息的服务器返回结果
            示例:
            {
              "reqid": "reqid",
              "result": "succ",
              "rsp": {
                "container-id-1": {
                  "cpuUsage": 0.0015125,
                  "usedMem": 28610560,
                  "networkRx": 0,
                  "networkTx": 0
                },
                "container-id-2": {
                  "cpuUsage": 0.011553884711779448,
                  "usedMem": 259833856,
                  "networkRx": 0,
                  "networkTx": 0
                }
              }
            }
        """
        response = await self.client.request_payload_with_response("appcgi.dockermgr.stats", {}, timeout)
        return response
    
    async def system_setting_get(self, timeout: float = 10.0) -> dict:
        """
        获取Docker系统设置
        
        Args:
            timeout: 请求超时时间（秒），默认为10.0秒
            
        Returns:
            dict: 包含Docker系统设置的服务器返回结果
            示例:
            {
              "reqid": "reqid",
              "result": "succ",
              "rsp": {
                "dataRoot": 1,
                "currentMirror": "",
                "mirrorsV2": [
                  {
                    "res": false,
                    "url": "https://example.com",
                    "name": "Example"
                  }
                ],
                "mirrors": {
                  "Example": {
                    "url": "https://example.com"
                  }
                },
                "autoBoot": true,
                "status": true
              }
            }
        """
        response = await self.client.request_payload_with_response("appcgi.dockermgr.systemSettingGet", {}, timeout)
        return response