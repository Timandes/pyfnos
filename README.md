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

def on_message_handler(message):
    """消息回调处理函数"""
    print(f"收到消息: {message}")


async def main():
    client = FnosClient()
    
    # 设置消息回调
    client.on_message(on_message_handler)
    
    # 连接到服务器
    await client.connect()

    # 等待连接建立
    await asyncio.sleep(3)

    # 登录
    result = await client.login("admin", "123")
    print("登录结果:", result)

    # 发送请求
    await client.request_payload("user.info", {})
    print("已发送请求，等待响应...")
    # 等待一段时间以接收响应
    await asyncio.sleep(5)
    
    # 关闭连接
    await client.close()

# 运行异步主函数
asyncio.run(main())
```

## 参考

| 类名 | 方法名 | 简介 |
| ---- | ---- | ---- |
| FnosClient | `__init__` | 初始化客户端 |
| FnosClient | `connect` | 连接到WebSocket服务器 |
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