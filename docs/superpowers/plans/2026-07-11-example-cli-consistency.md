# Example CLI Consistency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 9 个新增示例补齐与原有 `examples/` 一致的 CLI 帮助、运行提示、异常处理和 README 用法。

**Architecture:** 保留每个示例“一次执行全部查询”的现有结构，继续复用 `examples/common.py` 的认证、SSL 和 2FA 工具。通过真实子进程 `--help` 和注入连接失败的 `main()` 行为测试约束 CLI，不增加新的命令框架。

**Tech Stack:** Python 3.11+、`argparse`、`asyncio`、pytest 9、pytest-asyncio、uv。

## Global Constraints

- 不增加子命令、`--action` 或交互式选择。
- 不手写 `usage=`，由 `argparse` 自动生成 `usage:`。
- 不暴露 SDK `timeout` 参数。
- 不修改公共认证参数的默认策略。
- 不改变查询顺序、SDK endpoint 或响应结构。
- 所有示例必须在 `finally` 中关闭客户端。
- Git 提交使用英文 Conventional Commits，且不得包含 `Co-Authored-By`。

---

## File Structure

- `tests/test_examples_help.py`：统一验证新增示例的帮助输出、模块说明和连接失败行为。
- `examples/backup_manager.py`：备份方向参数与备份任务查询演示。
- `examples/download_center.py`：下载状态位掩码、初始化标志及下载查询演示。
- `examples/ip_blocker.py`：IP 规则查询演示。
- `examples/license_manager.py`：软件许可分页参数与查询演示。
- `examples/live_update.py`：在线更新状态查询演示。
- `examples/mount_manager.py`：挂载列表和设置查询演示。
- `examples/network_server.py`：DDNS 分页参数及网络服务查询演示。
- `examples/security.py`：防火墙和进程流量查询演示。
- `examples/system_restore.py`：系统恢复信息查询演示。
- `README.md`：提供 9 条可复制命令和领域参数表。

### Task 1: 完整的 `--help` 契约与领域参数

**Files:**
- Modify: `tests/test_examples_help.py`
- Modify: `examples/backup_manager.py`
- Modify: `examples/download_center.py`
- Modify: `examples/license_manager.py`
- Modify: `examples/network_server.py`

**Interfaces:**
- Consumes: `examples.common.add_auth_arguments(parser)`。
- Produces: `download_center.py --init-flag {true,false}`，以及所有领域参数的稳定中文帮助文本。

- [ ] **Step 1: 写帮助输出失败测试**

在 `tests/test_examples_help.py` 中加入以下契约数据和测试：

```python
NEW_EXAMPLE_HELP = {
    "backup_manager.py": {
        "description": "fnOS 备份任务查询示例",
        "domain_help": (
            "--direction {0,1}",
            "备份任务方向：0=上传，1=下载（默认：0）",
        ),
    },
    "download_center.py": {
        "description": "fnOS 下载中心查询示例",
        "domain_help": (
            "--state-filter STATE_FILTER",
            "下载任务状态位掩码（默认：65535）",
            "--init-flag {true,false}",
            "下载任务初始化标志（默认：true）",
        ),
    },
    "ip_blocker.py": {
        "description": "fnOS IP 阻止规则查询示例",
        "domain_help": (),
    },
    "license_manager.py": {
        "description": "fnOS 软件许可查询示例",
        "domain_help": (
            "--page PAGE",
            "软件许可页码（默认：1）",
            "--page-size PAGE_SIZE",
            "软件许可每页数量（默认：200）",
        ),
    },
    "live_update.py": {
        "description": "fnOS 在线更新状态查询示例",
        "domain_help": (),
    },
    "mount_manager.py": {
        "description": "fnOS 挂载管理查询示例",
        "domain_help": (),
    },
    "network_server.py": {
        "description": "fnOS 网络服务查询示例",
        "domain_help": (
            "--page PAGE",
            "DDNS 记录页码（默认：1）",
            "--page-size PAGE_SIZE",
            "DDNS 记录每页数量（默认：200）",
        ),
    },
    "security.py": {
        "description": "fnOS 安全状态查询示例",
        "domain_help": (),
    },
    "system_restore.py": {
        "description": "fnOS 系统恢复信息查询示例",
        "domain_help": (),
    },
}


@pytest.mark.parametrize(
    ("example_name", "contract"),
    sorted(NEW_EXAMPLE_HELP.items()),
    ids=lambda value: value if isinstance(value, str) else None,
)
def test_new_example_help_is_complete(example_name, contract):
    completed = subprocess.run(
        [sys.executable, str(ROOT / "examples" / example_name), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert completed.returncode == 0, completed.stderr
    expected = (
        "usage:",
        contract["description"],
        "--user USER",
        "--password PASSWORD",
        "--endpoint ENDPOINT",
        "--code CODE",
        "--trust-device",
        "--use-ssl",
        "--skip-ssl-verify SKIP_SSL_VERIFY",
        *contract["domain_help"],
    )
    for fragment in expected:
        assert fragment in completed.stdout, (example_name, fragment)
```

