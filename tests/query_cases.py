from tests.test_backup_download_queries import CASES as BACKUP_DOWNLOAD_CASES
from tests.test_docker_manager_queries import CASES as DOCKER_CASES
from tests.test_file_queries import CASES as FILE_CASES
from tests.test_ipblocker_security_queries import CASES as SECURITY_CASES
from tests.test_mount_network_server_queries import (
    CASES as MOUNT_NETWORK_SERVER_CASES,
)
from tests.test_network_queries import CASES as NETWORK_CASES
from tests.test_resource_monitor_queries import CASES as RESOURCE_MONITOR_CASES
from tests.test_sac_system_info_queries import CASES as SAC_SYSTEM_INFO_CASES
from tests.test_share_link_queries import CASES as SHARE_LINK_CASES
from tests.test_share_protocol_queries import CASES as SHARE_PROTOCOL_CASES
from tests.test_store_queries import CASES as STORE_CASES
from tests.test_system_service_queries import CASES as SYSTEM_SERVICE_CASES
from tests.test_user_queries import CASES as USER_CASES


ALL_QUERY_CASES = [
    *DOCKER_CASES,
    *NETWORK_CASES,
    *RESOURCE_MONITOR_CASES,
    *FILE_CASES,
    *STORE_CASES,
    *USER_CASES,
    *SHARE_PROTOCOL_CASES,
    *SHARE_LINK_CASES,
    *SAC_SYSTEM_INFO_CASES,
    *BACKUP_DOWNLOAD_CASES,
    *SECURITY_CASES,
    *SYSTEM_SERVICE_CASES,
    *MOUNT_NETWORK_SERVER_CASES,
]
