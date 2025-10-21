import json
import asyncio
from .client import FnosClient


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