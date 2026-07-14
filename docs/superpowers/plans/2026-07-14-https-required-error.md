# HTTPS Required Connection Error Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 fnOS 强制 HTTPS 导致的 WS→HTTPS 重定向识别为结构化、可单独捕获的 `HTTPSRequiredError`，同时保持其他连接异常的既有行为。

**Architecture:** 在 SDK 异常模块中定义不依赖第三方类型的公共异常，再由 `FnosClient` 私有辅助方法精确检查 `websockets` 的 `InvalidURI -> InvalidStatus` 异常链。`connect()` 只在非安全 WS 被标准 HTTP 3xx 重定向到匹配的 HTTPS URI 时转换异常，并通过显式 `raise ... from ...` 保留底层诊断链。

**Tech Stack:** Python 3.11+、websockets 15+、asyncio、pytest 9、pytest-asyncio、`unittest.mock.AsyncMock`、uv。

## Global Constraints

- 只抛出专用异常，不自动切换 WSS 或重试连接。
- 不改变 `FnosClient.connect()` 的签名、参数默认值和证书验证行为。
- 仅识别非安全 WS、标准重定向状态、匹配 Location 和 HTTPS 目标同时满足的场景。
- 其他 `InvalidURI`、握手、TLS 和网络异常必须原样抛出。
- `HTTPSRequiredError` 必须提供 `requested_uri`、`redirect_uri` 和 `status_code` 属性。
- 必须通过 `fnos` 包顶层导出 `HTTPSRequiredError`。
- 不新增运行时依赖，不重构现有异常体系。
- 使用 TDD：每项生产代码之前必须先观察对应测试正确失败。
- Git 提交使用英文 Angular/Conventional Commits，且不得包含 `Co-Authored-By`。

---

## File Structure

- Create `tests/test_https_required_error.py`: 验证公共异常 API、精准转换、异常链和所有负向边界。
- Modify `fnos/exceptions.py`: 定义结构化的 `HTTPSRequiredError`。
- Modify `fnos/__init__.py`: 从包顶层导出新异常并加入 `__all__`。
- Modify `fnos/client.py`: 检查 `websockets` 重定向异常链并转换为 SDK 异常。
- Modify `README.md`: 说明如何捕获异常并显式改用 WSS。
- Modify `CHANGELOG.md`: 在 Unreleased 中记录新增公共异常。

### Task 1: 公共 `HTTPSRequiredError` API

**Files:**
- Create: `tests/test_https_required_error.py`
- Modify: `fnos/exceptions.py`
- Modify: `fnos/__init__.py`

**Interfaces:**
- Produces: `HTTPSRequiredError(requested_uri: str, redirect_uri: str, status_code: int)`。
- Produces: `HTTPSRequiredError.requested_uri: str`、`redirect_uri: str`、`status_code: int`。
- Produces: `from fnos import HTTPSRequiredError`。

- [ ] **Step 1: 写公共异常 API 的失败测试**

创建 `tests/test_https_required_error.py`：

```python
import fnos


def test_https_required_error_is_public_and_structured():
    error_type = getattr(fnos, "HTTPSRequiredError", None)

    assert error_type is not None
    assert "HTTPSRequiredError" in fnos.__all__

    error = error_type(
        requested_uri="ws://nas.example.com:5666/websocket?type=main",
        redirect_uri="https://nas.example.com:5667/websocket?type=main",
        status_code=302,
    )

    assert isinstance(error, ConnectionError)
    assert error.requested_uri == "ws://nas.example.com:5666/websocket?type=main"
    assert error.redirect_uri == "https://nas.example.com:5667/websocket?type=main"
    assert error.status_code == 302
    assert "fnOS 服务端要求安全连接" in str(error)
    assert "wss://" in str(error)
    assert "use_ssl=True" in str(error)
    assert error.redirect_uri in str(error)
```

- [ ] **Step 2: 运行测试并确认 RED**

Run:

```bash
uv run pytest -q tests/test_https_required_error.py::test_https_required_error_is_public_and_structured
```

Expected: FAIL at `assert error_type is not None`，因为 `fnos` 尚未导出 `HTTPSRequiredError`。

- [ ] **Step 3: 实现结构化公共异常**

将 `fnos/exceptions.py` 改为：

