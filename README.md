# pyfnos

飞牛fnOS的Python SDK。

*注意：这个SDK非官方提供。*

## 上手

```python

def on_message_handler(message):
    """消息回调处理函数"""
    print(f"收到消息: {message}")


def main():
    client = FnosClient()
    
    # 设置消息回调
    client.on_message(on_message_handler)
    
    # 启动另一个线程保持连接
    connect_thread = threading.Thread(target=client.connect)
    connect_thread.daemon = True
    connect_thread.start()

    # 等待连接建立
    time.sleep(3)

    # 登录
    result = client.login("admin", "123")
    print("登录结果:", result)

    # 发送请求
    client.request_payload("user.info", {})
    print("已发送请求，等待响应...")
    # 等待一段时间以接收响应
    time.sleep(5)

```