import pytest

from fnos import BackupManager, DownloadCenter
from tests.query_contract import QueryCase, assert_query_case


CASES = [
    QueryCase(
        "backup-outbound",
        BackupManager,
        "list_tasks",
        "appcgi.backup.task.list",
        {"direction": 0},
        args=(0,),
    ),
    QueryCase(
        "backup-inbound",
        BackupManager,
        "list_tasks",
        "appcgi.backup.task.list",
        {"direction": 1},
        args=(1,),
    ),
    QueryCase(
        "download-save-dir",
        DownloadCenter,
        "get_default_save_directory",
        "appcgi.downloadcenter.config.getDefaultSaveDir",
        {},
    ),
    QueryCase(
        "download-stats",
        DownloadCenter,
        "get_statistics",
        "appcgi.downloadcenter.stat.all",
        {},
    ),
    *[
        QueryCase(
            f"download-state-{state_filter}",
            DownloadCenter,
            "query_tasks",
            "appcgi.downloadcenter.task.query",
            {"init_flag": True, "state_filter": state_filter},
            kwargs={} if state_filter == 65535 else {"state_filter": state_filter},
        )
        for state_filter in (16, 1, 2, 32, 4, 64, 65535, 8)
    ],
]


@pytest.mark.asyncio
@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
async def test_backup_download_query_contract(case):
    await assert_query_case(case)


@pytest.mark.asyncio
@pytest.mark.parametrize("direction", [-1, 2, True, 1.0, "0"])
async def test_backup_direction_is_restricted(direction):
    with pytest.raises(ValueError):
        await BackupManager(object()).list_tasks(direction)
