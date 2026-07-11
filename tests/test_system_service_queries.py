import pytest

from fnos import LicenseManager, LiveUpdate, SystemRestore
from tests.query_contract import QueryCase, assert_query_case


CASES = [
    QueryCase(
        "licenses",
        LicenseManager,
        "list",
        "appcgi.license.soft.list",
        {"data": {"page": 1, "pageSize": 200}},
    ),
    QueryCase(
        "restore-info",
        SystemRestore,
        "get_info",
        "appcgi.sysrestore.getInfo",
        {},
    ),
    QueryCase(
        "update-status", LiveUpdate, "get_status", "liveupdate.status", {}
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
async def test_system_service_query_contract(case):
    await assert_query_case(case)


@pytest.mark.asyncio
@pytest.mark.parametrize("field", ["page", "page_size"])
async def test_license_pagination_must_be_positive(field):
    kwargs = {"page": 1, "page_size": 200, field: 0}
    with pytest.raises(ValueError):
        await LicenseManager(object()).list(**kwargs)
