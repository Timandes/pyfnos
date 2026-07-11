import pytest

from fnos import Share
from tests.query_contract import QueryCase, assert_query_case


CASES = [
    QueryCase("dlna-options", Share, "dlna_options", "appcgi.share.dlna.opt", {}),
    QueryCase(
        "dlna-share-options",
        Share,
        "dlna_share_options",
        "appcgi.share.dlna.share.opt",
        {},
    ),
    QueryCase("ftp-options", Share, "ftp_options", "appcgi.share.ftp.opt", {}),
    QueryCase(
        "ftp-share-options",
        Share,
        "ftp_share_options",
        "appcgi.share.ftp.share.opt",
        {},
    ),
    QueryCase("nfs-options", Share, "nfs_options", "appcgi.share.nfs.opt", {}),
    QueryCase(
        "nfs-share-options",
        Share,
        "nfs_share_options",
        "appcgi.share.nfs.share.opt",
        {},
    ),
    QueryCase(
        "smb-share-options",
        Share,
        "smb_share_options",
        "appcgi.share.smb.share.opt",
        {},
    ),
    QueryCase(
        "webdav-options", Share, "webdav_options", "appcgi.share.webdav.opt", {}
    ),
    QueryCase(
        "webdav-share-options",
        Share,
        "webdav_share_options",
        "appcgi.share.webdav.share.opt",
        {},
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
async def test_share_protocol_query_contract(case):
    await assert_query_case(case)
