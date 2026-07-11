import pytest

from fnos import File
from tests.query_contract import QueryCase, assert_query_case


CASES = [
    QueryCase(
        "app-directories",
        File,
        "list_app_directories",
        "appcgi.filestor.getAppDirList",
        {},
    ),
    QueryCase("favorites", File, "list_favorites", "file.fav.list", {}),
    QueryCase(
        "directory-entries", File, "list_directory_entries", "file.lsDir", {}
    ),
    QueryCase("recent", File, "list_recent", "file.recent.list", {}),
    QueryCase("shared", File, "list_shared", "file.share.list", {}),
    QueryCase(
        "shared-by-others",
        File,
        "list_shared_by_others",
        "file.share.listOthers",
        {},
    ),
    QueryCase(
        "team-trash-bins",
        File,
        "list_team_trash_bins",
        "file.team.trash.listTrashbin",
        {},
    ),
    QueryCase("trash", File, "list_trash", "file.trash.list", {}),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
async def test_file_query_contract(case):
    await assert_query_case(case)
