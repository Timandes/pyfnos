# pyfnos

[![PyPI](https://img.shields.io/pypi/v/fnos)](https://pypi.org/project/fnos/)
[![GitHub](https://img.shields.io/github/license/Timandes/pyfnos)](https://github.com/Timandes/pyfnos)
[![DeepWiki](https://img.shields.io/badge/deepwiki-Timandes/pyfnos-blue)](https://deepwiki.com/Timandes/pyfnos)

飞牛fnOS的Python SDK。

*注意：这个SDK非官方提供。*

## 项目信息

- **源代码仓库**: [https://github.com/Timandes/pyfnos](https://github.com/Timandes/pyfnos)
- **问题追踪**: [GitHub Issues](https://github.com/Timandes/pyfnos/issues)

## 上手

```python
import asyncio
import argparse

def on_message_handler(message):
    """消息回调处理函数"""
    print(f"收到消息: {message}")


async def login_with_twofa(client, args):
    result = await client.login(args.user, args.password)
    if result.get("twofaRequired"):
        code = args.code or input("请输入 6 位两步验证码: ")
        result = await client.submit_twofa_code(code, trust_device=args.trust_device)
    elif result.get("twofaSetupRequired"):
        raise RuntimeError("该账号需要先绑定两步验证后才能继续登录")
    return result


async def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Fnos客户端')
    parser.add_argument('--user', type=str, required=True, help='用户名')
    parser.add_argument('--password', type=str, required=True, help='密码')
    parser.add_argument('-e', '--endpoint', type=str, default='your-custom-endpoint.com:5666', help='服务器地址 (默认: your-custom-endpoint.com:5666)')
    parser.add_argument('--code', type=str, help='6位两步验证码；不提供时从终端读取')
    parser.add_argument('--trust-device', action='store_true', help='请求服务器信任当前设备')
    parser.add_argument('--use-ssl', action='store_true', help='使用 SSL/WSS 连接')
    parser.add_argument('--skip-ssl-verify', type=lambda x: x.lower() == 'true', default=True, help='跳过 SSL 证书验证 (默认: True)')

    args = parser.parse_args()

    client = FnosClient()

    # 设置消息回调
    client.on_message(on_message_handler)

    # 连接到服务器（必须指定endpoint）
    # 可选参数：use_ssl=True 使用 WSS 连接，skip_ssl_verify=False 验证证书
    await client.connect(args.endpoint, use_ssl=args.use_ssl, skip_ssl_verify=args.skip_ssl_verify)

    # 登录
    result = await login_with_twofa(client, args)
    print("登录结果:", result)

    # 发送请求
    await client.request_payload("user.info", {})
    print("已发送请求，等待响应...")
    # 等待一段时间以接收响应
    await asyncio.sleep(5)

    # 演示重连功能（手动方式）
    await client.close()  # 先关闭连接
    print("连接已关闭，尝试重连...")
    await client.connect(args.endpoint, use_ssl=args.use_ssl, skip_ssl_verify=args.skip_ssl_verify)  # 重新连接（现在会等待连接完成）
    result = await login_with_twofa(client, args)  # 重新登录
    print("重连登录结果:", result)

    # 关闭连接
    await client.close()

# 运行异步主函数
if __name__ == "__main__":
    asyncio.run(main())
```

## 两步验证登录

如果账号已开启两步验证，`login()` 会先返回挑战信息，而不是完整登录凭据：

```python
result = await client.login(user, password)

if result.get("twofaRequired"):
    result = await client.submit_twofa_code("123456", trust_device=False)

if result.get("twofaSetupRequired"):
    raise RuntimeError("该账号需要先绑定两步验证后才能继续登录")
```

只有最终响应中包含 `token` 和 `secret` 后，SDK 才会保存登录态并允许后续 API 请求。`trust_device=True` 会请求服务器信任当前设备，后续是否免验证码由 fnOS 服务端决定。

也可以直接运行两步验证示例：

```bash
uv run examples/twofa_login.py --user myuser --password mypassword -e my-server.com:5666
```

## 参考

| 类名 | 方法名 | 简介 |
| ---- | ---- | ---- |
| FnosClient | `__init__` | 初始化客户端，支持type参数（"main"、"timer"或"file"，默认为"main"） |
| FnosClient | `connect` | 连接到WebSocket服务器（必填参数：endpoint；可选参数：use_ssl、skip_ssl_verify） |
| FnosClient | `login` | 用户登录方法 |
| FnosClient | `submit_twofa_code` | 提交两步验证码完成登录 |
| FnosClient | `get_decrypted_secret` | 获取解密后的secret |
| FnosClient | `on_message` | 设置消息回调函数 |
| FnosClient | `request` | 发送请求 |
| FnosClient | `request_payload` | 以payload为主体发送请求 |
| FnosClient | `request_payload_with_response` | 以payload为主体发送请求并返回响应 |
| FnosClient | `reconnect` | 重新连接到服务器 |
| FnosClient | `close` | 关闭WebSocket连接 |
| Store | `__init__` | 初始化Store类 |
| Store | `general` | 请求存储通用信息（需要管理员权限，非管理员访问会返回4352错误） |
| Store | `calculate_space` | 计算存储空间信息（需要管理员权限，非管理员访问会返回4352错误） |
| Store | `list_disks` | 列出磁盘信息（支持no_hot_spare参数，需要管理员权限，非管理员访问会返回4352错误） |
| Store | `get_disk_smart` | 获取磁盘SMART信息（支持disk参数，需要管理员权限，非管理员访问会返回4352错误） |
| Store | `get_state` | 获取存储状态信息（支持name和uuid参数，需要管理员权限，非管理员访问会返回4352错误） |
| ResourceMonitor | `__init__` | 初始化ResourceMonitor类 |
| ResourceMonitor | `cpu` | 请求CPU资源监控信息 |
| ResourceMonitor | `gpu` | 请求GPU资源监控信息 |
| ResourceMonitor | `memory` | 请求内存资源监控信息 |
| ResourceMonitor | `disk` | 请求磁盘资源监控信息 |
| ResourceMonitor | `net` | 请求网络资源监控信息 |
| ResourceMonitor | `general` | 请求通用资源监控信息（支持指定监控项列表，默认为["storeSpeed","netSpeed","cpuBusy","memPercent"]） |
| SAC | `__init__` | 初始化SAC类 |
| SAC | `ups_status` | 请求UPS状态信息 |
| SystemInfo | `__init__` | 初始化SystemInfo类 |
| SystemInfo | `get_host_name` | 请求主机名信息 |
| SystemInfo | `get_trim_version` | 请求Trim版本信息 |
| SystemInfo | `get_machine_id` | 请求机器ID信息 |
| SystemInfo | `get_hardware_info` | 请求硬件信息 |
| SystemInfo | `get_uptime` | 请求系统运行时间信息 |
| User | `__init__` | 初始化User类 |
| User | `getInfo` | 获取用户信息 |
| User | `listUserGroups` | 请求用户和组列表信息 |
| User | `groupUsers` | 请求用户分组信息 |
| User | `isAdmin` | 检查当前用户是否为管理员 |
| Network | `__init__` | 初始化Network类 |
| Network | `list` | 列出网络信息（支持type参数，可选值为0和1） |
| Network | `detect` | 检测网络接口（支持ifName参数） |
| File | `list` | 列出指定目录下的文件和文件夹 |
| File | `mkdir` | 创建文件夹 |
| File | `remove` | 删除文件或文件夹 |
| File | `get_acl` | 获取文件的ACL（访问控制列表）信息 |
| DockerManager | `__init__` | 初始化DockerManager类 |
| DockerManager | `list_composes` | 获取Docker Compose项目列表 |
| DockerManager | `list_containers` | 获取容器列表（支持all参数，默认为True） |
| DockerManager | `stats` | 获取容器统计信息 |
| DockerManager | `get_system_settings` | 获取Docker系统设置 |
| EventLogger | `__init__` | 初始化EventLogger类 |
| EventLogger | `common_list` | 获取事件日志列表 |
| Share | `__init__` | 初始化Share类 |
| Share | `smb_opt` | 获取SMB共享配置信息 |
| Notify | `__init__` | 初始化Notify类 |
| Notify | `unread_total` | 获取未读通知总数 |
| IscsiManager | `__init__` | 初始化IscsiManager类 |
| IscsiManager | `get_config` | 获取 iSCSI 配置信息 |
| IscsiManager | `list_initiators` | 获取 Initiator 列表 |
| IscsiManager | `list_luns` | 获取 LUN 列表 |
| IscsiManager | `list_lun_usergroups` | 获取 LUN 用户组列表（支持lunName和wwn参数） |
| IscsiManager | `list_targets` | 获取 Target 列表 |

### 扩展只读查询 API

| 模块 | 方法 | 功能说明 |
| --- | --- | --- |
| DockerManager | `list_image_downloads` | 获取 Docker 镜像下载任务 |
| DockerManager | `list_images` | 获取 Docker 镜像列表 |
| DockerManager | `list_networks` | 获取 Docker 网络列表 |
| DockerManager | `list_registry_repositories(keyword="", page=1, page_size=20)` | 分页查询镜像仓库 |
| Network | `get_gateway` | 获取默认网关信息 |
| Network | `get_multi_gateway_status` | 获取多网关状态 |
| Network | `get_nic_performance_mode` | 获取网卡性能模式 |
| Network | `get_info` | 获取指定网卡详情 |
| Network | `get_ssh_status` | 获取 SSH 服务状态 |
| ResourceMonitor | `npu` | 获取 NPU 资源监控信息 |
| ResourceMonitor | `processes` | 获取进程资源监控信息 |
| ResourceMonitor | `service_processes` | 获取服务进程资源监控信息 |
| ResourceMonitor | `system_fan` | 获取系统风扇信息 |
| File | `list_app_directories` | 获取应用目录列表 |
| File | `list_favorites` | 获取收藏文件列表 |
| File | `list_directory_entries` | 获取目录视图条目 |
| File | `list_recent` | 获取最近文件列表 |
| File | `list_shared` | 获取当前用户共享列表 |
| File | `list_shared_by_others` | 获取其他用户共享列表 |
| File | `list_team_trash_bins` | 获取团队回收站列表 |
| File | `list_trash` | 获取个人回收站内容 |
| Store | `get_cache_device_state` | 获取缓存设备状态 |
| Store | `get_disk_idle_time` | 获取磁盘空闲时间配置 |
| Store | `get_disk_wakeup` | 获取磁盘唤醒配置 |
| Store | `get_removable_config` | 获取可移动设备配置 |
| Store | `list_cache_devices` | 获取缓存设备列表 |
| Store | `list_removable_devices` | 获取可移动设备列表 |
| User | `list_tokens` | 获取当前账号登录令牌列表 |
| User | `get_my_twofa_config` | 获取当前用户两步验证配置 |
| User | `get_global_twofa_config` | 获取系统级两步验证配置 |
| User | `get_user_twofa_config` | 获取指定用户两步验证配置 |
| User | `get_active_state` | 获取当前用户活跃状态 |
| User | `get_group_info` | 获取指定用户组详情 |
| User | `list_groups` | 获取用户组列表 |
| User | `list_login_devices` | 获取登录设备列表 |
| User | `get_preference` | 获取指定用户偏好 |
| Share | `dlna_options` | 获取 DLNA 服务配置 |
| Share | `dlna_share_options` | 获取 DLNA 共享配置 |
| Share | `ftp_options` | 获取 FTP 服务配置 |
| Share | `ftp_share_options` | 获取 FTP 共享配置 |
| Share | `nfs_options` | 获取 NFS 服务配置 |
| Share | `nfs_share_options` | 获取 NFS 共享配置 |
| Share | `smb_share_options` | 获取 SMB 共享配置 |
| Share | `webdav_options` | 获取 WebDAV 服务配置 |
| Share | `webdav_share_options` | 获取 WebDAV 共享配置 |
| Share | `get_link_defaults` | 获取分享链接默认配置 |
| Share | `get_default_link` | 获取默认分享链接 |
| Share | `list_links(is_admin=False, keyword="", page=1, page_size=100, sort_column="createdTime", sort_type="DESC")` | 分页查询分享链接 |
| Share | `get_link_permission` | 获取分享链接权限配置 |
| SAC | `get_email_config` | 获取邮件通知配置 |
| SAC | `list_email_providers` | 获取邮件服务商列表 |
| SystemInfo | `get_reserved_partition` | 获取系统保留分区信息 |
| BackupManager | `list_tasks` | 按方向获取备份任务 |
| DownloadCenter | `get_default_save_directory` | 获取默认下载保存目录 |
| DownloadCenter | `get_statistics` | 获取下载中心统计信息 |
| DownloadCenter | `query_tasks(state_filter=65535, init_flag=True)` | 按状态位掩码查询下载任务 |
| IPBlocker | `list_allowed_addresses` | 获取 IP 允许列表 |
| IPBlocker | `get_auto_block_rule` | 获取自动阻止规则 |
| IPBlocker | `list_denied_addresses` | 获取 IP 拒绝列表 |
| Security | `get_firewall` | 获取防火墙配置 |
| Security | `get_process_traffic` | 获取指定进程流量信息 |
| LicenseManager | `list(page=1, page_size=200)` | 分页获取软件许可列表 |
| SystemRestore | `get_info` | 获取系统恢复信息 |
| LiveUpdate | `get_status` | 获取在线更新状态 |
| MountManager | `list_mounts` | 获取挂载列表 |
| MountManager | `get_settings` | 获取挂载设置 |
| NetworkServer | `list_certificates` | 获取证书列表 |
| NetworkServer | `get_connection_config` | 获取连接配置 |
| NetworkServer | `get_connection_status` | 获取连接状态 |
| NetworkServer | `list_ddns_providers` | 获取 DDNS 服务商列表 |
| NetworkServer | `list_ddns_records(page=1, page_size=200)` | 分页获取 DDNS 记录 |

### 尚未封装的抓包端点

以下响应 fixture 尚无配套的脱敏请求 fixture，因此本版本不猜测其请求参数：

- `appcgi.license.soft.get`
- `appcgi.license.soft.ipc.get`
- `appcgi.mountmgr.task.list`
- `appcgi.sac.entry.v1.getEntryList`
- `appcgi.sac.entry.v1.getUserDesktop`
- `taskState.list`
- `util.getSI`

## 命令行参数

示例程序支持以下命令行参数：

- `--user`: 用户名（必填）
- `--password`: 密码（必填）
- `-e, --endpoint`: 服务器地址（可选，默认为 your-custom-endpoint.com:5666）
  - 支持协议前缀：`wss://host:port` 或 `ws://host:port`
- `--use-ssl`: 使用 SSL/WSS 连接（可选，默认不使用）
- `--skip-ssl-verify`: 跳过 SSL 证书验证（可选，默认为 True）

## 运行示例

可以使用 `uv` 工具来运行 `examples` 目录下的示例程序：

```bash
# 基本语法
uv run examples/<示例文件名>.py --user <用户名> --password <密码> [-e <服务器地址>] [--code <验证码>] [--trust-device]

# 示例：运行user.py示例
uv run examples/user.py --user myuser --password mypassword -e my-server.com:5666
```

### 示例程序说明

下表列出了 `examples` 目录中各个示例程序的功能说明：

示例中的用户名密码登录已统一支持两步验证。账号需要验证码时，程序会提示输入；也可以通过 `--code 123456` 直接传入验证码。

| 文件名 | 功能说明 |
| ------ | -------- |
| `not_connected.py` | 演示如何捕获和处理NotConnectedError异常来判断是否需要重连 |
| `reconnect.py` | 演示如何使用FnosClient的自动重连功能 |
| `resource_monitor.py` | 演示 CPU、GPU、内存、磁盘、网络、NPU、进程、服务进程和风扇查询 |
| `resource_monitor_general.py` | 演示如何获取通用资源监控信息（支持指定监控项列表） |
| `sac.py` | 演示 UPS、邮件通知配置和邮件服务商查询 |
| `store.py` | 演示存储、缓存设备、可移动设备、休眠和唤醒配置查询 |
| `system_info.py` | 演示主机、版本、硬件、运行时间和保留分区查询 |
| `user.py` | 演示用户、用户组、令牌、登录设备、2FA 和用户偏好查询 |
| `twofa_login.py` | 演示如何处理两步验证登录流程 |
| `network.py` | 演示网卡、网关、多网关、性能模式和 SSH 状态查询 |
| `file.py` | 演示文件操作及应用目录、收藏、最近文件、共享和回收站查询 |
| `docker_manager.py` | 演示 Compose、容器、镜像、下载任务、网络和镜像仓库查询 |
| `event_logger.py` | 演示EventLogger模块的功能（获取事件日志） |
| `share.py` | 演示 SMB/NFS/FTP/WebDAV/DLNA 配置及分享链接查询 |
| `notify.py` | 演示Notify模块的功能（获取未读通知数） |
| `iscsi_manager.py` | 演示IscsiManager模块的功能（获取iSCSI配置、Initiator、LUN、用户组、Target） |
| `backup_manager.py` | 演示备份任务查询 |
| `download_center.py` | 演示下载目录、统计和任务查询 |
| `ip_blocker.py` | 演示 IP 允许列表、拒绝列表和自动阻止规则查询 |
| `license_manager.py` | 演示软件许可列表查询 |
| `mount_manager.py` | 演示挂载列表和挂载设置查询 |
| `network_server.py` | 演示证书、连接状态和 DDNS 查询 |
| `security.py` | 演示防火墙和进程流量查询 |
| `system_restore.py` | 演示系统恢复信息查询 |
| `live_update.py` | 演示在线更新状态查询 |

### SSL/WSS 连接示例

如果服务器使用 HTTPS/WSS 协议，可以通过以下方式连接：

```bash
# 方式1：使用 wss:// 前缀
uv run examples/user.py --user myuser --password mypassword -e wss://my-server.com:5667

# 方式2：使用 --use-ssl 参数
uv run examples/user.py --user myuser --password mypassword -e my-server.com:5667 --use-ssl

# 禁用证书验证跳过（验证服务器证书）
uv run examples/user.py --user myuser --password mypassword -e wss://my-server.com:5667 --skip-ssl-verify false
```