```python
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
```

在 `fnos/__init__.py` 中更新异常导入：

```python
from .exceptions import HTTPSRequiredError, NotConnectedError
```

并在 `__all__` 中紧随 `"FnosClient"` 加入：

```python
    "HTTPSRequiredError",
```

- [ ] **Step 4: 运行测试并确认 GREEN**

Run:

```bash
uv run pytest -q tests/test_https_required_error.py::test_https_required_error_is_public_and_structured
```

Expected: `1 passed`。

- [ ] **Step 5: 检查差异并提交公共异常 API**

Run:

```bash
git diff --check
git status --short
```

Expected: 仅 `tests/test_https_required_error.py`、`fnos/exceptions.py` 和 `fnos/__init__.py` 有预期变更，且 `git diff --check` 无输出。

Commit:

```bash
git add tests/test_https_required_error.py fnos/exceptions.py fnos/__init__.py
git commit -m "feat: add HTTPS-required connection error"
```

### Task 2: 精确转换强制 HTTPS 重定向并记录用法

**Files:**
- Modify: `tests/test_https_required_error.py`
- Modify: `fnos/client.py`
- Modify: `README.md`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: `HTTPSRequiredError(requested_uri, redirect_uri, status_code)` from Task 1。
- Consumes: `websockets.exceptions.InvalidURI.uri`，以及其显式 `__cause__` 或隐式 `__context__` 中的 `InvalidStatus.response`；`websockets 15.0.1` 的真实路径使用 `__context__`。
- Produces: `FnosClient.connect()` 对强制 HTTPS 重定向抛出 `HTTPSRequiredError`，其他异常保持原样。

- [ ] **Step 1: 写强制 HTTPS 重定向的失败测试**

在 `tests/test_https_required_error.py` 的导入区加入：

```python
import asyncio
from pathlib import Path
import subprocess
import sys
from unittest.mock import AsyncMock, patch

import pytest
from websockets.datastructures import Headers
from websockets.exceptions import InvalidStatus, InvalidURI
from websockets.http11 import Response

from fnos import FnosClient, HTTPSRequiredError


ROOT = Path(__file__).resolve().parents[1]
```

在同一文件加入异常链构造器和正向测试：

```python
def make_redirect_invalid_uri(
    *,
    redirect_uri: str,
    status_code: int = 302,
    location: str | None = None,
) -> InvalidURI:
    response = Response(
        status_code,
        "Redirect",
        Headers({"Location": location or redirect_uri}),
    )
    invalid_status = InvalidStatus(response)
    invalid_uri = InvalidURI(redirect_uri, "scheme isn't ws or wss")
    invalid_uri.__context__ = invalid_status
    return invalid_uri


@pytest.mark.asyncio
async def test_connect_translates_https_redirect_to_https_required_error():
    requested_uri = "ws://nas.example.com:5666/websocket?type=main"
    redirect_uri = "https://nas.example.com:5667/websocket?type=main"
    source_error = make_redirect_invalid_uri(redirect_uri=redirect_uri)
    connect_mock = AsyncMock(side_effect=source_error)
    client = FnosClient()

    with patch("fnos.client.websockets.connect", connect_mock):
        with pytest.raises(HTTPSRequiredError) as exc_info:
            await client.connect("nas.example.com:5666")

    error = exc_info.value
    assert error.requested_uri == requested_uri
    assert error.redirect_uri == redirect_uri
    assert error.status_code == 302
    assert error.__cause__ is source_error
    assert client.connected is False
    connect_mock.assert_awaited_once_with(requested_uri, ssl=None)
```

- [ ] **Step 2: 运行正向测试并确认 RED**

Run:

```bash
uv run pytest -q tests/test_https_required_error.py::test_connect_translates_https_redirect_to_https_required_error
```

Expected: FAIL，因为 `FnosClient.connect()` 仍原样抛出 `InvalidURI`。

- [ ] **Step 3: 实现最小异常链识别和转换**

在 `fnos/client.py` 导入区加入：

```python
from urllib.parse import urljoin, urlparse
from websockets.exceptions import InvalidStatus, InvalidURI
```

更新本地异常导入：

```python
from .exceptions import HTTPSRequiredError, NotConnectedError
```

