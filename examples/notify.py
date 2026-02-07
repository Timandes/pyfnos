#!/usr/bin/env python3
"""
Notify 示例代码

演示如何使用 Notify 类来获取通知信息。
"""

import asyncio
from fnos import FnosClient, Notify


async def main():
    # 创建客户端
    client = FnosClient()

    try:
        # 连接到 fnOS 服务
        await client.connect("127.0.0.1:5666")
        print("连接成功")

        # 登录
        login_result = await client.login("admin", "admin")
        if login_result.get("result") == "succ":
            print("登录成功")
        else:
            print(f"登录失败: {login_result}")
            return

        # 创建 Notify 实例
        notify = Notify(client)

        # 获取未读通知总数
        print("\n=== 通知信息 ===")
        unread_total = await notify.unread_total()
        if unread_total.get("result") == "succ":
            print(f"未读通知数: {unread_total['unreadTotal']}")

    finally:
        # 清理连接
        await client.close()
        print("\n连接已关闭")


if __name__ == "__main__":
    asyncio.run(main())