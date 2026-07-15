# Disk Temperature Error Details and 2FA Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让磁盘温度诊断工具支持与 examples 一致的 SSL/2FA 认证，并输出经过脱敏的失败阶段、异常详情和可选 traceback。

**Architecture:** 新增独立的 `tools/common.py`，提供与 `examples/common.py` 同接口的参数、连接和 2FA 登录辅助函数。诊断脚本通过这些辅助函数认证，并用统一的脱敏与异常格式化函数处理顶层致命错误和磁盘接口非致命错误。

**Tech Stack:** Python 3.11+、`argparse`、`asyncio`、`getpass`、`re`、`traceback`、现有 `fnos` SDK、pytest、pytest-asyncio。

## Global Constraints

- 不新增第三方依赖，不修改 `fnos` 包的公共 API。
- 新增 `tools/common.py`，公共接口为 `add_auth_arguments()`、`connect_client()`、`login_with_twofa()`。
- 认证参数和行为与 `examples/common.py` 一致，包括 `--code`、`--trust-device`、`--use-ssl` 和 `--skip-ssl-verify`。
- 未提供 `--code` 时必须使用 `getpass.getpass()`，验证码不得回显。
- 诊断脚本新增 `--debug`，默认关闭。
- 默认错误必须包含失败阶段、异常类型、异常详情和 debug 提示。
- debug traceback 与摘要必须经过同一脱敏函数。
- 密码、命令行验证码、token、longToken、accessToken 和 secret 不得出现在输出中。
- 不改变温度优先级、SMART 回退、磁盘顺序或部分失败继续处理的行为。
- Git 提交消息使用英文 Angular/Conventional Commits，禁止 `Co-Authored-By`。

---

## File Structure

- Create: `tools/common.py` — tools 独立的共享认证参数、连接和 2FA 登录辅助函数。
- Create: `tests/test_tools_common.py` — tools 认证辅助函数的行为测试。
- Modify: `tools/list_disk_temperatures.py` — 接入共享认证、阶段跟踪、异常详情、脱敏和 debug traceback。
- Modify: `tests/test_list_disk_temperatures_tool.py` — 更新 CLI、运行期、非致命错误和敏感信息测试。
- Reference: `examples/common.py` — tools common 的行为基准。
- Reference: `docs/superpowers/specs/2026-07-15-disk-temperature-error-details-and-twofa-design.md` — 已批准设计。

### Task 1: Tools Authentication Helpers and 2FA

**Files:**
- Create: `tests/test_tools_common.py`
- Create: `tools/common.py`

**Interfaces:**
- Consumes: `client.connect()`、`client.login()`、`client.submit_twofa_code()`。
- Produces: `add_auth_arguments(parser, *, default_user=None, default_password=None, default_endpoint="your-custom-endpoint.com:5666")`、`connect_client(client, args)`、`login_with_twofa(client, args_or_user, password=None, *, code=None, trust_device=False)`。

- [ ] **Step 1: Write failing tests for shared arguments, SSL connection, and 2FA**

Create `tests/test_tools_common.py`:

```python
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
```

- [ ] **Step 2: Run tests and verify the missing-module failure**

Run:

```bash
uv run pytest tests/test_tools_common.py -v
```

Expected: all tests FAIL inside their test bodies with `FileNotFoundError` because `tools/common.py` does not exist.

- [ ] **Step 3: Implement tools/common.py with examples-compatible behavior**

Create `tools/common.py`:

