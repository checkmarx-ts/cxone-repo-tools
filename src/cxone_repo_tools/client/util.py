from cxone_api import ApiRegionEndpoints


def mt_endpoints() -> str:
    return ",".join(sorted(ApiRegionEndpoints.keys()))