- [ ] **Step 2: 运行测试并确认 RED**

Run:

```bash
uv run pytest -q tests/test_examples_help.py::test_new_example_help_is_complete
```

Expected: FAIL；至少缺少 `--init-flag {true,false}`，且现有领域参数没有默认值帮助文本。

- [ ] **Step 3: 补齐四个示例的领域参数定义**

在 `examples/backup_manager.py` 中替换参数定义：

```python
parser.add_argument(
    "--direction",
    type=int,
    choices=(0, 1),
    default=0,
    help="备份任务方向：0=上传，1=下载（默认：0）",
)
```

在 `examples/download_center.py` 中加入严格布尔解析，并将两个参数传给 SDK：

```python
def parse_bool(value: str) -> bool:
    normalized = value.lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise argparse.ArgumentTypeError("必须是 true 或 false")


parser.add_argument(
    "--state-filter",
    type=int,
    default=65535,
    help="下载任务状态位掩码（默认：65535）",
)
parser.add_argument(
    "--init-flag",
    type=parse_bool,
    choices=(True, False),
    default=True,
    metavar="{true,false}",
    help="下载任务初始化标志（默认：true）",
)

print(
    "下载任务:",
    await download.query_tasks(
        state_filter=args.state_filter,
        init_flag=args.init_flag,
    ),
)
```

在 `examples/license_manager.py` 中替换分页参数：

```python
parser.add_argument(
    "--page",
    type=int,
    default=1,
    help="软件许可页码（默认：1）",
)
parser.add_argument(
    "--page-size",
    type=int,
    default=200,
    help="软件许可每页数量（默认：200）",
)
```

在 `examples/network_server.py` 中替换分页参数：

```python
parser.add_argument(
    "--page",
    type=int,
    default=1,
    help="DDNS 记录页码（默认：1）",
)
parser.add_argument(
    "--page-size",
    type=int,
    default=200,
    help="DDNS 记录每页数量（默认：200）",
)
```

- [ ] **Step 4: 运行帮助测试并确认 GREEN**

Run:

```bash
uv run pytest -q tests/test_examples_help.py::test_new_example_help_is_complete
```

Expected: `9 passed`。

- [ ] **Step 5: 提交帮助契约**

```bash
git add tests/test_examples_help.py examples/backup_manager.py examples/download_center.py examples/license_manager.py examples/network_server.py
git commit -m "feat: complete new example CLI help"
```

### Task 2: 与原有示例一致的运行和异常处理

**Files:**
- Modify: `tests/test_examples_help.py`
- Modify: `examples/backup_manager.py`
- Modify: `examples/download_center.py`
- Modify: `examples/ip_blocker.py`
- Modify: `examples/license_manager.py`
- Modify: `examples/live_update.py`
- Modify: `examples/mount_manager.py`
- Modify: `examples/network_server.py`
- Modify: `examples/security.py`
- Modify: `examples/system_restore.py`

**Interfaces:**
- Consumes: `add_auth_arguments`、`connect_client`、`login_with_twofa`。
- Produces: 每个 `main()` 在连接异常时打印统一状态并关闭客户端；每个模块提供中文 docstring。

- [ ] **Step 1: 写模块说明和连接失败行为测试**

在 `tests/test_examples_help.py` 中加入：

```python
@pytest.mark.parametrize("example_name", sorted(NEW_EXAMPLES))
def test_new_example_has_module_documentation(example_name, monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "examples"))
    module = load_example(ROOT / "examples" / example_name)

    assert module.__doc__
    assert "示例" in module.__doc__


@pytest.mark.asyncio
@pytest.mark.parametrize("example_name", sorted(NEW_EXAMPLES))
async def test_new_example_reports_connection_failure_and_closes(
    example_name,
    monkeypatch,
    capsys,
):
    monkeypatch.syspath_prepend(str(ROOT / "examples"))
    module = load_example(ROOT / "examples" / example_name)
    client = FailingConnectionClient()

    async def fail_connection(_client, _args):
        raise RuntimeError("connection failed")

    monkeypatch.setattr(module, "FnosClient", lambda: client)
    monkeypatch.setattr(module, "connect_client", fail_connection)
    monkeypatch.setattr(
        sys,
        "argv",
        [example_name, "--user", "admin", "--password", "admin"],
    )

    await module.main()

    output = capsys.readouterr().out
    assert "正在连接到服务器" in output
    assert "发生错误: connection failed" in output
    assert "连接已关闭" in output
    assert client.closed
```

