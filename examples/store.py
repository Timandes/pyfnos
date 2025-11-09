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
from fnos import FnosClient, Store

def on_message_handler(message):
    """消息回调处理函数"""
    print(f"收到消息: {message}")

async def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Fnos存储示例')
    parser.add_argument('--user', type=str, required=True, help='用户名')
    parser.add_argument('--password', type=str, required=True, help='密码')
    parser.add_argument('-e', '--endpoint', type=str, default='your-custom-endpoint.com:5666', help='服务器地址 (默认: your-custom-endpoint.com:5666)')
    
    args = parser.parse_args()
    
    client = FnosClient()
    
    # 设置消息回调
    client.on_message(on_message_handler)
    
    # 连接到服务器（必须指定endpoint）
    await client.connect(args.endpoint)
    
    if client.connected:
        print("连接成功，尝试登录...")
        try:
            # 使用命令行参数中的用户名和密码
            result = await client.login(args.user, args.password)
            print("登录结果:", result)
            
            # 创建Store实例
            store = Store(client)
            
            # 调用general方法
            try:
                store_result = await store.general()
                print("存储通用信息:", store_result)
            except Exception as e:
                print(f"获取存储信息失败: {e}")
            
            # 调用calculate_space方法
            try:
                space_result = await store.calculate_space()
                print("存储空间计算结果:", space_result)
            except Exception as e:
                print(f"计算存储空间失败: {e}")
            
            # 调用list_disks方法（排除热备盘，使用默认值）
            try:
                disks_result = await store.list_disks()
                print("磁盘列表信息（排除热备盘）:", disks_result)
            except Exception as e:
                print(f"获取磁盘列表失败: {e}")
            
            # 调用list_disks方法（包含热备盘）
            try:
                disks_result_with_hot_spare = await store.list_disks(no_hot_spare=False)
                print("磁盘列表信息（包含热备盘）:", disks_result_with_hot_spare)
            except Exception as e:
                print(f"获取磁盘列表（包含热备盘）失败: {e}")
        except Exception as e:
            print(f"登录失败: {e}")
    else:
        print("连接失败")
    
    # 关闭连接
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())