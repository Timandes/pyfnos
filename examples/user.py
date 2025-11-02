#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fnos User模块使用示例
"""

import asyncio
import argparse
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fnos import FnosClient, User

def on_message_handler(message):
    """消息回调处理函数"""
    print(f"收到消息: {message}")

async def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Fnos用户模块示例')
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
        for i in range(20):  # 最多等待10秒
            if client.connected:
                print("连接已建立")
                break
            await asyncio.sleep(0.5)
        else:
            print("连接超时")
            return
            
        # 登录
        print("正在登录...")
        login_result = await client.login(args.user, args.password)
        
        if login_result.get("result") == "succ":
            print("登录成功")
        else:
            print(f"登录失败: {login_result.get('msg', '未知错误')}")
            return
            
        # 创建User实例
        user = User(client)
        
        # 调用getInfo方法
        print("\n正在调用getInfo方法...")
        try:
            result = await user.getInfo()
            print("getInfo响应:")
            print(result)
        except Exception as e:
            print(f"getInfo调用失败: {e}")
            
        # 调用listUserGroups方法
        print("\n正在调用listUserGroups方法...")
        try:
            result = await user.listUserGroups()
            print("listUserGroups响应:")
            print(result)
        except Exception as e:
            print(f"listUserGroups调用失败: {e}")
            
        # 调用groupUsers方法
        print("\n正在调用groupUsers方法...")
        try:
            result = await user.groupUsers()
            print("groupUsers响应:")
            print(result)
        except Exception as e:
            print(f"groupUsers调用失败: {e}")
            
        # 调用isAdmin方法
        print("\n正在调用isAdmin方法...")
        try:
            result = await user.isAdmin()
            print("isAdmin响应:")
            print(result)
        except Exception as e:
            print(f"isAdmin调用失败: {e}")
            
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        # 关闭连接
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())