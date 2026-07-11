#!/usr/bin/env python3
import argparse
import asyncio

from fnos import DownloadCenter, FnosClient
from common import add_auth_arguments, connect_and_login


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
        await connect_and_login(client, args)
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
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
