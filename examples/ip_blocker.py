#!/usr/bin/env python3
"""IPBlocker IP 阻止规则查询示例。"""

import argparse
import asyncio

from fnos import FnosClient, IPBlocker
from common import add_auth_arguments, connect_client, login_with_twofa


async def main():
    parser = argparse.ArgumentParser(description="fnOS IP 阻止规则查询示例")
    add_auth_arguments(parser)
    args = parser.parse_args()
    client = FnosClient()
    try:
        print("正在连接到服务器...")
        await connect_client(client, args)
        print("连接已建立")

        print("正在登录...")
        await login_with_twofa(client, args)
        print("登录成功")

        blocker = IPBlocker(client)
        print("允许列表:", await blocker.list_allowed_addresses())
        print("自动阻止规则:", await blocker.get_auto_block_rule())
        print("拒绝列表:", await blocker.list_denied_addresses())
    except Exception as exc:
        print(f"发生错误: {exc}")
    finally:
        await client.close()
        print("连接已关闭")


if __name__ == "__main__":
    asyncio.run(main())
