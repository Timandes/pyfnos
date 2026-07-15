# fnOS 磁盘温度诊断工具设计

## 背景

fnOS 的磁盘温度可能来自资源监控接口，也可能只存在于磁盘 SMART 数据中。不同磁盘协议返回的 SMART 温度字段也不同：常规磁盘通常使用 `smart.temperature.current`，NVMe 磁盘可能只提供 `smart.nvme_smart_health_information_log.temperature`。资源监控接口还可能返回缺失或为 `0` 的温度，因此需要一个能展示取值来源和回退原因的独立诊断工具。

## 目标

新增 `tools/list_disk_temperatures.py`，实现以下流程：

1. 用 `Store.list_disks()` 枚举磁盘，并以其顺序和名称作为最终输出范围；
2. 用 `ResourceMonitor.disk()` 获取磁盘温度；
3. 监控温度缺失或为 `0` 时，调用 `Store.get_disk_smart(name)`；
4. SMART 温度先读取 `smart.temperature.current`，再回退到 `smart.nvme_smart_health_information_log.temperature`；
5. 输出每块磁盘的最终温度、采用的字段来源，以及所有实际检查但被跳过的候选值和原因。

## 非目标

- 不修改 `Store`、`ResourceMonitor` 或其他 SDK 公共接口；
- 不缓存或持续监控温度；
- 不输出 `ResourceMonitor.disk()` 中存在但 `Store.list_disks()` 未枚举的设备；
- 不并发调用多个 SMART 请求；
- 不把该工具安装为 Python 包的控制台入口；
- 不在本次工作中增加两步验证、SSL 或证书校验参数。

## 文件与命令行接口

新增目录和脚本：

```text
tools/
└── list_disk_temperatures.py
```

运行方式：

```bash
uv run python tools/list_disk_temperatures.py \
  --user admin \
  --password password \
  -e nas.example.com:5666
```

命令行参数参照现有示例的命名：

| 参数 | 行为 |
| --- | --- |
| `--user` | 必填，fnOS 用户名 |
| `--password` | 必填，fnOS 密码 |
| `-e`, `--endpoint` | 必填，fnOS WebSocket endpoint |

工具自行定义这些参数并直接使用 `FnosClient` 连接、登录。它不导入 `examples/common.py`，避免生产诊断工具依赖未打包的示例目录。

## 组件设计

所有实现保留在 `tools/list_disk_temperatures.py` 中，但按职责拆分为可独立测试的小单元：

### 温度结果

每块磁盘使用一个轻量结果对象保存：

- 磁盘名称；
- 最终温度，无法取得时为 `None`；
- 最终来源，无法取得时为 `None`；
- 按实际检查顺序记录的跳过原因列表。

跳过记录使用已经格式化的诊断文本，包含候选字段、原始值（若存在）和原因。这能保持实现简单，同时让测试直接验证最终用户可见信息。

### 温度有效性判断

候选温度必须是有限、非零的 `int` 或 `float`，且不能是 `bool`。下列情况会被跳过并记录原因：

- 字段不存在；
- 值为 `0`；
- 值是布尔值或其他非数字类型；
- 值是 `NaN`、正无穷或负无穷。

按需求不额外排除负数；有限且非零的负数仍被视为有效数值。

### 监控温度提取

从 `ResourceMonitor.disk()` 的 `data.disk` 列表建立磁盘名到 `temp` 候选值的映射。对 `Store.list_disks()` 枚举出的每块磁盘：

- 找到有效 `temp` 时直接采用，来源为 `ResourceMonitor.disk().data.disk[].temp`；
- 找不到对应磁盘、字段缺失或值无效时，记录原因并进入 SMART 回退。

### SMART 温度提取

仅对监控温度无效的磁盘调用 `Store.get_disk_smart(name)`，并按以下顺序求值：

1. `Store.get_disk_smart().smart.temperature.current`；
2. `Store.get_disk_smart().smart.nvme_smart_health_information_log.temperature`。

第一个字段有效时立即采用，不再检查 NVMe 字段。第一个字段无效时记录原因，再检查 NVMe 字段。两个字段都无效时，最终温度和来源均为 `None`。

### 编排与输出

异步编排函数接收 `Store` 和 `ResourceMonitor` 实例，返回与 `Store.list_disks()` 顺序一致的结果列表。通过传入依赖而不是在函数内创建客户端，测试可以使用假对象覆盖所有回退路径，无需真实 fnOS。