```python
"""Shared authentication helpers for pyfnos tools."""

import getpass


def add_auth_arguments(
    parser,
    *,
    default_user=None,
    default_password=None,
    default_endpoint="your-custom-endpoint.com:5666",
):
    """Add common connection, login, and two-factor arguments."""
    parser.add_argument(
        "--user",
        type=str,
        default=default_user,
        required=default_user is None,
        help="用户名",
    )
    parser.add_argument(
        "--password",
        type=str,
        default=default_password,
        required=default_password is None,
        help="密码",
    )
    parser.add_argument(
        "-e",
        "--endpoint",
        type=str,
        default=default_endpoint,
        help=f"服务器地址 (默认: {default_endpoint})",
    )
    parser.add_argument(
        "--code",
        type=str,
        help="6位两步验证码；不提供时从终端读取",
    )
    parser.add_argument(
        "--trust-device",
        action="store_true",
        help="请求服务器信任当前设备",
    )
    parser.add_argument(
        "--use-ssl",
        action="store_true",
        help="使用 SSL/WSS 连接",
    )
    parser.add_argument(
        "--skip-ssl-verify",
        type=lambda x: x.lower() == "true",
        default=True,
        help="跳过 SSL 证书验证 (默认: True)",
    )


async def connect_client(client, args):
    """Connect a client using common tool arguments."""
    await client.connect(
        args.endpoint,
        use_ssl=args.use_ssl,
        skip_ssl_verify=args.skip_ssl_verify,
    )


async def login_with_twofa(
    client,
    args_or_user,
    password=None,
    *,
    code=None,
    trust_device=False,
):
    """Login and complete optional two-factor verification."""
    if hasattr(args_or_user, "user") and hasattr(args_or_user, "password"):
        username = args_or_user.user
        password = args_or_user.password
        code = getattr(args_or_user, "code", code)
        trust_device = getattr(args_or_user, "trust_device", trust_device)
    else:
        username = args_or_user

    result = await client.login(username, password)

    if result.get("twofaRequired"):
        print(
            "账号需要两步验证，安全邮箱: "
            f"{result.get('secureEmail', '未知')}"
        )
        code = code or getpass.getpass("请输入 6 位两步验证码: ")
        result = await client.submit_twofa_code(
            code,
            trust_device=trust_device,
        )
    elif result.get("twofaSetupRequired"):
        raise RuntimeError("该账号需要先绑定两步验证后才能继续登录")

    if result.get("result") != "succ":
        raise RuntimeError(
            result.get(
                "msg",
                result.get("errmsg", f"登录失败: {result}"),
            )
        )

    return result
```

- [ ] **Step 4: Run tools common tests and verify they pass**

Run:

```bash
uv run pytest tests/test_tools_common.py -v
```

Expected: 6 tests PASS; ordinary login succeeds, and CLI code plus prompted code both reach `submit_twofa_code()`.

- [ ] **Step 5: Commit tools authentication helpers**

```bash
git add tools/common.py tests/test_tools_common.py
git commit -m "feat: add tools authentication helpers"
```

### Task 2: Detailed, Staged, and Redacted Diagnostic Errors

**Files:**
- Modify: `tools/list_disk_temperatures.py`
- Modify: `tests/test_list_disk_temperatures_tool.py`

**Interfaces:**
- Consumes: Task 1's `add_auth_arguments()`、`connect_client()`、`login_with_twofa()`。
- Produces: `_redact(text: str, sensitive_values: tuple[object, ...] = ()) -> str`、`_exception_summary(error: Exception, sensitive_values: tuple[object, ...] = ()) -> str`、`_print_failure(stage: str, error: Exception, args: argparse.Namespace) -> None`，以及包含 `--debug` 的 CLI。

- [ ] **Step 1: Update the test loader for tools/common.py and add a runtime argument helper**

Replace `load_tool_module()` in `tests/test_list_disk_temperatures_tool.py` with:

```python
def load_tool_module():
    module_name = "list_disk_temperatures_tool"
    tools_path = str(TOOL_PATH.parent)
    previous_common = sys.modules.pop("common", None)
    sys.path.insert(0, tools_path)
    try:
        spec = importlib.util.spec_from_file_location(module_name, TOOL_PATH)
        assert spec is not None
        assert spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(tools_path)
        sys.modules.pop("common", None)
        if previous_common is not None:
            sys.modules["common"] = previous_common
```

Add after `tool = load_tool_module()`:

```python
def make_args(**overrides):
    values = {
        "user": "admin",
        "password": "password",
        "endpoint": "nas.example.com:5666",
        "code": None,
        "trust_device": False,
        "use_ssl": False,
        "skip_ssl_verify": True,
        "debug": False,
    }
    values.update(overrides)
    return argparse.Namespace(**values)
```

- [ ] **Step 2: Write failing tests for detailed non-fatal errors and expanded CLI**

Update the expected skip records in `test_monitor_failure_falls_back_for_all_disks_and_smart_failure_isolated()` to:

```python
    assert results[0].skipped == [
        "ResourceMonitor.disk()（接口调用失败: "
        "TimeoutError: monitor unavailable）"
    ]
    assert results[1].skipped == [
        "ResourceMonitor.disk()（接口调用失败: "
        "TimeoutError: monitor unavailable）",
        "Store.get_disk_smart('sdb')（接口调用失败: "
        "OSError: device unavailable）",
    ]
```

Replace `test_parse_args_requires_credentials_and_endpoint()` with:

```python
def test_parse_args_includes_shared_auth_and_debug_options():
    args = tool.parse_args(
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
            "--debug",
        ]
    )

    assert args == make_args(
        code="123456",
        trust_device=True,
        use_ssl=True,
        skip_ssl_verify=False,
        debug=True,
    )
```

