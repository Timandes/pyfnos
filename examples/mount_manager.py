#!/usr/bin/env python3
"""MountManager 挂载管理查询示例。"""

import argparse
import asyncio

from fnos import FnosClient, MountManager
from common import add_auth_arguments, connect_client, login_with_twofa


async def main():
    parser = argparse.ArgumentParser(description="fnOS 挂载管理查询示例")
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

        mounts = MountManager(client)
        print("挂载列表:", await mounts.list_mounts())
        print("挂载设置:", await mounts.get_settings())
    except Exception as exc:
        print(f"发生错误: {exc}")
    finally:
        await client.close()
        print("连接已关闭")


if __name__ == "__main__":
    asyncio.run(main())
