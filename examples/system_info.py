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
from fnos import FnosClient, SystemInfo

def on_message_handler(message):
    """消息回调处理函数"""
    print(f"收到消息: {message}")

async def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Fnos系统信息示例')
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
            
            # 创建SystemInfo实例
            system_info = SystemInfo(client)
            
            # 调用get_host_name方法
            try:
                host_name_result = await system_info.get_host_name()
                print("主机名信息:", host_name_result)
            except Exception as e:
                print(f"获取主机名信息失败: {e}")
            
            # 调用get_trim_version方法
            try:
                trim_version_result = await system_info.get_trim_version()
                print("Trim版本信息:", trim_version_result)
            except Exception as e:
                print(f"获取Trim版本信息失败: {e}")
            
            # 调用get_machine_id方法
            try:
                machine_id_result = await system_info.get_machine_id()
                print("机器ID信息:", machine_id_result)
            except Exception as e:
                print(f"获取机器ID信息失败: {e}")
            
            # 调用get_hardware_info方法
            try:
                hardware_info_result = await system_info.get_hardware_info()
                print("硬件信息:", hardware_info_result)
            except Exception as e:
                print(f"获取硬件信息失败: {e}")
            
            # 调用get_uptime方法
            try:
                uptime_result = await system_info.get_uptime()
                print("系统运行时间信息:", uptime_result)
            except Exception as e:
                print(f"获取系统运行时间信息失败: {e}")
        except Exception as e:
            print(f"登录失败: {e}")
    else:
        print("连接失败")
    
    # 关闭连接
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())