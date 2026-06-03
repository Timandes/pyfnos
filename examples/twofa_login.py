#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FnosClient 两步验证登录示例
"""

import argparse
import asyncio
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fnos import FnosClient, User
from common import add_auth_arguments, connect_client, login_with_twofa


def on_message_handler(message):
    """消息回调处理函数"""
    print(f"收到消息: {message}")


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="FnosClient 两步验证登录示例")
    add_auth_arguments(parser)

    args = parser.parse_args()

    client = FnosClient()
    client.on_message(on_message_handler)

    try:
        print("正在连接到服务器...")
        await connect_client(client, args)
        print("连接已建立")

        print("正在登录...")
        result = await login_with_twofa(client, args)

        if result.get("result") != "succ":
            print(f"登录失败: {result.get('msg', result.get('errmsg', '未知错误'))}")
            return

        print("登录成功")
        print(f"token: {result.get('token', '')[:20]}...")

        user = User(client)
        user_info = await user.getInfo()
        print("user.info响应:")
        print(user_info)

    except Exception as e:
        print(f"发生错误: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