Run these two tests:

```bash
uv run pytest \
  tests/test_list_disk_temperatures_tool.py::test_monitor_failure_falls_back_for_all_disks_and_smart_failure_isolated \
  tests/test_list_disk_temperatures_tool.py::test_parse_args_includes_shared_auth_and_debug_options \
  -v
```

Expected: FAIL because exception messages and shared auth/debug options are not yet exposed.

- [ ] **Step 3: Write failing tests for stage details, traceback, and redaction**

Replace the existing login-failure and unexpected-failure tests with:

```python
@pytest.mark.asyncio
async def test_run_login_failure_reports_stage_type_and_detail(
    monkeypatch,
    capsys,
):
    class FailedLoginClient:
        async def connect(self, endpoint, *, use_ssl, skip_ssl_verify):
            return None

        async def login(self, user, password):
            return {"result": "fail", "errmsg": "验证码错误"}

        async def close(self):
            self.closed = True

    client = FailedLoginClient()
    monkeypatch.setattr(tool, "FnosClient", lambda: client)

    exit_code = await tool.run(make_args())

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == (
        "错误: 登录或两步验证阶段失败\n"
        "异常类型: RuntimeError\n"
        "异常详情: 验证码错误\n"
        "提示: 使用 --debug 查看完整 traceback\n"
    )
    assert client.closed is True


@pytest.mark.asyncio
async def test_run_debug_traceback_redacts_credentials(monkeypatch, capsys):
    password = "top-secret-password"
    code = "654321"
    token = "token-value"
    long_token = "long-token-value"
    access_token = "access-token-value"
    secret = "secret-value"

    class FailingClient:
        async def connect(self, endpoint, *, use_ssl, skip_ssl_verify):
            raise RuntimeError(
                f"password={password} token='{token}' "
                f"longToken={long_token} accessToken=\"{access_token}\" "
                f"secret={secret} code={code}"
            )

        async def close(self):
            self.closed = True

    client = FailingClient()
    monkeypatch.setattr(tool, "FnosClient", lambda: client)

    exit_code = await tool.run(
        make_args(password=password, code=code, debug=True)
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "错误: 连接阶段失败" in captured.err
    assert "异常类型: RuntimeError" in captured.err
    assert "Traceback (most recent call last):" in captured.err
    assert "password=***" in captured.err
    assert "token='***'" in captured.err
    assert password not in captured.err
    assert code not in captured.err
    assert token not in captured.err
    assert long_token not in captured.err
    assert access_token not in captured.err
    assert secret not in captured.err
    assert client.closed is True


@pytest.mark.asyncio
async def test_run_disk_enumeration_failure_reports_stage(monkeypatch, capsys):
    class Client:
        async def connect(self, endpoint, *, use_ssl, skip_ssl_verify):
            return None

        async def login(self, user, password):
            return {"result": "succ"}

        async def close(self):
            self.closed = True

    class FailingStore:
        def __init__(self, client):
            pass

        async def list_disks(self):
            raise RuntimeError("stor.listDisk failed")

    client = Client()
    monkeypatch.setattr(tool, "FnosClient", lambda: client)
    monkeypatch.setattr(tool, "Store", FailingStore)

    exit_code = await tool.run(make_args())

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "错误: 磁盘枚举与温度获取阶段失败" in captured.err
    assert "异常详情: stor.listDisk failed" in captured.err
    assert client.closed is True
```

Run:

```bash
uv run pytest \
  tests/test_list_disk_temperatures_tool.py::test_run_login_failure_reports_stage_type_and_detail \
  tests/test_list_disk_temperatures_tool.py::test_run_debug_traceback_redacts_credentials \
  tests/test_list_disk_temperatures_tool.py::test_run_disk_enumeration_failure_reports_stage \
  -v
```

Expected: FAIL because the current script does not track stages, print messages, support debug, or redact traceback output.

- [ ] **Step 4: Update successful runtime test to exercise tools common**

In `test_run_partial_unknown_returns_zero_and_always_closes_client()`, replace the fake client's connection signature and argument construction with:

```python
        async def connect(self, endpoint, *, use_ssl, skip_ssl_verify):
            self.connected_endpoint = endpoint
            self.ssl_options = (use_ssl, skip_ssl_verify)

        async def login(self, user, password):
            self.login_credentials = (user, password)
            return {"result": "succ", "token": "must-not-be-printed"}
```

Use `args = make_args()` and add:

```python
    assert client.ssl_options == (False, True)
```

This test intentionally remains RED before the production change because the old direct connection call does not pass the required SSL keyword arguments. After Step 5 it proves that `connect_client()` and `login_with_twofa()` integrate without changing successful temperature output.

