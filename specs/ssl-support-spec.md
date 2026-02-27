# WSS/SSL 连接支持规范

## 概述

为 `FnosClient` 添加 HTTPS/WSS (安全 WebSocket) 连接支持，允许用户通过 SSL/TLS 加密连接到服务器。

## 功能需求

### FR-1: use_ssl 参数

**WHEN** 用户调用 `connect()` 方法时，
**THEN THE SYSTEM SHALL** 接受一个 `use_ssl` 布尔参数（默认 `False`），
**AND** 当 `use_ssl=True` 时使用 `wss://` 协议连接。

### FR-2: endpoint 协议前缀支持

**WHEN** 用户在 `endpoint` 参数中指定 `ws://` 或 `wss://` 前缀时，
**THEN THE SYSTEM SHALL** 自动解析并使用该协议，
**AND** endpoint 中指定的协议前缀优先于 `use_ssl` 参数。

### FR-3: SSL 证书验证控制

**WHEN** 用户连接到使用自签名证书的服务器时，
**THEN THE SYSTEM SHALL** 提供 `skip_ssl_verify` 参数（默认 `True`）控制是否跳过证书验证，
**AND** 当 `skip_ssl_verify=True` 时跳过 SSL 证书验证，
**AND** 当 `skip_ssl_verify=False` 时验证 SSL 证书。

### FR-4: 重连时保持 SSL 配置

**WHEN** 用户调用 `reconnect()` 方法时，
**THEN THE SYSTEM SHALL** 自动使用之前保存的 SSL 配置（`use_ssl` 和 `skip_ssl_verify`）。

## 参数行为矩阵

| endpoint 格式 | use_ssl | 实际协议 |
|--------------|---------|---------|
| `wss://host:port` | 任意 | wss:// |
| `ws://host:port` | 任意 | ws:// |
| `host:port` | False | ws:// |
| `host:port` | True | wss:// |

## API 变更

### connect() 方法签名变更

```python
async def connect(
    self, 
    endpoint, 
    timeout: float = 3.0,
    use_ssl: bool = False,
    skip_ssl_verify: bool = True
):
```

### 新增实例属性

- `self.use_ssl: bool` - 保存 SSL 配置用于重连
- `self.skip_ssl_verify: bool` - 保存证书验证配置用于重连

## 验收标准

- [ ] `use_ssl=True` 时使用 wss:// 协议连接
- [ ] `use_ssl=False`（默认）时使用 ws:// 协议连接
- [ ] endpoint 包含 `wss://` 前缀时使用 wss:// 协议
- [ ] endpoint 包含 `ws://` 前缀时使用 ws:// 协议
- [ ] endpoint 中的协议前缀优先于 use_ssl 参数
- [ ] `skip_ssl_verify=True` 时跳过证书验证
- [ ] `skip_ssl_verify=False` 时验证证书
- [ ] `reconnect()` 方法使用保存的 SSL 配置
- [ ] 向后兼容：现有代码无需修改即可正常工作
