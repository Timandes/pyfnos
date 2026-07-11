#!/usr/bin/env python3
import argparse
import asyncio

from fnos import FnosClient, MountManager
from common import add_auth_arguments, connect_and_login


async def main():
    parser = argparse.ArgumentParser(description="fnOS 挂载管理查询示例")
    add_auth_arguments(parser)
    args = parser.parse_args()
    client = FnosClient()
    try:
        await connect_and_login(client, args)
        mounts = MountManager(client)
        print("挂载列表:", await mounts.list_mounts())
        print("挂载设置:", await mounts.get_settings())
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
