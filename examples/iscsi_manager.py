# Copyright 2025 Timandes White
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import argparse
from fnos import FnosClient, IscsiManager


def on_message_handler(message):
    """消息回调处理函数"""
    print(f"收到消息: {message}")


async def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Fnos iSCSI管理示例')
    parser.add_argument('--user', type=str, required=True, help='用户名')
    parser.add_argument('--password', type=str, required=True, help='密码')
    parser.add_argument('-e', '--endpoint', type=str, default='your-custom-endpoint.com:5666', help='服务器地址 (默认: your-custom-endpoint.com:5666)')

    args = parser.parse_args()

    client = FnosClient()

    # 设置消息回调
    client.on_message(on_message_handler)

    # 连接到服务器
    await client.connect(args.endpoint)

    if client.connected:
        print("连接成功，尝试登录...")
        try:
            result = await client.login(args.user, args.password)
            print("登录结果:", result)

            # 创建 IscsiManager 实例
            iscsi = IscsiManager(client)

            # 获取 iSCSI 配置
            try:
                config_result = await iscsi.get_config()
                print("iSCSI 配置信息:", config_result)
            except Exception as e:
                print(f"获取 iSCSI 配置失败: {e}")

            # 获取 Initiator 列表
            try:
                initiators_result = await iscsi.list_initiators()
                print("iSCSI Initiator 列表:", initiators_result)
            except Exception as e:
                print(f"获取 Initiator 列表失败: {e}")

            # 获取 LUN 列表
            try:
                luns_result = await iscsi.list_luns()
                print("iSCSI LUN 列表:", luns_result)
            except Exception as e:
                print(f"获取 LUN 列表失败: {e}")

            # 获取 LUN 用户组列表
            try:
                usergroups_result = await iscsi.list_lun_usergroups()
                print("iSCSI LUN 用户组列表:", usergroups_result)
            except Exception as e:
                print(f"获取 LUN 用户组列表失败: {e}")

            # 获取 Target 列表
            try:
                targets_result = await iscsi.list_targets()
                print("iSCSI Target 列表:", targets_result)
            except Exception as e:
                print(f"获取 Target 列表失败: {e}")
        except Exception as e:
            print(f"登录失败: {e}")
    else:
        print("连接失败")

    # 关闭连接
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
