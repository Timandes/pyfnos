#!/usr/bin/env python3
import argparse
import asyncio

from fnos import DownloadCenter, FnosClient
from common import add_auth_arguments, connect_and_login


async def main():
    parser = argparse.ArgumentParser(description="fnOS 下载中心查询示例")
    add_auth_arguments(parser)
    parser.add_argument("--state-filter", type=int, default=65535)
    args = parser.parse_args()
    client = FnosClient()
    try:
        await connect_and_login(client, args)
        download = DownloadCenter(client)
        print("默认保存目录:", await download.get_default_save_directory())
        print("下载统计:", await download.get_statistics())
        print("下载任务:", await download.query_tasks(args.state_filter))
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
