# Changelog

本文档记录 pyfnos 的所有重要更改。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.13.0] - 2026-06-20

### Added
- `FnosClient.login()` 支持识别登录阶段的两步验证挑战
  - 已绑定两步验证时返回 `twofaRequired=True`
  - 强制启用但尚未绑定时返回 `twofaSetupRequired=True`
- 新增 `FnosClient.submit_twofa_code(code, trust_device=False, timeout=10.0)`，用于提交6位验证码完成登录
- 新增 `examples/twofa_login.py`，演示两步验证登录流程
- `examples` 目录下的用户名密码登录示例统一支持两步验证验证码提交
- 新增基于 `fnos-mock-server` 的两步验证登录集成测试

### Changed
- 最终登录成功判断不再依赖 `longToken` 字段，兼容只返回 `token` 和 `secret` 的响应
- README 增加两步验证登录说明和示例入口

## [0.12.0] - 2026-04-04

### Added
- 新增 `IscsiManager` 类，支持管理 iSCSI 配置和资源
  - `get_config()`: 获取 iSCSI 配置信息
  - `list_initiators()`: 获取 Initiator 列表
  - `list_luns()`: 获取 LUN 列表
  - `list_lun_usergroups(lun_name, wwn)`: 获取 LUN 用户组列表
  - `list_targets()`: 获取 Target 列表
- `FnosClient.connect()` 新增 SSL/WSS 连接支持
  - `use_ssl` 参数：是否使用 WSS 协议连接（默认 False）
  - `skip_ssl_verify` 参数：是否跳过 SSL 证书验证（默认 True，便于自签名证书场景）
  - 支持 endpoint 带协议前缀（`wss://` 或 `ws://`），前缀优先于 `use_ssl` 参数

## [0.11.0] - 2026-02-15

### Added
- 新增 `DockerManager` 类，支持管理 Docker 容器和项目
  - `list_composes()`: 获取 Docker Compose 项目列表
  - `list_containers(all=True)`: 获取容器列表
  - `stats()`: 获取容器统计信息
  - `get_system_settings()`: 获取 Docker 系统设置
- 新增 `EventLogger` 类，支持获取事件日志
  - `common_list()`: 获取事件日志列表
- 新增 `Share` 类，支持获取共享配置信息
  - `smb_opt()`: 获取 SMB 共享配置信息
- 新增 `Notify` 类，支持获取通知信息
  - `unread_total()`: 获取未读通知总数
- 扩展 `File` 类，新增方法
  - `get_acl(files)`: 获取文件的 ACL（访问控制列表）信息
- 扩展 `Store` 类，新增方法
  - `get_user_storage(space_info, stor_info, quota_info)`: 获取用户存储信息

## [0.10.1] - 2026-01-31

### Fixed
- 修复了消息处理逻辑中的问题，确保 getHostName 响应优先传递给 pending_requests 中对应的 future，避免响应被错误消费导致请求超时
