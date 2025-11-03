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
from fnos import FnosClient, SAC

def on_message_handler(message):
    """消息回调处理函数"""
    print(f"收到消息: {message}")

async def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Fnos SAC UPS状态示例')
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
            
            # 创建SAC实例
            sac = SAC(client)
            
            # 调用ups_status方法
            try:
                ups_result = await sac.ups_status()
                print("UPS状态信息:", ups_result)
            except Exception as e:
                print(f"获取UPS状态信息失败: {e}")
        except Exception as e:
            print(f"登录失败: {e}")
    else:
        print("连接失败")
    
    # 关闭连接
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())