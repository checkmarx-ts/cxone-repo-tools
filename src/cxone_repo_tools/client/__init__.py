import os
from typing import Dict, Tuple
from cxone_api import (
    ApiRegionEndpoints,
    AuthRegionEndpoints,
    CxOneClient,
    CxOneApiEndpoint,
    CxOneAuthEndpoint,
)
from .. import AGENT


def mt_endpoints() -> str:
    return ",".join(sorted(ApiRegionEndpoints.keys()))


class CxOneClientFactory:
    """Builds a CxOneClient from command line options, authenticating with
    either an API key or OAuth client credentials."""

    API_KEY_ENV = "CX_API_KEY"
    CLIENT_SECRET_ENV = "CX_CLIENT_SECRET"

    @staticmethod
    def __secret(value: str | None, in_env: bool, env_var: str, label: str) -> str:
        secret = os.environ.get(env_var) if in_env else value

        if secret is None or len(secret) == 0:
            raise ValueError(f"{label} was not provided.")

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
            raise ValueError("Checkmarx One endpoints not defined.")

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
    ) -> CxOneClient:
        key = CxOneClientFactory.__secret(
            api_key, apikey_in_env, CxOneClientFactory.API_KEY_ENV, "API Key"
        )

        return CxOneClient.create_with_api_key(
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
    ) -> CxOneClient:
        secret = CxOneClientFactory.__secret(
            oauth_client_secret,
            secret_in_env,
            CxOneClientFactory.CLIENT_SECRET_ENV,
            "OAuth client secret",
        )

        return CxOneClient.create_with_oauth(
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
    ) -> CxOneClient:
        """Creates a CxOneClient. OAuth client credentials are used when
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

        return CxOneClientFactory.__api_client(
            api_key,
            apikey_in_env,
            auth_endpoint,
            api_endpoint,
            proxy,
            ssl_verify,
            retries,
        )
