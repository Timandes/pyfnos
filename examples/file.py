#!/usr/bin/env python3
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

"""
File Example
"""

import asyncio
import sys
import os
import argparse

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fnos.client import FnosClient
from fnos.file import File
from common import add_auth_arguments, connect_client, login_with_twofa

async def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='File Example')
    add_auth_arguments(parser, default_endpoint='localhost:8080')
    parser.add_argument('--dir', type=str, required=True, help='操作目录名称（如：test）')
    
    args = parser.parse_args()
    
    # 创建客户端实例
    client = FnosClient(type="file")
    
    try:
        # 连接到服务器
        print("正在连接到服务器...")
        await connect_client(client, args)
        
        # 登录
        print("正在登录...")
        login_result = await login_with_twofa(client, args)
        if login_result.get("result") != "succ":
            print(f"登录失败: {login_result}")
            return
        
        print("登录成功")
        
        # 创建File实例
        file = File(client)

        print("应用目录:", await file.list_app_directories())
        print("收藏文件:", await file.list_favorites())
        print("目录视图:", await file.list_directory_entries())
        print("最近文件:", await file.list_recent())
        print("我的共享:", await file.list_shared())
        print("他人共享:", await file.list_shared_by_others())
        print("团队回收站:", await file.list_team_trash_bins())
        print("个人回收站:", await file.list_trash())
        
        # 第一步：列出用户目录下的文件
        print("\n列出用户目录下的文件...")
        result = await file.list()
        print(f"文件列表: {result}")
        
        # 检查是否有文件
        files = result.get("files", [])
        if not files:
            print("用户目录下没有文件，程序退出")
            return
        
        # 查找指定的目录
        target_dir = None
        target_v = None
        target_uid = None
        for f in files:
            if f.get("name") == args.dir and f.get("dir") == 1:
                target_dir = f.get("name")
                target_v = f.get("v")
                target_uid = f.get("uid")
                break
        
        if not target_dir:
            print(f"未找到目录: {args.dir}")
            return
        
        # 拼出完整路径
        full_path = f"vol{target_v}/{target_uid}/{target_dir}"
        print(f"\n找到目标目录，完整路径: {full_path}")
        
        # 调用list方法，列出指定目录下的文件
        print(f"\n列出目录 {full_path} 下的文件...")
        result = await file.list(path=full_path)
        print(f"文件列表: {result}")
        
        # 获取目录下的文件列表
        existing_files = result.get("files", [])
        existing_names = {f.get("name") for f in existing_files}
        
        # 生成随机文件夹名称，直到找到不存在的名字
        import random
        import string
        
        print(f"\n在目录 {full_path} 下创建文件夹...")
        new_folder_name = None
        new_folder_path = None
        
        while True:
            # 生成随机文件夹名称（8位随机字符串）
            random_name = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            
            # 检查是否已存在同名文件
            if random_name not in existing_names:
                new_folder_name = random_name
                new_folder_path = f"{full_path}/{new_folder_name}"
                print(f"找到可用的文件夹名称: {new_folder_name}")
                break
            
            print(f"文件夹名称 {random_name} 已存在，重新生成...")
        
        # 创建文件夹
        result = await file.mkdir(path=new_folder_path)
        print(f"创建文件夹结果: {result}")
        
        # 调用remove方法，删除文件
        print(f"\n删除目录 {full_path} 下的文件...")
        test_file = f"{full_path}/test_file.txt"
        result = await file.remove(
            files=[test_file],
            move_to_trashbin=True
        )
        print(f"删除文件结果: {result}")
        
        # 调用remove方法，删除文件夹
        print(f"\n删除目录 {full_path} 下的文件夹...")
        result = await file.remove(
            files=[new_folder_path],
            move_to_trashbin=False
        )
        print(f"删除文件夹结果: {result}")
        
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        # 关闭连接
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
