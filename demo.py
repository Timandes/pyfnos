import time
import threading
import argparse
from fnos import FnosClient

def on_message_handler(message):
    """消息回调处理函数"""
    print(f"收到消息: {message}")

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Fnos客户端')
    parser.add_argument('--user', type=str, required=True, help='用户名')
    parser.add_argument('--password', type=str, required=True, help='密码')
    
    args = parser.parse_args()
    
    client = FnosClient()
    
    # 设置消息回调
    client.on_message(on_message_handler)
    
    # 连接到服务器
    connect_thread = threading.Thread(target=client.connect)
    connect_thread.daemon = True
    connect_thread.start()
    
    # 等待连接建立
    time.sleep(3)
    
    if client.connected:
        print("连接成功，尝试登录...")
        try:
            # 使用命令行参数中的用户名和密码
            result = client.login(args.user, args.password)
            print("登录结果:", result)
            
            # 获取解密后的secret
            decrypted_secret = client.get_decrypted_secret()
            if decrypted_secret:
                print(f"保存的secret: {decrypted_secret}")
                
                # 测试request方法
                try:
                    client.request_payload("user.info", {})
                    print("已发送请求，等待响应...")
                    # 等待一段时间以接收响应
                    time.sleep(5)
                except Exception as e:
                    print(f"Request失败: {e}")
            else:
                print("未找到secret")
        except Exception as e:
            print(f"登录失败: {e}")
    else:
        print("连接失败")

if __name__ == "__main__":
    main()