在 `_parse_endpoint()` 后加入私有辅助方法：

```python
    @staticmethod
    def _https_required_error(
        error: InvalidURI,
        requested_uri: str,
        actual_use_ssl: bool,
    ) -> HTTPSRequiredError | None:
        """将匹配 fnOS 强制 HTTPS 的重定向异常转换为 SDK 异常。"""
        if actual_use_ssl or urlparse(error.uri).scheme.lower() != "https":
            return None

        redirect_error = error.__cause__ or error.__context__
        if not isinstance(redirect_error, InvalidStatus):
            return None

        if redirect_error.response.status_code not in {301, 302, 303, 307, 308}:
            return None

        location = redirect_error.response.headers.get("Location")
        if location is None or urljoin(requested_uri, location) != error.uri:
            return None

        return HTTPSRequiredError(
            requested_uri=requested_uri,
            redirect_uri=error.uri,
            status_code=redirect_error.response.status_code,
        )
```

将 `connect()` 中创建连接的一行：

```python
            self.ws = await websockets.connect(uri, ssl=ssl_context)
```

替换为：

```python
            try:
                self.ws = await websockets.connect(uri, ssl=ssl_context)
            except InvalidURI as error:
                https_required_error = self._https_required_error(
                    error,
                    requested_uri=uri,
                    actual_use_ssl=actual_use_ssl,
                )
                if https_required_error is not None:
                    raise https_required_error from error
                raise
```

保留 `connect()` 外层既有 `except Exception`，使新异常仍只记录一次失败日志、设置 `connected=False` 并继续抛出。

- [ ] **Step 4: 运行正向测试并确认 GREEN**

Run:

```bash
uv run pytest -q tests/test_https_required_error.py::test_connect_translates_https_redirect_to_https_required_error
```

Expected: `1 passed`。

- [ ] **Step 5: 写无关 `InvalidURI` 不转换的回归测试**

在 `tests/test_https_required_error.py` 加入：

```python
@pytest.mark.asyncio
async def test_connect_preserves_invalid_uri_without_redirect_cause():
    source_error = InvalidURI("http://nas.example.com", "scheme isn't ws or wss")
    connect_mock = AsyncMock(side_effect=source_error)
    client = FnosClient()

    with patch("fnos.client.websockets.connect", connect_mock):
        with pytest.raises(InvalidURI) as exc_info:
            await client.connect("nas.example.com:5666")

    assert exc_info.value is source_error


@pytest.mark.parametrize(
    ("redirect_uri", "status_code", "location", "use_ssl"),
    [
        (
            "ftp://nas.example.com:5667/websocket?type=main",
            302,
            "ftp://nas.example.com:5667/websocket?type=main",
            False,
        ),
        (
            "https://nas.example.com:5667/websocket?type=main",
            305,
            "https://nas.example.com:5667/websocket?type=main",
            False,
        ),
        (
            "https://nas.example.com:5667/websocket?type=main",
            302,
            "https://other.example.com:5667/websocket?type=main",
            False,
        ),
        (
            "https://nas.example.com:5667/websocket?type=main",
            302,
            "https://nas.example.com:5667/websocket?type=main",
            True,
        ),
    ],
    ids=("non-https", "non-standard-status", "location-mismatch", "initial-wss"),
)
@pytest.mark.asyncio
async def test_connect_preserves_non_matching_redirect_errors(
    redirect_uri,
    status_code,
    location,
    use_ssl,
):
    source_error = make_redirect_invalid_uri(
        redirect_uri=redirect_uri,
        status_code=status_code,
        location=location,
    )
    connect_mock = AsyncMock(side_effect=source_error)
    client = FnosClient()

    with patch("fnos.client.websockets.connect", connect_mock):
        with pytest.raises(InvalidURI) as exc_info:
            await client.connect("nas.example.com:5666", use_ssl=use_ssl)

    assert exc_info.value is source_error
```

- [ ] **Step 6: 运行负向测试并确认它们约束转换边界**

Run:

```bash
uv run pytest -q tests/test_https_required_error.py
```

Expected: 全部 PASS。若任何负向用例被转换为 `HTTPSRequiredError`，收紧 `_https_required_error()` 对应条件后重跑，直到全部通过。

