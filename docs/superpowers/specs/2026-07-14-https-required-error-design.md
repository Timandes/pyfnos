# fnOS 强制 HTTPS 连接异常设计

## 背景

当 fnOS 服务端开启“强制 HTTPS”后，客户端仍以 `ws://` 连接 HTTP 端点时，服务端会返回 HTTP 重定向，例如：

```text
HTTP 302
Location: https://nas.example.com:5667/websocket?type=main
```

`websockets 15.0.1` 会尝试跟随重定向，但它只接受 `ws://` 和 `wss://` URI。由于 `Location` 使用 `https://`，重定向解析最终抛出 `websockets.exceptions.InvalidURI`。该异常是在处理原始 `InvalidStatus(302)` 时隐式抛出的，因此真实异常链将 `InvalidStatus` 保存在 `InvalidURI.__context__`，而不是 `__cause__`。当前 SDK 原样抛出该底层异常，调用方无法稳定区分“fnOS 要求安全连接”和普通 URI 配置错误。

## 目标

当且仅当非安全 WebSocket 连接被服务端通过 HTTP 重定向引导到 HTTPS 地址时，SDK 抛出一个可单独捕获的公共异常，明确告知调用方应使用 WSS。

## 非目标

- 不自动切换到 WSS，也不自动重试连接。
- 不改变 `connect()` 的参数、默认值或现有 SSL 证书验证行为。
- 不将其他 URI、握手、TLS 或网络错误包装为该异常。
- 不引入新的异常基类或重构现有异常体系。

## 公共 API

在 `fnos.exceptions` 中新增：

```python
class HTTPSRequiredError(ConnectionError):
    requested_uri: str
    redirect_uri: str
    status_code: int
```

该异常从 `fnos` 包顶层导出，并加入 `fnos.__all__`。调用方可以使用以下方式处理：

```python
from fnos import FnosClient, HTTPSRequiredError

client = FnosClient()

try:
    await client.connect("nas.example.com:5666")
except HTTPSRequiredError as exc:
    print(f"fnOS 要求安全连接，重定向地址：{exc.redirect_uri}")
```

异常消息应包含以下信息：

- fnOS 服务端要求安全连接；
- 当前 WS 连接被重定向到 HTTPS；
- 调用方应改用 `wss://` endpoint 或传入 `use_ssl=True`；
- 服务端返回的重定向地址。

异常属性含义：

| 属性 | 含义 |
| --- | --- |
| `requested_uri` | SDK 本次尝试连接的完整 `ws://.../websocket?type=...` URI |
| `redirect_uri` | `websockets` 解析出的完整 `https://...` 重定向 URI |
| `status_code` | 服务端返回的 HTTP 重定向状态码 |

## 识别规则

`FnosClient.connect()` 仅在以下条件全部满足时转换异常：

1. 本次连接使用非安全 WebSocket，即 `actual_use_ssl` 为 `False`；
2. `websockets.connect()` 抛出 `websockets.exceptions.InvalidURI`；
3. `InvalidURI.uri` 的 scheme 为 `https`；
4. `InvalidURI` 的显式 `__cause__`（若存在）或隐式 `__context__` 是 `websockets.exceptions.InvalidStatus`；`websockets 15.0.1` 的真实重定向路径使用 `__context__`；
5. 原始 HTTP 状态码是 `301`、`302`、`303`、`307` 或 `308`；
6. 原始响应的 `Location` 头存在，且其经 `websockets` 解析后的目标就是上述 HTTPS URI。

满足全部条件时：

```python
raise HTTPSRequiredError(
    requested_uri=uri,
    redirect_uri=error.uri,
    status_code=redirect_error.response.status_code,
) from error
```

SDK 使用显式 `raise ... from error` 让 `HTTPSRequiredError.__cause__` 指向 `InvalidURI`；原始 `InvalidURI.__context__` 继续指向 `InvalidStatus`，便于日志和高级诊断。

若任一条件不满足，原异常必须原样抛出。这保证普通 endpoint 拼写错误、缺少主机名、WSS 连接失败以及非重定向握手错误不会被误报为 fnOS 强制 HTTPS。

## 组件与数据流

### `fnos/exceptions.py`

负责定义 `HTTPSRequiredError`，保存结构化诊断属性并生成面向调用方的中文错误信息。异常自身不依赖 `websockets` 类型，避免将第三方库对象暴露为公共 API 属性。

### `fnos/client.py`

负责识别第三方异常链并转换为 SDK 异常。识别逻辑放在一个私有辅助方法中，使 `connect()` 保持聚焦，也便于用独立单元测试覆盖正反例。

连接失败的数据流如下：

```text
ws:// endpoint
    -> fnOS 返回 HTTP 3xx + Location: https://...
    -> websockets 抛出 InvalidURI（context: InvalidStatus）
    -> FnosClient 精确匹配异常链
    -> 抛出 HTTPSRequiredError（cause: InvalidURI）
    -> 调用方选择是否改用 WSS 再次连接
```

### `fnos/__init__.py`

从包顶层导出 `HTTPSRequiredError`，让调用方不必依赖内部模块路径。

