#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FnosClient重连功能示例
演示如何在断线后重新连接并重新登录
"""

import asyncio
import argparse
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fnos.client import FnosClient
from common import add_auth_arguments, connect_client, login_with_twofa

def on_message_handler(message):
    """消息回调处理函数"""
    print(f"收到消息: {message}")

async def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='FnosClient重连功能示例')
    add_auth_arguments(parser)
    
    args = parser.parse_args()
    
    # 创建客户端实例
    client = FnosClient()
    
    # 设置消息回调
    client.on_message(on_message_handler)
    
    try:
        # 连接到服务器
        print("正在连接到服务器...")
        await connect_client(client, args)
        
        if client.connected:
            # 登录
            print("正在登录...")
            login_result = await login_with_twofa(client, args)
            
            if login_result and login_result.get("result") == "succ":
                print("登录成功")
                
                # 模拟一些操作
                print("执行一些操作...")
                await asyncio.sleep(2)
                
                # 模拟连接断开
                print("模拟连接断开...")
                await client.close()
                
                # 尝试重连
                print("尝试重连...")
                client = FnosClient()
                client.on_message(on_message_handler)
                await connect_client(client, args)
                await login_with_twofa(client, args)
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
