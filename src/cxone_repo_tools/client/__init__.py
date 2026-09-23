import os
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


def client_factory(
    api_key: str,
    use_env: bool,
    fqdn: str,
    region: str,
    tenant: str,
    proxy_url: str | None,
    ssl_verify: bool,
    retries: int,
):

    try:
        key = api_key if not use_env else os.environ["CX_API_KEY"]
    except KeyError as kex:
        key = None

    if key is None or len(key) == 0:
        raise ValueError("API Key was not provided.")

    if fqdn is not None and len(fqdn) > 0:
        api_endpoint = CxOneApiEndpoint(fqdn)
        auth_endpoint = CxOneAuthEndpoint(tenant, fqdn)
    elif region is not None and len(region) > 0:
        api_endpoint = ApiRegionEndpoints[region]()
        auth_endpoint = AuthRegionEndpoints[region](tenant)
    else:
        raise ValueError("Checkmarx One endpoints not defined.")

    if proxy_url is not None and len(proxy_url) > 0:
        proxy = {"https": proxy_url}
    else:
        proxy = None

    return CxOneClient.create_with_api_key(
        key,
        AGENT,
        auth_endpoint,
        api_endpoint,
        proxy=proxy,
        ssl_verify=ssl_verify,
        retries=retries,
    )
