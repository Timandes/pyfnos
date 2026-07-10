# Extended Query API Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add explicit, tested, documented pyfnos wrappers and runnable examples for all 71 fnOS read-only endpoints that have paired request and response fixtures.

**Architecture:** Extend existing domain classes where ownership is already clear and add nine focused manager classes for new domains. Every method builds the exact captured payload, calls `FnosClient.request_payload_with_response()`, and returns the raw response. A reusable recording-client contract harness represents all 82 captured request cases and is reused by unit, integration, and cross-repository verification.

**Tech Stack:** Python 3.11+, asyncio, pytest 9, pytest-asyncio, uv, websockets, fnos-mock-server fixtures.

## Global Constraints

- Use mock-server source commit `d9592a05a8e07082b954921acfae3a9a915f3c01`.
- Implement exactly the 71 request endpoints listed in the approved design and all 82 captured request cases.
- Do not wrap the seven response-only endpoints listed in the approved design.
- Add read-only operations only; do not infer mutation APIs.
- New public methods use snake_case and keep `timeout: float = 10.0` as the final argument.
- Preserve all existing classes, method names, signatures, imports, and raw-`dict` response behavior.
- Do not add runtime dependencies, response models, code generation, caching, or retries.
- pyfnos must not depend on the sibling mock-server at runtime or package install time.
- Every new class is exported from `fnos.__init__` and included in `__all__`.
- Add or extend all 18 example programs named in the approved design; every call added by this feature is read-only.
- Reuse `examples/common.py` for authentication, SSL, and optional 2FA handling.
- Use TDD: observe each new test fail before implementing its production method.
- Use Conventional Commits in English; never add `Co-Authored-By`.

## File Map

**Shared infrastructure**

- Create `fnos/_validation.py`: private argument validators and defensive list copying.
- Create `tests/query_contract.py`: `QueryCase`, `RecordingClient`, and the shared contract assertion.
- Create `tests/test_query_validation.py`: validator behavior.

**Existing domains**

- Modify `fnos/docker_manager.py`, `fnos/network.py`, `fnos/resource_monitor.py`, `fnos/file.py`, `fnos/store.py`, `fnos/user.py`, `fnos/share.py`, `fnos/sac.py`, and `fnos/system_info.py`.
- Modify the matching nine existing programs under `examples/`.
- Create one focused query-contract test module per domain or cohesive domain pair.

**New domains**

- Create `fnos/backup_manager.py`, `fnos/download_center.py`, `fnos/ip_blocker.py`, `fnos/license_manager.py`, `fnos/mount_manager.py`, `fnos/network_server.py`, `fnos/security.py`, `fnos/system_restore.py`, and `fnos/live_update.py`.
- Create matching runnable programs under `examples/`.
- Modify `fnos/__init__.py` as each new public class lands.

**Integration and documentation**

- Create `tests/test_extended_query_integration.py` and `tests/test_examples_help.py`.
- Modify `.github/workflows/integration-tests.yml`, `README.md`, and `CHANGELOG.md`.

---

### Task 1: Shared Contract Harness and Query Validators

**Files:**
- Create: `tests/query_contract.py`
- Create: `tests/test_query_validation.py`
- Create: `fnos/_validation.py`

**Interfaces:**
- Produces: `QueryCase(name, owner, method, endpoint, payload, args=(), kwargs={})`.
- Produces: `assert_query_case(case, timeout=2.5)` for every later unit contract test.
- Produces: `require_non_empty_string(name, value)`, `require_positive_int(name, value)`, `require_non_negative_int(name, value)`, and `copy_dict_list(name, value)`.

- [ ] **Step 1: Write the failing validator tests and shared contract harness**

Create `tests/query_contract.py`:

```python
"""Shared helpers for fnOS query wrapper contract tests."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class QueryCase:
    name: str
    owner: type
    method: str
    endpoint: str
    payload: dict
    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] = field(default_factory=dict)


class RecordingClient:
    def __init__(self):
        self.calls: list[tuple[str, dict, float]] = []
        self.response = {"result": "sentinel"}

    async def request_payload_with_response(
        self, req: str, payload: dict, timeout: float = 10.0
    ) -> dict:
        self.calls.append((req, payload, timeout))
        return self.response


async def assert_query_case(case: QueryCase, timeout: float = 2.5) -> None:
    client = RecordingClient()
    owner = case.owner(client)
    kwargs = dict(case.kwargs)
    kwargs["timeout"] = timeout

    result = await getattr(owner, case.method)(*case.args, **kwargs)

    assert client.calls == [(case.endpoint, case.payload, timeout)]
    assert result is client.response
```

Create `tests/test_query_validation.py`:

```python
import pytest

from fnos._validation import (
    copy_dict_list,
    require_non_empty_string,
    require_non_negative_int,
    require_positive_int,
)


@pytest.mark.parametrize("value", [None, "", "   ", 1])
def test_require_non_empty_string_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        require_non_empty_string("name", value)


@pytest.mark.parametrize("value", [0, -1, True, 1.5, "1"])
def test_require_positive_int_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        require_positive_int("page", value)


@pytest.mark.parametrize("value", [-1, True, 1.5, "1"])
def test_require_non_negative_int_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        require_non_negative_int("uid", value)


def test_valid_scalar_values_are_accepted():
    require_non_empty_string("name", "date-format")
    require_positive_int("page", 1)
    require_non_negative_int("uid", 0)


@pytest.mark.parametrize("value", [None, {}, [1], [{"pid": 1}, "bad"]])
def test_copy_dict_list_rejects_non_dict_lists(value):
    with pytest.raises(ValueError):
        copy_dict_list("processes", value)


def test_copy_dict_list_returns_new_list_and_dicts():
    source = [{"pid": 1001, "process": "example-process"}]
    result = copy_dict_list("processes", source)

    assert result == source
    assert result is not source
    assert result[0] is not source[0]
```

- [ ] **Step 2: Run the validator tests to verify RED**

Run:

```bash
uv run pytest -q tests/test_query_validation.py
```

Expected: collection fails with `ModuleNotFoundError: No module named 'fnos._validation'`.

- [ ] **Step 3: Implement the private validators**

Create `fnos/_validation.py`:

```python
"""Private validation helpers for query wrapper arguments."""


def require_non_empty_string(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name}参数不能为空字符串")


def require_positive_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name}参数必须是正整数")


def require_non_negative_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name}参数必须是非负整数")


def copy_dict_list(name: str, value: list[dict]) -> list[dict]:
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise ValueError(f"{name}参数必须是字典列表")
    return [dict(item) for item in value]
```

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```bash
uv run pytest -q tests/test_query_validation.py
```

Expected: all validator tests pass.

- [ ] **Step 5: Commit**

```bash
git add fnos/_validation.py tests/query_contract.py tests/test_query_validation.py
git commit -m "feat: add query contract test helpers"
```

---

### Task 2: Docker Query Wrappers and Example

**Files:**
- Create: `tests/test_docker_manager_queries.py`
- Modify: `fnos/docker_manager.py`
- Modify: `examples/docker_manager.py`

**Interfaces:**
- Produces: `DockerManager.list_image_downloads(timeout=10.0)`.
- Produces: `DockerManager.list_images(timeout=10.0)`.
- Produces: `DockerManager.list_networks(timeout=10.0)`.
- Produces: `DockerManager.list_registry_repositories(keyword="", page=1, page_size=20, timeout=10.0)`.
- Produces: four captured `CASES` for later integration and fixture comparison.

- [ ] **Step 1: Write failing Docker contracts**

Create `tests/test_docker_manager_queries.py`:

```python
import pytest

from fnos import DockerManager
from tests.query_contract import QueryCase, assert_query_case


CASES = [
    QueryCase("image-downloads", DockerManager, "list_image_downloads", "appcgi.dockermgr.imageDownloadList", {}),
    QueryCase("images", DockerManager, "list_images", "appcgi.dockermgr.imageList", {}),
    QueryCase("networks", DockerManager, "list_networks", "appcgi.dockermgr.networkList", {}),
    QueryCase(
        "registry-repositories",
        DockerManager,
        "list_registry_repositories",
        "appcgi.dockermgr.registryHubRepoList",
        {"key": "", "page": 1, "pageSize": 20},
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
async def test_docker_query_contract(case):
    await assert_query_case(case)


@pytest.mark.asyncio
@pytest.mark.parametrize("field", ["page", "page_size"])
async def test_registry_pagination_must_be_positive(field):
    manager = DockerManager(object())
    kwargs = {"page": 1, "page_size": 20, field: 0}
    with pytest.raises(ValueError):
        await manager.list_registry_repositories(**kwargs)
```

- [ ] **Step 2: Run Docker contracts to verify RED**

Run: `uv run pytest -q tests/test_docker_manager_queries.py`

Expected: failures report missing `DockerManager.list_image_downloads` and the other new methods.

- [ ] **Step 3: Implement the Docker methods**

Add `from ._validation import require_positive_int` to `fnos/docker_manager.py`, then add:

```python
    async def list_image_downloads(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response(
            "appcgi.dockermgr.imageDownloadList", {}, timeout
        )

    async def list_images(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response(
            "appcgi.dockermgr.imageList", {}, timeout
        )

    async def list_networks(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response(
            "appcgi.dockermgr.networkList", {}, timeout
        )

    async def list_registry_repositories(
        self,
        keyword: str = "",
        page: int = 1,
        page_size: int = 20,
        timeout: float = 10.0,
    ) -> dict:
        require_positive_int("page", page)
        require_positive_int("page_size", page_size)
        payload = {"key": keyword, "page": page, "pageSize": page_size}
        return await self.client.request_payload_with_response(
            "appcgi.dockermgr.registryHubRepoList", payload, timeout
        )
```

- [ ] **Step 4: Extend the Docker example**

Before the existing `finally` block in `examples/docker_manager.py`, add:

```python
        print("\n=== Docker 镜像下载任务 ===")
        print(await docker_mgr.list_image_downloads())

        print("\n=== Docker 镜像 ===")
        print(await docker_mgr.list_images())

        print("\n=== Docker 网络 ===")
        print(await docker_mgr.list_networks())

        print("\n=== Docker 镜像仓库 ===")
        print(await docker_mgr.list_registry_repositories())
```

- [ ] **Step 5: Verify Docker tests and example CLI**

Run:

```bash
uv run pytest -q tests/test_docker_manager_queries.py
uv run python examples/docker_manager.py --help
```

Expected: tests pass and the example exits 0 after displaying argparse help without connecting.

- [ ] **Step 6: Commit**

```bash
git add fnos/docker_manager.py examples/docker_manager.py tests/test_docker_manager_queries.py
git commit -m "feat: add Docker query APIs"
```

---

### Task 3: Network Query Wrappers and Example

**Files:**
- Create: `tests/test_network_queries.py`
- Modify: `fnos/network.py`
- Modify: `examples/network.py`

**Interfaces:**
- Produces: `Network.get_gateway()`, `get_multi_gateway_status()`, `get_nic_performance_mode()`, `get_info(if_name)`, and `get_ssh_status()`.
- Produces: five captured `CASES`.

- [ ] **Step 1: Write failing Network contracts**

Create `tests/test_network_queries.py`:

```python
import pytest

from fnos import Network
from tests.query_contract import QueryCase, assert_query_case


CASES = [
    QueryCase("gateway", Network, "get_gateway", "appcgi.network.gw.getting", {}),
    QueryCase("multi-gateway", Network, "get_multi_gateway_status", "appcgi.network.net.getMultiGWStatus", {}),
    QueryCase("nic-performance", Network, "get_nic_performance_mode", "appcgi.network.net.getNicPerformanceMode", {}),
    QueryCase("interface-info", Network, "get_info", "appcgi.network.net.info", {"ifName": "eth0"}, args=("eth0",)),
    QueryCase("ssh-status", Network, "get_ssh_status", "appcgi.network.ssh.status", {}),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
async def test_network_query_contract(case):
    await assert_query_case(case)


@pytest.mark.asyncio
async def test_get_info_rejects_empty_interface_name():
    with pytest.raises(ValueError):
        await Network(object()).get_info("")
```

- [ ] **Step 2: Run Network contracts to verify RED**

Run: `uv run pytest -q tests/test_network_queries.py`

Expected: failures report missing Network query methods.

- [ ] **Step 3: Implement the Network methods**

Add `from ._validation import require_non_empty_string` and these methods to `fnos/network.py`:

```python
    async def get_gateway(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response(
            "appcgi.network.gw.getting", {}, timeout
        )

    async def get_multi_gateway_status(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response(
            "appcgi.network.net.getMultiGWStatus", {}, timeout
        )

    async def get_nic_performance_mode(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response(
            "appcgi.network.net.getNicPerformanceMode", {}, timeout
        )

    async def get_info(self, if_name: str, timeout: float = 10.0) -> dict:
        require_non_empty_string("if_name", if_name)
        return await self.client.request_payload_with_response(
            "appcgi.network.net.info", {"ifName": if_name}, timeout
        )

    async def get_ssh_status(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response(
            "appcgi.network.ssh.status", {}, timeout
        )
```

- [ ] **Step 4: Extend the Network example**

Add `parser.add_argument("--if-name", default="eth0", help="查询详情的网卡名称")` before `parse_args()`. After creating `network`, add:

```python
        print("\n默认网关:", await network.get_gateway())
        print("\n多网关状态:", await network.get_multi_gateway_status())
        print("\n网卡性能模式:", await network.get_nic_performance_mode())
        print("\n网卡详情:", await network.get_info(args.if_name))
        print("\nSSH 状态:", await network.get_ssh_status())
```

- [ ] **Step 5: Verify Network tests and example CLI**

Run:

```bash
uv run pytest -q tests/test_network_queries.py
uv run python examples/network.py --help
```

Expected: tests pass and help exits 0.

- [ ] **Step 6: Commit**

```bash
git add fnos/network.py examples/network.py tests/test_network_queries.py
git commit -m "feat: add network query APIs"
```

---

### Task 4: Resource Monitor Query Wrappers and Example

**Files:**
- Create: `tests/test_resource_monitor_queries.py`
- Modify: `fnos/resource_monitor.py`
- Modify: `examples/resource_monitor.py`

**Interfaces:**
- Produces: `ResourceMonitor.npu()`, `processes()`, `service_processes()`, and `system_fan()`.
- Produces: four captured `CASES`.

- [ ] **Step 1: Write failing ResourceMonitor contracts**

Create `tests/test_resource_monitor_queries.py`:

```python
import pytest

from fnos import ResourceMonitor
from tests.query_contract import QueryCase, assert_query_case


CASES = [
    QueryCase("npu", ResourceMonitor, "npu", "appcgi.resmon.npu", {}),
    QueryCase("processes", ResourceMonitor, "processes", "appcgi.resmon.proc.list", {}),
    QueryCase("service-processes", ResourceMonitor, "service_processes", "appcgi.resmon.proc.srv", {}),
    QueryCase("system-fan", ResourceMonitor, "system_fan", "appcgi.resmon.sysFan", {}),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
async def test_resource_monitor_query_contract(case):
    await assert_query_case(case)
```

- [ ] **Step 2: Run contracts to verify RED**

Run: `uv run pytest -q tests/test_resource_monitor_queries.py`

Expected: missing-method failures.

- [ ] **Step 3: Implement the ResourceMonitor methods**

Add to `fnos/resource_monitor.py`:

```python
    async def npu(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response("appcgi.resmon.npu", {}, timeout)

    async def processes(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response("appcgi.resmon.proc.list", {}, timeout)

    async def service_processes(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response("appcgi.resmon.proc.srv", {}, timeout)

    async def system_fan(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response("appcgi.resmon.sysFan", {}, timeout)
```

- [ ] **Step 4: Extend the ResourceMonitor example**

After the existing network monitor call, add:

```python
            print("NPU资源信息:", await resource_monitor.npu())
            print("进程资源信息:", await resource_monitor.processes())
            print("服务进程资源信息:", await resource_monitor.service_processes())
            print("系统风扇信息:", await resource_monitor.system_fan())
```

- [ ] **Step 5: Verify and commit**

Run:

```bash
uv run pytest -q tests/test_resource_monitor_queries.py
uv run python examples/resource_monitor.py --help
git add fnos/resource_monitor.py examples/resource_monitor.py tests/test_resource_monitor_queries.py
git commit -m "feat: add resource monitor query APIs"
```

Expected: tests and help pass; commit succeeds.

---

### Task 5: File Query Wrappers and Example

**Files:**
- Create: `tests/test_file_queries.py`
- Modify: `fnos/file.py`
- Modify: `examples/file.py`

**Interfaces:**
- Produces eight empty-payload query methods for app directories, favorites, directory entries, recent files, shares, and trash.
- Produces: eight captured `CASES`.

- [ ] **Step 1: Write failing File contracts**

Create `tests/test_file_queries.py`:

```python
import pytest

from fnos import File
from tests.query_contract import QueryCase, assert_query_case


CASES = [
    QueryCase("app-directories", File, "list_app_directories", "appcgi.filestor.getAppDirList", {}),
    QueryCase("favorites", File, "list_favorites", "file.fav.list", {}),
    QueryCase("directory-entries", File, "list_directory_entries", "file.lsDir", {}),
    QueryCase("recent", File, "list_recent", "file.recent.list", {}),
    QueryCase("shared", File, "list_shared", "file.share.list", {}),
    QueryCase("shared-by-others", File, "list_shared_by_others", "file.share.listOthers", {}),
    QueryCase("team-trash-bins", File, "list_team_trash_bins", "file.team.trash.listTrashbin", {}),
    QueryCase("trash", File, "list_trash", "file.trash.list", {}),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
async def test_file_query_contract(case):
    await assert_query_case(case)
```

- [ ] **Step 2: Run contracts to verify RED**

Run: `uv run pytest -q tests/test_file_queries.py`

Expected: missing-method failures.

- [ ] **Step 3: Implement all eight File methods**

Add to `fnos/file.py`:

```python
    async def list_app_directories(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response("appcgi.filestor.getAppDirList", {}, timeout)

    async def list_favorites(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response("file.fav.list", {}, timeout)

    async def list_directory_entries(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response("file.lsDir", {}, timeout)

    async def list_recent(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response("file.recent.list", {}, timeout)

    async def list_shared(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response("file.share.list", {}, timeout)

    async def list_shared_by_others(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response("file.share.listOthers", {}, timeout)

    async def list_team_trash_bins(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response("file.team.trash.listTrashbin", {}, timeout)

    async def list_trash(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response("file.trash.list", {}, timeout)
```

