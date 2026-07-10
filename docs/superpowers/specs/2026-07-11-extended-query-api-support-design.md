# Extended Query API Support Design

## Summary

Extend pyfnos with explicit, domain-oriented wrappers for the read-only fnOS
requests captured by `fnos-mock-server`. The source corpus is mock-server commit
`d9592a05a8e07082b954921acfae3a9a915f3c01`, which contains 78 new response
fixtures and 82 request cases covering 71 of those response endpoints.

This change will expose the 71 endpoints for which both a sanitized request and
response fixture exist. Seven response-only endpoints remain out of the public
SDK until matching request fixtures are captured.

## Goals

- Add discoverable async Python methods for all 71 paired query endpoints.
- Preserve the exact request field names and nesting captured from fnOS.
- Follow the existing SDK convention of returning the raw response `dict`.
- Keep all existing classes, methods, imports, and response behavior compatible.
- Verify every wrapper independently and against the mock server.
- Provide runnable example programs for every new domain class and every
  extended existing class.
- Document the new modules, methods, examples, and deferred endpoints.

## Non-goals

- Do not add write, delete, start, stop, or configuration mutation operations.
- Do not infer request signatures for response-only fixtures.
- Do not add response models, schema conversion, caching, transparent retries,
  or runtime code generation.
- Do not make pyfnos depend on the sibling `fnos-mock-server` project at runtime.
- Do not rename existing camelCase methods as part of this feature.

## Source Corpus and Scope

The mock-server corpus contains:

- 78 newly captured response endpoints;
- 71 request endpoint directories;
- 82 request cases, including alternate backup directions, download task state
  filters, DDNS page sizes, share-link administrative modes, and user-data names.

The following seven response fixtures have no matching request case and are
therefore deferred:

- `appcgi.license.soft.get`
- `appcgi.license.soft.ipc.get`
- `appcgi.mountmgr.task.list`
- `appcgi.sac.entry.v1.getEntryList`
- `appcgi.sac.entry.v1.getUserDesktop`
- `taskState.list`
- `util.getSI`

## Architectural Decision

Use explicit domain classes and methods. This follows the current SDK design,
makes features discoverable through normal Python tooling, and allows parameter
names and validation to express known fnOS semantics.

Rejected alternatives:

1. A generic endpoint catalog would reduce implementation code but would still
   require users to know raw fnOS endpoint names and payload shapes.
2. Fixture-driven code generation would synchronize endpoint names cheaply, but
   cannot reliably generate stable method names, parameter semantics, defaults,
   validation, or documentation from sanitized JSON alone.

`FnosClient.request_payload_with_response()` remains the low-level escape hatch
for advanced callers and future endpoints.

## Module Boundaries

Existing classes gain methods when the captured endpoint clearly belongs to
their current responsibility:

| Existing class | Added responsibility |
| --- | --- |
| `DockerManager` | Images, image downloads, Docker networks, registry repositories |
| `Network` | Gateway, multi-gateway, NIC mode/details, SSH status |
| `ResourceMonitor` | NPU, processes, service processes, system fan |
| `SAC` | External email notification configuration and providers |
| `Share` | Protocol options, share options, share links, link permissions |
| `File` | Directory views, favorites, recent files, shares, trash, app directories |
| `Store` | Cache devices, removable devices, disk idle and wake-up settings |
| `User` | Activity, groups, login devices, tokens, 2FA, user preferences |
| `SystemInfo` | Reserved partition information |

New classes provide coherent namespaces for fnOS areas not represented today:

- `BackupManager`
- `DownloadCenter`
- `IPBlocker`
- `LicenseManager`
- `MountManager`
- `NetworkServer`
- `Security`
- `SystemRestore`
- `LiveUpdate`

Each new class accepts an `FnosClient` in its constructor, matching all existing
domain classes. New public classes are exported from `fnos.__init__`.

## Public Endpoint Inventory

New public methods use snake_case. Existing public names remain unchanged.

