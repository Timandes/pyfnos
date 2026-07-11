#!/usr/bin/env python3
import argparse
import asyncio

from fnos import FnosClient, SystemRestore
from common import add_auth_arguments, connect_and_login


async def main():
    parser = argparse.ArgumentParser(description="fnOS 系统恢复信息查询示例")
    add_auth_arguments(parser)
    args = parser.parse_args()
    client = FnosClient()
    try:
        await connect_and_login(client, args)
        print(await SystemRestore(client).get_info())
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