- [ ] **Step 4: Extend the File example without changing its existing mutation demo**

Immediately after `file = File(client)`, before the current early return on an empty directory, add:

```python
        print("应用目录:", await file.list_app_directories())
        print("收藏文件:", await file.list_favorites())
        print("目录视图:", await file.list_directory_entries())
        print("最近文件:", await file.list_recent())
        print("我的共享:", await file.list_shared())
        print("他人共享:", await file.list_shared_by_others())
        print("团队回收站:", await file.list_team_trash_bins())
        print("个人回收站:", await file.list_trash())
```

- [ ] **Step 5: Verify and commit**

Run:

```bash
uv run pytest -q tests/test_file_queries.py
uv run python examples/file.py --help
git add fnos/file.py examples/file.py tests/test_file_queries.py
git commit -m "feat: add file query APIs"
```

Expected: tests and help pass; existing create/remove example code remains intact.

---

### Task 6: Storage Query Wrappers and Example

**Files:**
- Create: `tests/test_store_queries.py`
- Modify: `fnos/store.py`
- Modify: `examples/store.py`

**Interfaces:**
- Produces: `Store.get_cache_device_state()`, `get_disk_idle_time()`, `get_disk_wakeup()`, `get_removable_config()`, `list_cache_devices()`, and `list_removable_devices()`.
- Produces: six captured `CASES`.

- [ ] **Step 1: Write failing Store contracts**

Create `tests/test_store_queries.py`:

```python
import pytest

from fnos import Store
from tests.query_contract import QueryCase, assert_query_case


CASES = [
    QueryCase("cache-state", Store, "get_cache_device_state", "stor.cachedevState", {}),
    QueryCase("disk-idle-time", Store, "get_disk_idle_time", "stor.getDiskIdleTime", {}),
    QueryCase("disk-wakeup", Store, "get_disk_wakeup", "stor.getDiskWakeup", {}),
    QueryCase("removable-config", Store, "get_removable_config", "stor.getRemovableConf", {}),
    QueryCase("cache-devices", Store, "list_cache_devices", "stor.listCachedev", {}),
    QueryCase("removable-devices", Store, "list_removable_devices", "stor.listRemovable", {}),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
async def test_store_query_contract(case):
    await assert_query_case(case)
```

- [ ] **Step 2: Run contracts to verify RED**

Run: `uv run pytest -q tests/test_store_queries.py`

Expected: missing-method failures.

- [ ] **Step 3: Implement the Store methods**

Add to `fnos/store.py`:

```python
    async def get_cache_device_state(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response("stor.cachedevState", {}, timeout)

    async def get_disk_idle_time(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response("stor.getDiskIdleTime", {}, timeout)

    async def get_disk_wakeup(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response("stor.getDiskWakeup", {}, timeout)

    async def get_removable_config(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response("stor.getRemovableConf", {}, timeout)

    async def list_cache_devices(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response("stor.listCachedev", {}, timeout)

    async def list_removable_devices(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response("stor.listRemovable", {}, timeout)
```

- [ ] **Step 4: Extend the Store example**

After creating `store`, add:

```python
            print("缓存设备状态:", await store.get_cache_device_state())
            print("磁盘空闲时间:", await store.get_disk_idle_time())
            print("磁盘唤醒配置:", await store.get_disk_wakeup())
            print("可移动设备配置:", await store.get_removable_config())
            print("缓存设备列表:", await store.list_cache_devices())
            print("可移动设备列表:", await store.list_removable_devices())
```

- [ ] **Step 5: Verify and commit**

```bash
uv run pytest -q tests/test_store_queries.py
uv run python examples/store.py --help
git add fnos/store.py examples/store.py tests/test_store_queries.py
git commit -m "feat: add storage query APIs"
```

Expected: tests and help pass; commit succeeds.

---

### Task 7: User, Account, 2FA, and Preference Query Wrappers

**Files:**
- Create: `tests/test_user_queries.py`
- Modify: `fnos/user.py`
- Modify: `examples/user.py`

**Interfaces:**
- Produces nine endpoint methods: `list_tokens()`, `get_my_twofa_config()`, `get_global_twofa_config()`, `get_user_twofa_config(uid)`, `get_active_state()`, `get_group_info(group)`, `list_groups()`, `list_login_devices()`, and `get_preference(name)`.
- Produces ten captured `CASES`, including both user preference names.

- [ ] **Step 1: Write failing User contracts and validation tests**

Create `tests/test_user_queries.py`:

```python
import pytest

from fnos import User
from tests.query_contract import QueryCase, assert_query_case


CASES = [
    QueryCase("tokens", User, "list_tokens", "appcgi.accountsrv.v1.token.list", {"data": {}}),
    QueryCase("my-twofa", User, "get_my_twofa_config", "appcgi.tfa.security.v1.me.getConfig", {}),
    QueryCase("global-twofa", User, "get_global_twofa_config", "appcgi.tfa.security.v1.twofa.getConfig", {}),
    QueryCase("user-twofa", User, "get_user_twofa_config", "appcgi.tfa.security.v1.user.getTwofaConfig", {"data": {"uid": 1000}}, args=(1000,)),
    QueryCase("active", User, "get_active_state", "user.active", {}),
    QueryCase("group-info", User, "get_group_info", "user.groupInfo", {"group": "group"}, args=("group",)),
    QueryCase("groups", User, "list_groups", "user.groupList", {}),
    QueryCase("login-devices", User, "list_login_devices", "user.listLoginDevice", {}),
    QueryCase("preference-namesake", User, "get_preference", "usrdat.get", {"name": "browser.namesakeConf"}, args=("browser.namesakeConf",)),
    QueryCase("preference-date", User, "get_preference", "usrdat.get", {"name": "date-format"}, args=("date-format",)),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
async def test_user_query_contract(case):
    await assert_query_case(case)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "argument"),
    [("get_user_twofa_config", -1), ("get_group_info", ""), ("get_preference", "")],
)
async def test_user_query_validation(method, argument):
    with pytest.raises(ValueError):
        await getattr(User(object()), method)(argument)
```

- [ ] **Step 2: Run User contracts to verify RED**

Run: `uv run pytest -q tests/test_user_queries.py`

Expected: missing-method failures.

- [ ] **Step 3: Implement all User query methods**

Add these imports to `fnos/user.py`:

```python
from ._validation import require_non_empty_string, require_non_negative_int
```

Add these methods:

```python
    async def list_tokens(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response(
            "appcgi.accountsrv.v1.token.list", {"data": {}}, timeout
        )

    async def get_my_twofa_config(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response(
            "appcgi.tfa.security.v1.me.getConfig", {}, timeout
        )

    async def get_global_twofa_config(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response(
            "appcgi.tfa.security.v1.twofa.getConfig", {}, timeout
        )

    async def get_user_twofa_config(self, uid: int, timeout: float = 10.0) -> dict:
        require_non_negative_int("uid", uid)
        return await self.client.request_payload_with_response(
            "appcgi.tfa.security.v1.user.getTwofaConfig",
            {"data": {"uid": uid}},
            timeout,
        )

    async def get_active_state(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response("user.active", {}, timeout)

    async def get_group_info(self, group: str, timeout: float = 10.0) -> dict:
        require_non_empty_string("group", group)
        return await self.client.request_payload_with_response(
            "user.groupInfo", {"group": group}, timeout
        )

    async def list_groups(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response("user.groupList", {}, timeout)

    async def list_login_devices(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response(
            "user.listLoginDevice", {}, timeout
        )

    async def get_preference(self, name: str, timeout: float = 10.0) -> dict:
        require_non_empty_string("name", name)
        return await self.client.request_payload_with_response(
            "usrdat.get", {"name": name}, timeout
        )
```

- [ ] **Step 4: Extend the User example**

Before `parse_args()`, add:

```python
    parser.add_argument("--uid", type=int, default=1000, help="查询两步验证配置的用户 ID")
    parser.add_argument("--group", default="users", help="查询详情的用户组名称")
    parser.add_argument("--preference", default="date-format", help="用户偏好名称")
```

After creating `user`, add:

```python
        print("登录令牌:", await user.list_tokens())
        print("我的两步验证配置:", await user.get_my_twofa_config())
        print("全局两步验证配置:", await user.get_global_twofa_config())
        print("指定用户两步验证配置:", await user.get_user_twofa_config(args.uid))
        print("用户活跃状态:", await user.get_active_state())
        print("用户组详情:", await user.get_group_info(args.group))
        print("用户组列表:", await user.list_groups())
        print("登录设备:", await user.list_login_devices())
        print("用户偏好:", await user.get_preference(args.preference))
```

- [ ] **Step 5: Verify and commit**

```bash
uv run pytest -q tests/test_user_queries.py
uv run python examples/user.py --help
git add fnos/user.py examples/user.py tests/test_user_queries.py
git commit -m "feat: add user query APIs"
```

Expected: ten contracts and validation tests pass; help exits 0.

---

### Task 8: Share Protocol Query Wrappers

**Files:**
- Create: `tests/test_share_protocol_queries.py`
- Modify: `fnos/share.py`
- Modify: `examples/share.py`

