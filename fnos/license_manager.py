from ._validation import require_positive_int
from .client import FnosClient


class LicenseManager:
    """fnOS 软件许可查询。"""

    def __init__(self, client: FnosClient):
        self.client = client

    async def list(
        self, page: int = 1, page_size: int = 200, timeout: float = 10.0
    ) -> dict:
        """分页获取软件许可列表。"""
        require_positive_int("page", page)
        require_positive_int("page_size", page_size)
        payload = {"data": {"page": page, "pageSize": page_size}}
        return await self.client.request_payload_with_response(
            "appcgi.license.soft.list", payload, timeout
        )
