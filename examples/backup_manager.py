#!/usr/bin/env python3
import argparse
import asyncio

from fnos import BackupManager, FnosClient
from common import add_auth_arguments, connect_and_login


async def main():
    parser = argparse.ArgumentParser(description="fnOS 备份任务查询示例")
    add_auth_arguments(parser)
    parser.add_argument("--direction", type=int, choices=(0, 1), default=0)
    args = parser.parse_args()
    client = FnosClient()
    try:
        await connect_and_login(client, args)
        print(await BackupManager(client).list_tasks(args.direction))
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
