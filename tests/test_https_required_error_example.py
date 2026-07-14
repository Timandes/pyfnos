import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from fnos import HTTPSRequiredError


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "https_required_error.py"


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


@pytest.mark.asyncio
async def test_run_reports_https_required_error_without_retry(monkeypatch, capsys):
    module = load_example()
    error = HTTPSRequiredError(
        requested_uri="ws://nas.example.com:5666/websocket?type=main",
        redirect_uri="https://nas.example.com:5667/websocket?type=main",
        status_code=302,
    )
    client = FakeClient(error)
    monkeypatch.setattr(module, "FnosClient", lambda: client, raising=False)

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


def test_readme_and_changelog_document_https_required_error_example():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    assert "`https_required_error.py`" in readme
    assert (
        "uv run python examples/https_required_error.py "
        "-e nas-10.timandes.net:5666"
    ) in readme
    assert "新增 `examples/https_required_error.py` 强制 HTTPS 诊断示例" in changelog
