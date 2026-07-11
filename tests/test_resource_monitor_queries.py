import pytest

from fnos import ResourceMonitor
from tests.query_contract import QueryCase, assert_query_case


CASES = [
    QueryCase("npu", ResourceMonitor, "npu", "appcgi.resmon.npu", {}),
    QueryCase(
        "processes",
        ResourceMonitor,
        "processes",
        "appcgi.resmon.proc.list",
        {},
    ),
    QueryCase(
        "service-processes",
        ResourceMonitor,
        "service_processes",
        "appcgi.resmon.proc.srv",
        {},
    ),
    QueryCase(
        "system-fan",
        ResourceMonitor,
        "system_fan",
        "appcgi.resmon.sysFan",
        {},
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
async def test_resource_monitor_query_contract(case):
    await assert_query_case(case)