- [ ] **Step 2: 运行测试并确认 RED**

Run:

```bash
uv run pytest -q tests/test_examples_help.py -k "module_documentation or reports_connection_failure"
```

Expected: FAIL；模块 docstring 为空，且 `connect_and_login()` 异常会直接向外传播。

- [ ] **Step 3: 统一 9 个示例的公共运行骨架**

每个文件把公共工具导入替换为：

```python
from common import add_auth_arguments, connect_client, login_with_twofa
```

在 shebang 后加入与文件领域对应的 docstring，例如：

```python
"""BackupManager 备份任务查询示例。"""
```

9 个 docstring 分别使用：

```text
BackupManager 备份任务查询示例。
DownloadCenter 下载中心查询示例。
IPBlocker IP 阻止规则查询示例。
LicenseManager 软件许可查询示例。
LiveUpdate 在线更新状态查询示例。
MountManager 挂载管理查询示例。
NetworkServer 网络服务查询示例。
Security 安全状态查询示例。
SystemRestore 系统恢复信息查询示例。
```

每个 `main()` 在创建 `client` 后使用以下控制流；将紧随其后的逐文件查询体插入
`print("登录成功")` 与 `except Exception` 之间：

```python
client = FnosClient()
try:
    print("正在连接到服务器...")
    await connect_client(client, args)
    print("连接已建立")

    print("正在登录...")
    await login_with_twofa(client, args)
    print("登录成功")

except Exception as exc:
    print(f"发生错误: {exc}")
finally:
    await client.close()
    print("连接已关闭")
```

各文件必须保留的查询体如下：

```python
# backup_manager.py
print("备份任务:", await BackupManager(client).list_tasks(args.direction))

# download_center.py
download = DownloadCenter(client)
print("默认保存目录:", await download.get_default_save_directory())
print("下载统计:", await download.get_statistics())
print(
    "下载任务:",
    await download.query_tasks(
        state_filter=args.state_filter,
        init_flag=args.init_flag,
    ),
)

# ip_blocker.py
blocker = IPBlocker(client)
print("允许列表:", await blocker.list_allowed_addresses())
print("自动阻止规则:", await blocker.get_auto_block_rule())
print("拒绝列表:", await blocker.list_denied_addresses())

# license_manager.py
print(
    "软件许可:",
    await LicenseManager(client).list(args.page, args.page_size),
)

# live_update.py
print("在线更新状态:", await LiveUpdate(client).get_status())

# mount_manager.py
mounts = MountManager(client)
print("挂载列表:", await mounts.list_mounts())
print("挂载设置:", await mounts.get_settings())

# network_server.py
server = NetworkServer(client)
print("证书:", await server.list_certificates())
print("连接配置:", await server.get_connection_config())
print("连接状态:", await server.get_connection_status())
print("DDNS 服务商:", await server.list_ddns_providers())
print("DDNS 记录:", await server.list_ddns_records(args.page, args.page_size))

# security.py
security = Security(client)
print("防火墙:", await security.get_firewall())
response = await ResourceMonitor(client).processes()
items = response.get("data", {}).get("list", [])
processes = [
    {"pid": item["pid"], "process": item["name"]}
    for item in items
    if "pid" in item and "name" in item
]
print("进程流量:", await security.get_process_traffic(processes))

# system_restore.py
print("系统恢复信息:", await SystemRestore(client).get_info())
```

- [ ] **Step 4: 运行运行时测试并确认 GREEN**

Run:

```bash
uv run pytest -q tests/test_examples_help.py -k "module_documentation or reports_connection_failure"
```

Expected: `18 passed`。

- [ ] **Step 5: 运行全部示例帮助测试**

Run:

```bash
uv run pytest -q tests/test_examples_help.py
```

Expected: 全部 PASS，无网络连接或 traceback。

- [ ] **Step 6: 提交运行一致性修改**

```bash
git add tests/test_examples_help.py examples/backup_manager.py examples/download_center.py examples/ip_blocker.py examples/license_manager.py examples/live_update.py examples/mount_manager.py examples/network_server.py examples/security.py examples/system_restore.py
git commit -m "refactor: align new example runtime flow"
```

### Task 3: README 可复制命令和参数说明

**Files:**
- Modify: `tests/test_examples_help.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: Task 1 确定的 CLI 参数名和默认值。
- Produces: README 中每个新增示例的完整 `uv run` 命令。

- [ ] **Step 1: 写 README 命令失败测试**

在 `tests/test_examples_help.py` 中加入：

```python
NEW_EXAMPLE_COMMANDS = {
    "backup_manager.py": "--direction 0",
    "download_center.py": "--state-filter 65535 --init-flag true",
    "ip_blocker.py": "",
    "license_manager.py": "--page 1 --page-size 200",
    "live_update.py": "",
    "mount_manager.py": "",
    "network_server.py": "--page 1 --page-size 200",
    "security.py": "",
    "system_restore.py": "",
}


