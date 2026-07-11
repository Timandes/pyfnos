#!/usr/bin/env python3
"""
Share 示例代码

演示如何使用 Share 类来获取共享配置信息。
"""

import asyncio
import argparse
from fnos import FnosClient, Share
from common import add_auth_arguments, connect_client, login_with_twofa


async def main():
    parser = argparse.ArgumentParser(description="Share 示例")
    add_auth_arguments(
        parser,
        default_user="admin",
        default_password="admin",
        default_endpoint="127.0.0.1:5666",
    )
    args = parser.parse_args()

    # 创建客户端
    client = FnosClient()

    try:
        # 连接到 fnOS 服务
        await connect_client(client, args)
        print("连接成功")

        # 登录
        login_result = await login_with_twofa(client, args)
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

        print("DLNA 配置:", await share.dlna_options())
        print("DLNA 共享配置:", await share.dlna_share_options())
        print("FTP 配置:", await share.ftp_options())
        print("FTP 共享配置:", await share.ftp_share_options())
        print("NFS 配置:", await share.nfs_options())
        print("NFS 共享配置:", await share.nfs_share_options())
        print("SMB 共享配置:", await share.smb_share_options())
        print("WebDAV 配置:", await share.webdav_options())
        print("WebDAV 共享配置:", await share.webdav_share_options())

        print("分享链接默认配置:", await share.get_link_defaults())
        print("默认分享链接:", await share.get_default_link())
        print("分享链接列表:", await share.list_links())
        print("分享链接权限:", await share.get_link_permission())

    finally:
        # 清理连接
        await client.close()
        print("\n连接已关闭")


if __name__ == "__main__":
    asyncio.run(main())