**Interfaces:**
- Produces nine protocol and per-share option methods.
- Produces nine captured `CASES`.

- [ ] **Step 1: Write failing Share protocol contracts**

Create `tests/test_share_protocol_queries.py`:

```python
import pytest

from fnos import Share
from tests.query_contract import QueryCase, assert_query_case


CASES = [
    QueryCase("dlna-options", Share, "dlna_options", "appcgi.share.dlna.opt", {}),
    QueryCase("dlna-share-options", Share, "dlna_share_options", "appcgi.share.dlna.share.opt", {}),
    QueryCase("ftp-options", Share, "ftp_options", "appcgi.share.ftp.opt", {}),
    QueryCase("ftp-share-options", Share, "ftp_share_options", "appcgi.share.ftp.share.opt", {}),
    QueryCase("nfs-options", Share, "nfs_options", "appcgi.share.nfs.opt", {}),
    QueryCase("nfs-share-options", Share, "nfs_share_options", "appcgi.share.nfs.share.opt", {}),
    QueryCase("smb-share-options", Share, "smb_share_options", "appcgi.share.smb.share.opt", {}),
    QueryCase("webdav-options", Share, "webdav_options", "appcgi.share.webdav.opt", {}),
    QueryCase("webdav-share-options", Share, "webdav_share_options", "appcgi.share.webdav.share.opt", {}),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
async def test_share_protocol_query_contract(case):
    await assert_query_case(case)
```

- [ ] **Step 2: Run contracts to verify RED**

Run: `uv run pytest -q tests/test_share_protocol_queries.py`

Expected: missing-method failures.

- [ ] **Step 3: Implement all protocol methods**

Add to `fnos/share.py`:

```python
    async def dlna_options(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response("appcgi.share.dlna.opt", {}, timeout)

    async def dlna_share_options(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response("appcgi.share.dlna.share.opt", {}, timeout)

    async def ftp_options(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response("appcgi.share.ftp.opt", {}, timeout)

    async def ftp_share_options(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response("appcgi.share.ftp.share.opt", {}, timeout)

    async def nfs_options(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response("appcgi.share.nfs.opt", {}, timeout)

    async def nfs_share_options(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response("appcgi.share.nfs.share.opt", {}, timeout)

    async def smb_share_options(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response("appcgi.share.smb.share.opt", {}, timeout)

    async def webdav_options(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response("appcgi.share.webdav.opt", {}, timeout)

    async def webdav_share_options(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response("appcgi.share.webdav.share.opt", {}, timeout)
```

- [ ] **Step 4: Extend the Share example with protocol calls**

After the existing SMB output, add:

```python
        print("DLNA 配置:", await share.dlna_options())
        print("DLNA 共享配置:", await share.dlna_share_options())
        print("FTP 配置:", await share.ftp_options())
        print("FTP 共享配置:", await share.ftp_share_options())
        print("NFS 配置:", await share.nfs_options())
        print("NFS 共享配置:", await share.nfs_share_options())
        print("SMB 共享配置:", await share.smb_share_options())
        print("WebDAV 配置:", await share.webdav_options())
        print("WebDAV 共享配置:", await share.webdav_share_options())
```

- [ ] **Step 5: Verify and commit**

```bash
uv run pytest -q tests/test_share_protocol_queries.py
uv run python examples/share.py --help
git add fnos/share.py examples/share.py tests/test_share_protocol_queries.py
git commit -m "feat: add share protocol query APIs"
```

Expected: nine contracts pass and help exits 0.

---

### Task 9: Share Link Query Wrappers

**Files:**
- Create: `tests/test_share_link_queries.py`
- Modify: `fnos/share.py`
- Modify: `examples/share.py`

**Interfaces:**
- Produces: `Share.get_link_defaults()`, `get_default_link()`, `list_links(...)`, and `get_link_permission()`.
- Produces five captured `CASES`, including both administrative modes.

- [ ] **Step 1: Write failing Share link contracts**

Create `tests/test_share_link_queries.py`:

```python
import pytest

from fnos import Share
from tests.query_contract import QueryCase, assert_query_case


DEFAULT_LINK_PAYLOAD = {
    "data": {
        "isAdmin": False,
        "keyword": "",
        "page": 1,
        "pageSize": 100,
        "sortColumn": "createdTime",
        "sortType": "DESC",
    }
}

CASES = [
    QueryCase("link-defaults", Share, "get_link_defaults", "appcgi.sharesvr.share.link.default.get", {}),
    QueryCase("default-link", Share, "get_default_link", "appcgi.sharesvr.share.link.default", {}),
    QueryCase("links-user", Share, "list_links", "appcgi.sharesvr.share.link.list", DEFAULT_LINK_PAYLOAD),
    QueryCase(
        "links-admin",
        Share,
        "list_links",
        "appcgi.sharesvr.share.link.list",
        {"data": {**DEFAULT_LINK_PAYLOAD["data"], "isAdmin": True}},
        kwargs={"is_admin": True},
    ),
    QueryCase("link-permission", Share, "get_link_permission", "appcgi.sharesvr.share.permission.get", {}),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
async def test_share_link_query_contract(case):
    await assert_query_case(case)


@pytest.mark.asyncio
@pytest.mark.parametrize("field", ["page", "page_size"])
async def test_share_link_pagination_must_be_positive(field):
    kwargs = {"page": 1, "page_size": 100, field: 0}
    with pytest.raises(ValueError):
        await Share(object()).list_links(**kwargs)
```

- [ ] **Step 2: Run contracts to verify RED**

Run: `uv run pytest -q tests/test_share_link_queries.py`

Expected: missing-method failures.

- [ ] **Step 3: Implement the Share link methods**

Add `from ._validation import require_positive_int` and these methods to `fnos/share.py`:

```python
    async def get_link_defaults(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response(
            "appcgi.sharesvr.share.link.default.get", {}, timeout
        )

    async def get_default_link(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response(
            "appcgi.sharesvr.share.link.default", {}, timeout
        )

    async def list_links(
        self,
        is_admin: bool = False,
        keyword: str = "",
        page: int = 1,
        page_size: int = 100,
        sort_column: str = "createdTime",
        sort_type: str = "DESC",
        timeout: float = 10.0,
    ) -> dict:
        require_positive_int("page", page)
        require_positive_int("page_size", page_size)
        payload = {
            "data": {
                "isAdmin": is_admin,
                "keyword": keyword,
                "page": page,
                "pageSize": page_size,
                "sortColumn": sort_column,
                "sortType": sort_type,
            }
        }
        return await self.client.request_payload_with_response(
            "appcgi.sharesvr.share.link.list", payload, timeout
        )

    async def get_link_permission(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response(
            "appcgi.sharesvr.share.permission.get", {}, timeout
        )
```

- [ ] **Step 4: Extend the Share example with link calls**

Add:

```python
        print("分享链接默认配置:", await share.get_link_defaults())
        print("默认分享链接:", await share.get_default_link())
        print("分享链接列表:", await share.list_links())
        print("分享链接权限:", await share.get_link_permission())
```

- [ ] **Step 5: Verify and commit**

```bash
uv run pytest -q tests/test_share_link_queries.py tests/test_share_protocol_queries.py
uv run python examples/share.py --help
git add fnos/share.py examples/share.py tests/test_share_link_queries.py
git commit -m "feat: add share link query APIs"
```

Expected: all Share query tests pass and help exits 0.

---

### Task 10: SAC and System Information Query Wrappers

**Files:**
- Create: `tests/test_sac_system_info_queries.py`
- Modify: `fnos/sac.py`
- Modify: `fnos/system_info.py`
- Modify: `examples/sac.py`
- Modify: `examples/system_info.py`

**Interfaces:**
- Produces: `SAC.get_email_config()`, `SAC.list_email_providers()`, and `SystemInfo.get_reserved_partition()`.
- Produces three captured `CASES`.

- [ ] **Step 1: Write failing SAC/SystemInfo contracts**

Create `tests/test_sac_system_info_queries.py`:

```python
import pytest

from fnos import SAC, SystemInfo
from tests.query_contract import QueryCase, assert_query_case


CASES = [
    QueryCase("email-config", SAC, "get_email_config", "appcgi.sac.externalnotify.v1.email.getConfig", {}),
    QueryCase("email-providers", SAC, "list_email_providers", "appcgi.sac.externalnotify.v1.email.getProviders", {}),
    QueryCase("reserved-partition", SystemInfo, "get_reserved_partition", "appcgi.sysinfo.getReservedPartition", {}),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
async def test_sac_system_info_query_contract(case):
    await assert_query_case(case)
```

- [ ] **Step 2: Run contracts to verify RED**

Run: `uv run pytest -q tests/test_sac_system_info_queries.py`

Expected: missing-method failures.

- [ ] **Step 3: Implement the three methods**

Add to `fnos/sac.py`:

```python
    async def get_email_config(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response(
            "appcgi.sac.externalnotify.v1.email.getConfig", {}, timeout
        )

    async def list_email_providers(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response(
            "appcgi.sac.externalnotify.v1.email.getProviders", {}, timeout
        )
```

Add to `fnos/system_info.py`:

```python
    async def get_reserved_partition(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response(
            "appcgi.sysinfo.getReservedPartition", {}, timeout
        )
```

