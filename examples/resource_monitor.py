import asyncio
import argparse
from fnos import FnosClient, ResourceMonitor

def on_message_handler(message):
    """消息回调处理函数"""
    print(f"收到消息: {message}")

async def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Fnos资源监控示例')
    parser.add_argument('--user', type=str, required=True, help='用户名')
    parser.add_argument('--password', type=str, required=True, help='密码')
    
    args = parser.parse_args()
    
    client = FnosClient()
    
    # 设置消息回调
    client.on_message(on_message_handler)
    
    # 连接到服务器
    await client.connect()
    
    # 等待连接建立
    await asyncio.sleep(3)
    
    if client.connected:
        print("连接成功，尝试登录...")
        try:
            # 使用命令行参数中的用户名和密码
            result = await client.login(args.user, args.password)
            print("登录结果:", result)
            
            # 创建ResourceMonitor实例
            resource_monitor = ResourceMonitor(client)
            
            # 调用cpu方法
            try:
                cpu_result = await resource_monitor.cpu()
                print("CPU资源信息:", cpu_result)
            except Exception as e:
                print(f"获取CPU资源信息失败: {e}")
            
            # 调用gpu方法
            try:
                gpu_result = await resource_monitor.gpu()
                print("GPU资源信息:", gpu_result)
            except Exception as e:
                print(f"获取GPU资源信息失败: {e}")
            
            # 调用memory方法
            try:
                memory_result = await resource_monitor.memory()
                print("内存资源信息:", memory_result)
            except Exception as e:
                print(f"获取内存资源信息失败: {e}")
        except Exception as e:
            print(f"登录失败: {e}")
    else:
        print("连接失败")
    
    # 关闭连接
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())