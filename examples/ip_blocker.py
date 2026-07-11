#!/usr/bin/env python3
import argparse
import asyncio

from fnos import FnosClient, IPBlocker
from common import add_auth_arguments, connect_and_login


async def main():
    parser = argparse.ArgumentParser(description="fnOS IP 阻止规则查询示例")
    add_auth_arguments(parser)
    args = parser.parse_args()
    client = FnosClient()
    try:
        await connect_and_login(client, args)
        blocker = IPBlocker(client)
        print("允许列表:", await blocker.list_allowed_addresses())
        print("自动阻止规则:", await blocker.get_auto_block_rule())
        print("拒绝列表:", await blocker.list_denied_addresses())
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
