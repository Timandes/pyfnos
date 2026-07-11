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
from common import add_auth_arguments, connect_client, login_with_twofa

def on_message_handler(message):
    """消息回调处理函数"""
    print(f"收到消息: {message}")

async def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Fnos用户模块示例')
    add_auth_arguments(parser)
    parser.add_argument("--uid", type=int, default=1000, help="查询两步验证配置的用户 ID")
    parser.add_argument("--group", default="users", help="查询详情的用户组名称")
    parser.add_argument("--preference", default="date-format", help="用户偏好名称")
    
    args = parser.parse_args()
    
    # 创建客户端实例
    client = FnosClient()
    
    # 设置消息回调
    client.on_message(on_message_handler)
    
    try:
        # 连接到服务器
        print("正在连接到服务器...")
        await connect_client(client, args)
        print("连接已建立")
            
        # 登录
        print("正在登录...")
        login_result = await login_with_twofa(client, args)
        
        if login_result.get("result") == "succ":
            print("登录成功")
        else:
            print(f"登录失败: {login_result.get('msg', '未知错误')}")
            return
            
        # 创建User实例
        user = User(client)

        print("登录令牌:", await user.list_tokens())
        print("我的两步验证配置:", await user.get_my_twofa_config())
        print("全局两步验证配置:", await user.get_global_twofa_config())
        print("指定用户两步验证配置:", await user.get_user_twofa_config(args.uid))
        print("用户活跃状态:", await user.get_active_state())
        print("用户组详情:", await user.get_group_info(args.group))
        print("用户组列表:", await user.list_groups())
        print("登录设备:", await user.list_login_devices())
        print("用户偏好:", await user.get_preference(args.preference))
        
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
