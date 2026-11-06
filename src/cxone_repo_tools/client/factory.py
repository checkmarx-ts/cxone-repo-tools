from __future__ import annotations
import os
from typing import Dict, Tuple
from cxone_api import (
    ApiRegionEndpoints,
    AuthRegionEndpoints,
    CxOneApiEndpoint,
    CxOneAuthEndpoint,
)
from cxone_repo_tools import AGENT
from cxone_repo_tools.convert.exceptions import AbortedConversionException
from .client_subclass import CxOneRepoToolsClient


class CxOneClientFactory:
    """Builds a CxOneRepoToolsClient from command line options, authenticating
    with either an API key or OAuth client credentials.

    :cvar API_KEY_ENV: The environment variable holding the API key.
    :cvar CLIENT_SECRET_ENV: The environment variable holding the OAuth
                             client secret.
    """

    API_KEY_ENV = "CX_API_KEY"
    CLIENT_SECRET_ENV = "CX_CLIENT_SECRET"

    @staticmethod
    def __secret(value: str | None, in_env: bool, env_var: str, label: str) -> str:
        """Resolves a secret from either a supplied value or an environment
        variable.

        :param value: The secret supplied on the command line.
        :type value: str | None

        :param in_env: True to read the secret from `env_var` instead of
                       using `value`.
        :type in_env: bool

        :param env_var: The environment variable holding the secret.
        :type env_var: str

        :param label: A description of the secret for error messages.
        :type label: str

        :return: The secret value.
        :rtype: str

        :raises AbortedConversionException: The secret is missing or empty.
        """
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
        """Builds the IAM and API endpoints from either an FQDN or a
        multi-tenant region moniker.  The FQDN takes precedence.

        :param fqdn: The hostname of the Checkmarx One deployment.
        :type fqdn: str | None

        :param region: A key of cxone-async-api's `ApiRegionEndpoints`.
        :type region: str | None

        :param tenant: The Checkmarx One tenant name.
        :type tenant: str

        :return: The IAM and API endpoints, or (None, None) if neither
                 `fqdn` nor `region` is supplied.
        :rtype: Tuple[CxOneAuthEndpoint, CxOneApiEndpoint]
        """
        if fqdn is not None and len(fqdn) > 0:
            return CxOneAuthEndpoint(tenant, fqdn), CxOneApiEndpoint(fqdn)
        elif region is not None and len(region) > 0:
            return AuthRegionEndpoints[region](tenant), ApiRegionEndpoints[region]()
        else:
            return None, None

    @staticmethod
    def __proxy(proxy_url: str | None) -> Dict[str, str] | None:
        """Builds the proxy mapping passed to the client.

        :param proxy_url: The URL of the HTTPS proxy.
        :type proxy_url: str | None

        :return: A scheme-to-URL mapping, or None if no proxy is supplied.
        :rtype: Dict[str, str] | None
        """
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
        """Creates a client that authenticates with an API key.

        :param api_key: The API key supplied on the command line.
        :type api_key: str | None

        :param apikey_in_env: True to read the API key from `API_KEY_ENV`.
        :type apikey_in_env: bool

        :param auth_endpoint: The Checkmarx One IAM endpoint.
        :type auth_endpoint: CxOneAuthEndpoint

        :param api_endpoint: The Checkmarx One API endpoint.
        :type api_endpoint: CxOneApiEndpoint

        :param proxy: A scheme-to-URL proxy mapping.
        :type proxy: Dict[str, str] | None

        :param ssl_verify: True to verify SSL certificates.
        :type ssl_verify: bool

        :param retries: The number of times a failed API call is retried.
        :type retries: int

        :return: A client authenticating with an API key.
        :rtype: CxOneRepoToolsClient

        :raises AbortedConversionException: The API key is missing or empty.
        """
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
        """Creates a client that authenticates with OAuth client credentials.

        :param oauth_client_id: The OAuth client ID.
        :type oauth_client_id: str

        :param oauth_client_secret: The OAuth client secret supplied on the
                                    command line.
        :type oauth_client_secret: str | None

        :param secret_in_env: True to read the client secret from
                              `CLIENT_SECRET_ENV`.
        :type secret_in_env: bool

        :param auth_endpoint: The Checkmarx One IAM endpoint.
        :type auth_endpoint: CxOneAuthEndpoint

        :param api_endpoint: The Checkmarx One API endpoint.
        :type api_endpoint: CxOneApiEndpoint

        :param proxy: A scheme-to-URL proxy mapping.
        :type proxy: Dict[str, str] | None

        :param ssl_verify: True to verify SSL certificates.
        :type ssl_verify: bool

        :param retries: The number of times a failed API call is retried.
        :type retries: int

        :return: A client authenticating with OAuth client credentials.
        :rtype: CxOneRepoToolsClient

        :raises AbortedConversionException: The client secret is missing or
                                            empty.
        """
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
    ) -> CxOneRepoToolsClient | None:
        """Creates a CxOneRepoToolsClient. OAuth client credentials are used when
        oauth_client_id is provided, otherwise an API key is used.

        :param api_key: The API key supplied on the command line.
        :type api_key: str | None

        :param apikey_in_env: True to read the API key from `API_KEY_ENV`.
        :type apikey_in_env: bool

        :param oauth_client_id: The OAuth client ID.
        :type oauth_client_id: str | None

        :param oauth_client_secret: The OAuth client secret supplied on the
                                    command line.
        :type oauth_client_secret: str | None

        :param secret_in_env: True to read the client secret from
                              `CLIENT_SECRET_ENV`.
        :type secret_in_env: bool

        :param fqdn: The hostname of the Checkmarx One deployment.  Takes
                     precedence over `region`.
        :type fqdn: str | None

        :param region: A key of cxone-async-api's `ApiRegionEndpoints`.
        :type region: str | None

        :param tenant: The Checkmarx One tenant name.
        :type tenant: str

        :param proxy_url: The URL of the HTTPS proxy.
        :type proxy_url: str | None

        :param ssl_verify: True to verify SSL certificates.
        :type ssl_verify: bool

        :param retries: The number of times a failed API call is retried.
        :type retries: int

        :return: The client, or None if neither OAuth client credentials nor
                 an API key are supplied.
        :rtype: CxOneRepoToolsClient | None

        :raises AbortedConversionException: The selected secret is missing or
                                            empty.
        """

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
