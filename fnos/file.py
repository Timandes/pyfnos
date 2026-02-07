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


class File:
    def __init__(self, client: FnosClient):
        """
        初始化File类
        
        Args:
            client: FnosClient实例
        """
        self.client = client
    
    async def list(self, path: str = None, timeout: float = 10.0) -> dict:
        """
        列出指定目录下的文件和文件夹
        
        Args:
            path: 查询目录路径(为None默认为用户目录)，格式为vol{stor_id}/{user_id}/{path}
            timeout: 请求超时时间（秒），默认为10.0秒
            
        Returns:
            dict: 包含文件列表的服务器返回结果
            示例:
            {
              "files": [
                {
                  "name": "微软.jpg", // 文件名称
                  "uid": 1000, // 所属用户id
                  "size": 814378, // 文件大小
                  "mtim": 1762805820, // 创建时间
                  "btim": 1763036958 // 修改时间
                },
                {
                  "name": "12131", // 文件夹名称
                  "uid": 1000, // 所属用户id
                  "mtim": 1763038335, // 创建时间
                  "btim": 1763038335, // 修改时间
                  "dir": 1, // 1为文件夹 文件不返回该字段
                  "v": 1 // 存储空间id 只有用户根目录才返回
                }
              ],
              "uver": 115541950529538,
              "reqid": "reqid"
            }
        """
        # 构造请求参数
        payload = {}
        if path is not None:
            payload["path"] = path
        
        # 使用FnoClient的新方法发送请求并等待响应
        response = await self.client.request_payload_with_response("file.ls", payload, timeout)
        return response
    
    async def mkdir(self, path: str, timeout: float = 10.0) -> dict:
        """
        创建文件夹
        
        Args:
            path: 文件夹路径，格式为vol{stor_id}/{user_id}/{path}
            timeout: 请求超时时间（秒），默认为10.0秒
            
        Returns:
            dict: 服务器返回的结果
            示例:
            {"result":"succ","reqid":"reqid"}
        """
        # 验证参数
        if not path:
            raise ValueError("path参数不能为空")
        
        # 构造请求参数
        payload = {
            "path": path
        }
        
        # 使用FnoClient的新方法发送请求并等待响应
        response = await self.client.request_payload_with_response("file.mkdir", payload, timeout)
        return response
    
    async def remove(self, files: list, move_to_trashbin: bool = True, 
                     details: dict = None, timeout: float = 10.0) -> dict:
        """
        删除文件或文件夹
        
        Args:
            files: 需要删除的文件绝对路径数组
            move_to_trashbin: 是否移至回收站，默认为True
            details: 用于显示文件任务描述的可选参数，包含name、count、dir字段
            timeout: 请求超时时间（秒），默认为10.0秒
            
        Returns:
            dict: 服务器返回的结果
            示例:
            {"result":"succ","reqid":"reqid"}
        """
        # 验证参数
        if not files or not isinstance(files, list):
            raise ValueError("files参数必须是非空列表")
        
        # 构造请求参数
        payload = {
            "files": files,
            "moveToTrashbin": move_to_trashbin
        }
        
        # 添加可选的details参数
        if details is not None:
            payload["details"] = details
        
        # 使用FnoClient的新方法发送请求并等待响应
        response = await self.client.request_payload_with_response("file.rm", payload, timeout)
        return response
    
    async def get_acl(self, files: list, timeout: float = 10.0) -> dict:
        """
        获取文件的ACL（访问控制列表）信息
        
        Args:
            files: 需要查询ACL的文件路径列表，格式为vol{stor_id}/{path}
            timeout: 请求超时时间（秒），默认为10.0秒
            
        Returns:
            dict: 包含文件ACL信息的服务器返回结果
            示例:
            {
              "data": [
                {
                  "defaultPermset": [
                    {
                      "owner": 6
                    },
                    {
                      "group": 0
                    },
                    {
                      "gid": 1001,
                      "perm": 6
                    },
                    {
                      "other": 1
                    }
                  ],
                  "permset": [
                    {
                      "owner": 6
                    },
                    {
                      "group": 0
                    },
                    {
                      "gid": 1001,
                      "perm": 6
                    },
                    {
                      "other": 1
                    }
                  ]
                }
              ],
              "uver": 115993656164352,
              "result": "succ",
              "reqid": "reqid"
            }
        """
        # 验证参数
        if not files or not isinstance(files, list):
            raise ValueError("files参数必须是非空列表")
        
        # 构造请求参数
        payload = {
            "files": files
        }
        
        # 使用FnoClient的新方法发送请求并等待响应
        response = await self.client.request_payload_with_response("file.getAcl", payload, timeout)
        return response