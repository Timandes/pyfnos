#!/usr/bin/env python3
# Copyright 2025 Timandes White
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# you may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Network Example
"""

import asyncio
import sys
import os
import argparse

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fnos.client import FnosClient
from fnos.network import Network

async def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Network Example')
    parser.add_argument('--user', type=str, required=True, help='用户名')
    parser.add_argument('--password', type=str, required=True, help='密码')
    parser.add_argument('-e', '--endpoint', type=str, default='localhost:8080', help='服务器地址 (默认: localhost:8080)')
    
    args = parser.parse_args()
    
    # 创建客户端实例
    client = FnosClient()
    
    try:
        # 连接到服务器
        print("正在连接到服务器...")
        await client.connect(args.endpoint)
        
        # 登录
        print("正在登录...")
        login_result = await client.login(args.user, args.password)
        if login_result.get("result") != "succ":
            print(f"登录失败: {login_result}")
            return
        
        print("登录成功")
        
        # 创建Network实例
        network = Network(client)
        
        # 调用list方法，type为0
        print("\n获取网络信息 (type=0)...")
        result = await network.list(type=0)
        print(f"网络信息 (type=0): {result}")
        
        # 调用list方法，type为1
        print("\n获取网络信息 (type=1)...")
        result = await network.list(type=1)
        print(f"网络信息 (type=1): {result}")
        
        # 调用detect方法
        print("\n检测网络接口 (ifName=bond1)...")
        result = await network.detect(if_name="bond1")
        print(f"网络接口检测结果: {result}")
        
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        # 关闭连接
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())