from pathlib import Path

import pytest

from tests import query_contract
from tests.query_cases import ALL_QUERY_CASES


pytestmark = pytest.mark.integration

MOCK_REQUESTS = (
    Path(__file__).resolve().parents[2] / "fnos-mock-server" / "requests"
)


def test_query_cases_match_mock_server_request_fixtures():
    query_contract.assert_fixture_parity(
        ALL_QUERY_CASES,
        MOCK_REQUESTS,
        expected_case_count=82,
        expected_endpoint_count=71,
    )
