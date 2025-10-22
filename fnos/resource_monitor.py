import json
import asyncio
from .client import FnosClient


class ResourceMonitor:
    def __init__(self, client: FnosClient):
        """
        初始化ResourceMonitor类
        
        Args:
            client: FnosClient实例
        """
        self.client = client
    
    async def cpu(self, timeout: float = 10.0) -> dict:
        """
        请求CPU资源监控信息
        
        Args:
            timeout: 请求超时时间（秒），默认为10.0秒
            
        Returns:
            dict: 服务器返回的结果
        """
        # 使用FnoClient的新方法发送请求并等待响应
        response = await self.client.request_payload_with_response("appcgi.resmon.cpu", {}, timeout)
        return response
    
    async def gpu(self, timeout: float = 10.0) -> dict:
        """
        请求GPU资源监控信息
        
        Args:
            timeout: 请求超时时间（秒），默认为10.0秒
            
        Returns:
            dict: 服务器返回的结果
        """
        # 使用FnoClient的新方法发送请求并等待响应
        response = await self.client.request_payload_with_response("appcgi.resmon.gpu", {}, timeout)
        return response
    
    async def memory(self, timeout: float = 10.0) -> dict:
        """
        请求内存资源监控信息
        
        Args:
            timeout: 请求超时时间（秒），默认为10.0秒
            
        Returns:
            dict: 服务器返回的结果
        """
        # 使用FnoClient的新方法发送请求并等待响应
        response = await self.client.request_payload_with_response("appcgi.resmon.mem", {}, timeout)
        return response