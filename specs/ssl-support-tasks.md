# WSS/SSL 连接支持 - 任务分解

## 任务列表

### Task-1: 添加实例属性
**文件:** `fnos/client.py`
**内容:** 在 `__init__()` 中添加 `self.use_ssl` 和 `self.skip_ssl_verify` 属性
**验收:** 属性初始化正确

---

### Task-2: 实现 endpoint 解析方法
**文件:** `fnos/client.py`
**内容:** 添加 `_parse_endpoint()` 方法，解析 `ws://` 和 `wss://` 前缀
**验收:** 
- `wss://host:port` → `("host:port", True)`
- `ws://host:port` → `("host:port", False)`
- `host:port` → `("host:port", use_ssl)`

---

### Task-3: 修改 connect() 方法签名和逻辑
**文件:** `fnos/client.py`
**内容:** 
- 添加 `use_ssl` 和 `skip_ssl_verify` 参数
- 调用 `_parse_endpoint()` 解析 endpoint
- 根据 `use_ssl` 构建 `ws://` 或 `wss://` URI
- 配置 SSL 上下文（当 `use_ssl=True` 时）
- 传递 `ssl` 参数给 `websockets.connect()`
**验收:** 连接使用正确的协议和 SSL 配置

---

### Task-4: 保存 SSL 配置用于重连
**文件:** `fnos/client.py`
**内容:** 在 `connect()` 中保存 `use_ssl` 和 `skip_ssl_verify` 到实例属性
**验收:** `reconnect()` 时使用保存的配置

---

### Task-5: 更新 demo.py 命令行参数
**文件:** `demo.py`
**内容:** 添加 `--use-ssl` 和 `--skip-ssl-verify` 命令行参数
**验收:** 
- `uv run demo.py -e host:port --use-ssl` 正确传递参数
- `uv run demo.py -e wss://host:port` 自动识别协议

---

### Task-6: 验证实现
**内容:** 运行现有测试确保向后兼容性
**验收:** 所有现有测试通过

## 依赖关系

```
Task-1 ─┐
        ├──> Task-3 ──> Task-4 ──> Task-6
Task-2 ─┘                      │
                               │
Task-5 ────────────────────────┘
```

## 执行顺序

1. Task-1: 添加实例属性
2. Task-2: 实现 endpoint 解析方法
3. Task-3: 修改 connect() 方法
4. Task-4: 保存 SSL 配置
5. Task-5: 更新 demo.py
6. Task-6: 验证实现