| Class | Method | fnOS request |
| --- | --- | --- |
| `User` | `list_tokens()` | `appcgi.accountsrv.v1.token.list` |
| `BackupManager` | `list_tasks(direction)` | `appcgi.backup.task.list` |
| `DockerManager` | `list_image_downloads()` | `appcgi.dockermgr.imageDownloadList` |
| `DockerManager` | `list_images()` | `appcgi.dockermgr.imageList` |
| `DockerManager` | `list_networks()` | `appcgi.dockermgr.networkList` |
| `DockerManager` | `list_registry_repositories(keyword, page, page_size)` | `appcgi.dockermgr.registryHubRepoList` |
| `DownloadCenter` | `get_default_save_directory()` | `appcgi.downloadcenter.config.getDefaultSaveDir` |
| `DownloadCenter` | `get_statistics()` | `appcgi.downloadcenter.stat.all` |
| `DownloadCenter` | `query_tasks(state_filter, init_flag)` | `appcgi.downloadcenter.task.query` |
| `File` | `list_app_directories()` | `appcgi.filestor.getAppDirList` |
| `IPBlocker` | `list_allowed_addresses()` | `appcgi.ipblocker.queryAllowList` |
| `IPBlocker` | `get_auto_block_rule()` | `appcgi.ipblocker.queryAutoBlockRule` |
| `IPBlocker` | `list_denied_addresses()` | `appcgi.ipblocker.queryDenyList` |
| `LicenseManager` | `list(page, page_size)` | `appcgi.license.soft.list` |
| `MountManager` | `list_mounts()` | `appcgi.mountmgr.list` |
| `MountManager` | `get_settings()` | `appcgi.mountmgr.setting.detail` |
| `NetworkServer` | `list_certificates()` | `appcgi.netsvr.cert.list` |
| `NetworkServer` | `get_connection_config()` | `appcgi.netsvr.conn.getconfig` |
| `NetworkServer` | `get_connection_status()` | `appcgi.netsvr.conn.status` |
| `NetworkServer` | `list_ddns_providers()` | `appcgi.netsvr.ddns.provider.list` |
| `NetworkServer` | `list_ddns_records(page, page_size)` | `appcgi.netsvr.ddns.record.list` |
| `Network` | `get_gateway()` | `appcgi.network.gw.getting` |
| `Network` | `get_multi_gateway_status()` | `appcgi.network.net.getMultiGWStatus` |
| `Network` | `get_nic_performance_mode()` | `appcgi.network.net.getNicPerformanceMode` |
| `Network` | `get_info(if_name)` | `appcgi.network.net.info` |
| `Network` | `get_ssh_status()` | `appcgi.network.ssh.status` |
| `ResourceMonitor` | `npu()` | `appcgi.resmon.npu` |
| `ResourceMonitor` | `processes()` | `appcgi.resmon.proc.list` |
| `ResourceMonitor` | `service_processes()` | `appcgi.resmon.proc.srv` |
| `ResourceMonitor` | `system_fan()` | `appcgi.resmon.sysFan` |
| `SAC` | `get_email_config()` | `appcgi.sac.externalnotify.v1.email.getConfig` |
| `SAC` | `list_email_providers()` | `appcgi.sac.externalnotify.v1.email.getProviders` |
| `Security` | `get_firewall()` | `appcgi.security.firewall.getting` |
| `Security` | `get_process_traffic(processes)` | `appcgi.security.flowaudit.traffic` |
| `Share` | `dlna_options()` | `appcgi.share.dlna.opt` |
| `Share` | `dlna_share_options()` | `appcgi.share.dlna.share.opt` |
| `Share` | `ftp_options()` | `appcgi.share.ftp.opt` |
| `Share` | `ftp_share_options()` | `appcgi.share.ftp.share.opt` |
| `Share` | `nfs_options()` | `appcgi.share.nfs.opt` |
| `Share` | `nfs_share_options()` | `appcgi.share.nfs.share.opt` |
| `Share` | `smb_share_options()` | `appcgi.share.smb.share.opt` |
| `Share` | `webdav_options()` | `appcgi.share.webdav.opt` |
| `Share` | `webdav_share_options()` | `appcgi.share.webdav.share.opt` |
| `Share` | `get_link_defaults()` | `appcgi.sharesvr.share.link.default.get` |
| `Share` | `get_default_link()` | `appcgi.sharesvr.share.link.default` |
| `Share` | `list_links(is_admin, keyword, page, page_size, sort_column, sort_type)` | `appcgi.sharesvr.share.link.list` |
| `Share` | `get_link_permission()` | `appcgi.sharesvr.share.permission.get` |
| `SystemInfo` | `get_reserved_partition()` | `appcgi.sysinfo.getReservedPartition` |
| `SystemRestore` | `get_info()` | `appcgi.sysrestore.getInfo` |
| `User` | `get_my_twofa_config()` | `appcgi.tfa.security.v1.me.getConfig` |
| `User` | `get_global_twofa_config()` | `appcgi.tfa.security.v1.twofa.getConfig` |
| `User` | `get_user_twofa_config(uid)` | `appcgi.tfa.security.v1.user.getTwofaConfig` |
| `File` | `list_favorites()` | `file.fav.list` |
| `File` | `list_directory_entries()` | `file.lsDir` |
| `File` | `list_recent()` | `file.recent.list` |
| `File` | `list_shared()` | `file.share.list` |
| `File` | `list_shared_by_others()` | `file.share.listOthers` |
| `File` | `list_team_trash_bins()` | `file.team.trash.listTrashbin` |
| `File` | `list_trash()` | `file.trash.list` |
| `LiveUpdate` | `get_status()` | `liveupdate.status` |
| `Store` | `get_cache_device_state()` | `stor.cachedevState` |
| `Store` | `get_disk_idle_time()` | `stor.getDiskIdleTime` |
| `Store` | `get_disk_wakeup()` | `stor.getDiskWakeup` |
| `Store` | `get_removable_config()` | `stor.getRemovableConf` |
| `Store` | `list_cache_devices()` | `stor.listCachedev` |
| `Store` | `list_removable_devices()` | `stor.listRemovable` |
| `User` | `get_active_state()` | `user.active` |
| `User` | `get_group_info(group)` | `user.groupInfo` |
| `User` | `list_groups()` | `user.groupList` |
| `User` | `list_login_devices()` | `user.listLoginDevice` |
| `User` | `get_preference(name)` | `usrdat.get` |

