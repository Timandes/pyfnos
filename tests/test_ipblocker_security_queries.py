import pytest

from fnos import IPBlocker, Security
from tests.query_contract import QueryCase, RecordingClient, assert_query_case


PROCESSES = [
    {"pid": 1001, "process": "example-process"},
    {"pid": 1002, "process": "example-worker"},
]

CASES = [
    QueryCase(
        "allow-list",
        IPBlocker,
        "list_allowed_addresses",
        "appcgi.ipblocker.queryAllowList",
        {},
    ),
    QueryCase(
        "auto-block",
        IPBlocker,
        "get_auto_block_rule",
        "appcgi.ipblocker.queryAutoBlockRule",
        {},
    ),
    QueryCase(
        "deny-list",
        IPBlocker,
        "list_denied_addresses",
        "appcgi.ipblocker.queryDenyList",
        {},
    ),
    QueryCase(
        "firewall", Security, "get_firewall", "appcgi.security.firewall.getting", {}
    ),
    QueryCase(
        "process-traffic",
        Security,
        "get_process_traffic",
        "appcgi.security.flowaudit.traffic",
        {"data": PROCESSES},
        args=(PROCESSES,),
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
async def test_security_domain_query_contract(case):
    await assert_query_case(case)


@pytest.mark.asyncio
async def test_process_traffic_copies_mutable_input():
    source = [{"pid": 1001, "process": "example-process"}]
    client = RecordingClient()
    await Security(client).get_process_traffic(source)
    sent = client.calls[0][1]["data"]
    assert sent == source
    assert sent is not source
    assert sent[0] is not source[0]


@pytest.mark.asyncio
async def test_process_traffic_rejects_non_dict_list():
    with pytest.raises(ValueError):
        await Security(object()).get_process_traffic([1])
