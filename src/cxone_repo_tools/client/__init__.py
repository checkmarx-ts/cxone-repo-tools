from __future__ import annotations
import os
from typing import Dict, FrozenSet, Tuple
from urllib.parse import urlsplit
from cxone_api import (
    ApiRegionEndpoints,
    AuthRegionEndpoints,
    CxOneClient,
    CxOneApiEndpoint,
    CxOneAuthEndpoint,
)
from cxone_repo_tools import AGENT
from cxone_repo_tools.convert import AbortedConversionException


def mt_endpoints() -> str:
    return ",".join(sorted(ApiRegionEndpoints.keys()))


def _hostname(url: str) -> str | None:
    host = urlsplit(url).hostname
    return host.lower() if host is not None else None


def _regional_hostnames() -> FrozenSet[str]:
    """The IAM and API hostnames of every well-known multi-tenant region."""
    hosts = set()
    for region in ApiRegionEndpoints.values():
        hosts.add(_hostname(str(region())))
    for region in AuthRegionEndpoints.values():
        hosts.add(_hostname(str(region("tenant"))))
    hosts.discard(None)
    return frozenset(hosts)


class CxOneRepoToolsClient(CxOneClient):
    """A CxOneClient that also reports whether it is connected to a
    single-tenant Checkmarx One deployment.

    cxone-async-api's CxOneClient factory methods are static and always
    construct a CxOneClient, so the instances they return are re-classed
    as CxOneRepoToolsClient rather than constructed directly."""

    __REGIONAL_HOSTNAMES = _regional_hostnames()

    @staticmethod
    def __adopt(client: CxOneClient) -> CxOneRepoToolsClient:
        client.__class__ = CxOneRepoToolsClient
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
        return (
            _hostname(self.api_endpoint)
            not in CxOneRepoToolsClient.__REGIONAL_HOSTNAMES
        )


class CxOneClientFactory:
    """Builds a CxOneRepoToolsClient from command line options, authenticating
    with either an API key or OAuth client credentials."""

    API_KEY_ENV = "CX_API_KEY"
    CLIENT_SECRET_ENV = "CX_CLIENT_SECRET"

    @staticmethod
    def __secret(value: str | None, in_env: bool, env_var: str, label: str) -> str:
        if in_env:
            secret = os.environ.get(env_var)
            if secret is None or len(secret) == 0:
                raise AbortedConversionException.missing_secret_env(env_var, label)
        else:
            secret = value
            if secret is None or len(secret) == 0:
                raise AbortedConversionException.empty_secret(label)

        return secret

    @staticmethod
    def __endpoints(
        fqdn: str | None, region: str | None, tenant: str
    ) -> Tuple[CxOneAuthEndpoint, CxOneApiEndpoint]:
        if fqdn is not None and len(fqdn) > 0:
            return CxOneAuthEndpoint(tenant, fqdn), CxOneApiEndpoint(fqdn)
        elif region is not None and len(region) > 0:
            return AuthRegionEndpoints[region](tenant), ApiRegionEndpoints[region]()
        else:
            return None, None

    @staticmethod
    def __proxy(proxy_url: str | None) -> Dict[str, str] | None:
        if proxy_url is not None and len(proxy_url) > 0:
            return {"https": proxy_url}
        return None

    @staticmethod
    def __api_client(
        api_key: str | None,
        apikey_in_env: bool,
        auth_endpoint: CxOneAuthEndpoint,
        api_endpoint: CxOneApiEndpoint,
        proxy: Dict[str, str] | None,
        ssl_verify: bool,
        retries: int,
    ) -> CxOneRepoToolsClient:
        key = CxOneClientFactory.__secret(
            api_key, apikey_in_env, CxOneClientFactory.API_KEY_ENV, "API Key"
        )

        return CxOneRepoToolsClient.create_with_api_key(
            key,
            AGENT,
            auth_endpoint,
            api_endpoint,
            proxy=proxy,
            ssl_verify=ssl_verify,
            retries=retries,
        )

    @staticmethod
    def __oauth_client(
        oauth_client_id: str,
        oauth_client_secret: str | None,
        secret_in_env: bool,
        auth_endpoint: CxOneAuthEndpoint,
        api_endpoint: CxOneApiEndpoint,
        proxy: Dict[str, str] | None,
        ssl_verify: bool,
        retries: int,
    ) -> CxOneRepoToolsClient:
        secret = CxOneClientFactory.__secret(
            oauth_client_secret,
            secret_in_env,
            CxOneClientFactory.CLIENT_SECRET_ENV,
            "OAuth client secret",
        )

        return CxOneRepoToolsClient.create_with_oauth(
            oauth_client_id,
            secret,
            AGENT,
            auth_endpoint,
            api_endpoint,
            proxy=proxy,
            ssl_verify=ssl_verify,
            retries=retries,
        )

    @staticmethod
    def client_factory(
        api_key: str | None,
        apikey_in_env: bool,
        oauth_client_id: str | None,
        oauth_client_secret: str | None,
        secret_in_env: bool,
        fqdn: str | None,
        region: str | None,
        tenant: str,
        proxy_url: str | None,
        ssl_verify: bool,
        retries: int,
    ) -> CxOneRepoToolsClient:
        """Creates a CxOneRepoToolsClient. OAuth client credentials are used when
        oauth_client_id is provided, otherwise an API key is used."""

        auth_endpoint, api_endpoint = CxOneClientFactory.__endpoints(
            fqdn, region, tenant
        )
        proxy = CxOneClientFactory.__proxy(proxy_url)

        if oauth_client_id is not None and len(oauth_client_id) > 0:
            return CxOneClientFactory.__oauth_client(
                oauth_client_id,
                oauth_client_secret,
                secret_in_env,
                auth_endpoint,
                api_endpoint,
                proxy,
                ssl_verify,
                retries,
            )

        if api_key is not None or apikey_in_env:
            return CxOneClientFactory.__api_client(
                api_key,
                apikey_in_env,
                auth_endpoint,
                api_endpoint,
                proxy,
                ssl_verify,
                retries,
            )