def test_readme_documents_new_example_commands():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    for example_name, domain_args in NEW_EXAMPLE_COMMANDS.items():
        command = (
            f"uv run examples/{example_name} "
            "--user <用户名> --password <密码> -e <服务器地址>"
        )
        if domain_args:
            command = f"{command} {domain_args}"
        assert command in readme

    assert "`--direction`" in readme
    assert "`--state-filter`" in readme
    assert "`--init-flag`" in readme
    assert "`--page`" in readme
    assert "`--page-size`" in readme
```

- [ ] **Step 2: 运行测试并确认 RED**

Run:

```bash
uv run pytest -q tests/test_examples_help.py::test_readme_documents_new_example_commands
```

Expected: FAIL；README 目前只有通用语法和示例文件表，没有 9 条具体命令。

- [ ] **Step 3: 在 README“运行示例”章节加入命令**

在通用命令之后加入以下代码块：

````markdown
### 新增查询示例

以下命令沿用统一的认证、SSL 和两步验证参数：

```bash
uv run examples/backup_manager.py --user <用户名> --password <密码> -e <服务器地址> --direction 0
uv run examples/download_center.py --user <用户名> --password <密码> -e <服务器地址> --state-filter 65535 --init-flag true
uv run examples/ip_blocker.py --user <用户名> --password <密码> -e <服务器地址>
uv run examples/license_manager.py --user <用户名> --password <密码> -e <服务器地址> --page 1 --page-size 200
uv run examples/live_update.py --user <用户名> --password <密码> -e <服务器地址>
uv run examples/mount_manager.py --user <用户名> --password <密码> -e <服务器地址>
uv run examples/network_server.py --user <用户名> --password <密码> -e <服务器地址> --page 1 --page-size 200
uv run examples/security.py --user <用户名> --password <密码> -e <服务器地址>
uv run examples/system_restore.py --user <用户名> --password <密码> -e <服务器地址>
```

专用参数：

| 参数 | 使用示例 | 说明 |
| --- | --- | --- |
| `--direction` | `backup_manager.py` | 备份方向：`0` 为上传，`1` 为下载，默认 `0` |
| `--state-filter` | `download_center.py` | 下载任务状态位掩码，默认 `65535` |
| `--init-flag` | `download_center.py` | 是否初始化任务查询，取值 `true` 或 `false`，默认 `true` |
| `--page` | `license_manager.py`、`network_server.py` | 页码，默认 `1` |
| `--page-size` | `license_manager.py`、`network_server.py` | 每页数量，默认 `200` |
````

- [ ] **Step 4: 运行 README 测试并确认 GREEN**

Run:

```bash
uv run pytest -q tests/test_examples_help.py::test_readme_documents_new_example_commands
```

Expected: `1 passed`。

- [ ] **Step 5: 提交 README 配套文档**

```bash
git add tests/test_examples_help.py README.md
git commit -m "docs: add new example CLI usage"
```

### Task 4: 完整验证和审查

**Files:**
- Verify: `examples/*.py`
- Verify: `tests/test_examples_help.py`
- Verify: `README.md`

**Interfaces:**
- Consumes: Tasks 1–3 的所有提交。
- Produces: 可供合并前代码审查的干净分支。

- [ ] **Step 1: 运行非集成测试**

```bash
uv run pytest -q -m "not integration"
```

Expected: 全部 PASS。

- [ ] **Step 2: 启动固定提交的 mock server 并运行完整测试**

在相邻 `fnos-mock-server` 仓库确认：

```bash
git rev-parse HEAD
```

Expected: `d9592a05a8e07082b954921acfae3a9a915f3c01`。

启动服务：

```bash
FNOS_MOCK_TWOFA_USERS=twofauser uv run python -m server.main
```

在 pyfnos 中运行：

```bash
uv run pytest -q
```

Expected: 全部 PASS，包括 82 request case / 71 endpoint parity。

- [ ] **Step 3: 运行编译和差异检查**

```bash
python3 -m compileall -q fnos examples tests
git diff --check main..HEAD
git status --short --branch
```

Expected: 编译和差异检查退出码为 0，工作树干净。

- [ ] **Step 4: 请求合并前代码审查**

使用 `superpowers:requesting-code-review`，审查设计提交之前的功能 HEAD 到当前 HEAD，重点检查帮助文本、参数透传、错误处理、README 命令和测试覆盖。
