import unittest
from cxone_api import ApiRegionEndpoints, CxOneClient
from cxone_repo_tools.client import CxOneClientFactory, CxOneRepoToolsClient


def _client(*, fqdn=None, region=None, oauth=False) -> CxOneRepoToolsClient:
    return CxOneClientFactory.client_factory(
        None if oauth else "key",
        False,
        "client-id" if oauth else None,
        "secret" if oauth else None,
        False,
        fqdn,
        region,
        "tenant",
        None,
        True,
        3,
    )


class ClientFactoryTestCase(unittest.TestCase):

    def test_api_key_client_is_derived_type(self):
        client = _client(region="US")
        self.assertIsInstance(client, CxOneRepoToolsClient)
        self.assertIsInstance(client, CxOneClient)

    def test_oauth_client_is_derived_type(self):
        client = _client(region="US", oauth=True)
        self.assertIsInstance(client, CxOneRepoToolsClient)

    def test_region_moniker_is_multi_tenant(self):
        for region in ApiRegionEndpoints.keys():
            with self.subTest(region=region):
                self.assertFalse(_client(region=region).is_single_tenant)

    def test_fqdn_matching_regional_api_host_is_multi_tenant(self):
        self.assertFalse(_client(fqdn="eu.ast.checkmarx.net").is_single_tenant)
        self.assertFalse(_client(fqdn="EU.AST.Checkmarx.NET").is_single_tenant)

    def test_fqdn_matching_regional_iam_host_is_multi_tenant(self):
        self.assertFalse(_client(fqdn="iam.checkmarx.net").is_single_tenant)

    def test_fqdn_not_matching_region_is_single_tenant(self):
        self.assertTrue(_client(fqdn="cxone.example.com").is_single_tenant)
        self.assertTrue(_client(fqdn="cxone.example.com:8443").is_single_tenant)
        self.assertTrue(
            _client(fqdn="acme.ast.checkmarx.net", oauth=True).is_single_tenant
        )


if __name__ == "__main__":
    unittest.main()
