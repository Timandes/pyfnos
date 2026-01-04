#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FnosClient login_via_token 方法验证示例
演示如何使用用户名密码登录后，获取token再用token重新登录
"""

import asyncio
import argparse
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fnos.client import FnosClient

def on_message_handler(message):
    """消息回调处理函数"""
    print(f"收到消息: {message}")

async def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='FnosClient login_via_token 方法验证示例')
    parser.add_argument('--user', type=str, required=True, help='用户名')
    parser.add_argument('--password', type=str, required=True, help='密码')
    parser.add_argument('-e', '--endpoint', type=str, default='your-custom-endpoint.com:5666', help='服务器地址 (默认: your-custom-endpoint.com:5666)')
    
    args = parser.parse_args()
    
    # 创建客户端实例
    client = FnosClient()
    
    # 设置消息回调
    client.on_message(on_message_handler)
    
    try:
        # 第一步：连接到服务器
        print("第一步：连接到服务器...")
        await client.connect(args.endpoint)
        print("✓ 连接已建立")
            
        # 第二步：使用用户名密码登录
        print("\n第二步：使用用户名密码登录...")
        login_result = await client.login(args.user, args.password)
        
        if login_result.get("result") != "succ":
            print(f"✗ 登录失败: {login_result.get('msg', '未知错误')}")
            return
        
        print("✓ 用户名密码登录成功")
        
        # 获取登录后的token、long_token和secret
        token = login_result.get("token")
        long_token = login_result.get("longToken")
        secret = client.get_decrypted_secret()
        
        print(f"  - token: {token[:20]}..." if token else "  - token: None")
        print(f"  - long_token: {long_token[:20]}..." if long_token else "  - long_token: None")
        print(f"  - secret: {secret[:20]}..." if secret else "  - secret: None")
        
        if not token or not long_token or not secret:
            print("✗ 未能获取完整的登录信息，无法进行token登录验证")
            return
        
        # 第三步：关闭连接
        print("\n第三步：关闭连接...")
        await client.close()
        print("✓ 连接已关闭")
        
        # 第四步：重新连接
        print("\n第四步：重新连接...")
        client = FnosClient()  # 创建新的客户端实例
        client.on_message(on_message_handler)
        await client.connect(args.endpoint)
        print("✓ 连接已建立")
        
        # 第五步：使用token重新登录
        print("\n第五步：使用token重新登录...")
        token_login_result = await client.login_via_token(token, long_token, secret)
        
        if token_login_result.get("result") == "succ" or token_login_result.get("errno") == 0:
            print("✓ Token登录成功")
            print(f"  - 响应: {token_login_result}")
        else:
            print(f"✗ Token登录失败: {token_login_result.get('msg', token_login_result.get('errmsg', '未知错误'))}")
            print(f"  - 响应: {token_login_result}")
            
    except Exception as e:
        print(f"✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 关闭连接
        if client.connected:
            await client.close()
            print("\n✓ 连接已关闭")

if __name__ == "__main__":
    asyncio.run(main())