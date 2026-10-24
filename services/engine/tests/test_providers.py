import unittest
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

if __name__ == '__main__':
    unittest.main()
