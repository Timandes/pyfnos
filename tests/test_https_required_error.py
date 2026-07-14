import asyncio
from pathlib import Path
import subprocess
import sys
from unittest.mock import AsyncMock, patch

import pytest
from websockets.datastructures import Headers
from websockets.exceptions import InvalidStatus, InvalidURI
from websockets.http11 import Response

import fnos
from fnos import FnosClient, HTTPSRequiredError


ROOT = Path(__file__).resolve().parents[1]


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


def test_fnos_import_does_not_require_preloading_websockets_exceptions():
    completed = subprocess.run(
        [sys.executable, "-c", "import fnos"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert completed.returncode == 0, completed.stderr


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