格式化函数负责生成稳定的人类可读输出。示例：

```text
sda => 38°C
  来源: ResourceMonitor.disk().data.disk[].temp

nvme0n1 => 42°C
  来源: Store.get_disk_smart().smart.nvme_smart_health_information_log.temperature
  跳过: ResourceMonitor.disk().data.disk[].temp = 0（值为 0）
  跳过: Store.get_disk_smart().smart.temperature.current（字段不存在）

sdb => 未知
  跳过: ResourceMonitor.disk()（未找到该磁盘）
  跳过: Store.get_disk_smart().smart.temperature.current = 0（值为 0）
  跳过: Store.get_disk_smart().smart.nvme_smart_health_information_log.temperature（字段不存在）
```

只列出实际检查过的候选项。若资源监控温度有效，则不调用 SMART，也不输出 SMART 字段的跳过记录；若 `smart.temperature.current` 有效，则不检查 NVMe 字段。

整数温度不显示无意义的小数位；浮点温度保留 API 返回的正常字符串形式。

## 数据流

```text
解析 --user / --password / -e
    -> FnosClient.connect(endpoint)
    -> FnosClient.login(user, password)
    -> Store.list_disks()
       -> 得到有序磁盘名称
    -> ResourceMonitor.disk()
       -> 为每块磁盘检查 temp
          -> 有效：记录温度和监控来源
          -> 缺失或为 0：记录原因
             -> Store.get_disk_smart(name)
                -> 检查 smart.temperature.current
                -> 无效时检查 NVMe temperature
                -> 记录采用来源或全部跳过原因
    -> 按磁盘顺序格式化输出
    -> finally 关闭客户端
```

## 异常处理

- 连接失败、登录失败、`Store.list_disks()` 调用失败，或磁盘列表响应结构无效时，工具无法完成核心任务：向标准错误输出简洁错误信息并返回非零退出码；
- `ResourceMonitor.disk()` 整体失败时不中止：每块磁盘记录该接口调用失败，然后全部进入 SMART 回退；
- 单块磁盘的 `Store.get_disk_smart(name)` 失败时不中止其他磁盘：该磁盘记录调用失败并输出“未知”，之后继续处理下一块磁盘；
- 只要成功枚举磁盘并输出结果，即使部分磁盘温度为“未知”，进程也返回 `0`；
- 客户端始终在 `finally` 中关闭；
- 错误和诊断信息不得输出用户名、密码、token 或 secret。

## 测试策略

新增 `tests/test_list_disk_temperatures_tool.py`，先写失败测试再实现。测试通过动态加载工具模块和假 `Store`、假 `ResourceMonitor`、假客户端执行真实编排与格式化逻辑，覆盖：

1. 直接采用有效的资源监控温度，且不调用 SMART；
2. 监控温度缺失时调用 SMART，并记录“未找到该磁盘”或“字段不存在”；
3. 监控温度为 `0` 时调用 SMART，并记录原值和原因；
4. `smart.temperature.current` 有效时优先采用，且不检查 NVMe 字段；
5. 常规 SMART 温度缺失或为 `0` 时采用 NVMe 温度，并保留先前跳过原因；
6. 两个 SMART 字段都无效时输出“未知”及全部跳过原因；
7. 布尔值、非数字、`NaN` 和无穷值被拒绝并说明原因；
8. 资源监控接口整体失败时，所有磁盘都执行 SMART 回退；
9. 单块磁盘 SMART 失败不影响后续磁盘；
10. 结果和输出顺序严格跟随 `Store.list_disks()`；
11. `--help` 包含 `--user`、`--password`、`-e/--endpoint`，且三个参数均为必填；
12. 成功、部分温度未知和致命失败路径都关闭客户端，并返回约定的退出码；
13. 输出包含最终来源和所有实际跳过候选项的原因。

完成定向测试后运行全量非集成测试，确认新增工具没有影响现有 SDK 和示例。

## 兼容性与风险

工具只调用现有公共 API，不改变 SDK 行为，因此兼容性风险较低。主要风险是服务端响应结构随 fnOS 版本变化；实现通过防御式字段读取、明确的跳过记录和逐盘回退，让结构差异直接体现在诊断输出中，而不是导致整个程序崩溃。

工具串行获取 SMART 数据，可能比并发方式稍慢，但能减少瞬时请求压力，并使输出顺序、调用顺序和故障诊断保持确定。
