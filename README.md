# pyfnos

[![PyPI](https://img.shields.io/pypi/v/fnos)](https://pypi.org/project/fnos/)
[![GitHub](https://img.shields.io/github/license/Timandes/pyfnos)](https://github.com/Timandes/pyfnos)

飞牛fnOS的Python SDK。

*注意：这个SDK非官方提供。*

## 项目信息

- **源代码仓库**: [https://github.com/Timandes/pyfnos](https://github.com/Timandes/pyfnos)
- **问题追踪**: [GitHub Issues](https://github.com/Timandes/pyfnos/issues)

## 上手

```python
import asyncio
import argparse

def on_message_handler(message):
    """消息回调处理函数"""
    print(f"收到消息: {message}")


async def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Fnos客户端')
    parser.add_argument('--user', type=str, required=True, help='用户名')
    parser.add_argument('--password', type=str, required=True, help='密码')
    parser.add_argument('-e', '--endpoint', type=str, default='your-custom-endpoint.com:5666', help='服务器地址 (默认: your-custom-endpoint.com:5666)')

    args = parser.parse_args()

    client = FnosClient()

    # 设置消息回调
    client.on_message(on_message_handler)

    # 连接到服务器（必须指定endpoint）
    await client.connect(args.endpoint)

    # 登录
    result = await client.login(args.user, args.password)
    print("登录结果:", result)

    # 发送请求
    await client.request_payload("user.info", {})
    print("已发送请求，等待响应...")
    # 等待一段时间以接收响应
    await asyncio.sleep(5)

    # 演示重连功能（手动方式）
    await client.close()  # 先关闭连接
    print("连接已关闭，尝试重连...")
    await client.connect(args.endpoint)  # 重新连接（现在会等待连接完成）
    result = await client.login(args.user, args.password)  # 重新登录
    print("重连登录结果:", result)

    # 或者使用内置的重连方法（需要先确保连接已断开）
    # await client.reconnect()  # 使用内置重连方法

    # 关闭连接
    await client.close()

# 运行异步主函数
if __name__ == "__main__":
    asyncio.run(main())
```

## 参考

| 类名 | 方法名 | 简介 |
| ---- | ---- | ---- |
| FnosClient | `__init__` | 初始化客户端，支持type参数（"main"或"timer"，默认为"main"） |
| FnosClient | `connect` | 连接到WebSocket服务器（必填参数：endpoint） |
| FnosClient | `login` | 用户登录方法 |
| FnosClient | `get_decrypted_secret` | 获取解密后的secret |
| FnosClient | `on_message` | 设置消息回调函数 |
| FnosClient | `request` | 发送请求 |
| FnosClient | `request_payload` | 以payload为主体发送请求 |
| FnosClient | `request_payload_with_response` | 以payload为主体发送请求并返回响应 |
| FnosClient | `reconnect` | 重新连接到服务器 |
| FnosClient | `close` | 关闭WebSocket连接 |
| Store | `__init__` | 初始化Store类 |
| Store | `general` | 请求存储通用信息（需要管理员权限，非管理员访问会返回4352错误） |
| Store | `calculate_space` | 计算存储空间信息（需要管理员权限，非管理员访问会返回4352错误） |
| Store | `list_disks` | 列出磁盘信息（支持no_hot_spare参数，需要管理员权限，非管理员访问会返回4352错误） |
| Store | `get_disk_smart` | 获取磁盘SMART信息（支持disk参数，需要管理员权限，非管理员访问会返回4352错误） |
| Store | `get_state` | 获取存储状态信息（支持name和uuid参数，需要管理员权限，非管理员访问会返回4352错误） |
| ResourceMonitor | `__init__` | 初始化ResourceMonitor类 |
| ResourceMonitor | `cpu` | 请求CPU资源监控信息 |
| ResourceMonitor | `gpu` | 请求GPU资源监控信息 |
| ResourceMonitor | `memory` | 请求内存资源监控信息 |
| ResourceMonitor | `disk` | 请求磁盘资源监控信息 |
| ResourceMonitor | `net` | 请求网络资源监控信息 |
| ResourceMonitor | `general` | 请求通用资源监控信息（支持指定监控项列表，默认为["storeSpeed","netSpeed","cpuBusy","memPercent"]） |
| SAC | `__init__` | 初始化SAC类 |
| SAC | `ups_status` | 请求UPS状态信息 |
| SystemInfo | `__init__` | 初始化SystemInfo类 |
| SystemInfo | `get_host_name` | 请求主机名信息 |
| SystemInfo | `get_trim_version` | 请求Trim版本信息 |
| SystemInfo | `get_machine_id` | 请求机器ID信息 |
| SystemInfo | `get_hardware_info` | 请求硬件信息 |
| SystemInfo | `get_uptime` | 请求系统运行时间信息 |
| User | `__init__` | 初始化User类 |
| User | `getInfo` | 获取用户信息 |
| User | `listUserGroups` | 请求用户和组列表信息 |
| User | `groupUsers` | 请求用户分组信息 |
| User | `isAdmin` | 检查当前用户是否为管理员 |
| Network | `__init__` | 初始化Network类 |
| Network | `list` | 列出网络信息（支持type参数，可选值为0和1） |
| Network | `detect` | 检测网络接口（支持ifName参数） |
| File | `list` | 列出指定目录下的文件和文件夹 |
| File | `mkdir` | 创建文件夹 |
| File | `remove` | 删除文件或文件夹 |

## 命令行参数

示例程序支持以下命令行参数：

- `--user`: 用户名（必填）
- `--password`: 密码（必填）
- `-e, --endpoint`: 服务器地址（可选，默认为 your-custom-endpoint.com:5666）

## 运行示例

可以使用 `uv` 工具来运行 `examples` 目录下的示例程序：

```bash
# 基本语法
uv run examples/<示例文件名>.py --user <用户名> --password <密码> [-e <服务器地址>]

# 示例：运行user.py示例
uv run examples/user.py --user myuser --password mypassword -e my-server.com:5666
```

### 示例程序说明

下表列出了 `examples` 目录中各个示例程序的功能说明：

| 文件名 | 功能说明 |
| ------ | -------- |
| `not_connected.py` | 演示如何捕获和处理NotConnectedError异常来判断是否需要重连 |
| `reconnect.py` | 演示如何使用FnosClient的自动重连功能 |
| `resource_monitor.py` | 演示如何获取系统资源监控信息（CPU、GPU、内存、磁盘、网络） |
| `resource_monitor_general.py` | 演示如何获取通用资源监控信息（支持指定监控项列表） |
| `sac.py` | 演示如何获取UPS状态信息 |
| `store.py` | 演示如何获取存储相关信息 |
| `system_info.py` | 演示如何获取系统信息（主机名、版本、硬件等） |
| `user.py` | 演示User模块的各种功能（获取用户信息、用户组等） |
| `network.py` | 演示如何获取网络信息（支持type参数，可选值为0和1）和检测网络接口（支持ifName参数） |