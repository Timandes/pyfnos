import pytest

from fnos import DockerManager
from tests.query_contract import QueryCase, assert_query_case


CASES = [
    QueryCase(
        "image-downloads",
        DockerManager,
        "list_image_downloads",
        "appcgi.dockermgr.imageDownloadList",
        {},
    ),
    QueryCase(
        "images",
        DockerManager,
        "list_images",
        "appcgi.dockermgr.imageList",
        {},
    ),
    QueryCase(
        "networks",
        DockerManager,
        "list_networks",
        "appcgi.dockermgr.networkList",
        {},
    ),
    QueryCase(
        "registry-repositories",
        DockerManager,
        "list_registry_repositories",
        "appcgi.dockermgr.registryHubRepoList",
        {"key": "", "page": 1, "pageSize": 20},
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
async def test_docker_query_contract(case):
    await assert_query_case(case)


@pytest.mark.asyncio
@pytest.mark.parametrize("field", ["page", "page_size"])
async def test_registry_pagination_must_be_positive(field):
    manager = DockerManager(object())
    kwargs = {"page": 1, "page_size": 20, field: 0}
    with pytest.raises(ValueError):
        await manager.list_registry_repositories(**kwargs)
