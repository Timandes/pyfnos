# 磁盘温度诊断异常详情与 2FA 设计

## 背景与根因

`tools/list_disk_temperatures.py` 当前将所有顶层异常统一格式化为异常类名：

```text
错误: 磁盘温度诊断失败（Exception）
```

根因是 `_exception_summary()` 只返回 `type(error).__name__`，主动丢弃了 `str(error)`。连接、登录和磁盘查询又共用一个 `except`，因此输出既没有服务端或 SDK 提供的错误详情，也无法确定失败阶段。

当前工具还直接调用 `FnosClient.login()`，没有处理 `twofaRequired` 和 `twofaSetupRequired`。开启两步验证的账号不能通过该工具完成登录，而 `examples/common.py` 已有成熟的 2FA、SSL 和连接辅助行为。

## 目标

1. 为 `tools` 目录提供与 `examples/common.py` 相同的公共认证辅助接口；
2. 支持命令行或安全交互输入的两步验证码，以及信任设备选项；
3. 默认输出失败阶段、异常类型和异常详情；
4. 使用 `--debug` 时输出经过脱敏的完整 traceback；
5. 磁盘监控与 SMART 的非致命跳过原因也包含异常详情；
6. 不输出密码、验证码、token、secret 或其他认证凭据。

## 非目标

- 不修改 `FnosClient`、`Store`、`ResourceMonitor` 或其他 SDK 公共 API；
- 不改变磁盘温度优先级、SMART 回退顺序或最终输出格式；
- 不自动保存或复用两步验证码；
- 不将 `tools` 安装为 Python 包或控制台入口；
- 不在本次修复中重构 `examples/common.py`。

## 文件结构

```text
tools/
├── common.py
└── list_disk_temperatures.py

tests/
├── test_tools_common.py
└── test_list_disk_temperatures_tool.py
```

### `tools/common.py`

提供与 `examples/common.py` 相同的三个公共函数：

- `add_auth_arguments()`；
- `connect_client()`；
- `login_with_twofa()`。

其参数和行为与示例辅助模块保持一致：

- `--user`、`--password`；
- `-e/--endpoint`；
- `--code`；
- `--trust-device`；
- `--use-ssl`；
- `--skip-ssl-verify`；
- `twofaRequired` 时优先使用 `--code`，否则通过 `getpass.getpass()` 安全读取；
- 将 `trust_device` 传递给 `submit_twofa_code()`；
- `twofaSetupRequired` 时明确提示账号需先完成绑定；
- 普通登录或 2FA 最终响应不是 `succ` 时，优先使用 `msg` 或 `errmsg` 报错。

该文件独立存在于 `tools` 中，不在运行时导入 `examples/common.py`。直接运行 `python tools/list_disk_temperatures.py` 时，`from common import ...` 会解析到同目录的 `tools/common.py`。

### `tools/list_disk_temperatures.py`

改用：

```python
from common import add_auth_arguments, connect_client, login_with_twofa
```

脚本继续直接导入 `FnosClient`、`Store` 和 `ResourceMonitor`，但将连接和认证编排交给 `tools/common.py`。

命令行解析先调用 `add_auth_arguments(parser)`，再增加工具专属的 `--debug`。共享参数行为因此与 examples 保持一致；`--debug` 默认为关闭。

## 登录与 2FA 数据流

```text
解析共享认证参数和 --debug
    -> connect_client(client, args)
       -> 根据 --use-ssl / --skip-ssl-verify 连接
    -> login_with_twofa(client, args)
       -> FnosClient.login(user, password)
       -> twofaRequired?
          -> 使用 --code，或通过 getpass 安全读取
          -> submit_twofa_code(code, trust_device=...)
       -> twofaSetupRequired?
          -> 抛出明确 RuntimeError
       -> 最终 result == succ?
          -> 是：进入磁盘温度诊断
          -> 否：使用 msg / errmsg 抛出 RuntimeError
```

## 失败阶段与输出

`run()` 在每个外部边界前更新当前阶段：

1. `连接`；
2. `登录或两步验证`；
3. `磁盘枚举与温度获取`。

默认失败输出示例：

```text
错误: 登录或两步验证阶段失败
异常类型: Exception
异常详情: 未获取到公钥或会话ID
提示: 使用 --debug 查看完整 traceback
```

异常消息为空时，`异常详情` 显示“无详细信息”。顶层输出不再只显示异常类名。

当 `--debug` 开启时，在上述摘要之后输出 Python traceback。traceback 先格式化为字符串，再经过与摘要相同的脱敏逻辑，禁止直接调用未脱敏的 `traceback.print_exception()`。

## 脱敏规则

输出前至少处理以下敏感内容：

- 本次命令行密码；
- 本次通过 `--code` 提供的两步验证码；
- 常见认证字段名后面的值，包括 `token`、`longToken`、`accessToken`、`secret` 和 `password`。

密码和命令行验证码采用精确值替换；认证字段采用大小写不敏感的键值模式替换为 `***`，同时兼容 Python 字典的单引号和 JSON 的双引号形式。交互验证码只存在于 `tools/common.py` 的局部变量中，不插入异常消息，格式化 traceback 时也不包含局部变量。工具不打印完整登录响应。

`tools/common.py` 不负责格式化顶层异常；它只返回成功结果或抛出异常。脱敏和 traceback 由诊断脚本统一处理。

## 非致命接口错误

`ResourceMonitor.disk()` 或单盘 `Store.get_disk_smart(name)` 失败时仍继续现有回退逻辑，但跳过原因从：

```text
接口调用失败: TimeoutError
```

升级为：

```text
接口调用失败: TimeoutError: 请求 appcgi.resmon.disk 超时
```

这些详情同样经过脱敏。由于该路径没有登录凭据参数，使用通用认证字段脱敏；不得输出原始响应对象。

## 测试策略

新增 `tests/test_tools_common.py`，覆盖：

1. 共享参数包含 endpoint、SSL、2FA 和信任设备选项；
2. `connect_client()` 正确传递 SSL 配置；
3. 普通登录成功；
4. `--code` 完成 2FA 并传递 `trust_device`；
5. 未提供 `--code` 时调用 `getpass.getpass()`；
6. `twofaSetupRequired` 和最终登录失败产生明确错误详情。

更新 `tests/test_list_disk_temperatures_tool.py`，覆盖：

1. 诊断脚本通过 tools 公共认证函数连接和登录；
2. 参数解析包含共享认证参数和 `--debug`；
3. 顶层异常输出阶段、类型、详情和 debug 提示；
4. `--debug` 输出 traceback；
5. 密码、验证码、token 和 secret 在摘要及 traceback 中均被遮盖；
6. 监控和 SMART 跳过原因包含异常类型与详情；
7. 现有温度优先级、输出顺序和部分失败行为保持不变。

完成定向测试后运行全量非集成测试，并手工执行 `--help`，确认工具可以从 `tools` 目录正确加载同目录 `common.py`。

## 兼容性与风险

该修改不改变 SDK 公共接口。CLI 新增参数来自 examples 的既有约定，原有显式传入 `--user`、`--password` 和 `-e` 的命令仍可运行。

主要风险是详细异常可能携带敏感值，因此摘要和 traceback 必须共用同一脱敏函数，并用包含模拟密码、验证码、token 和 secret 的测试约束。`--debug` 只增加调用栈，不允许绕过脱敏。
