import pytest

from fnos import SAC, SystemInfo
from tests.query_contract import QueryCase, assert_query_case


CASES = [
    QueryCase(
        "email-config",
        SAC,
        "get_email_config",
        "appcgi.sac.externalnotify.v1.email.getConfig",
        {},
    ),
    QueryCase(
        "email-providers",
        SAC,
        "list_email_providers",
        "appcgi.sac.externalnotify.v1.email.getProviders",
        {},
    ),
    QueryCase(
        "reserved-partition",
        SystemInfo,
        "get_reserved_partition",
        "appcgi.sysinfo.getReservedPartition",
        {},
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
async def test_sac_system_info_query_contract(case):
    await assert_query_case(case)
