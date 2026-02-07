#!/usr/bin/env python3
"""
EventLogger 示例代码

演示如何使用 EventLogger 类来获取事件日志。
"""

import asyncio
from fnos import FnosClient, EventLogger


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

        # 创建 EventLogger 实例
        event_logger = EventLogger(client)

        # 获取事件日志列表
        print("\n=== 事件日志 ===")
        event_list = await event_logger.common_list()
        if event_list.get("result") == "succ":
            data = event_list["data"]
            print(f"总事件数: {data['total']}")
            print(f"\n最近 {len(data['rows'])} 条事件:")

            for event in data["rows"]:
                print(f"ID: {event['id']}")
                print(f"  用户: {event['username']}")
                print(f"  时间: {event['eventtm']}")
                print(f"  内容: {event['content']}")
                print()

    finally:
        # 清理连接
        await client.close()
        print("\n连接已关闭")


if __name__ == "__main__":
    asyncio.run(main())