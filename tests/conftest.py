"""pytest integration helpers for the sibling fnos-mock-server project."""

from __future__ import annotations

import os
import socket
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path

import pytest


MOCK_HOST = "127.0.0.1"
MOCK_PORT = 5666


def _find_mock_server_dir() -> Path | None:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "fnos-mock-server"
        if (candidate / "server" / "main.py").exists():
            return candidate
    return None


def _is_port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex((host, port)) == 0


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((MOCK_HOST, 0))
        return sock.getsockname()[1]


def _start_mock_server(port: int, env: dict[str, str] | None = None) -> subprocess.Popen:
    mock_server_dir = _find_mock_server_dir()
    if mock_server_dir is None:
        pytest.skip("未找到相邻的 fnos-mock-server 项目")

    process_env = os.environ.copy()
    if env:
        process_env.update(env)

    process = subprocess.Popen(
        [
            "uv",
            "run",
            "python",
            "-m",
            "server.main",
            "--host",
            MOCK_HOST,
            "--port",
            str(port),
            "--log-level",
            "ERROR",
        ],
        cwd=mock_server_dir,
        env=process_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout else ""
            raise RuntimeError(f"fnos-mock-server 启动失败: {output}")
        if _is_port_open(MOCK_HOST, port):
            return process
        time.sleep(0.1)

    process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()
    raise RuntimeError(f"fnos-mock-server 未能在端口 {port} 启动")


def _stop_mock_server(process: subprocess.Popen) -> None:
    process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=3)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    integration_items = [
        item for item in items if item.get_closest_marker("integration")
    ]
    mock_server_dir = _find_mock_server_dir()

    if integration_items and mock_server_dir is None and not _is_port_open(MOCK_HOST, MOCK_PORT):
        skip_marker = pytest.mark.skip(reason="未找到相邻的 fnos-mock-server 项目")
        for item in integration_items:
            item.add_marker(skip_marker)
        config._fnos_needs_mock_server = False  # type: ignore[attr-defined]
        return

    config._fnos_needs_mock_server = bool(integration_items)  # type: ignore[attr-defined]


@pytest.fixture(scope="session", autouse=True)
def fnos_mock_server(pytestconfig: pytest.Config) -> Iterator[str | None]:
    if not getattr(pytestconfig, "_fnos_needs_mock_server", False):
        yield None
        return

    endpoint = f"{MOCK_HOST}:{MOCK_PORT}"
    if _is_port_open(MOCK_HOST, MOCK_PORT):
        yield endpoint
        return

    process = _start_mock_server(MOCK_PORT)
    try:
        yield endpoint
    finally:
        _stop_mock_server(process)


@pytest.fixture
def fnos_twofa_mock_endpoint() -> Iterator[str]:
    port = _free_port()
    process = _start_mock_server(port, env={"FNOS_MOCK_TWOFA_USERS": "admin"})
    try:
        yield f"{MOCK_HOST}:{port}"
    finally:
        _stop_mock_server(process)
