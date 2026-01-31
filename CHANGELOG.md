# Changelog

本文档记录 pyfnos 的所有重要更改。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

## [0.10.1] - 2026-01-31

### Fixed
- 修复了消息处理逻辑中的问题，确保 getHostName 响应优先传递给 pending_requests 中对应的 future，避免响应被错误消费导致请求超时