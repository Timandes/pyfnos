"""Shared helpers for fnOS query wrapper contract tests."""

import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class QueryCase:
    name: str
    owner: type
    method: str
    endpoint: str
    payload: dict
    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] = field(default_factory=dict)


class RecordingClient:
    def __init__(self):
        self.calls: list[tuple[str, dict, float]] = []
        self.response = {"result": "sentinel"}

    async def request_payload_with_response(
        self, req: str, payload: dict, timeout: float = 10.0
    ) -> dict:
        self.calls.append((req, payload, timeout))
        return self.response


async def assert_query_case(case: QueryCase, timeout: float = 2.5) -> None:
    client = RecordingClient()
    owner = case.owner(client)
    kwargs = dict(case.kwargs)
    kwargs["timeout"] = timeout

    result = await getattr(owner, case.method)(*case.args, **kwargs)

    assert client.calls == [(case.endpoint, case.payload, timeout)]
    assert result is client.response


def _canonical_payload(payload: dict) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def assert_fixture_parity(
    cases: list[QueryCase],
    requests_dir: Path,
    *,
    expected_case_count: int,
    expected_endpoint_count: int,
) -> None:
    """Assert SDK query cases exactly match fnos-mock-server requests."""
    assert requests_dir.is_dir(), f"mock requests directory not found: {requests_dir}"

    sdk_payloads: dict[str, set[str]] = defaultdict(set)
    for case in cases:
        sdk_payloads[case.endpoint].add(_canonical_payload(case.payload))

    fixture_paths = sorted(requests_dir.glob("*/case-*.json"))
    mock_payloads: dict[str, set[str]] = defaultdict(set)
    for path in fixture_paths:
        request = json.loads(path.read_text(encoding="utf-8"))
        endpoint = request.pop("req")
        request.pop("reqid", None)
        mock_payloads[endpoint].add(_canonical_payload(request))

    assert len(cases) == expected_case_count
    assert len(fixture_paths) == expected_case_count
    assert len(sdk_payloads) == expected_endpoint_count
    assert len(mock_payloads) == expected_endpoint_count
    assert dict(sdk_payloads) == dict(mock_payloads)
