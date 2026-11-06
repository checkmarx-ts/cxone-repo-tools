from cxone_repo_tools.client import CxOneRepoToolsClient
from .scm_project_index import AbstractScmProjectIndex
from .single_tenant_index import SingleTenantIndex
from .multi_tenant_index import MultiTenantIndex


class ScmProjectIndexFactory:
    """Creates the AbstractScmProjectIndex implementation for a client."""

    @staticmethod
    def create_index(
        client: CxOneRepoToolsClient, *, threads: int = 2
    ) -> AbstractScmProjectIndex:
        """Creates an SCM project index for the deployment the client is
        connected to.

        :param client: The client used to build the index.
        :type client: CxOneRepoToolsClient

        :param threads: The maximum number of concurrent API calls the index
                        makes.  Defaults to 2.
        :type threads: int, optional

        :return: A SingleTenantIndex if the client is connected to a
                 single-tenant deployment, otherwise a MultiTenantIndex.
        :rtype: AbstractScmProjectIndex
        """
        if client.is_single_tenant:
            return SingleTenantIndex(client, threads=threads)
        return MultiTenantIndex(client, threads=threads)
