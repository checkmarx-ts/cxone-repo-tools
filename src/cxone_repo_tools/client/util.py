from cxone_api import ApiRegionEndpoints


def mt_endpoints() -> str:
    """Lists the multi-tenant region monikers defined by cxone-async-api.

    :return: The region monikers, sorted and comma-separated.
    :rtype: str
    """
    return ",".join(sorted(ApiRegionEndpoints.keys()))
