# 新增示例 CLI 配套设施设计

## 背景

本次扩展查询 API 新增了 9 个示例程序，但这些文件只具备最基本的
`argparse` 调用。与仓库原有示例相比，它们缺少完整的模块说明、领域参数帮助、
运行过程提示、统一异常输出，以及 README 中可直接复制的运行命令。

本设计让新示例与原有 `examples/` 程序保持一致，不引入新的命令模型。

## 范围

调整以下文件：

- `examples/backup_manager.py`
- `examples/download_center.py`
- `examples/ip_blocker.py`
- `examples/license_manager.py`
- `examples/live_update.py`
- `examples/mount_manager.py`
- `examples/network_server.py`
- `examples/security.py`
- `examples/system_restore.py`
- `tests/test_examples_help.py`
- `README.md`

## CLI 约定

### 保持原有调用模型

- 每个示例启动后仍执行该领域内的全部查询。
- 不增加子命令、`--action` 或交互式选择。
- 不手写 `usage=`；继续由 `argparse` 自动生成 `usage:`，与原有示例一致。
- 继续复用 `examples/common.py` 提供的用户名、密码、endpoint、SSL 和 2FA 参数。
- 不暴露原有示例普遍未暴露的 SDK `timeout` 参数。

### 领域参数

| 示例 | 参数 | 约束与默认值 | 用途 |
| --- | --- | --- | --- |
| `backup_manager.py` | `--direction` | `0` 或 `1`，默认 `0` | 备份任务方向 |
| `download_center.py` | `--state-filter` | 整数，默认 `65535` | 下载任务状态位掩码 |
| `download_center.py` | `--init-flag` | `true` 或 `false`，默认 `true` | 下载任务初始化标志 |
| `license_manager.py` | `--page` | 整数，默认 `1` | 软件许可页码 |
| `license_manager.py` | `--page-size` | 整数，默认 `200` | 软件许可每页数量 |
| `network_server.py` | `--page` | 整数，默认 `1` | DDNS 记录页码 |
| `network_server.py` | `--page-size` | 整数，默认 `200` | DDNS 记录每页数量 |

`ip_blocker.py`、`live_update.py`、`mount_manager.py`、`security.py` 和
`system_restore.py` 调用的公开方法没有额外标量参数，因此只展示公共连接参数。
`security.py` 所需进程列表继续从 `ResourceMonitor.processes()` 的实时响应构造，
不虚构额外 CLI 参数。

所有领域参数的 `help` 文本明确写出含义、允许值和默认值。`--init-flag` 的布尔值
解析方式与现有 `--skip-ssl-verify` 参数保持一致。

## 示例文件结构

每个新示例采用原有简单查询示例的结构：

1. shebang 和中文模块 docstring，说明演示的管理器及查询能力；
2. 创建带中文 `description` 的 `ArgumentParser`；
3. 注册公共认证参数和该示例的领域参数；
4. 打印连接、登录和查询阶段提示；
5. 调用管理器并为每项结果添加中文标签；
6. 使用外层 `except Exception` 输出统一的 `发生错误` 信息；
7. 在 `finally` 中关闭客户端并提示连接已关闭。

示例保持教学用途，不抽象新的 CLI 框架，也不改动 SDK 公共 API。

## README 配套说明

在现有“运行示例”章节增加：

- 9 个新示例的可复制命令；
- 有领域参数的 4 个示例的参数说明；
- 无领域参数示例复用公共命令格式的说明；
- 下载中心 `--init-flag` 的 `true`/`false` 示例。

README 中的默认值必须与 Python 方法签名和 `argparse` 配置一致。

## 测试策略

遵循 RED-GREEN-REFACTOR：

1. 先扩展 `tests/test_examples_help.py`，对 9 个新示例运行真实的 `--help`；
2. 断言每个输出包含自动生成的 `usage:`、中文 description、公共认证参数；
3. 分别断言领域参数、允许值以及帮助文本中的默认值；
4. 在实现前运行这些测试，确认因帮助设施缺失而失败；
5. 最小修改示例使目标测试通过；
6. 运行全部非集成测试、完整 mock-server 集成测试、`compileall` 和
   `git diff --check`。

帮助测试通过子进程调用真实示例，不建立网络连接，不以源码文本匹配代替行为验证。

## 不在本次范围内

- 不统一重写全部历史示例；
- 不修改公共认证参数的默认策略；
- 不增加 JSON 输出、日志级别、超时、子命令或操作选择器；
- 不改变查询顺序、SDK endpoint 或响应结构。

## 验收标准

- 9 个新示例的 `--help` 均包含完整 usage、公共参数和准确的领域参数说明；
- README 中每个新示例都有可直接运行的命令；
- 新示例运行流程和错误处理与原有简单查询示例一致；
- 所有测试通过，且工作树差异无格式错误。
