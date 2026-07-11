from ._validation import require_positive_int
from .client import FnosClient


class NetworkServer:
    """fnOS 网络服务查询。"""

    def __init__(self, client: FnosClient):
        self.client = client

    async def list_certificates(self, timeout: float = 10.0) -> dict:
        """获取证书列表。"""
        return await self.client.request_payload_with_response(
            "appcgi.netsvr.cert.list", {}, timeout
        )

    async def get_connection_config(self, timeout: float = 10.0) -> dict:
        """获取连接配置。"""
        return await self.client.request_payload_with_response(
            "appcgi.netsvr.conn.getconfig", {}, timeout
        )

    async def get_connection_status(self, timeout: float = 10.0) -> dict:
        """获取连接状态。"""
        return await self.client.request_payload_with_response(
            "appcgi.netsvr.conn.status", {}, timeout
        )

    async def list_ddns_providers(self, timeout: float = 10.0) -> dict:
        """获取 DDNS 服务商列表。"""
        return await self.client.request_payload_with_response(
            "appcgi.netsvr.ddns.provider.list", {}, timeout
        )

    async def list_ddns_records(
        self, page: int = 1, page_size: int = 200, timeout: float = 10.0
    ) -> dict:
        """分页获取 DDNS 记录。"""
        require_positive_int("page", page)
        require_positive_int("page_size", page_size)
        payload = {"data": {"page": page, "pageSize": page_size}}
        return await self.client.request_payload_with_response(
            "appcgi.netsvr.ddns.record.list", payload, timeout
        )
