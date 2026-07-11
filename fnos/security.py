from ._validation import copy_dict_list
from .client import FnosClient


class Security:
    """fnOS 安全状态查询。"""

    def __init__(self, client: FnosClient):
        self.client = client

    async def get_firewall(self, timeout: float = 10.0) -> dict:
        """获取防火墙配置。"""
        return await self.client.request_payload_with_response(
            "appcgi.security.firewall.getting", {}, timeout
        )

    async def get_process_traffic(
        self, processes: list[dict], timeout: float = 10.0
    ) -> dict:
        """获取指定进程的流量信息。"""
        payload = {"data": copy_dict_list("processes", processes)}
        return await self.client.request_payload_with_response(
            "appcgi.security.flowaudit.traffic", payload, timeout
        )
