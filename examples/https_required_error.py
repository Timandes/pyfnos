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

import argparse
import asyncio

from fnos import FnosClient, HTTPSRequiredError


async def run(endpoint: str) -> int:
    client = FnosClient()

    try:
        await client.connect(endpoint)
    except HTTPSRequiredError as error:
        suggested_wss_uri = error.redirect_uri.replace("https://", "wss://", 1)
        print("检测到 fnOS 服务端强制 HTTPS：")
        print(f"HTTP 重定向状态码: {error.status_code}")
        print(f"原始 WS 请求 URI: {error.requested_uri}")
        print(f"服务端 HTTPS 重定向 URI: {error.redirect_uri}")
        print(f"建议使用 WSS URI: {suggested_wss_uri}")
        print("SDK 未自动重试；请由调用方明确改用 WSS。")
        return 0
    except Exception as error:
        print(f"连接失败，但不是已识别的强制 HTTPS 重定向: {error}")
        return 1
    else:
        print("连接成功，未检测到强制 HTTPS 重定向。")
        return 0
    finally:
        await client.close()


def main():
    parser = argparse.ArgumentParser(description="fnOS 强制 HTTPS 连接诊断示例")
    parser.add_argument(
        "-e",
        "--endpoint",
        required=True,
        help="HTTP/WS 服务器地址，例如 nas.example.com:5666",
    )
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run(args.endpoint)))


if __name__ == "__main__":
    main()
