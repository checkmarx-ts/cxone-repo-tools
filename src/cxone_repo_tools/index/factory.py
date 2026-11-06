import logging
from cxone_repo_tools.client import CxOneRepoToolsClient
from .scm_project_index import ScmProjectIndex
from .single_tenant_index import SingleTenantIndex
from .multi_tenant_index import MultiTenantIndex

_log = logging.getLogger(__name__)


class ScmProjectIndexFactory:
    """Creates the ScmProjectIndex implementation for a client."""

    @staticmethod
    def create_index(
        client: CxOneRepoToolsClient, *, threads: int = 2
    ) -> ScmProjectIndex:
        """Creates an SCM project index for the deployment the client is
        connected to.

        :param client: The client used to build the index.
        :type client: CxOneRepoToolsClient

        :param threads: The maximum number of concurrent API calls the index
                        makes.  Defaults to 2.
        :type threads: int, optional

        :return: A SingleTenantIndex if the client is connected to a
                 single-tenant deployment, otherwise a MultiTenantIndex.
        :rtype: ScmProjectIndex
        """
        index_type = SingleTenantIndex if client.is_single_tenant else MultiTenantIndex
        _log.debug(
            f"Creating {index_type.__name__} for API endpoint {client.api_endpoint}"
        )
        return index_type(client, threads=threads)