- [ ] **Step 4: Extend both examples**

Add to `examples/sac.py` after `SAC(client)`:

```python
            print("邮件通知配置:", await sac.get_email_config())
            print("邮件服务商:", await sac.list_email_providers())
```

Add to `examples/system_info.py` after `SystemInfo(client)`:

```python
            print("保留分区信息:", await system_info.get_reserved_partition())
```

- [ ] **Step 5: Verify and commit**

```bash
uv run pytest -q tests/test_sac_system_info_queries.py
uv run python examples/sac.py --help
uv run python examples/system_info.py --help
git add fnos/sac.py fnos/system_info.py examples/sac.py examples/system_info.py tests/test_sac_system_info_queries.py
git commit -m "feat: add SAC and system query APIs"
```

Expected: three contracts pass and both examples show help without connecting.

---

### Task 11: BackupManager and DownloadCenter

**Files:**
- Create: `fnos/backup_manager.py`
- Create: `fnos/download_center.py`
- Create: `tests/test_backup_download_queries.py`
- Create: `examples/backup_manager.py`
- Create: `examples/download_center.py`
- Modify: `fnos/__init__.py`

**Interfaces:**
- Produces: `BackupManager.list_tasks(direction, timeout=10.0)`.
- Produces: `DownloadCenter.get_default_save_directory()`, `get_statistics()`, and `query_tasks(state_filter=65535, init_flag=True, timeout=10.0)`.
- Produces 12 captured `CASES`: two backup directions, two fixed download queries, and eight state filters.

- [ ] **Step 1: Write failing Backup and DownloadCenter contracts**

Create `tests/test_backup_download_queries.py`:

```python
import pytest

from fnos import BackupManager, DownloadCenter
from tests.query_contract import QueryCase, assert_query_case


CASES = [
    QueryCase("backup-outbound", BackupManager, "list_tasks", "appcgi.backup.task.list", {"direction": 0}, args=(0,)),
    QueryCase("backup-inbound", BackupManager, "list_tasks", "appcgi.backup.task.list", {"direction": 1}, args=(1,)),
    QueryCase("download-save-dir", DownloadCenter, "get_default_save_directory", "appcgi.downloadcenter.config.getDefaultSaveDir", {}),
    QueryCase("download-stats", DownloadCenter, "get_statistics", "appcgi.downloadcenter.stat.all", {}),
    *[
        QueryCase(
            f"download-state-{state_filter}",
            DownloadCenter,
            "query_tasks",
            "appcgi.downloadcenter.task.query",
            {"init_flag": True, "state_filter": state_filter},
            kwargs={} if state_filter == 65535 else {"state_filter": state_filter},
        )
        for state_filter in (16, 1, 2, 32, 4, 64, 65535, 8)
    ],
]


@pytest.mark.asyncio
@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
async def test_backup_download_query_contract(case):
    await assert_query_case(case)


@pytest.mark.asyncio
@pytest.mark.parametrize("direction", [-1, 2, True, 1.0, "0"])
async def test_backup_direction_is_restricted(direction):
    with pytest.raises(ValueError):
        await BackupManager(object()).list_tasks(direction)
```

- [ ] **Step 2: Run contracts to verify RED**

Run: `uv run pytest -q tests/test_backup_download_queries.py`

Expected: import fails because `BackupManager` and `DownloadCenter` are not exported.

- [ ] **Step 3: Implement and export both classes**

Create `fnos/backup_manager.py`:

```python
from .client import FnosClient


class BackupManager:
    def __init__(self, client: FnosClient):
        self.client = client

    async def list_tasks(self, direction: int, timeout: float = 10.0) -> dict:
        if (
            isinstance(direction, bool)
            or not isinstance(direction, int)
            or direction not in (0, 1)
        ):
            raise ValueError("direction参数必须为0或1")
        return await self.client.request_payload_with_response(
            "appcgi.backup.task.list", {"direction": direction}, timeout
        )
```

Create `fnos/download_center.py`:

```python
from .client import FnosClient


class DownloadCenter:
    def __init__(self, client: FnosClient):
        self.client = client

    async def get_default_save_directory(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response(
            "appcgi.downloadcenter.config.getDefaultSaveDir", {}, timeout
        )

    async def get_statistics(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response(
            "appcgi.downloadcenter.stat.all", {}, timeout
        )

    async def query_tasks(
        self,
        state_filter: int = 65535,
        init_flag: bool = True,
        timeout: float = 10.0,
    ) -> dict:
        payload = {"init_flag": init_flag, "state_filter": state_filter}
        return await self.client.request_payload_with_response(
            "appcgi.downloadcenter.task.query", payload, timeout
        )
```

Add imports and names to `fnos/__init__.py`:

```python
from .backup_manager import BackupManager
from .download_center import DownloadCenter
```

Append `"BackupManager"` and `"DownloadCenter"` to `__all__`.

- [ ] **Step 4: Add both runnable examples**

Create `examples/backup_manager.py`:

```python
#!/usr/bin/env python3
import argparse
import asyncio

from fnos import BackupManager, FnosClient
from common import add_auth_arguments, connect_and_login


async def main():
    parser = argparse.ArgumentParser(description="fnOS 备份任务查询示例")
    add_auth_arguments(parser)
    parser.add_argument("--direction", type=int, choices=(0, 1), default=0)
    args = parser.parse_args()
    client = FnosClient()
    try:
        await connect_and_login(client, args)
        print(await BackupManager(client).list_tasks(args.direction))
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
```

Create `examples/download_center.py`:

```python
#!/usr/bin/env python3
import argparse
import asyncio

from fnos import DownloadCenter, FnosClient
from common import add_auth_arguments, connect_and_login


async def main():
    parser = argparse.ArgumentParser(description="fnOS 下载中心查询示例")
    add_auth_arguments(parser)
    parser.add_argument("--state-filter", type=int, default=65535)
    args = parser.parse_args()
    client = FnosClient()
    try:
        await connect_and_login(client, args)
        download = DownloadCenter(client)
        print("默认保存目录:", await download.get_default_save_directory())
        print("下载统计:", await download.get_statistics())
        print("下载任务:", await download.query_tasks(args.state_filter))
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 5: Verify and commit**

```bash
uv run pytest -q tests/test_backup_download_queries.py
uv run python examples/backup_manager.py --help
uv run python examples/download_center.py --help
git add fnos/backup_manager.py fnos/download_center.py fnos/__init__.py examples/backup_manager.py examples/download_center.py tests/test_backup_download_queries.py
git commit -m "feat: add backup and download query APIs"
```

Expected: 12 contracts pass and both example help commands exit 0.

---

### Task 12: IPBlocker and Security

**Files:**
- Create: `fnos/ip_blocker.py`
- Create: `fnos/security.py`
- Create: `tests/test_ipblocker_security_queries.py`
- Create: `examples/ip_blocker.py`
- Create: `examples/security.py`
- Modify: `fnos/__init__.py`

**Interfaces:**
- Produces three IP blocker query methods.
- Produces `Security.get_firewall()` and `get_process_traffic(processes)`.
- Produces five captured `CASES` and defensive-copy validation.

- [ ] **Step 1: Write failing security-domain contracts**

Create `tests/test_ipblocker_security_queries.py`:

```python
import pytest

from fnos import IPBlocker, Security
from tests.query_contract import QueryCase, RecordingClient, assert_query_case


PROCESSES = [
    {"pid": 1001, "process": "example-process"},
    {"pid": 1002, "process": "example-worker"},
]

