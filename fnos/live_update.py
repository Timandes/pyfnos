from .client import FnosClient


class LiveUpdate:
    """fnOS 在线更新状态查询。"""

    def __init__(self, client: FnosClient):
        self.client = client

    async def get_status(self, timeout: float = 10.0) -> dict:
        """获取在线更新状态。"""
        return await self.client.request_payload_with_response(
            "liveupdate.status", {}, timeout
        )
