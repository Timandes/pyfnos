#!/usr/bin/env python3
"""
DockerManager 示例代码

演示如何使用 DockerManager 类来管理 Docker 容器和项目。
"""

import asyncio
from fnos import FnosClient, DockerManager


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

        # 创建 DockerManager 实例
        docker_mgr = DockerManager(client)

        # 1. 获取 Docker Compose 项目列表
        print("\n=== Docker Compose 项目列表 ===")
        compose_list = await docker_mgr.compose_list()
        if compose_list.get("result") == "succ":
            for project in compose_list["rsp"]:
                print(f"项目名称: {project['Name']}")
                print(f"  状态: {project['Status']}")
                print(f"  容器数: {project['Containers']['running']}/{project['Containers']['total']}")
                print(f"  配置文件: {project['ConfigFiles']}")
                print()

        # 2. 获取容器列表（包含所有容器）
        print("\n=== 容器列表 ===")
        container_list = await docker_mgr.container_list(all=True)
        if container_list.get("result") == "succ":
            for container in container_list["rsp"]:
                print(f"容器名称: {container['Names'][0]}")
                print(f"  状态: {container['State']}")
                print(f"  镜像: {container['Image']}")
                print(f"  项目: {container['Project']}")
                print()

        # 3. 获取容器统计信息
        print("\n=== 容器统计信息 ===")
        stats = await docker_mgr.stats()
        if stats.get("result") == "succ":
            for container_id, stat in stats["rsp"].items():
                print(f"容器 ID: {container_id[:12]}...")
                print(f"  CPU 使用率: {stat['cpuUsage']:.2%}")
                print(f"  内存使用: {stat['usedMem'] / 1024 / 1024:.2f} MB")
                print(f"  网络接收: {stat['networkRx']} bytes")
                print(f"  网络发送: {stat['networkTx']} bytes")
                print()

        # 4. 获取 Docker 系统设置
        print("\n=== Docker 系统设置 ===")
        system_setting = await docker_mgr.system_setting_get()
        if system_setting.get("result") == "succ":
            settings = system_setting["rsp"]
            print(f"数据根目录: {settings['dataRoot']}")
            print(f"当前镜像源: {settings['currentMirror']}")
            print(f"自动启动: {settings['autoBoot']}")
            print(f"Docker 状态: {'运行中' if settings['status'] else '已停止'}")
            print(f"可用镜像源:")
            for mirror in settings["mirrorsV2"]:
                status = "✓" if mirror["res"] else "✗"
                print(f"  {status} {mirror['name']}: {mirror['url']}")

    finally:
        # 清理连接
        await client.close()
        print("\n连接已关闭")


if __name__ == "__main__":
    asyncio.run(main())
