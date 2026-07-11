from .client import FnosClient


class SystemRestore:
    """fnOS 系统恢复信息查询。"""

    def __init__(self, client: FnosClient):
        self.client = client

    async def get_info(self, timeout: float = 10.0) -> dict:
        """获取系统恢复信息。"""
        return await self.client.request_payload_with_response(
            "appcgi.sysrestore.getInfo", {}, timeout
        )
