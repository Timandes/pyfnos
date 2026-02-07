#!/usr/bin/env python3
"""
Share 示例代码

演示如何使用 Share 类来获取共享配置信息。
"""

import asyncio
from fnos import FnosClient, Share


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

        # 创建 Share 实例
        share = Share(client)

        # 获取 SMB 配置信息
        print("\n=== SMB 配置信息 ===")
        smb_config = await share.smb_opt()
        if smb_config.get("result") == "succ":
            config = smb_config["data"]
            print(f"SMB 服务: {'启用' if config['smbEnable'] else '禁用'}")
            print(f"WSDD 服务: {'启用' if config['wsddEnable'] else '禁用'}")
            print(f"IPv4 地址: {config['ipv4Addr']}")
            print(f"服务端口: {config['svcPort']}")
            print(f"挂载名称: {config['mount']}")
            print(f"工作模式: {config['mode']}")

            print("\nSMB 选项:")
            option = config["option"]
            print(f"  工作组: {option['workGroup'] or '默认'}")
            print(f"  机会锁: {'启用' if option['oplocks'] else '禁用'}")
            print(f"  NTLMv1: {'启用' if option['ntlmv1'] else '禁用'}")
            print(f"  服务器签名: {option['serverSigning']}")
            print(f"  传输加密: {option['transportEncryption']}")
            print(f"  支持 SMB1: {'启用' if option['supportSmb1'] else '禁用'}")
            print(f"  多通道: {'启用' if option['enableMultiChannel'] else '禁用'}")

            print("\nTime Machine:")
            time_machine = config["timeMachine"]
            print(f"  状态: {'启用' if time_machine['enable'] else '禁用'}")
            if time_machine['enable']:
                print(f"  存储空间: {time_machine['vol']}")
                print(f"  配额: {time_machine['quota'] / 1024 / 1024 / 1024:.2f} GB")
                print(f"  文件夹: {time_machine['folder']}")
                print(f"  当前状态: {time_machine['status']}")

    finally:
        # 清理连接
        await client.close()
        print("\n连接已关闭")


if __name__ == "__main__":
    asyncio.run(main())