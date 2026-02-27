# Changelog

本文档记录 pyfnos 的所有重要更改。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Added
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
