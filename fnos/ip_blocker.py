from .client import FnosClient


class IPBlocker:
    """fnOS IP 阻止规则查询。"""

    def __init__(self, client: FnosClient):
        self.client = client

    async def list_allowed_addresses(self, timeout: float = 10.0) -> dict:
        """获取 IP 允许列表。"""
        return await self.client.request_payload_with_response(
            "appcgi.ipblocker.queryAllowList", {}, timeout
        )

    async def get_auto_block_rule(self, timeout: float = 10.0) -> dict:
        """获取自动阻止规则。"""
        return await self.client.request_payload_with_response(
            "appcgi.ipblocker.queryAutoBlockRule", {}, timeout
        )

    async def list_denied_addresses(self, timeout: float = 10.0) -> dict:
        """获取 IP 拒绝列表。"""
        return await self.client.request_payload_with_response(
            "appcgi.ipblocker.queryDenyList", {}, timeout
        )
