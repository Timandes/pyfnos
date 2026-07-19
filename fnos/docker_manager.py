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


class DockerManager:
    def __init__(self, client: FnosClient):
        """
        初始化DockerManager类
        
        Args:
            client: FnosClient实例
        """
        self.client = client
    
    async def list_composes(self, timeout: float = 10.0) -> dict:
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
    
    async def list_containers(self, all: bool = True, timeout: float = 10.0) -> dict:
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
    
    async def get_system_settings(self, timeout: float = 10.0) -> dict:
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

    async def list_image_downloads(self, timeout: float = 10.0) -> dict:
        """获取 Docker 镜像下载任务。"""
        return await self.client.request_payload_with_response(
            "appcgi.dockermgr.imageDownloadList", {}, timeout
        )

    async def list_images(self, timeout: float = 10.0) -> dict:
        """获取 Docker 镜像列表。"""
        return await self.client.request_payload_with_response(
            "appcgi.dockermgr.imageList", {}, timeout
        )

    async def list_networks(self, timeout: float = 10.0) -> dict:
        """获取 Docker 网络列表。"""
        return await self.client.request_payload_with_response(
            "appcgi.dockermgr.networkList", {}, timeout
        )

    async def list_registry_repositories(
        self,
        keyword: str = "",
        page: int = 1,
        page_size: int = 20,
        timeout: float = 10.0,
    ) -> dict:
        """分页查询镜像仓库。"""
        require_positive_int("page", page)
        require_positive_int("page_size", page_size)
        payload = {"key": keyword, "page": page, "pageSize": page_size}
        return await self.client.request_payload_with_response(
            "appcgi.dockermgr.registryHubRepoList", payload, timeout
        )

    # ── Container lifecycle ──────────────────────────────────────────

    async def container_inspect(
        self, container_id: str, timeout: float = 10.0
    ) -> dict:
        """查看容器详情。"""
        return await self.client.request_payload_with_response(
            "appcgi.dockermgr.containerInspect",
            {"containerId": container_id},
            timeout,
        )

    async def container_top(
        self, container_id: str, timeout: float = 10.0
    ) -> dict:
        """查看容器进程。"""
        return await self.client.request_payload_with_response(
            "appcgi.dockermgr.containerTop",
            {"containerId": container_id},
            timeout,
        )

    async def container_stats(
        self, container_id: str, timeout: float = 10.0
    ) -> dict:
        """查看单容器资源统计（CPU/内存/网络）。"""
        return await self.client.request_payload_with_response(
            "appcgi.dockermgr.containerStats",
            {"containerId": container_id},
            timeout,
        )

    async def container_start(self, container_id: str, timeout: float = 30.0) -> dict:
        """启动容器。"""
        return await self.client.request_payload_with_response(
            "appcgi.dockermgr.containerStart",
            {"containerId": container_id},
            timeout,
        )

    async def container_stop(self, container_id: str, timeout: float = 30.0) -> dict:
        """停止容器。"""
        return await self.client.request_payload_with_response(
            "appcgi.dockermgr.containerStop",
            {"containerId": container_id},
            timeout,
        )

    async def container_restart(self, container_id: str, timeout: float = 30.0) -> dict:
        """重启容器。"""
        return await self.client.request_payload_with_response(
            "appcgi.dockermgr.containerRestart",
            {"containerId": container_id},
            timeout,
        )

    async def container_kill(self, container_id: str, timeout: float = 30.0) -> dict:
        """强制终止容器。"""
        return await self.client.request_payload_with_response(
            "appcgi.dockermgr.containerKill",
            {"containerId": container_id},
            timeout,
        )

    async def container_remove(
        self, container_id: str, force: bool = False, timeout: float = 30.0
    ) -> dict:
        """删除容器。"""
        payload: dict[str, object] = {"containerId": container_id}
        if force:
            payload["force"] = True
        return await self.client.request_payload_with_response(
            "appcgi.dockermgr.containerRemove", payload, timeout
        )

    # ── Image management ─────────────────────────────────────────────

    async def image_pull(
        self,
        image_ref: str,
        timeout: float = 120.0,
    ) -> dict:
        """拉取镜像。

        Args:
            image_ref: 镜像引用，如 'nginx:latest' 或 'registry:5000/ns/app:1.0'
        """
        if ":" in image_ref:
            last_colon = image_ref.rfind(":")
            from_image = image_ref[:last_colon]
            tag = image_ref[last_colon + 1:]
        else:
            from_image = image_ref
            tag = "latest"
        return await self.client.request_payload_with_response(
            "appcgi.dockermgr.imagePull",
            {"fromImage": from_image, "tag": tag},
            timeout,
        )

    async def image_remove(
        self, image_id: str, force: bool = False, timeout: float = 30.0
    ) -> dict:
        """删除镜像。"""
        payload: dict[str, object] = {"imageId": image_id}
        if force:
            payload["force"] = True
        return await self.client.request_payload_with_response(
            "appcgi.dockermgr.imageRemove", payload, timeout
        )

    async def image_inspect(
        self, image_id: str, timeout: float = 10.0
    ) -> dict:
        """查看镜像详情。"""
        return await self.client.request_payload_with_response(
            "appcgi.dockermgr.imageInspect",
            {"imageId": image_id},
            timeout,
        )
