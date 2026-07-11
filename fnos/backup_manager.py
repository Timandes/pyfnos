from .client import FnosClient


class BackupManager:
    """fnOS 备份查询。"""

    def __init__(self, client: FnosClient):
        self.client = client

    async def list_tasks(self, direction: int, timeout: float = 10.0) -> dict:
        """按方向获取备份任务。"""
        if (
            isinstance(direction, bool)
            or not isinstance(direction, int)
            or direction not in (0, 1)
        ):
            raise ValueError("direction参数必须为0或1")
        return await self.client.request_payload_with_response(
            "appcgi.backup.task.list", {"direction": direction}, timeout
        )
