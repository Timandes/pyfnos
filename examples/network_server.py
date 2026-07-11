#!/usr/bin/env python3
import argparse
import asyncio

from fnos import FnosClient, NetworkServer
from common import add_auth_arguments, connect_and_login


async def main():
    parser = argparse.ArgumentParser(description="fnOS 网络服务查询示例")
    add_auth_arguments(parser)
    parser.add_argument(
        "--page",
        type=int,
        default=1,
        help="DDNS 记录页码（默认：1）",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=200,
        help="DDNS 记录每页数量（默认：200）",
    )
    args = parser.parse_args()
    client = FnosClient()
    try:
        await connect_and_login(client, args)
        server = NetworkServer(client)
        print("证书:", await server.list_certificates())
        print("连接配置:", await server.get_connection_config())
        print("连接状态:", await server.get_connection_status())
        print("DDNS 服务商:", await server.list_ddns_providers())
        print("DDNS 记录:", await server.list_ddns_records(args.page, args.page_size))
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
