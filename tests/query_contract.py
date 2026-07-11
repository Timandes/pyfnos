"""Shared helpers for fnOS query wrapper contract tests."""

from dataclasses import dataclass, field
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