## Request Construction

Each wrapper performs exactly four operations:

1. Accept Python-style arguments.
2. Validate only constraints that are reliable from the request corpus.
3. Build a new payload with the captured field names and nesting.
4. Call `request_payload_with_response(endpoint, payload, timeout)` and return
   the response unchanged.

The client continues to add `req` and `reqid`; domain methods do not include
those fields in their payloads.

### Captured payload mappings

- `User.list_tokens()` sends `{"data": {}}`, not an empty top-level payload.
- `BackupManager.list_tasks()` sends top-level `direction` and accepts only `0`
  or `1`.
- `DockerManager.list_registry_repositories()` maps `keyword` to top-level `key`
  and sends top-level `page` and `pageSize`.
- `DownloadCenter.query_tasks()` maps directly to top-level `state_filter` and
  `init_flag`. Its defaults are `65535` and `True`.
- `LicenseManager.list()` and `NetworkServer.list_ddns_records()` wrap pagination
  fields under `data`.
- `Network.get_info()` maps `if_name` to top-level `ifName`.
- `Security.get_process_traffic()` wraps the supplied list under top-level
  `data` without mutating the caller's list or its dictionaries.
- `Share.list_links()` wraps all filter, paging, and sorting fields under `data`.
- `User.get_user_twofa_config()` wraps `uid` under `data`.
- `User.get_group_info()` sends top-level `group`.
- `User.get_preference()` sends top-level `name`.
- All other scoped requests send an empty payload.

### Defaults

- Every method accepts `timeout: float = 10.0` as its final argument.
- Registry repository pagination defaults to page `1`, page size `20`, and an
  empty keyword.
- License and DDNS record pagination defaults to page `1`, page size `200`.
- Share-link listing defaults to non-administrator mode, empty keyword, page
  `1`, page size `100`, sort column `createdTime`, and sort type `DESC`.
- Download task queries default to all captured states (`65535`) and initial
  query mode (`True`). The integer state filter remains open to other valid
  bitmask combinations rather than being restricted to captured examples.

