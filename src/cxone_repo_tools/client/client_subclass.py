from __future__ import annotations
from typing import FrozenSet
from urllib.parse import urlsplit
from cxone_api import ApiRegionEndpoints, AuthRegionEndpoints, CxOneClient


class CxOneRepoToolsClient(CxOneClient):
    """A CxOneClient that also reports whether it is connected to a
    single-tenant Checkmarx One deployment.

    cxone-async-api's CxOneClient factory methods are static and always
    construct a CxOneClient, so the instances they return are re-classed
    as CxOneRepoToolsClient rather than constructed directly.  Use
    `create_with_oauth` or `create_with_api_key` to create an instance.
    """

    @staticmethod
    def __hostname(url: str) -> str | None:
        """Extracts the lower-cased hostname from a URL.

        :param url: The URL to parse.
        :type url: str

        :return: The lower-cased hostname, or None if the URL has no hostname.
        :rtype: str | None
        """
        host = urlsplit(url).hostname
        return host.lower() if host is not None else None

    @staticmethod
    def __regional_hostnames() -> FrozenSet[str]:
        """Collects the IAM and API hostnames of every well-known multi-tenant
        region defined by cxone-async-api.

        :return: The lower-cased regional hostnames.
        :rtype: FrozenSet[str]
        """
        hosts = set()
        for region in ApiRegionEndpoints.values():
            hosts.add(CxOneRepoToolsClient.__hostname(str(region())))
        for region in AuthRegionEndpoints.values():
            hosts.add(CxOneRepoToolsClient.__hostname(str(region("tenant"))))
        hosts.discard(None)
        return frozenset(hosts)

    @staticmethod
    def __adopt(client: CxOneClient) -> CxOneRepoToolsClient:
        """Re-classes a CxOneClient as a CxOneRepoToolsClient and determines
        whether it is connected to a single-tenant deployment.

        :param client: A client created by one of cxone-async-api's
                       CxOneClient factory methods.
        :type client: CxOneClient

        :return: The same instance, now of type CxOneRepoToolsClient.
        :rtype: CxOneRepoToolsClient
        """
        client.__class__ = CxOneRepoToolsClient
        client.__single_tenant = (
            CxOneRepoToolsClient.__hostname(client.api_endpoint)
            not in CxOneRepoToolsClient.__regional_hostnames()
        )
        return client

    @staticmethod
    def create_with_oauth(*args, **kwargs) -> CxOneRepoToolsClient:
        """Creates an instance that uses OAuth client credentials to
        authenticate with Checkmarx One.

        :param args: Positional arguments passed to cxone-async-api's
                     `CxOneClient.create_with_oauth`.
        :param kwargs: Keyword arguments passed to cxone-async-api's
                       `CxOneClient.create_with_oauth`.

        :return: A client authenticating with OAuth client credentials.
        :rtype: CxOneRepoToolsClient
        """
        return CxOneRepoToolsClient.__adopt(
            CxOneClient.create_with_oauth(*args, **kwargs)
        )

    @staticmethod
    def create_with_api_key(*args, **kwargs) -> CxOneRepoToolsClient:
        """Creates an instance that uses an API key to authenticate with
        Checkmarx One.

        :param args: Positional arguments passed to cxone-async-api's
                     `CxOneClient.create_with_api_key`.
        :param kwargs: Keyword arguments passed to cxone-async-api's
                       `CxOneClient.create_with_api_key`.

        :return: A client authenticating with an API key.
        :rtype: CxOneRepoToolsClient
        """
        return CxOneRepoToolsClient.__adopt(
            CxOneClient.create_with_api_key(*args, **kwargs)
        )

    @property
    def is_single_tenant(self) -> bool:
        """True when the client connects to an FQDN hostname that is not the
        hostname of any regional multi-tenant moniker.

        :rtype: bool
        """
        # Set by __adopt, which pylint cannot see as defining the member.
        return self.__single_tenant  # pylint: disable=no-member
