import argparse
import importlib.util
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
COMMON_PATH = ROOT / "tools" / "common.py"


def load_tools_common():
    module_name = "tools_common_under_test"
    spec = importlib.util.spec_from_file_location(module_name, COMMON_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_add_auth_arguments_exposes_ssl_and_twofa_options():
    common = load_tools_common()
    parser = argparse.ArgumentParser()

    common.add_auth_arguments(parser)
    args = parser.parse_args(
        [
            "--user",
            "admin",
            "--password",
            "password",
            "-e",
            "nas.example.com:5666",
            "--code",
            "123456",
            "--trust-device",
            "--use-ssl",
            "--skip-ssl-verify",
            "false",
        ]
    )

    assert args == argparse.Namespace(
        user="admin",
        password="password",
        endpoint="nas.example.com:5666",
        code="123456",
        trust_device=True,
        use_ssl=True,
        skip_ssl_verify=False,
    )


@pytest.mark.asyncio
async def test_connect_client_passes_ssl_options():
    common = load_tools_common()

    class Client:
        async def connect(self, endpoint, *, use_ssl, skip_ssl_verify):
            self.call = (endpoint, use_ssl, skip_ssl_verify)

    client = Client()
    args = argparse.Namespace(
        endpoint="nas.example.com:5666",
        use_ssl=True,
        skip_ssl_verify=False,
    )

    await common.connect_client(client, args)

    assert client.call == ("nas.example.com:5666", True, False)


@pytest.mark.asyncio
async def test_login_without_twofa_returns_success():
    common = load_tools_common()

    class Client:
        async def login(self, user, password):
            self.login_call = (user, password)
            return {"result": "succ", "token": "token-value"}

    client = Client()

    result = await common.login_with_twofa(client, "admin", "password")

    assert result["result"] == "succ"
    assert client.login_call == ("admin", "password")


@pytest.mark.asyncio
async def test_login_with_twofa_uses_cli_code_and_trust_device():
    common = load_tools_common()

    class Client:
        async def login(self, user, password):
            self.login_call = (user, password)
            return {
                "result": "fail",
                "twofaRequired": True,
                "secureEmail": "a***@example.com",
            }

        async def submit_twofa_code(self, code, *, trust_device):
            self.twofa_call = (code, trust_device)
            return {"result": "succ", "token": "token-value"}

    client = Client()
    args = argparse.Namespace(
        user="admin",
        password="password",
        code="123456",
        trust_device=True,
    )

    result = await common.login_with_twofa(client, args)

    assert result["result"] == "succ"
    assert client.login_call == ("admin", "password")
    assert client.twofa_call == ("123456", True)


@pytest.mark.asyncio
async def test_login_with_twofa_prompts_without_cli_code(monkeypatch):
    common = load_tools_common()

    class Client:
        async def login(self, user, password):
            return {"result": "fail", "twofaRequired": True}

        async def submit_twofa_code(self, code, *, trust_device):
            self.twofa_call = (code, trust_device)
            return {"result": "succ"}

    client = Client()
    monkeypatch.setattr(common.getpass, "getpass", lambda prompt: "654321")
    args = argparse.Namespace(
        user="admin",
        password="password",
        code=None,
        trust_device=False,
    )

    await common.login_with_twofa(client, args)

    assert client.twofa_call == ("654321", False)


@pytest.mark.asyncio
async def test_login_with_twofa_reports_setup_and_server_failures():
    common = load_tools_common()

    class SetupClient:
        async def login(self, user, password):
            return {"result": "fail", "twofaSetupRequired": True}

    with pytest.raises(RuntimeError, match="需要先绑定两步验证"):
        await common.login_with_twofa(SetupClient(), "admin", "password")

    class FailedClient:
        async def login(self, user, password):
            return {"result": "fail", "errmsg": "验证码错误"}

    with pytest.raises(RuntimeError, match="验证码错误"):
        await common.login_with_twofa(FailedClient(), "admin", "password")


@pytest.mark.asyncio
async def test_connect_and_login_combines_common_auth_steps():
    common = load_tools_common()

    class Client:
        async def connect(self, endpoint, *, use_ssl, skip_ssl_verify):
            self.connect_call = (endpoint, use_ssl, skip_ssl_verify)

        async def login(self, user, password):
            self.login_call = (user, password)
            return {"result": "succ"}

    client = Client()
    args = argparse.Namespace(
        user="admin",
        password="password",
        endpoint="nas.example.com:5666",
        code=None,
        trust_device=False,
        use_ssl=True,
        skip_ssl_verify=False,
    )

    result = await common.connect_and_login(client, args)

    assert result == {"result": "succ"}
    assert client.connect_call == ("nas.example.com:5666", True, False)
    assert client.login_call == ("admin", "password")
