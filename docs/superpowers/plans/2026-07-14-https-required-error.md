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
- Create `examples/https_required_error.py`: 独立诊断强制 HTTPS 重定向并展示结构化异常。
- Create `tests/test_https_required_error_example.py`: 验证诊断示例的 CLI、三条运行分支、资源关闭和文档。

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

### Task 3: 独立强制 HTTPS 诊断示例

**Files:**
- Create: `examples/https_required_error.py`
- Create: `tests/test_https_required_error_example.py`
- Modify: `README.md`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: `FnosClient.connect(endpoint)` 和 `HTTPSRequiredError(requested_uri, redirect_uri, status_code)`。
- Produces: `run(endpoint: str) -> int`，目标异常和连接成功返回 `0`，其他异常返回 `1`。
- Produces: `main()`，解析必填 `-e/--endpoint` 并将 `run()` 返回值作为进程退出码。

- [ ] **Step 1: 写独立帮助输出的失败测试**

创建 `tests/test_https_required_error_example.py`：

```python
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "https_required_error.py"


def test_https_required_error_example_has_endpoint_only_help():
    completed = subprocess.run(
        [sys.executable, str(EXAMPLE), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert completed.returncode == 0, completed.stderr
    assert "fnOS 强制 HTTPS 连接诊断示例" in completed.stdout
    assert "-e ENDPOINT" in completed.stdout
    assert "--endpoint ENDPOINT" in completed.stdout
    assert "HTTP/WS 服务器地址" in completed.stdout
    assert "--user" not in completed.stdout
    assert "--password" not in completed.stdout
```

- [ ] **Step 2: 运行帮助测试并确认 RED**

Run:

```bash
uv run pytest -q tests/test_https_required_error_example.py::test_https_required_error_example_has_endpoint_only_help
```

Expected: FAIL，因为 `examples/https_required_error.py` 尚不存在，子进程返回非零退出码。

- [ ] **Step 3: 实现最小 CLI 外壳**

创建 `examples/https_required_error.py`：

```python
# Copyright 2025 Timandes White
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse


def main():
    parser = argparse.ArgumentParser(description="fnOS 强制 HTTPS 连接诊断示例")
    parser.add_argument(
        "-e",
        "--endpoint",
        required=True,
        help="HTTP/WS 服务器地址，例如 nas.example.com:5666",
    )
    parser.parse_args()


if __name__ == "__main__":
    main()
```

这一阶段只建立经过测试的 CLI 参数契约；连接行为由下一轮失败测试驱动加入。

- [ ] **Step 4: 运行帮助测试并确认 GREEN**

Run:

```bash
uv run pytest -q tests/test_https_required_error_example.py::test_https_required_error_example_has_endpoint_only_help
```

Expected: `1 passed`。

- [ ] **Step 5: 写专用异常展示的失败测试**

将 `tests/test_https_required_error_example.py` 的导入区扩展为：

```python
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from fnos import HTTPSRequiredError
```

加入模块加载器、网络边界替身和目标异常测试：

```python
def load_example():
    spec = importlib.util.spec_from_file_location("example_https_required_error", EXAMPLE)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeClient:
    def __init__(self, error=None):
        self.error = error
        self.connect_calls = []
        self.closed = False

    async def connect(self, endpoint):
        self.connect_calls.append(endpoint)
        if self.error is not None:
            raise self.error

    async def close(self):
        self.closed = True


@pytest.mark.asyncio
async def test_run_reports_https_required_error_without_retry(monkeypatch, capsys):
    module = load_example()
    error = HTTPSRequiredError(
        requested_uri="ws://nas.example.com:5666/websocket?type=main",
        redirect_uri="HTTPS://nas.example.com:5667/websocket?type=main",
        status_code=302,
    )
    client = FakeClient(error)
    monkeypatch.setattr(module, "FnosClient", lambda: client)

    result = await module.run("nas.example.com:5666")

    output = capsys.readouterr().out
    assert result == 0
    assert "HTTP 重定向状态码: 302" in output
    assert error.requested_uri in output
    assert error.redirect_uri in output
    assert "wss://nas.example.com:5667/websocket?type=main" in output
    assert "SDK 未自动重试" in output
    assert client.connect_calls == ["nas.example.com:5666"]
    assert client.closed is True
```

- [ ] **Step 6: 运行专用异常测试并确认 RED**

Run:

```bash
uv run pytest -q tests/test_https_required_error_example.py::test_run_reports_https_required_error_without_retry
```

Expected: FAIL with `AttributeError`，因为示例尚未定义 `run()`。

- [ ] **Step 7: 实现目标异常分支并确认 GREEN**

在 `examples/https_required_error.py` 的导入区加入：

```python
import asyncio
from urllib.parse import urlsplit

from fnos import FnosClient, HTTPSRequiredError
```

在 `main()` 前加入：

```python
async def run(endpoint: str) -> int:
    client = FnosClient()

    try:
        await client.connect(endpoint)
    except HTTPSRequiredError as error:
        suggested_wss_uri = urlsplit(error.redirect_uri)._replace(scheme="wss").geturl()
        print("检测到 fnOS 服务端强制 HTTPS：")
        print(f"HTTP 重定向状态码: {error.status_code}")
        print(f"原始 WS 请求 URI: {error.requested_uri}")
        print(f"服务端 HTTPS 重定向 URI: {error.redirect_uri}")
        print(f"建议使用 WSS URI: {suggested_wss_uri}")
        print("SDK 未自动重试；请由调用方明确改用 WSS。")
        return 0
    finally:
        await client.close()
```

