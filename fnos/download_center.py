from .client import FnosClient


class DownloadCenter:
    """fnOS 下载中心查询。"""

    def __init__(self, client: FnosClient):
        self.client = client

    async def get_default_save_directory(self, timeout: float = 10.0) -> dict:
        """获取默认下载保存目录。"""
        return await self.client.request_payload_with_response(
            "appcgi.downloadcenter.config.getDefaultSaveDir", {}, timeout
        )

    async def get_statistics(self, timeout: float = 10.0) -> dict:
        """获取下载中心统计信息。"""
        return await self.client.request_payload_with_response(
            "appcgi.downloadcenter.stat.all", {}, timeout
        )

    async def query_tasks(
        self,
        state_filter: int = 65535,
        init_flag: bool = True,
        timeout: float = 10.0,
    ) -> dict:
        """按状态位掩码查询下载任务。"""
        payload = {"init_flag": init_flag, "state_filter": state_filter}
        return await self.client.request_payload_with_response(
            "appcgi.downloadcenter.task.query", payload, timeout
        )
