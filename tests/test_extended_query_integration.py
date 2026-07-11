import pytest

from fnos import FnosClient
from tests.query_cases import ALL_QUERY_CASES


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_all_extended_query_endpoints_are_routable():
    assert len(ALL_QUERY_CASES) == 82
    unique_cases = {}
    for case in ALL_QUERY_CASES:
        unique_cases.setdefault(case.endpoint, case)
    assert len(unique_cases) == 71

    client = FnosClient()
    try:
        await client.connect("127.0.0.1:5666")
        login = await client.login("admin", "admin")
        assert login.get("result") == "succ"

        for endpoint, case in unique_cases.items():
            owner = case.owner(client)
            result = await getattr(owner, case.method)(*case.args, **case.kwargs)
            assert isinstance(result, dict), endpoint
            assert "Unknown request type" not in result.get("errmsg", ""), endpoint
    finally:
        await client.close()
