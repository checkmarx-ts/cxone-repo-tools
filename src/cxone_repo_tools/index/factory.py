import logging
from cxone_api.low.misc import retrieve_versions
from cxone_api.util import json_on_ok
from cxone_repo_tools.client import CxOneRepoToolsClient
from .scm_project_index import ScmProjectIndex
from .legacy_index import LegacyIndex
from .unified_index import UnifiedIndex

_log = logging.getLogger(__name__)


class ScmProjectIndexFactory:
    """Creates the ScmProjectIndex implementation for a client."""

    __UNIFIED_INDEX_MIN_VERSION = (3, 70, 1)

    @staticmethod
    async def create_index(
        client: CxOneRepoToolsClient, *, threads: int = 2
    ) -> ScmProjectIndex:
        """Creates an SCM project index for the deployment the client is
        connected to.

        Version checks are done on for single-tenant only since deployments
        lag behind multi-tenant deployments by an unknown number of versions.

        CxOne 3.70.1 unified the API that returns the projects assigned to an
        SCM so that it also returns the project ID.  A single-tenant
        deployment on CxOne 3.70.1 or later always gets a UnifiedIndex.
        Single-tenant deployments on earlier versions do not have the unified
        API and use LegacyIndex.

        :param client: The client used to build the index.
        :type client: CxOneRepoToolsClient

        :param threads: The maximum number of concurrent API calls the index
                        makes.  Defaults to 2.
        :type threads: int, optional

        :return: The index for the deployment.
        :rtype: ScmProjectIndex

        :raises ResponseException: The version data could not be retrieved.
        """
        index_type = UnifiedIndex

        if client.is_single_tenant:
            version_data = json_on_ok(await retrieve_versions(client))
            cxone_version = version_data["CxOne"]
            _log.debug(f"CxOne version: {cxone_version}")

            version = tuple(int(part) for part in cxone_version.split("."))
            if version < ScmProjectIndexFactory.__UNIFIED_INDEX_MIN_VERSION:
                index_type = LegacyIndex

        _log.debug(
            f"Creating {index_type.__name__} for API endpoint {client.api_endpoint}"
        )
        return index_type(client, threads=threads)
