import pytest

from fnos import Share
from tests.query_contract import QueryCase, assert_query_case


DEFAULT_LINK_PAYLOAD = {
    "data": {
        "isAdmin": False,
        "keyword": "",
        "page": 1,
        "pageSize": 100,
        "sortColumn": "createdTime",
        "sortType": "DESC",
    }
}

CASES = [
    QueryCase(
        "link-defaults",
        Share,
        "get_link_defaults",
        "appcgi.sharesvr.share.link.default.get",
        {},
    ),
    QueryCase(
        "default-link",
        Share,
        "get_default_link",
        "appcgi.sharesvr.share.link.default",
        {},
    ),
    QueryCase(
        "links-user",
        Share,
        "list_links",
        "appcgi.sharesvr.share.link.list",
        DEFAULT_LINK_PAYLOAD,
    ),
    QueryCase(
        "links-admin",
        Share,
        "list_links",
        "appcgi.sharesvr.share.link.list",
        {"data": {**DEFAULT_LINK_PAYLOAD["data"], "isAdmin": True}},
        kwargs={"is_admin": True},
    ),
    QueryCase(
        "link-permission",
        Share,
        "get_link_permission",
        "appcgi.sharesvr.share.permission.get",
        {},
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
async def test_share_link_query_contract(case):
    await assert_query_case(case)


@pytest.mark.asyncio
@pytest.mark.parametrize("field", ["page", "page_size"])
async def test_share_link_pagination_must_be_positive(field):
    kwargs = {"page": 1, "page_size": 100, field: 0}
    with pytest.raises(ValueError):
        await Share(object()).list_links(**kwargs)