CASES = [
    QueryCase("allow-list", IPBlocker, "list_allowed_addresses", "appcgi.ipblocker.queryAllowList", {}),
    QueryCase("auto-block", IPBlocker, "get_auto_block_rule", "appcgi.ipblocker.queryAutoBlockRule", {}),
    QueryCase("deny-list", IPBlocker, "list_denied_addresses", "appcgi.ipblocker.queryDenyList", {}),
    QueryCase("firewall", Security, "get_firewall", "appcgi.security.firewall.getting", {}),
    QueryCase("process-traffic", Security, "get_process_traffic", "appcgi.security.flowaudit.traffic", {"data": PROCESSES}, args=(PROCESSES,)),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
async def test_security_domain_query_contract(case):
    await assert_query_case(case)


@pytest.mark.asyncio
async def test_process_traffic_copies_mutable_input():
    source = [{"pid": 1001, "process": "example-process"}]
    client = RecordingClient()
    await Security(client).get_process_traffic(source)
    sent = client.calls[0][1]["data"]
    assert sent == source
    assert sent is not source
    assert sent[0] is not source[0]


@pytest.mark.asyncio
async def test_process_traffic_rejects_non_dict_list():
    with pytest.raises(ValueError):
        await Security(object()).get_process_traffic([1])
```

- [ ] **Step 2: Run contracts to verify RED**

Run: `uv run pytest -q tests/test_ipblocker_security_queries.py`

Expected: import fails for the two new classes.

- [ ] **Step 3: Implement and export IPBlocker and Security**

Create `fnos/ip_blocker.py`:

```python
from .client import FnosClient


class IPBlocker:
    def __init__(self, client: FnosClient):
        self.client = client

    async def list_allowed_addresses(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response(
            "appcgi.ipblocker.queryAllowList", {}, timeout
        )

    async def get_auto_block_rule(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response(
            "appcgi.ipblocker.queryAutoBlockRule", {}, timeout
        )

    async def list_denied_addresses(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response(
            "appcgi.ipblocker.queryDenyList", {}, timeout
        )
```

Create `fnos/security.py`:

```python
from ._validation import copy_dict_list
from .client import FnosClient


class Security:
    def __init__(self, client: FnosClient):
        self.client = client

    async def get_firewall(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response(
            "appcgi.security.firewall.getting", {}, timeout
        )

    async def get_process_traffic(
        self, processes: list[dict], timeout: float = 10.0
    ) -> dict:
        payload = {"data": copy_dict_list("processes", processes)}
        return await self.client.request_payload_with_response(
            "appcgi.security.flowaudit.traffic", payload, timeout
        )
```

Export `IPBlocker` and `Security` from `fnos/__init__.py` and add both to `__all__`.

- [ ] **Step 4: Add both runnable examples**

Create `examples/ip_blocker.py`:

```python
#!/usr/bin/env python3
import argparse
import asyncio

from fnos import FnosClient, IPBlocker
from common import add_auth_arguments, connect_and_login


async def main():
    parser = argparse.ArgumentParser(description="fnOS IP 阻止规则查询示例")
    add_auth_arguments(parser)
    args = parser.parse_args()
    client = FnosClient()
    try:
        await connect_and_login(client, args)
        blocker = IPBlocker(client)
        print("允许列表:", await blocker.list_allowed_addresses())
        print("自动阻止规则:", await blocker.get_auto_block_rule())
        print("拒绝列表:", await blocker.list_denied_addresses())
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
```

Create `examples/security.py`:

```python
#!/usr/bin/env python3
import argparse
import asyncio

from fnos import FnosClient, ResourceMonitor, Security
from common import add_auth_arguments, connect_and_login


async def main():
    parser = argparse.ArgumentParser(description="fnOS 安全状态查询示例")
    add_auth_arguments(parser)
    args = parser.parse_args()
    client = FnosClient()
    try:
        await connect_and_login(client, args)
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
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 5: Verify and commit**

```bash
uv run pytest -q tests/test_ipblocker_security_queries.py
uv run python examples/ip_blocker.py --help
uv run python examples/security.py --help
git add fnos/ip_blocker.py fnos/security.py fnos/__init__.py examples/ip_blocker.py examples/security.py tests/test_ipblocker_security_queries.py
git commit -m "feat: add security query APIs"
```

Expected: five contracts, validation, copying, and help checks pass.

---

### Task 13: LicenseManager, SystemRestore, and LiveUpdate

**Files:**
- Create: `fnos/license_manager.py`
- Create: `fnos/system_restore.py`
- Create: `fnos/live_update.py`
- Create: `tests/test_system_service_queries.py`
- Create: `examples/license_manager.py`
- Create: `examples/system_restore.py`
- Create: `examples/live_update.py`
- Modify: `fnos/__init__.py`

**Interfaces:**
- Produces `LicenseManager.list(page=1, page_size=200, timeout=10.0)` with nested `data` pagination.
- Produces `SystemRestore.get_info()` and `LiveUpdate.get_status()`.
- Produces three captured `CASES`.

- [ ] **Step 1: Write failing system-service contracts**

Create `tests/test_system_service_queries.py`:

```python
import pytest

from fnos import LicenseManager, LiveUpdate, SystemRestore
from tests.query_contract import QueryCase, assert_query_case


CASES = [
    QueryCase("licenses", LicenseManager, "list", "appcgi.license.soft.list", {"data": {"page": 1, "pageSize": 200}}),
    QueryCase("restore-info", SystemRestore, "get_info", "appcgi.sysrestore.getInfo", {}),
    QueryCase("update-status", LiveUpdate, "get_status", "liveupdate.status", {}),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
async def test_system_service_query_contract(case):
    await assert_query_case(case)


@pytest.mark.asyncio
@pytest.mark.parametrize("field", ["page", "page_size"])
async def test_license_pagination_must_be_positive(field):
    kwargs = {"page": 1, "page_size": 200, field: 0}
    with pytest.raises(ValueError):
        await LicenseManager(object()).list(**kwargs)
```

- [ ] **Step 2: Run contracts to verify RED**

Run: `uv run pytest -q tests/test_system_service_queries.py`

Expected: import failures for the new classes.

- [ ] **Step 3: Implement and export all three classes**

Create `fnos/license_manager.py`:

```python
from ._validation import require_positive_int
from .client import FnosClient


class LicenseManager:
    def __init__(self, client: FnosClient):
        self.client = client

    async def list(
        self, page: int = 1, page_size: int = 200, timeout: float = 10.0
    ) -> dict:
        require_positive_int("page", page)
        require_positive_int("page_size", page_size)
        payload = {"data": {"page": page, "pageSize": page_size}}
        return await self.client.request_payload_with_response(
            "appcgi.license.soft.list", payload, timeout
        )
```

Create `fnos/system_restore.py`:

```python
from .client import FnosClient


class SystemRestore:
    def __init__(self, client: FnosClient):
        self.client = client

    async def get_info(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response(
            "appcgi.sysrestore.getInfo", {}, timeout
        )
```

Create `fnos/live_update.py`:

```python
from .client import FnosClient


class LiveUpdate:
    def __init__(self, client: FnosClient):
        self.client = client

    async def get_status(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response(
            "liveupdate.status", {}, timeout
        )
```

Export `LicenseManager`, `SystemRestore`, and `LiveUpdate` from `fnos/__init__.py` and add them to `__all__`.

- [ ] **Step 4: Add the three runnable examples**

Create `examples/license_manager.py`:

```python
#!/usr/bin/env python3
import argparse
import asyncio

from fnos import FnosClient, LicenseManager
from common import add_auth_arguments, connect_and_login


async def main():
    parser = argparse.ArgumentParser(description="fnOS 软件许可查询示例")
    add_auth_arguments(parser)
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=200)
    args = parser.parse_args()
    client = FnosClient()
    try:
        await connect_and_login(client, args)
        print(await LicenseManager(client).list(args.page, args.page_size))
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
```

Create `examples/system_restore.py`:

```python
#!/usr/bin/env python3
import argparse
import asyncio

from fnos import FnosClient, SystemRestore
from common import add_auth_arguments, connect_and_login


async def main():
    parser = argparse.ArgumentParser(description="fnOS 系统恢复信息查询示例")
    add_auth_arguments(parser)
    args = parser.parse_args()
    client = FnosClient()
    try:
        await connect_and_login(client, args)
        print(await SystemRestore(client).get_info())
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
```

Create `examples/live_update.py`:

```python
#!/usr/bin/env python3
import argparse
import asyncio

from fnos import FnosClient, LiveUpdate
from common import add_auth_arguments, connect_and_login


async def main():
    parser = argparse.ArgumentParser(description="fnOS 在线更新状态查询示例")
    add_auth_arguments(parser)
    args = parser.parse_args()
    client = FnosClient()
    try:
        await connect_and_login(client, args)
        print(await LiveUpdate(client).get_status())
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 5: Verify and commit**

```bash
uv run pytest -q tests/test_system_service_queries.py
uv run python examples/license_manager.py --help
uv run python examples/system_restore.py --help
uv run python examples/live_update.py --help
git add fnos/license_manager.py fnos/system_restore.py fnos/live_update.py fnos/__init__.py examples/license_manager.py examples/system_restore.py examples/live_update.py tests/test_system_service_queries.py
git commit -m "feat: add system service query APIs"
```

Expected: three contracts and all help checks pass.

---

### Task 14: MountManager and NetworkServer

**Files:**
- Create: `fnos/mount_manager.py`
- Create: `fnos/network_server.py`
- Create: `tests/test_mount_network_server_queries.py`
- Create: `examples/mount_manager.py`
- Create: `examples/network_server.py`
- Modify: `fnos/__init__.py`

**Interfaces:**
- Produces two MountManager methods and five NetworkServer methods.
- Produces eight captured `CASES`, including both DDNS page-size captures.

- [ ] **Step 1: Write failing mount and network-server contracts**

Create `tests/test_mount_network_server_queries.py`:

```python
import pytest

from fnos import MountManager, NetworkServer
from tests.query_contract import QueryCase, assert_query_case


CASES = [
    QueryCase("mounts", MountManager, "list_mounts", "appcgi.mountmgr.list", {}),
    QueryCase("mount-settings", MountManager, "get_settings", "appcgi.mountmgr.setting.detail", {}),
    QueryCase("certificates", NetworkServer, "list_certificates", "appcgi.netsvr.cert.list", {}),
    QueryCase("connection-config", NetworkServer, "get_connection_config", "appcgi.netsvr.conn.getconfig", {}),
    QueryCase("connection-status", NetworkServer, "get_connection_status", "appcgi.netsvr.conn.status", {}),
    QueryCase("ddns-providers", NetworkServer, "list_ddns_providers", "appcgi.netsvr.ddns.provider.list", {}),
    QueryCase("ddns-records-default", NetworkServer, "list_ddns_records", "appcgi.netsvr.ddns.record.list", {"data": {"page": 1, "pageSize": 200}}),
    QueryCase("ddns-records-large", NetworkServer, "list_ddns_records", "appcgi.netsvr.ddns.record.list", {"data": {"page": 1, "pageSize": 999}}, kwargs={"page_size": 999}),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
async def test_mount_network_server_query_contract(case):
    await assert_query_case(case)


@pytest.mark.asyncio
@pytest.mark.parametrize("field", ["page", "page_size"])
async def test_ddns_pagination_must_be_positive(field):
    kwargs = {"page": 1, "page_size": 200, field: 0}
    with pytest.raises(ValueError):
        await NetworkServer(object()).list_ddns_records(**kwargs)
```

- [ ] **Step 2: Run contracts to verify RED**

Run: `uv run pytest -q tests/test_mount_network_server_queries.py`

Expected: import failures for `MountManager` and `NetworkServer`.

- [ ] **Step 3: Implement and export both classes**

Create `fnos/mount_manager.py`:

```python
from .client import FnosClient


class MountManager:
    def __init__(self, client: FnosClient):
        self.client = client

    async def list_mounts(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response(
            "appcgi.mountmgr.list", {}, timeout
        )

    async def get_settings(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response(
            "appcgi.mountmgr.setting.detail", {}, timeout
        )
```

Create `fnos/network_server.py`:

```python
from ._validation import require_positive_int
from .client import FnosClient


class NetworkServer:
    def __init__(self, client: FnosClient):
        self.client = client

    async def list_certificates(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response(
            "appcgi.netsvr.cert.list", {}, timeout
        )

    async def get_connection_config(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response(
            "appcgi.netsvr.conn.getconfig", {}, timeout
        )

    async def get_connection_status(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response(
            "appcgi.netsvr.conn.status", {}, timeout
        )

    async def list_ddns_providers(self, timeout: float = 10.0) -> dict:
        return await self.client.request_payload_with_response(
            "appcgi.netsvr.ddns.provider.list", {}, timeout
        )

    async def list_ddns_records(
        self, page: int = 1, page_size: int = 200, timeout: float = 10.0
    ) -> dict:
        require_positive_int("page", page)
        require_positive_int("page_size", page_size)
        payload = {"data": {"page": page, "pageSize": page_size}}
        return await self.client.request_payload_with_response(
            "appcgi.netsvr.ddns.record.list", payload, timeout
        )
```

Export `MountManager` and `NetworkServer` from `fnos/__init__.py` and add them to `__all__`.

- [ ] **Step 4: Add both runnable examples**

Create `examples/mount_manager.py`:

```python
#!/usr/bin/env python3
import argparse
import asyncio

from fnos import FnosClient, MountManager
from common import add_auth_arguments, connect_and_login


async def main():
    parser = argparse.ArgumentParser(description="fnOS 挂载管理查询示例")
    add_auth_arguments(parser)
    args = parser.parse_args()
    client = FnosClient()
    try:
        await connect_and_login(client, args)
        mounts = MountManager(client)
        print("挂载列表:", await mounts.list_mounts())
        print("挂载设置:", await mounts.get_settings())
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
```

Create `examples/network_server.py`:

```python
#!/usr/bin/env python3
import argparse
import asyncio

from fnos import FnosClient, NetworkServer
from common import add_auth_arguments, connect_and_login


async def main():
    parser = argparse.ArgumentParser(description="fnOS 网络服务查询示例")
    add_auth_arguments(parser)
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=200)
    args = parser.parse_args()
    client = FnosClient()
    try:
        await connect_and_login(client, args)
        server = NetworkServer(client)
        print("证书:", await server.list_certificates())
        print("连接配置:", await server.get_connection_config())
        print("连接状态:", await server.get_connection_status())
        print("DDNS 服务商:", await server.list_ddns_providers())
        print("DDNS 记录:", await server.list_ddns_records(args.page, args.page_size))
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 5: Verify and commit**

```bash
uv run pytest -q tests/test_mount_network_server_queries.py
uv run python examples/mount_manager.py --help
uv run python examples/network_server.py --help
git add fnos/mount_manager.py fnos/network_server.py fnos/__init__.py examples/mount_manager.py examples/network_server.py tests/test_mount_network_server_queries.py
git commit -m "feat: add mount and network service query APIs"
```

Expected: eight contracts, validation, and both help checks pass.

---

### Task 15: Full Mock-Server Integration Coverage and CI Pin

**Files:**
- Create: `tests/query_cases.py`
- Create: `tests/test_extended_query_integration.py`
- Modify: `.github/workflows/integration-tests.yml`

**Interfaces:**
- Produces: `ALL_QUERY_CASES`, containing exactly 82 cases across 71 endpoints.
- Consumes: all `CASES` constants from Tasks 2 through 14.
- Verifies: every public wrapper routes successfully through fnos-mock-server.

- [ ] **Step 1: Create the aggregate case registry**

Create `tests/query_cases.py`:

```python
from tests.test_backup_download_queries import CASES as BACKUP_DOWNLOAD_CASES
from tests.test_docker_manager_queries import CASES as DOCKER_CASES
from tests.test_file_queries import CASES as FILE_CASES
from tests.test_ipblocker_security_queries import CASES as SECURITY_CASES
from tests.test_mount_network_server_queries import CASES as MOUNT_NETWORK_SERVER_CASES
from tests.test_network_queries import CASES as NETWORK_CASES
from tests.test_resource_monitor_queries import CASES as RESOURCE_MONITOR_CASES
from tests.test_sac_system_info_queries import CASES as SAC_SYSTEM_INFO_CASES
from tests.test_share_link_queries import CASES as SHARE_LINK_CASES
from tests.test_share_protocol_queries import CASES as SHARE_PROTOCOL_CASES
from tests.test_store_queries import CASES as STORE_CASES
from tests.test_system_service_queries import CASES as SYSTEM_SERVICE_CASES
from tests.test_user_queries import CASES as USER_CASES


ALL_QUERY_CASES = [
    *DOCKER_CASES,
    *NETWORK_CASES,
    *RESOURCE_MONITOR_CASES,
    *FILE_CASES,
    *STORE_CASES,
    *USER_CASES,
    *SHARE_PROTOCOL_CASES,
    *SHARE_LINK_CASES,
    *SAC_SYSTEM_INFO_CASES,
    *BACKUP_DOWNLOAD_CASES,
    *SECURITY_CASES,
    *SYSTEM_SERVICE_CASES,
    *MOUNT_NETWORK_SERVER_CASES,
]
```

- [ ] **Step 2: Write the failing integration coverage**

Create `tests/test_extended_query_integration.py`:

```python
import pytest

from fnos import FnosClient
from tests.query_cases import ALL_QUERY_CASES


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_all_extended_query_endpoints_are_routable():
    assert len(ALL_QUERY_CASES) == 82
    unique_cases = {}
    for case in ALL_QUERY_CASES:
        unique_cases.setdefault(case.endpoint, case)
    assert len(unique_cases) == 71

    client = FnosClient()
    try:
        await client.connect("127.0.0.1:5666")
        login = await client.login("admin", "admin")
        assert login.get("result") == "succ"

        for endpoint, case in unique_cases.items():
            owner = case.owner(client)
            result = await getattr(owner, case.method)(*case.args, **case.kwargs)
            assert isinstance(result, dict), endpoint
            assert "Unknown request type" not in result.get("errmsg", ""), endpoint
    finally:
        await client.close()
```

- [ ] **Step 3: Run against the old CI mock pin to verify RED**

Use a temporary detached worktree so the sibling mock-server checkout is not switched or modified:

```bash
git -C ../fnos-mock-server worktree add --detach /tmp/fnos-mock-old d26b2d21efc2ed1cfffbc09868d3445340ed1acc
pushd /tmp/fnos-mock-old
uv sync --python 3.11
uv run python -m server.main >/tmp/pyfnos-old-mock.log 2>&1 &
OLD_MOCK_PID=$!
popd
for attempt in $(seq 1 30); do
  nc -z 127.0.0.1 5666 && break
  sleep 1
done
uv run pytest -q tests/test_extended_query_integration.py -m integration
kill "$OLD_MOCK_PID"
wait "$OLD_MOCK_PID" 2>/dev/null || true
git -C ../fnos-mock-server worktree remove /tmp/fnos-mock-old
```

Expected: FAIL with an unknown request or timeout because the old pinned mock-server commit lacks the new fixtures. Stop the old server and remove the temporary worktree even after the expected failure.

- [ ] **Step 4: Update the CI mock-server pin**

In `.github/workflows/integration-tests.yml`, change:

```yaml
FNOS_MOCK_SERVER_REF: d26b2d21efc2ed1cfffbc09868d3445340ed1acc
```

to:

```yaml
FNOS_MOCK_SERVER_REF: d9592a05a8e07082b954921acfae3a9a915f3c01
```

- [ ] **Step 5: Run integration against the updated sibling checkout**

Run from the pyfnos repository:

```bash
pushd ../fnos-mock-server
uv run python -m server.main >/tmp/pyfnos-extended-mock.log 2>&1 &
MOCK_PID=$!
popd
for attempt in $(seq 1 30); do
  nc -z 127.0.0.1 5666 && break
  sleep 1
done
uv run pytest -q tests/test_extended_query_integration.py -m integration
kill "$MOCK_PID"
wait "$MOCK_PID" 2>/dev/null || true
```

Expected: the integration test passes with `82` cases and `71` unique routable endpoints.

- [ ] **Step 6: Commit**

```bash
git add tests/query_cases.py tests/test_extended_query_integration.py .github/workflows/integration-tests.yml
git commit -m "test: cover extended query APIs with mock server"
```

---

### Task 16: Example Smoke Tests, README, and Changelog

**Files:**
- Create: `tests/test_examples_help.py`
- Modify: `README.md`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: all 18 new or extended example files.
- Produces: non-network `--help` smoke coverage for every `examples/*.py` file.
- Produces: complete public API, example inventory, and deferred-endpoint documentation.

- [ ] **Step 1: Write the example smoke test**

Create `tests/test_examples_help.py`:

```python
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = sorted((ROOT / "examples").glob("*.py"))
NEW_EXAMPLES = {
    "backup_manager.py",
    "download_center.py",
    "ip_blocker.py",
    "license_manager.py",
    "live_update.py",
    "mount_manager.py",
    "network_server.py",
    "security.py",
    "system_restore.py",
}


def test_new_example_inventory_is_complete():
    assert NEW_EXAMPLES <= {path.name for path in EXAMPLES}


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda path: path.name)
def test_example_help_does_not_connect(example):
    completed = subprocess.run(
        [sys.executable, str(example), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr
    assert "Traceback" not in completed.stderr
```

- [ ] **Step 2: Run the smoke test before documentation changes**

Run: `uv run pytest -q tests/test_examples_help.py`

Expected: all example help commands pass. If a newly added example import or parser is broken, fix that example before proceeding.

- [ ] **Step 3: Extend the README API table with the exact public surface**

Add one row per method under its class. Use these exact class-to-method mappings and describe each as a read-only query:

```text
DockerManager: list_image_downloads, list_images, list_networks, list_registry_repositories
Network: get_gateway, get_multi_gateway_status, get_nic_performance_mode, get_info, get_ssh_status
ResourceMonitor: npu, processes, service_processes, system_fan
File: list_app_directories, list_favorites, list_directory_entries, list_recent, list_shared, list_shared_by_others, list_team_trash_bins, list_trash
Store: get_cache_device_state, get_disk_idle_time, get_disk_wakeup, get_removable_config, list_cache_devices, list_removable_devices
User: list_tokens, get_my_twofa_config, get_global_twofa_config, get_user_twofa_config, get_active_state, get_group_info, list_groups, list_login_devices, get_preference
Share: dlna_options, dlna_share_options, ftp_options, ftp_share_options, nfs_options, nfs_share_options, smb_share_options, webdav_options, webdav_share_options, get_link_defaults, get_default_link, list_links, get_link_permission
SAC: get_email_config, list_email_providers
SystemInfo: get_reserved_partition
BackupManager: list_tasks
DownloadCenter: get_default_save_directory, get_statistics, query_tasks
IPBlocker: list_allowed_addresses, get_auto_block_rule, list_denied_addresses
Security: get_firewall, get_process_traffic
LicenseManager: list
SystemRestore: get_info
LiveUpdate: get_status
MountManager: list_mounts, get_settings
NetworkServer: list_certificates, get_connection_config, get_connection_status, list_ddns_providers, list_ddns_records
```

The resulting README table must contain all 71 methods, show the documented defaults for pagination/filter arguments, and keep all pre-existing rows.

- [ ] **Step 4: Update the README example inventory**

Update the descriptions for these existing rows to mention their new query coverage:

```markdown
| `resource_monitor.py` | 演示 CPU、GPU、内存、磁盘、网络、NPU、进程、服务进程和风扇查询 |
| `sac.py` | 演示 UPS、邮件通知配置和邮件服务商查询 |
| `store.py` | 演示存储、缓存设备、可移动设备、休眠和唤醒配置查询 |
| `system_info.py` | 演示主机、版本、硬件、运行时间和保留分区查询 |
| `user.py` | 演示用户、用户组、令牌、登录设备、2FA 和用户偏好查询 |
| `network.py` | 演示网卡、网关、多网关、性能模式和 SSH 状态查询 |
| `file.py` | 演示文件操作及应用目录、收藏、最近文件、共享和回收站查询 |
| `docker_manager.py` | 演示 Compose、容器、镜像、下载任务、网络和镜像仓库查询 |
| `share.py` | 演示 SMB/NFS/FTP/WebDAV/DLNA 配置及分享链接查询 |
```

Append the nine new rows:

```markdown
| `backup_manager.py` | 演示备份任务查询 |
| `download_center.py` | 演示下载目录、统计和任务查询 |
| `ip_blocker.py` | 演示 IP 允许列表、拒绝列表和自动阻止规则查询 |
| `license_manager.py` | 演示软件许可列表查询 |
| `mount_manager.py` | 演示挂载列表和挂载设置查询 |
| `network_server.py` | 演示证书、连接状态和 DDNS 查询 |
| `security.py` | 演示防火墙和进程流量查询 |
| `system_restore.py` | 演示系统恢复信息查询 |
| `live_update.py` | 演示在线更新状态查询 |
```

- [ ] **Step 5: Document deferred endpoints**

Add a README subsection named `尚未封装的抓包端点` with this exact list and explain that each is deferred because no matching sanitized request fixture exists:

```text
appcgi.license.soft.get
appcgi.license.soft.ipc.get
appcgi.mountmgr.task.list
appcgi.sac.entry.v1.getEntryList
appcgi.sac.entry.v1.getUserDesktop
taskState.list
util.getSI
```

- [ ] **Step 6: Add the changelog entry**

Insert before version `0.13.0` in `CHANGELOG.md`:

```markdown
## [Unreleased]

### Added
- 新增 71 个基于 fnos-mock-server 请求/响应 fixtures 验证的只读查询接口
- 新增 `BackupManager`、`DownloadCenter`、`IPBlocker`、`LicenseManager`、`MountManager`、`NetworkServer`、`Security`、`SystemRestore` 和 `LiveUpdate`
- 扩展 Docker、网络、资源监控、文件、存储、用户、共享、SAC 和系统信息查询能力
- 新增 9 个领域示例程序，并扩展 9 个现有示例程序
- 新增 82 个请求案例的单元契约验证和 71 个端点的 mock-server 集成覆盖
```

- [ ] **Step 7: Verify docs, examples, and commit**

Run:

```bash
uv run pytest -q tests/test_examples_help.py
git diff --check
git add tests/test_examples_help.py README.md CHANGELOG.md
git commit -m "docs: document extended query APIs"
```

Expected: all example help smoke tests pass, no whitespace errors, and commit succeeds.

---

### Task 17: Fixture Parity and Full Regression Verification

**Files:**
- Verify only; no repository files should change.

**Interfaces:**
- Consumes: `tests.query_cases.ALL_QUERY_CASES` and sibling `fnos-mock-server/requests/`.
- Verifies: exactly 82 canonical payload cases and 71 endpoints match both repositories.

- [ ] **Step 1: Compare unit contracts to the request fixture corpus**

Run from the pyfnos repository:

```bash
uv run python - <<'PY'
import json
from collections import defaultdict
from pathlib import Path

from tests.query_cases import ALL_QUERY_CASES


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


sdk = defaultdict(set)
for case in ALL_QUERY_CASES:
    sdk[case.endpoint].add(canonical(case.payload))

mock = defaultdict(set)
requests_dir = Path("../fnos-mock-server/requests")
for case_path in requests_dir.glob("*/case-*.json"):
    request = json.loads(case_path.read_text(encoding="utf-8"))
    endpoint = request.pop("req")
    request.pop("reqid", None)
    mock[endpoint].add(canonical(request))

assert len(ALL_QUERY_CASES) == 82
assert len(sdk) == 71
assert dict(sdk) == dict(mock)
print("82 request cases across 71 endpoints match")
PY
```

Expected: prints `82 request cases across 71 endpoints match`.

- [ ] **Step 2: Run all non-integration tests**

Run:

```bash
uv run pytest -q -m "not integration"
```

Expected: all unit, validation, contract, existing non-integration, and example smoke tests pass.

- [ ] **Step 3: Run the complete suite with the updated mock server**

Run:

```bash
pushd ../fnos-mock-server
uv run python -m server.main >/tmp/pyfnos-extended-mock.log 2>&1 &
MOCK_PID=$!
popd
trap 'kill "$MOCK_PID" 2>/dev/null || true' EXIT
for attempt in $(seq 1 30); do
  nc -z 127.0.0.1 5666 && break
  sleep 1
done
uv run pytest -q
kill "$MOCK_PID"
wait "$MOCK_PID" 2>/dev/null || true
trap - EXIT
```

Expected: the full current and new test suite passes.

- [ ] **Step 4: Audit scope, exports, and worktree state**

Run:

```bash
git diff --check
git status --short
uv run python - <<'PY'
import fnos

expected = {
    "BackupManager",
    "DownloadCenter",
    "IPBlocker",
    "LicenseManager",
    "LiveUpdate",
    "MountManager",
    "NetworkServer",
    "Security",
    "SystemRestore",
}
assert expected <= set(fnos.__all__)
print("all new public classes exported")
PY
```

Expected: no whitespace errors, only intentional files are listed by Git, and the export audit prints `all new public classes exported`.