- [ ] **Step 6a: 用真实 HTTP 302 握手验证第三方异常链契约**

在 `tests/test_https_required_error.py` 加入一个由 `asyncio.start_server()` 驱动的真实握手测试。服务端返回一次 `302 + Location: https://...`，测试实际调用 `FnosClient.connect()`，不 mock `websockets.connect()`：

```python
@pytest.mark.asyncio
async def test_connect_translates_real_https_redirect_to_https_required_error():
    connection_count = 0
    redirect_uri = "https://nas.example.com:5667/websocket?type=main"

    async def redirect_to_https(reader, writer):
        nonlocal connection_count
        connection_count += 1
        await reader.readuntil(b"\r\n\r\n")
        writer.write(
            b"HTTP/1.1 302 Found\r\n"
            + f"Location: {redirect_uri}\r\n".encode()
            + b"Content-Length: 0\r\n"
            b"Connection: close\r\n\r\n"
        )
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(redirect_to_https, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    requested_uri = f"ws://127.0.0.1:{port}/websocket?type=main"
    client = FnosClient()

    try:
        with pytest.raises(HTTPSRequiredError) as exc_info:
            await client.connect(f"127.0.0.1:{port}")
    finally:
        server.close()
        await server.wait_closed()

    error = exc_info.value
    assert error.requested_uri == requested_uri
    assert error.redirect_uri == redirect_uri
    assert error.status_code == 302
    assert isinstance(error.__cause__, InvalidURI)
    assert error.__cause__.__cause__ is None
    assert isinstance(error.__cause__.__context__, InvalidStatus)
    assert client.connected is False
    assert connection_count == 1
```

Run:

```bash
uv run pytest -q tests/test_https_required_error.py::test_connect_translates_real_https_redirect_to_https_required_error
```

Expected: 修复前 FAIL 并原样抛出 `InvalidURI`；读取 `error.__context__` 后 PASS。

- [ ] **Step 6b: 验证全新解释器可直接导入公共 API**

加入不预加载 `websockets.exceptions` 的子进程回归测试：

```python
def test_fnos_import_does_not_require_preloading_websockets_exceptions():
    completed = subprocess.run(
        [sys.executable, "-c", "import fnos"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert completed.returncode == 0, completed.stderr
```

该测试要求 `fnos/client.py` 直接从 `websockets.exceptions` 导入新增代码使用的异常类型，不能在模块级类型注解中依赖顶层惰性属性 `websockets.exceptions`。

- [ ] **Step 7: 补充 README 和 CHANGELOG**

在 README 的“SSL/WSS 连接示例”代码块后加入：

````markdown
当 fnOS 开启“强制 HTTPS”而调用方仍连接 HTTP/WS 端点时，SDK 会抛出 `HTTPSRequiredError`，但不会自动重试：

```python
from fnos import HTTPSRequiredError

try:
    await client.connect("my-server.com:5666")
except HTTPSRequiredError as error:
    print(f"请改用 WSS，服务端重定向到：{error.redirect_uri}")
```

调用方可以根据自身配置改用 `wss://` endpoint，或再次调用 `connect(..., use_ssl=True)`。
````

在 CHANGELOG 的 `[Unreleased]` → `Added` 中加入：

```markdown
- 新增 `HTTPSRequiredError`，用于识别 fnOS 强制 HTTPS 导致的 WS→HTTPS 重定向并提示调用方改用 WSS
```

- [ ] **Step 8: 运行定向与全量非集成验证**

Run:

```bash
uv run pytest -q tests/test_https_required_error.py
uv run pytest -q -m "not integration"
git diff --check
```

Expected:

- `tests/test_https_required_error.py` 全部 PASS；
- 全量非集成测试全部 PASS，无 error 或新增 warning；
- `git diff --check` 无输出。

- [ ] **Step 9: 检查最终差异并提交连接行为和文档**

Run:

```bash
git status --short
git diff -- fnos/client.py tests/test_https_required_error.py README.md CHANGELOG.md
```

Expected: 差异仅包含精准异常转换、对应测试和已批准文档，不包含自动重试或无关重构。

Commit:

```bash
git add fnos/client.py tests/test_https_required_error.py README.md CHANGELOG.md
git commit -m "fix: identify fnOS HTTPS redirects"
```
