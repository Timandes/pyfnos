import pytest

from fnos import MountManager, NetworkServer
from tests.query_contract import QueryCase, assert_query_case


CASES = [
    QueryCase("mounts", MountManager, "list_mounts", "appcgi.mountmgr.list", {}),
    QueryCase(
        "mount-settings",
        MountManager,
        "get_settings",
        "appcgi.mountmgr.setting.detail",
        {},
    ),
    QueryCase(
        "certificates",
        NetworkServer,
        "list_certificates",
        "appcgi.netsvr.cert.list",
        {},
    ),
    QueryCase(
        "connection-config",
        NetworkServer,
        "get_connection_config",
        "appcgi.netsvr.conn.getconfig",
        {},
    ),
    QueryCase(
        "connection-status",
        NetworkServer,
        "get_connection_status",
        "appcgi.netsvr.conn.status",
        {},
    ),
    QueryCase(
        "ddns-providers",
        NetworkServer,
        "list_ddns_providers",
        "appcgi.netsvr.ddns.provider.list",
        {},
    ),
    QueryCase(
        "ddns-records-default",
        NetworkServer,
        "list_ddns_records",
        "appcgi.netsvr.ddns.record.list",
        {"data": {"page": 1, "pageSize": 200}},
    ),
    QueryCase(
        "ddns-records-large",
        NetworkServer,
        "list_ddns_records",
        "appcgi.netsvr.ddns.record.list",
        {"data": {"page": 1, "pageSize": 999}},
        kwargs={"page_size": 999},
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
async def test_mount_network_server_query_contract(case):
    await assert_query_case(case)


@pytest.mark.asyncio
@pytest.mark.parametrize("field", ["page", "page_size"])
async def test_ddns_pagination_must_be_positive(field):
    kwargs = {"page": 1, "page_size": 200, field: 0}
    with pytest.raises(ValueError):
        await NetworkServer(object()).list_ddns_records(**kwargs)
