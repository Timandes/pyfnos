#!/usr/bin/env python3
"""BackupManager 备份任务查询示例。"""

import argparse
import asyncio

from fnos import BackupManager, FnosClient
from common import add_auth_arguments, connect_client, login_with_twofa


async def main():
    parser = argparse.ArgumentParser(description="fnOS 备份任务查询示例")
    add_auth_arguments(parser)
    parser.add_argument(
        "--direction",
        type=int,
        choices=(0, 1),
        default=0,
        help="备份任务方向：0=上传，1=下载（默认：0）",
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

        print("备份任务:", await BackupManager(client).list_tasks(args.direction))
    except Exception as exc:
        print(f"发生错误: {exc}")
    finally:
        await client.close()
        print("连接已关闭")


if __name__ == "__main__":
    asyncio.run(main())
