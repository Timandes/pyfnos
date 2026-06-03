"""Shared helpers for pyfnos examples."""

import getpass


def add_auth_arguments(
    parser,
    *,
    default_user=None,
    default_password=None,
    default_endpoint="your-custom-endpoint.com:5666",
):
    """Add common connection, login, and two-factor arguments."""
    parser.add_argument("--user", type=str, default=default_user, required=default_user is None, help="用户名")
    parser.add_argument("--password", type=str, default=default_password, required=default_password is None, help="密码")
    parser.add_argument(
        "-e",
        "--endpoint",
        type=str,
        default=default_endpoint,
        help=f"服务器地址 (默认: {default_endpoint})",
    )
    parser.add_argument("--code", type=str, help="6位两步验证码；不提供时从终端读取")
    parser.add_argument("--trust-device", action="store_true", help="请求服务器信任当前设备")
    parser.add_argument("--use-ssl", action="store_true", help="使用 SSL/WSS 连接")
    parser.add_argument(
        "--skip-ssl-verify",
        type=lambda x: x.lower() == "true",
        default=True,
        help="跳过 SSL 证书验证 (默认: True)",
    )


async def connect_client(client, args):
    """Connect a client using common example arguments."""
    await client.connect(
        args.endpoint,
        use_ssl=args.use_ssl,
        skip_ssl_verify=args.skip_ssl_verify,
    )


async def login_with_twofa(client, args_or_user, password=None, *, code=None, trust_device=False):
    """Login and complete optional two-factor verification."""
    if hasattr(args_or_user, "user") and hasattr(args_or_user, "password"):
        username = args_or_user.user
        password = args_or_user.password
        code = getattr(args_or_user, "code", code)
        trust_device = getattr(args_or_user, "trust_device", trust_device)
    else:
        username = args_or_user

    result = await client.login(username, password)

    if result.get("twofaRequired"):
        print(f"账号需要两步验证，安全邮箱: {result.get('secureEmail', '未知')}")
        code = args.code or getpass.getpass("请输入 6 位两步验证码: ")
        result = await client.submit_twofa_code(code, trust_device=args.trust_device)
    elif result.get("twofaSetupRequired"):
        raise RuntimeError("该账号需要先绑定两步验证后才能继续登录")

    if result.get("result") != "succ":
        raise RuntimeError(result.get("msg", result.get("errmsg", f"登录失败: {result}")))

    return result


async def connect_and_login(client, args):
    """Connect and login, including optional two-factor verification."""
    await connect_client(client, args)
    return await login_with_twofa(client, args)
