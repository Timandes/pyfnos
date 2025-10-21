# pyfnos

飞牛fnOS的Python SDK。

*注意：这个SDK非官方提供。*

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