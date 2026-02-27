# WSS/SSL 连接支持 - 技术实现计划

## 修改范围

### 主要文件

| 文件 | 修改类型 | 说明 |
|-----|---------|-----|
| `fnos/client.py` | 修改 | 添加 SSL 支持逻辑 |
| `demo.py` | 修改 | 添加命令行参数支持 |

## 实现细节

### 1. FnosClient 类变更

#### 1.1 新增实例属性

在 `__init__()` 中添加：

```python
self.use_ssl = False
self.skip_ssl_verify = True
```

#### 1.2 connect() 方法变更

**新增参数：**
- `use_ssl: bool = False` - 是否使用 SSL 连接
- `skip_ssl_verify: bool = True` - 是否跳过证书验证

**endpoint 解析逻辑：**
```python
def _parse_endpoint(self, endpoint: str, use_ssl: bool) -> tuple[str, bool]:
    """
    解析 endpoint，返回 (host_port, actual_use_ssl)
    
    - 如果 endpoint 以 wss:// 开头，返回去掉前缀的地址和 True
    - 如果 endpoint 以 ws:// 开头，返回去掉前缀的地址和 False
    - 否则返回原地址和 use_ssl 参数值
    """
    if endpoint.startswith("wss://"):
        return endpoint[6:], True
    elif endpoint.startswith("ws://"):
        return endpoint[5:], False
    else:
        return endpoint, use_ssl
```

**WebSocket 连接构建：**
```python
# 根据 use_ssl 选择协议
protocol = "wss" if use_ssl else "ws"
uri = f"{protocol}://{endpoint}/websocket?type={self.type}"

# 配置 SSL 上下文
ssl_context = None
if use_ssl and skip_ssl_verify:
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

# 创建连接
self.ws = await websockets.connect(uri, ssl=ssl_context)
```

#### 1.3 reconnect() 方法变更

无需修改，因为 `connect()` 会自动使用保存的 SSL 配置。

### 2. demo.py 变更

添加命令行参数：

```python
parser.add_argument('--use-ssl', action='store_true', help='使用 SSL/WSS 连接')
parser.add_argument('--skip-ssl-verify', type=lambda x: x.lower() == 'true', 
                    default=True, help='跳过 SSL 证书验证 (默认: True)')
```

## 依赖

- `ssl` 模块（Python 标准库）
- `websockets` 库已支持 SSL 参数

## 测试策略

### 单元测试

- 测试 endpoint 解析逻辑（各种前缀组合）
- 测试协议选择逻辑

### 集成测试

- 测试 ws:// 连接（现有行为）
- 测试 wss:// 连接（需要测试服务器）
- 测试自签名证书跳过验证

## 风险与缓解

| 风险 | 缓解措施 |
|-----|---------|
| 向后兼容性破坏 | 默认值保持 `use_ssl=False` |
| SSL 验证失败 | 默认 `skip_ssl_verify=True` 便于自签名证书场景 |
