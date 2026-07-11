import pytest

from fnos import Store
from tests.query_contract import QueryCase, assert_query_case


CASES = [
    QueryCase(
        "cache-state", Store, "get_cache_device_state", "stor.cachedevState", {}
    ),
    QueryCase(
        "disk-idle-time", Store, "get_disk_idle_time", "stor.getDiskIdleTime", {}
    ),
    QueryCase(
        "disk-wakeup", Store, "get_disk_wakeup", "stor.getDiskWakeup", {}
    ),
    QueryCase(
        "removable-config",
        Store,
        "get_removable_config",
        "stor.getRemovableConf",
        {},
    ),
    QueryCase(
        "cache-devices", Store, "list_cache_devices", "stor.listCachedev", {}
    ),
    QueryCase(
        "removable-devices",
        Store,
        "list_removable_devices",
        "stor.listRemovable",
        {},
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
async def test_store_query_contract(case):
    await assert_query_case(case)
