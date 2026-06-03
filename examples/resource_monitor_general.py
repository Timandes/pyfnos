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
from fnos import FnosClient, ResourceMonitor
from common import add_auth_arguments, connect_client, login_with_twofa

def on_message_handler(message):
    """消息回调处理函数"""
    print(f"收到消息: {message}")

async def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Fnos资源监控通用信息示例')
    add_auth_arguments(parser)
    
    args = parser.parse_args()
    
    client = FnosClient()
    
    # 设置消息回调
    client.on_message(on_message_handler)
    
    # 连接到服务器（必须指定endpoint）
    await connect_client(client, args)
    
    if client.connected:
        print("连接成功，尝试登录...")
        try:
            # 使用命令行参数中的用户名和密码
            result = await login_with_twofa(client, args)
            print("登录结果:", result)
            
            # 创建ResourceMonitor实例
            resource_monitor = ResourceMonitor(client)
            
            # 调用general方法（使用默认items参数）
            try:
                general_result = await resource_monitor.general()
                print("通用资源信息（默认items）:", general_result)
            except Exception as e:
                print(f"获取通用资源信息失败: {e}")
            
            # 调用general方法（使用自定义items参数）
            try:
                custom_items = ["cpuBusy", "memPercent"]
                general_result = await resource_monitor.general(items=custom_items)
                print("通用资源信息（自定义items）:", general_result)
            except Exception as e:
                print(f"获取通用资源信息失败: {e}")
                
        except Exception as e:
            print(f"登录失败: {e}")
    else:
        print("连接失败")
    
    # 关闭连接
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
