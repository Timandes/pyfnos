class NotConnectedError(Exception):
    """当FnosClient未连接到服务器时抛出的异常"""
    pass


class HTTPSRequiredError(ConnectionError):
    """当 fnOS 将非安全 WebSocket 连接重定向到 HTTPS 时抛出。"""

    def __init__(
        self,
        requested_uri: str,
        redirect_uri: str,
        status_code: int,
    ):
        self.requested_uri = requested_uri
        self.redirect_uri = redirect_uri
        self.status_code = status_code
        super().__init__(
            "fnOS 服务端要求安全连接；当前 WS 连接被重定向到 HTTPS。"
            "请使用 wss:// endpoint 或传入 use_ssl=True。"
            f"重定向地址：{redirect_uri}"
        )