将 `main()` 中的：

```python
    parser.parse_args()
```

替换为：

```python
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run(args.endpoint)))
```

Run:

```bash
uv run pytest -q tests/test_https_required_error_example.py::test_run_reports_https_required_error_without_retry
```

Expected: `1 passed`。

- [ ] **Step 8: 写其他连接错误的失败测试**

在测试文件加入：

```python
@pytest.mark.asyncio
async def test_run_reports_unrecognized_connection_error(monkeypatch, capsys):
    module = load_example()
    client = FakeClient(RuntimeError("connection refused"))
    monkeypatch.setattr(module, "FnosClient", lambda: client)

    result = await module.run("nas.example.com:5666")

    output = capsys.readouterr().out
    assert result == 1
    assert "不是已识别的强制 HTTPS 重定向" in output
    assert "connection refused" in output
    assert client.connect_calls == ["nas.example.com:5666"]
    assert client.closed is True
```

Run:

```bash
uv run pytest -q tests/test_https_required_error_example.py::test_run_reports_unrecognized_connection_error
```

Expected: FAIL，因为 `RuntimeError` 仍原样抛出。

- [ ] **Step 9: 实现其他错误分支并确认 GREEN**

在 `run()` 的 `except HTTPSRequiredError` 与 `finally` 之间加入：

```python
    except Exception as error:
        print(f"连接失败，但不是已识别的强制 HTTPS 重定向: {error}")
        return 1
```

Run:

```bash
uv run pytest -q tests/test_https_required_error_example.py::test_run_reports_unrecognized_connection_error
```

Expected: `1 passed`。

- [ ] **Step 10: 写正常连接成功的失败测试**

在测试文件加入：

```python
@pytest.mark.asyncio
async def test_run_reports_when_https_redirect_is_not_detected(monkeypatch, capsys):
    module = load_example()
    client = FakeClient()
    monkeypatch.setattr(module, "FnosClient", lambda: client)

    result = await module.run("nas.example.com:5666")

    output = capsys.readouterr().out
    assert result == 0
    assert "未检测到强制 HTTPS 重定向" in output
    assert client.connect_calls == ["nas.example.com:5666"]
    assert client.closed is True
```

Run:

```bash
uv run pytest -q tests/test_https_required_error_example.py::test_run_reports_when_https_redirect_is_not_detected
```

Expected: FAIL，因为成功路径当前隐式返回 `None` 且没有诊断输出。

- [ ] **Step 11: 实现成功分支并确认 GREEN**

在 `run()` 的两个 `except` 与 `finally` 之间加入：

```python
    else:
        print("连接成功，未检测到强制 HTTPS 重定向。")
        return 0
```

Run:

```bash
uv run pytest -q tests/test_https_required_error_example.py
```

Expected: `4 passed`。

- [ ] **Step 12: 写 README 和 CHANGELOG 的失败测试**

在测试文件加入：

```python
def test_readme_and_changelog_document_https_required_error_example():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    unreleased = changelog.split("## [Unreleased]", 1)[1].split("## [", 1)[0]

    assert (
        "| `https_required_error.py` | 演示如何识别 fnOS 强制 HTTPS 重定向"
        "并提示调用方改用 WSS |"
    ) in readme
    assert (
        "uv run python examples/https_required_error.py "
        "-e nas-10.timandes.net:5666"
    ) in readme
    assert "本诊断脚本只接受 endpoint" in readme
    assert "### Added" in unreleased
    assert "新增 `examples/https_required_error.py` 强制 HTTPS 诊断示例" in unreleased
```

Run:

```bash
uv run pytest -q tests/test_https_required_error_example.py::test_readme_and_changelog_document_https_required_error_example
```

Expected: FAIL，因为 README 和 CHANGELOG 尚未记录新示例。

- [ ] **Step 13: 补充 README 与 CHANGELOG 并确认 GREEN**

在 README 的示例程序表加入：

```markdown
| `https_required_error.py` | 演示如何识别 fnOS 强制 HTTPS 重定向并提示调用方改用 WSS |
```

在 README 的 SSL/WSS 连接说明末尾加入：

````markdown
不同于上述认证示例，本诊断脚本只接受 endpoint；它只检测并展示异常，不会自动重试：

```bash
uv run python examples/https_required_error.py -e nas-10.timandes.net:5666
```
````

在 CHANGELOG 的 `[Unreleased]` → `Added` 中加入：

```markdown
- 新增 `examples/https_required_error.py` 强制 HTTPS 诊断示例
```

Run:

```bash
uv run pytest -q tests/test_https_required_error_example.py
```

Expected: `5 passed`。

- [ ] **Step 14: 运行全量验证并提交示例**

Run:

```bash
uv run pytest -q tests/test_https_required_error.py tests/test_https_required_error_example.py
uv run pytest -q -m "not integration"
git diff --check
git status --short
```

Expected:

- 两个 HTTPS-required 测试模块全部 PASS；
- 全量非集成测试全部 PASS，无 error 或新增 warning；
- `git diff --check` 无输出；
- 差异仅包含示例、对应测试、README 和 CHANGELOG。

Commit:

```bash
git add examples/https_required_error.py tests/test_https_required_error_example.py README.md CHANGELOG.md
git commit -m "feat: add HTTPS-required error example"
```
