#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FnosClient 两步验证登录示例
"""

import argparse
import asyncio
import getpass
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fnos import FnosClient, User


def on_message_handler(message):
    """消息回调处理函数"""
    print(f"收到消息: {message}")


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="FnosClient 两步验证登录示例")
    parser.add_argument("--user", type=str, required=True, help="用户名")
    parser.add_argument("--password", type=str, required=True, help="密码")
    parser.add_argument(
        "-e",
        "--endpoint",
        type=str,
        default="your-custom-endpoint.com:5666",
        help="服务器地址 (默认: your-custom-endpoint.com:5666)",
    )
    parser.add_argument("--code", type=str, help="6位两步验证码；不提供时从终端读取")
    parser.add_argument("--trust-device", action="store_true", help="请求服务器信任当前设备")
    parser.add_argument("--use-ssl", action="store_true", help="使用 SSL/WSS 连接")
    parser.add_argument(
        "--skip-ssl-verify",
        type=lambda x: x.lower() == "true",
        default=True,
        help="跳过 SSL 证书验证 (默认: True)",
    )

    args = parser.parse_args()

    client = FnosClient()
    client.on_message(on_message_handler)

    try:
        print("正在连接到服务器...")
        await client.connect(
            args.endpoint,
            use_ssl=args.use_ssl,
            skip_ssl_verify=args.skip_ssl_verify,
        )
        print("连接已建立")

        print("正在登录...")
        result = await client.login(args.user, args.password)

        if result.get("twofaRequired"):
            print(f"账号需要两步验证，安全邮箱: {result.get('secureEmail', '未知')}")
            code = args.code or getpass.getpass("请输入 6 位两步验证码: ")
            result = await client.submit_twofa_code(
                code,
                trust_device=args.trust_device,
            )
        elif result.get("twofaSetupRequired"):
            raise RuntimeError("该账号需要先绑定两步验证后才能继续登录")

        if result.get("result") != "succ":
            print(f"登录失败: {result.get('msg', result.get('errmsg', '未知错误'))}")
            return

        print("登录成功")
        print(f"token: {result.get('token', '')[:20]}...")

        user = User(client)
        user_info = await user.getInfo()
        print("user.info响应:")
        print(user_info)

    except Exception as e:
        print(f"发生错误: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
