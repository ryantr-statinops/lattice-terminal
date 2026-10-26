import unittest
from unittest.mock import patch
from datetime import datetime, timezone
from kestrel_engine.providers import (
    ProviderRouter,
    VndirectCommunityProvider,
    SyntheticFixtureProvider,
    SsiFastConnectProvider,
    DnseBrokerProvider,
    TcbsCommunityProvider,
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

    def test_routing_policy_rejects_provider_without_role_coverage(self):
        router = ProviderRouter()
        with self.assertRaisesRegex(ValueError, 'does not declare realtime_provider coverage'):
            router.update_policy({'realtime_provider': 'tcbs'})
        self.assertEqual(router.policy.realtime_provider, 'fixture')
        with self.assertRaisesRegex(ValueError, 'unknown provider for historical_provider'):
            router.update_policy({'historical_provider': 'unknown-provider'})
        self.assertEqual(router.policy.historical_provider, 'vndirect')

    def test_routing_policy_accepts_declared_provider_role_coverage(self):
        router = ProviderRouter()
        updated = router.update_policy({
            'historical_provider': 'fixture',
            'realtime_provider': 'dnse',
            'financials_provider': 'tcbs',
        })
        self.assertEqual(updated.historical_provider, 'fixture')
        self.assertEqual(updated.realtime_provider, 'dnse')
        self.assertEqual(updated.financials_provider, 'tcbs')

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

    def test_tcbs_does_not_return_vndirect_data_under_tcbs_identity(self):
        provider = TcbsCommunityProvider()
        with patch.object(VndirectCommunityProvider, 'fetch_candles', side_effect=AssertionError('fallback called')):
            with self.assertRaisesRegex(NotImplementedError, 'refusing to return VNDIRECT data'):
                provider.fetch_candles('HPG', '1d', datetime.now(timezone.utc), datetime.now(timezone.utc))
        with patch.object(VndirectCommunityProvider, 'fetch_instruments', side_effect=AssertionError('fallback called')):
            with self.assertRaisesRegex(NotImplementedError, 'refusing to return VNDIRECT instruments'):
                provider.fetch_instruments()

    def test_vndirect_rejects_unsupported_interval_without_requesting_daily(self):
        provider = VndirectCommunityProvider()
        with patch('kestrel_engine.providers.urllib.request.urlopen', side_effect=AssertionError('request sent')):
            with self.assertRaisesRegex(ValueError, 'does not support candle interval: 5m'):
                provider.fetch_candles('HPG', '5m', datetime.now(timezone.utc), datetime.now(timezone.utc))

    def test_capability_registry_separates_documentation_implementation_and_rights(self):
        registry = ProviderRouter().capabilities
        vndirect_daily = next(
            item for item in registry.list()
            if item.provider_id == 'vndirect' and item.dataset == 'candles.1d'
        )
        self.assertFalse(vndirect_daily.documented)
        self.assertTrue(vndirect_daily.implemented)
        self.assertEqual(vndirect_daily.rights_state, 'unverified')

if __name__ == '__main__':
    unittest.main()