## Validation and Error Behavior

- Empty required strings such as `if_name`, `group`, and preference `name`
  raise `ValueError` before any request is sent.
- Page and page-size arguments must be positive integers.
- Backup direction must be integer `0` or `1`.
- A user ID must be a non-negative integer.
- `processes` must be a list of dictionaries. The method copies the list and
  dictionaries before constructing the payload.
- Other server-owned semantics are not guessed or restricted.
- `NotConnectedError`, request timeouts, and other client exceptions propagate.
- A server response with `result: fail` is returned unchanged, matching existing
  SDK behavior.
- Domain methods do not cache, retry, reshape, or translate responses.

## Testing Strategy

### Independent wrapper contract tests

Add non-integration async tests using a recording fake client. A parameterized
contract matrix covers all 71 methods and asserts:

- exact endpoint name;
- exact payload, including top-level versus `data` nesting;
- default arguments;
- representative custom arguments;
- timeout propagation;
- unchanged response return value.

Dedicated tests cover each validation rule and confirm that mutable caller input
is unchanged.

### Mock-server integration tests

Update the CI mock-server pin from
`d26b2d21efc2ed1cfffbc09868d3445340ed1acc` to
`d9592a05a8e07082b954921acfae3a9a915f3c01`. Add grouped integration tests that
connect and log in once per domain group, invoke every new method, and assert a
dictionary response is received without an unknown-request error or timeout.

During implementation, run a read-only cross-repository comparison between the
unit-test contract matrix and all 82 sanitized request cases after removing
fixture-owned `req` and `reqid` fields. This comparison is a development
verification step, not a runtime or packaging dependency.

### Regression verification

Run the full pyfnos test suite with the updated mock server. Existing login,
2FA, reconnect, and domain tests must continue to pass.

Run every file under `examples/` with `--help` in a non-network smoke test so
syntax errors, invalid imports, stale public class names, and broken argument
parser setup fail CI before any connection is attempted. The endpoint contract
tests remain the behavioral coverage for calls demonstrated by the examples;
the example programs themselves are not executed against a live server in the
unit-test job.

## Example Programs

Extend the existing examples for classes that gain methods:

- `examples/docker_manager.py`
- `examples/network.py`
- `examples/resource_monitor.py`
- `examples/sac.py`
- `examples/share.py`
- `examples/file.py`
- `examples/store.py`
- `examples/user.py`
- `examples/system_info.py`

Add one runnable example program for each new domain class:

- `examples/backup_manager.py`
- `examples/download_center.py`
- `examples/ip_blocker.py`
- `examples/license_manager.py`
- `examples/mount_manager.py`
- `examples/network_server.py`
- `examples/security.py`
- `examples/system_restore.py`
- `examples/live_update.py`

Every example will reuse the connection, authentication, SSL, and optional 2FA
helpers from `examples/common.py`, close the client in `finally`, and perform
read-only calls only. New examples require credentials through the shared CLI
arguments rather than embedding real credentials or environment values. Output
will favor concise labels plus the returned query data, without assuming that
lists are non-empty.

## Documentation

- Extend the README API table with all new methods grouped by class.
- Add the runnable programs listed in the Example Programs section and include
  representative calls for every newly added method.
- Extend the README example-program table with all nine new files and update the
  descriptions of the nine extended files.
- Export every new class from `fnos.__init__` and include it in `__all__`.
- Add an Unreleased changelog entry summarizing the 71 new read-only query
  wrappers.
- List the seven deferred endpoints and the missing-request-fixture reason in
  the implementation documentation so they are not mistaken for omissions.

## Completion Criteria

The feature is complete when:

1. All 71 paired endpoints have explicit public wrappers matching this inventory.
2. Every captured request shape and alternate case is represented by contract
   tests or an equivalent custom-argument test.
3. Validation, timeout propagation, and mutable-input behavior are tested.
4. The updated mock-server integration suite and full pyfnos suite pass.
5. All 18 new or extended example files cover the new public surface and pass
   non-network `--help` smoke checks.
6. README, exports, example inventory, and changelog reflect the new public
   surface.
7. No wrapper is added for the seven response-only endpoints.
