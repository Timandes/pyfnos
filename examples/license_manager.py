#!/usr/bin/env python3
import argparse
import asyncio

from fnos import FnosClient, LicenseManager
from common import add_auth_arguments, connect_and_login


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
        await connect_and_login(client, args)
        print(await LicenseManager(client).list(args.page, args.page_size))
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
