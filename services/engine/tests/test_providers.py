import unittest
from unittest.mock import patch
from datetime import datetime, timezone
from kestrel_engine.providers import (
    ProviderRouter,
    VndirectCommunityProvider,
    SyntheticFixtureProvider,
    SsiFastConnectProvider,
    DnseBrokerProvider,
)

class TestProviders(unittest.TestCase):
    def test_provider_router_registration_and_statuses(self):
        router = ProviderRouter()
        self.assertIn('vndirect', router.providers)
        self.assertIn('tcbs', router.providers)
        self.assertIn('dnse', router.providers)
        self.assertIn('ssi', router.providers)
        self.assertIn('fixture', router.providers)

        fixture_status = router.ping('fixture')
        self.assertEqual(fixture_status.id, 'fixture')
        self.assertEqual(fixture_status.state, 'fixture')

        ssi_status = router.ping('ssi')
        self.assertEqual(ssi_status.id, 'ssi')
        self.assertEqual(ssi_status.state, 'blocked')

    def test_routing_policy_update(self):
        router = ProviderRouter()
        self.assertEqual(router.policy.historical_provider, 'vndirect')
        self.assertTrue(router.policy.fallback_enabled)

        updated = router.update_policy({'historical_provider': 'tcbs', 'fallback_enabled': False})
        self.assertEqual(updated.historical_provider, 'tcbs')
        self.assertFalse(updated.fallback_enabled)

    def test_fixture_provider_lifecycle(self):
        p = SyntheticFixtureProvider()
        status = p.ping()
        self.assertEqual(status.state, 'fixture')
        self.assertTrue(status.configured)

    def test_dnse_provider_unconfigured(self):
        p = DnseBrokerProvider()
        status = p.ping()
        self.assertEqual(status.state, 'blocked')
        self.assertFalse(status.configured)
        with self.assertRaises(ValueError):
            p.fetch_candles('HPG', '1d', datetime.now(timezone.utc), datetime.now(timezone.utc))

    def test_dnse_credentials_do_not_imply_connected(self):
        p = DnseBrokerProvider(api_key='configured-key', api_secret='configured-secret')
        status = p.ping()
        self.assertEqual(status.state, 'blocked')
        self.assertTrue(status.configured)
        self.assertIsNone(status.latency_ms)
        self.assertIn('connectivity is unverified', status.error)

    def test_listing_providers_does_not_probe_external_network(self):
        router = ProviderRouter()
        with patch.object(VndirectCommunityProvider, 'ping', side_effect=AssertionError('network probe called')):
            statuses = router.list_statuses()
        vndirect = next(status for status in statuses if status.id == 'vndirect')
        tcbs = next(status for status in statuses if status.id == 'tcbs')
        self.assertEqual(vndirect.state, 'unknown')
        self.assertEqual(tcbs.state, 'unknown')
        self.assertIsNone(vndirect.latency_ms)

if __name__ == '__main__':
    unittest.main()
