#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FnosClient重连功能示例
演示如何使用FnosClient的自动重连功能
"""

import asyncio
import argparse
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fnos.client import FnosClient

def on_message_handler(message):
    """消息回调处理函数"""
    print(f"收到消息: {message}")

async def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='FnosClient重连功能示例')
    parser.add_argument('--user', type=str, required=True, help='用户名')
    parser.add_argument('--password', type=str, required=True, help='密码')
    parser.add_argument('-e', '--endpoint', type=str, default='your-custom-endpoint.com:5666', help='服务器地址 (默认: your-custom-endpoint.com:5666)')
    
    args = parser.parse_args()
    
    # 创建客户端实例
    client = FnosClient()
    
    # 设置消息回调
    client.on_message(on_message_handler)
    
    try:
        # 连接到服务器
        print("正在连接到服务器...")
        await client.connect(args.endpoint)
        
        # 等待连接建立
        await asyncio.sleep(3)
        
        if client.connected:
            # 登录
            print("正在登录...")
            login_result = await client.login(args.user, args.password)
            
            if login_result and login_result.get("result") == "succ":
                print("登录成功")
                
                # 模拟一些操作
                print("执行一些操作...")
                await asyncio.sleep(2)
                
                # 模拟连接断开
                print("模拟连接断开...")
                client.connected = False
                
                # 尝试重连
                print("尝试重连...")
                await client.reconnect()
                print("重连成功")
                
                # 继续执行操作
                print("继续执行操作...")
                await asyncio.sleep(2)
                
            else:
                print("登录失败:", login_result.get("msg", "未知错误"))
        else:
            print("连接失败")
            
    except Exception as e:
        print(f"发生错误: {e}")
        
    finally:
        # 关闭连接
        await client.close()
        print("连接已关闭")

if __name__ == "__main__":
    asyncio.run(main())