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

    # 等待连接建立
    await asyncio.sleep(3)

    # 登录
    result = await client.login(args.user, args.password)
    print("登录结果:", result)

    # 发送请求
    await client.request_payload("user.info", {})
    print("已发送请求，等待响应...")
    # 等待一段时间以接收响应
    await asyncio.sleep(5)
    
    # 关闭连接
    await client.close()

# 运行异步主函数
if __name__ == "__main__":
    asyncio.run(main())
```

## 参考

| 类名 | 方法名 | 简介 |
| ---- | ---- | ---- |
| FnosClient | `__init__` | 初始化客户端 |
| FnosClient | `connect` | 连接到WebSocket服务器（必填参数：endpoint） |
| FnosClient | `login` | 用户登录方法 |
| FnosClient | `get_decrypted_secret` | 获取解密后的secret |
| FnosClient | `on_message` | 设置消息回调函数 |
| FnosClient | `request` | 发送请求 |
| FnosClient | `request_payload` | 以payload为主体发送请求 |
| FnosClient | `request_payload_with_response` | 以payload为主体发送请求并返回响应 |
| FnosClient | `close` | 关闭WebSocket连接 |
| Store | `__init__` | 初始化Store类 |
| Store | `general` | 请求存储通用信息 |
| ResourceMonitor | `__init__` | 初始化ResourceMonitor类 |
| ResourceMonitor | `cpu` | 请求CPU资源监控信息 |
| ResourceMonitor | `gpu` | 请求GPU资源监控信息 |
| ResourceMonitor | `memory` | 请求内存资源监控信息 |
| SAC | `__init__` | 初始化SAC类 |
| SAC | `ups_status` | 请求UPS状态信息 |
| SystemInfo | `__init__` | 初始化SystemInfo类 |
| SystemInfo | `get_host_name` | 请求主机名信息 |
| SystemInfo | `get_trim_version` | 请求Trim版本信息 |
| SystemInfo | `get_machine_id` | 请求机器ID信息 |
| SystemInfo | `get_hardware_info` | 请求硬件信息 |
| SystemInfo | `get_uptime` | 请求系统运行时间信息 |

## 命令行参数

示例程序支持以下命令行参数：

- `--user`: 用户名（必填）
- `--password`: 密码（必填）
- `-e, --endpoint`: 服务器地址（可选，默认为 your-custom-endpoint.com:5666）