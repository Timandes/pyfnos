#!/usr/bin/env python3
import argparse
import asyncio

from fnos import FnosClient, ResourceMonitor, Security
from common import add_auth_arguments, connect_and_login


async def main():
    parser = argparse.ArgumentParser(description="fnOS 安全状态查询示例")
    add_auth_arguments(parser)
    args = parser.parse_args()
    client = FnosClient()
    try:
        await connect_and_login(client, args)
        security = Security(client)
        print("防火墙:", await security.get_firewall())
        response = await ResourceMonitor(client).processes()
        items = response.get("data", {}).get("list", [])
        processes = [
            {"pid": item["pid"], "process": item["name"]}
            for item in items
            if "pid" in item and "name" in item
        ]
        print("进程流量:", await security.get_process_traffic(processes))
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
