#!/usr/bin/env python3
"""DownloadCenter 下载中心查询示例。"""

import argparse
import asyncio

from fnos import DownloadCenter, FnosClient
from common import add_auth_arguments, connect_client, login_with_twofa


def parse_bool(value: str) -> bool:
    normalized = value.lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise argparse.ArgumentTypeError("必须是 true 或 false")


async def main():
    parser = argparse.ArgumentParser(description="fnOS 下载中心查询示例")
    add_auth_arguments(parser)
    parser.add_argument(
        "--state-filter",
        type=int,
        default=65535,
        help="下载任务状态位掩码（默认：65535）",
    )
    parser.add_argument(
        "--init-flag",
        type=parse_bool,
        choices=(True, False),
        default=True,
        metavar="{true,false}",
        help="下载任务初始化标志（默认：true）",
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

        download = DownloadCenter(client)
        print("默认保存目录:", await download.get_default_save_directory())
        print("下载统计:", await download.get_statistics())
        print(
            "下载任务:",
            await download.query_tasks(
                state_filter=args.state_filter,
                init_flag=args.init_flag,
            ),
        )
    except Exception as exc:
        print(f"发生错误: {exc}")
    finally:
        await client.close()
        print("连接已关闭")


if __name__ == "__main__":
    asyncio.run(main())
