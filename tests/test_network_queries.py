import pytest

from fnos import Network
from tests.query_contract import QueryCase, assert_query_case


CASES = [
    QueryCase(
        "gateway", Network, "get_gateway", "appcgi.network.gw.getting", {}
    ),
    QueryCase(
        "multi-gateway",
        Network,
        "get_multi_gateway_status",
        "appcgi.network.net.getMultiGWStatus",
        {},
    ),
    QueryCase(
        "nic-performance",
        Network,
        "get_nic_performance_mode",
        "appcgi.network.net.getNicPerformanceMode",
        {},
    ),
    QueryCase(
        "interface-info",
        Network,
        "get_info",
        "appcgi.network.net.info",
        {"ifName": "eth0"},
        args=("eth0",),
    ),
    QueryCase(
        "ssh-status", Network, "get_ssh_status", "appcgi.network.ssh.status", {}
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
async def test_network_query_contract(case):
    await assert_query_case(case)


@pytest.mark.asyncio
async def test_get_info_rejects_empty_interface_name():
    with pytest.raises(ValueError):
        await Network(object()).get_info("")