- [ ] **Step 5: Implement shared auth integration, detail formatting, redaction, and traceback**

Add imports to `tools/list_disk_temperatures.py`:

```python
import re
import traceback

from common import add_auth_arguments, connect_client, login_with_twofa
```

Add after `MISSING = object()`:

```python
AUTH_VALUE_PATTERN = re.compile(
    r"(?i)(?P<prefix>[\"']?(?:accessToken|longToken|token|secret|password)"
    r"[\"']?\s*[:=]\s*)(?P<quote>[\"']?)(?P<value>[^\"',\s}\]]+)"
    r"(?P=quote)"
)
```

Replace `_exception_summary()` with these complete helpers:

```python
def _redact(
    text: str,
    sensitive_values: tuple[object, ...] = (),
) -> str:
    redacted = text
    for value in sensitive_values:
        if value is not None and str(value):
            redacted = redacted.replace(str(value), "***")

    def replace_auth_value(match: re.Match) -> str:
        return (
            f"{match.group('prefix')}"
            f"{match.group('quote')}***{match.group('quote')}"
        )

    return AUTH_VALUE_PATTERN.sub(replace_auth_value, redacted)


def _exception_parts(
    error: Exception,
    sensitive_values: tuple[object, ...] = (),
) -> tuple[str, str]:
    detail = str(error).strip() or "无详细信息"
    return type(error).__name__, _redact(detail, sensitive_values)


def _exception_summary(
    error: Exception,
    sensitive_values: tuple[object, ...] = (),
) -> str:
    error_type, detail = _exception_parts(error, sensitive_values)
    return f"{error_type}: {detail}"


def _print_failure(
    stage: str,
    error: Exception,
    args: argparse.Namespace,
) -> None:
    sensitive_values = (
        getattr(args, "password", None),
        getattr(args, "code", None),
    )
    error_type, detail = _exception_parts(error, sensitive_values)
    print(f"错误: {stage}阶段失败", file=sys.stderr)
    print(f"异常类型: {error_type}", file=sys.stderr)
    print(f"异常详情: {detail}", file=sys.stderr)

    if getattr(args, "debug", False):
        formatted = "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )
        print(_redact(formatted, sensitive_values), file=sys.stderr, end="")
    else:
        print("提示: 使用 --debug 查看完整 traceback", file=sys.stderr)
```

Replace `parse_args()` with:

```python
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="fnOS 磁盘温度诊断工具")
    add_auth_arguments(parser)
    parser.add_argument(
        "--debug",
        action="store_true",
        help="输出经过脱敏的完整 traceback",
    )
    return parser.parse_args(argv)
```

Replace `run()` with:

```python
async def run(args: argparse.Namespace) -> int:
    client = FnosClient()
    stage = "连接"
    try:
        await connect_client(client, args)
        stage = "登录或两步验证"
        await login_with_twofa(client, args)
        stage = "磁盘枚举与温度获取"
        results = await collect_disk_temperatures(
            Store(client),
            ResourceMonitor(client),
        )
        print(format_disk_temperatures(results))
        return 0
    except Exception as error:
        _print_failure(stage, error, args)
        return 1
    finally:
        await client.close()
```

The existing non-fatal exception call sites continue calling `_exception_summary(error)`; the new helper automatically upgrades them to `Type: detail` and applies auth-field redaction.

- [ ] **Step 6: Run all targeted tests and fix only implementation defects**

Run:

```bash
uv run pytest \
  tests/test_tools_common.py \
  tests/test_list_disk_temperatures_tool.py \
  -v
```

Expected: all tools common and disk diagnostic tests PASS; no secret test values appear in captured output.

- [ ] **Step 7: Verify CLI help and repository regression suite**

Run:

```bash
uv run python tools/list_disk_temperatures.py --help
uv run python -m py_compile tools/common.py tools/list_disk_temperatures.py
uv run pytest -m "not integration"
git diff --check
```

Expected: help includes shared auth options and `--debug`; both files compile; all non-integration tests PASS; diff check emits no output.

- [ ] **Step 8: Review and commit the diagnostic fix**

Run:

```bash
git diff -- tools/common.py tools/list_disk_temperatures.py tests/test_tools_common.py tests/test_list_disk_temperatures_tool.py
git status --short
```

Expected: only Task 2 changes are uncommitted; authentication helpers remain unchanged from Task 1.

Commit:

```bash
git add tools/list_disk_temperatures.py tests/test_list_disk_temperatures_tool.py
git commit -m "fix: expose disk diagnostic error details"
```
