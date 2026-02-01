#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FnosClient 端点自动识别与 SSL 配置示例
演示如何使用 _detect_endpoint() 自动探测服务器地址，以及如何处理 SSL 验证
"""

import asyncio
import argparse
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fnos.client import FnosClient


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="FnosClient 端点探测示例")
    parser.add_argument("--user", type=str, required=True, help="用户名")
    parser.add_argument("--password", type=str, required=True, help="密码")

    # 示例 1: 原始 IP:PORT 写法，将自动探测是否需要 HTTPS/WSS
    parser.add_argument(
        "-e",
        "--endpoint",
        type=str,
        default="192.168.1.100:5666",
        help="服务器地址，支持 IP:PORT, ws://IP:PORT 或 wss://IP:PORT",
    )

    # 是否跳过 SSL 验证 (如果是自签证书)
    parser.add_argument(
        "--no-verify", action="store_true", help="禁用 SSL 证书验证 (适用于自签证书)"
    )

    args = parser.parse_args()

    client = FnosClient()

    try:
        # 连接到服务器
        # 1. 如果 endpoint 是 "192.168.1.100:5666"，会自动探测并转为 ws:// 或 wss://
        # 2. 如果 endpoint 是 "ws://..." 或 "wss://..."，将直接使用指定的协议
        # 3. 如果是自签证书 wss 连接，设置 ssl_verify=False

        print(f"正在尝试连接到: {args.endpoint}")
        ssl_verify = not args.no_verify

        await client.connect(args.endpoint, ssl_verify=ssl_verify)

        if client.connected:
            print(f"连接成功! 实际使用的端点为: {client.endpoint}")

            # 登录
            print("正在登录...")
            login_result = await client.login(args.user, args.password)

            if login_result and login_result.get("result") == "succ":
                print("登录成功")
                # 获取系统信息作为演示
                print("获取主机名...")
                from fnos.system_info import SystemInfo

                sys_info = SystemInfo(client)
                host_name = await sys_info.get_host_name()
                print(f"主机名: {host_name}")
            else:
                print(f"登录失败: {login_result.get('msg', '未知错误')}")
        else:
            print("连接失败")

    except Exception as e:
        print(f"发生错误: {e}")

    finally:
        await client.close()
        print("连接已关闭")


if __name__ == "__main__":
    asyncio.run(main())