### 用户文档

在 README 的 SSL/WSS 连接说明中增加 `HTTPSRequiredError` 捕获示例，并在 CHANGELOG 的 Unreleased 部分记录新增公共异常。文档只描述异常识别与人工改用 WSS 的流程，不暗示 SDK 会自动重试。

## 日志与状态

异常转换仍走 `connect()` 现有的连接失败路径：记录一次错误日志、将 `client.connected` 设为 `False`，然后向调用方抛出异常。SDK 不修改 endpoint、`use_ssl` 或证书验证配置，也不会产生隐藏的第二次连接尝试。

## 测试策略

新增独立测试，通过本地临时 TCP 服务返回真实 HTTP 302 握手响应，并用合成异常覆盖负向边界，无需依赖真实 fnOS 服务：

1. HTTP 302 重定向到 HTTPS 时抛出 `HTTPSRequiredError`；
2. 异常的 `requested_uri`、`redirect_uri`、`status_code` 和提示信息正确；
3. `HTTPSRequiredError.__cause__` 保留原始 `InvalidURI`，且 `InvalidURI.__context__` 保留 `InvalidStatus`；
4. 不带重定向原因的普通 `InvalidURI` 原样抛出；
5. 非 HTTPS 目标或非标准重定向状态不转换；
6. 真实 HTTP 服务只收到一次连接，验证 SDK 没有自动重试；
7. 全新 Python 解释器无需预加载 `websockets.exceptions` 即可导入 `fnos`；
8. `HTTPSRequiredError` 可从 `fnos` 顶层导入；
9. README 示例和 CHANGELOG 描述与公共 API 一致。

完成定向测试后运行全量非集成测试，确认现有调用方式和异常行为未回归。

## 兼容性与风险

这是一个仅针对新增可识别场景的异常细化。过去调用方通常捕获 `Exception`，仍可捕获继承自 `ConnectionError` 的新异常；需要精确处理该场景的调用方则可新增 `except HTTPSRequiredError`。

主要兼容性风险来自对 `websockets` 私有实现细节的假设。设计只使用公开异常类型及其公开属性（`InvalidURI.uri`、`InvalidStatus.response`），并通过负向测试约束误判范围。项目当前依赖为 `websockets>=15.0`，测试以该版本系列的异常结构为基准。

## 独立诊断示例

### 目标与范围

新增 `examples/https_required_error.py`，专门演示调用方如何捕获 `HTTPSRequiredError`。强制 HTTPS 重定向发生在登录前，因此示例只接受 endpoint，不要求用户名、密码或两步验证码。

示例只诊断和展示，不自动切换 WSS、不自动重试，也不修改 SDK 的连接行为。

### 命令行接口

```bash
uv run python examples/https_required_error.py \
  -e nas-10.timandes.net:5666
```

参数：

- `-e, --endpoint`：必填；支持 `host:port` 或 `ws://host:port`，示例以非安全 WS 发起连接。

不提供 `--user`、`--password`、`--use-ssl` 或自动重试参数，避免与“检测服务端强制 HTTPS”的单一目的冲突。

### 组件与流程

示例拆分为两个小单元：

- `run(endpoint: str) -> int`：创建 `FnosClient`、执行连接、处理异常并在 `finally` 中关闭客户端；便于直接单元测试真实示例行为。
- `main()`：解析命令行参数，调用 `asyncio.run(run(...))`，并将返回值作为进程退出码。

运行流程：

```text
endpoint
    -> FnosClient.connect(endpoint)
    -> HTTPSRequiredError
       -> 输出 status_code、requested_uri、redirect_uri
       -> 将 https:// 前缀替换为 wss://，输出建议 WSS URI
       -> 明确说明未自动重试
       -> 返回 0
    -> 连接成功
       -> 输出未检测到强制 HTTPS 重定向
       -> 返回 0
    -> 其他异常
       -> 输出“不是已识别的强制 HTTPS 重定向”及原错误
       -> 返回 1
    -> finally 关闭客户端
```

成功检测到目标异常属于该诊断程序的预期结果，因此返回 `0`；其他无法归类的连接失败返回 `1`。

### 输出要求

捕获 `HTTPSRequiredError` 时，输出必须包含：

- HTTP 重定向状态码；
- 原始 WS 请求 URI；
- 服务端 HTTPS 重定向 URI；
- 建议的 `wss://` URI；
- “SDK 未自动重试”的明确说明。

示例不得打印用户名、密码、token 或其他认证信息。

### 测试与文档

新增示例测试，替换网络边界但执行真实 `run()` 逻辑，覆盖：

1. `--help` 可独立运行，包含必填 endpoint，且不包含用户名密码参数；
2. 捕获 `HTTPSRequiredError` 时输出全部结构化信息、返回 `0` 并关闭客户端；
3. 其他连接异常不会被误报，返回 `1` 并关闭客户端；
4. 连接成功时返回 `0` 并关闭客户端；
5. README 包含可复制命令和示例清单条目；
6. CHANGELOG 的 Unreleased 部分记录新增诊断示例。
