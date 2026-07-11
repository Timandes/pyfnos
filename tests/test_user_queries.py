import pytest

from fnos import User
from tests.query_contract import QueryCase, assert_query_case


CASES = [
    QueryCase(
        "tokens",
        User,
        "list_tokens",
        "appcgi.accountsrv.v1.token.list",
        {"data": {}},
    ),
    QueryCase(
        "my-twofa",
        User,
        "get_my_twofa_config",
        "appcgi.tfa.security.v1.me.getConfig",
        {},
    ),
    QueryCase(
        "global-twofa",
        User,
        "get_global_twofa_config",
        "appcgi.tfa.security.v1.twofa.getConfig",
        {},
    ),
    QueryCase(
        "user-twofa",
        User,
        "get_user_twofa_config",
        "appcgi.tfa.security.v1.user.getTwofaConfig",
        {"data": {"uid": 1000}},
        args=(1000,),
    ),
    QueryCase("active", User, "get_active_state", "user.active", {}),
    QueryCase(
        "group-info",
        User,
        "get_group_info",
        "user.groupInfo",
        {"group": "group"},
        args=("group",),
    ),
    QueryCase("groups", User, "list_groups", "user.groupList", {}),
    QueryCase(
        "login-devices", User, "list_login_devices", "user.listLoginDevice", {}
    ),
    QueryCase(
        "preference-namesake",
        User,
        "get_preference",
        "usrdat.get",
        {"name": "browser.namesakeConf"},
        args=("browser.namesakeConf",),
    ),
    QueryCase(
        "preference-date",
        User,
        "get_preference",
        "usrdat.get",
        {"name": "date-format"},
        args=("date-format",),
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
async def test_user_query_contract(case):
    await assert_query_case(case)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "argument"),
    [("get_user_twofa_config", -1), ("get_group_info", ""), ("get_preference", "")],
)
async def test_user_query_validation(method, argument):
    with pytest.raises(ValueError):
        await getattr(User(object()), method)(argument)
