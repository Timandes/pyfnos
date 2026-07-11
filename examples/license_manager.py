#!/usr/bin/env python3
"""LicenseManager 软件许可查询示例。"""

import argparse
import asyncio

from fnos import FnosClient, LicenseManager
from common import add_auth_arguments, connect_client, login_with_twofa


async def main():
    parser = argparse.ArgumentParser(description="fnOS 软件许可查询示例")
    add_auth_arguments(parser)
    parser.add_argument(
        "--page",
        type=int,
        default=1,
        help="软件许可页码（默认：1）",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=200,
        help="软件许可每页数量（默认：200）",
    )
    args = parser.parse_args()
    client = FnosClient()
    try:
        print("正在连接到服务器...")
        await connect_client(client, args)
        print("连接已建立")

        print("正在登录...")
        await login_with_twofa(client, args)
        print("登录成功")

        print(
            "软件许可:",
            await LicenseManager(client).list(args.page, args.page_size),
        )
    except Exception as exc:
        print(f"发生错误: {exc}")
    finally:
        await client.close()
        print("连接已关闭")


if __name__ == "__main__":
    asyncio.run(main())
