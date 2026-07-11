from .client import FnosClient


class MountManager:
    """fnOS 挂载查询。"""

    def __init__(self, client: FnosClient):
        self.client = client

    async def list_mounts(self, timeout: float = 10.0) -> dict:
        """获取挂载列表。"""
        return await self.client.request_payload_with_response(
            "appcgi.mountmgr.list", {}, timeout
        )

    async def get_settings(self, timeout: float = 10.0) -> dict:
        """获取挂载设置。"""
        return await self.client.request_payload_with_response(
            "appcgi.mountmgr.setting.detail", {}, timeout
        )
