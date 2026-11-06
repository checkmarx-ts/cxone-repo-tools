from __future__ import annotations
from typing import FrozenSet
from urllib.parse import urlsplit
from cxone_api import ApiRegionEndpoints, AuthRegionEndpoints, CxOneClient


class CxOneRepoToolsClient(CxOneClient):
    """A CxOneClient that also reports whether it is connected to a
    single-tenant Checkmarx One deployment.

    cxone-async-api's CxOneClient factory methods are static and always
    construct a CxOneClient, so the instances they return are re-classed
    as CxOneRepoToolsClient rather than constructed directly."""

    @staticmethod
    def __hostname(url: str) -> str | None:
        host = urlsplit(url).hostname
        return host.lower() if host is not None else None

    @staticmethod
    def __regional_hostnames() -> FrozenSet[str]:
        """The IAM and API hostnames of every well-known multi-tenant region."""
        hosts = set()
        for region in ApiRegionEndpoints.values():
            hosts.add(CxOneRepoToolsClient.__hostname(str(region())))
        for region in AuthRegionEndpoints.values():
            hosts.add(CxOneRepoToolsClient.__hostname(str(region("tenant"))))
        hosts.discard(None)
        return frozenset(hosts)

    @staticmethod
    def __adopt(client: CxOneClient) -> CxOneRepoToolsClient:
        client.__class__ = CxOneRepoToolsClient
        client.__single_tenant = (
            CxOneRepoToolsClient.__hostname(client.api_endpoint)
            not in CxOneRepoToolsClient.__regional_hostnames()
        )
        return client

    @staticmethod
    def create_with_oauth(*args, **kwargs) -> CxOneRepoToolsClient:
        return CxOneRepoToolsClient.__adopt(
            CxOneClient.create_with_oauth(*args, **kwargs)
        )

    @staticmethod
    def create_with_api_key(*args, **kwargs) -> CxOneRepoToolsClient:
        return CxOneRepoToolsClient.__adopt(
            CxOneClient.create_with_api_key(*args, **kwargs)
        )

    @property
    def is_single_tenant(self) -> bool:
        """True when the client connects to an FQDN hostname that is not the
        hostname of any regional multi-tenant moniker."""
        return self.__single_tenant
