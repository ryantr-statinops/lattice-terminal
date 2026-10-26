import unittest
import urllib.error
import io
import json
from unittest.mock import patch
from datetime import datetime, timezone
from kestrel_engine.providers import (
    ProviderRouter,
    ProviderRequestLimiter,
    retry_read,
    VndirectCommunityProvider,
    SyntheticFixtureProvider,
    SsiFastConnectProvider,
    DnseBrokerProvider,
    TcbsCommunityProvider,
    normalize_ssi_hose_equity_catalogue,
)

class TestProviders(unittest.TestCase):
    def test_ssi_hose_catalogue_normalizes_only_stock_security_types(self):
        payload = {
            'status': 'Success',
            'totalRecord': 4,
            'data': [{
                'RepeatedInfo': [
                    {'SecType': 'ST', 'Isin': 'vn000000aaa1', 'Symbol': 'aaa', 'SymbolName': 'Alpha JSC', 'Exchange': 'HOSE', 'LotSize': '100'},
                    {'SecType': 'CW', 'Isin': 'vn000000aaa2', 'Symbol': 'aaa1', 'SymbolName': 'Alpha warrant', 'Exchange': 'HOSE'},
                    {'SecType': 'FU', 'Symbol': 'VN30F1M', 'SymbolName': 'VN30 futures', 'Exchange': 'DER'},
                    {'Symbol': 'UNKNOWN', 'SymbolName': 'Unclassified security', 'Exchange': 'HOSE'},
                ],
            }],
        }

        instruments = normalize_ssi_hose_equity_catalogue(payload)

        self.assertEqual(len(instruments), 1)
        self.assertEqual(instruments[0].id, 'SSI:ISIN:VN000000AAA1')
        self.assertEqual(instruments[0].venue, 'HOSE')
        self.assertEqual(instruments[0].instrument_class, 'equity')
        self.assertEqual(instruments[0].metadata, {'isin': 'VN000000AAA1', 'lot_size': '100'})
        self.assertIsNone(instruments[0].currency)
        self.assertFalse(instruments[0].is_synthetic)

    def test_ssi_hose_catalogue_fails_closed_for_another_venue(self):
        with self.assertRaisesRegex(ValueError, 'another venue'):
            normalize_ssi_hose_equity_catalogue({
                'status': 'Success',
                'data': [{'SecType': 'ST', 'Symbol': 'ABC', 'Exchange': 'HNX'}],
            })

    def test_ssi_hose_catalogue_page_uses_documented_endpoint_and_paging(self):
        provider = SsiFastConnectProvider()
        credential = {'consumerID': 'test-id', 'consumerSecret': 'test-secret'}
        payload = {'status': 'Success', 'data': [{'SecType': 'ST', 'Symbol': 'AAA', 'Exchange': 'HOSE'}]}
        with patch.object(provider, 'get_json', return_value=payload) as get_json:
            instruments = provider.fetch_hose_equity_catalogue_page(2, credential=credential)

        get_json.assert_called_once_with(
            'SecuritiesDetails', {'market': 'HOSE', 'pageIndex': 2, 'pageSize': 1000}, credential=credential,
        )
        self.assertEqual([item.native_symbol for item in instruments], ['AAA'])

    def test_ssi_hose_catalogue_page_rejects_undocumented_page_range(self):
        provider = SsiFastConnectProvider()
        with patch.object(provider, 'get_json') as get_json:
            with self.assertRaisesRegex(ValueError, 'between 1 and 10'):
                provider.fetch_hose_equity_catalogue_page(11, credential={})
        get_json.assert_not_called()

    def test_read_retry_uses_exponential_backoff_for_transient_errors(self):
        operation = unittest.mock.Mock(side_effect=[
            urllib.error.URLError('temporary network failure'),
            TimeoutError('temporary timeout'),
            'read result',
        ])
        before_attempt = unittest.mock.Mock()
        with patch('kestrel_engine.providers.time.sleep') as sleep:
            result = retry_read(operation, before_attempt=before_attempt)
        self.assertEqual(result, 'read result')
        self.assertEqual(operation.call_count, 3)
        self.assertEqual(before_attempt.call_count, 3)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [0.25, 0.5])

    def test_read_retry_does_not_retry_non_transient_http_errors(self):
        unauthorized = urllib.error.HTTPError('https://provider.test/data', 401, 'unauthorized', None, None)
        operation = unittest.mock.Mock(side_effect=unauthorized)
        with patch('kestrel_engine.providers.time.sleep') as sleep:
            with self.assertRaises(urllib.error.HTTPError):
                retry_read(operation)
        operation.assert_called_once()
        sleep.assert_not_called()

    def test_provider_request_limiter_paces_requests_per_provider(self):
        limiter = ProviderRequestLimiter(0.5)
        clock_values = iter([100.0, 100.1, 100.5])
        with patch('kestrel_engine.providers.time.monotonic', side_effect=lambda: next(clock_values)):
            with patch('kestrel_engine.providers.time.sleep') as sleep:
                limiter.acquire()
                limiter.acquire()
        sleep.assert_called_once()
        self.assertAlmostEqual(sleep.call_args.args[0], 0.4)

    def test_provider_router_keeps_separate_request_limiters(self):
        router = ProviderRouter()
        self.assertIsNot(router.request_limiters['vndirect'], router.request_limiters['tcbs'])
        self.assertIs(router.providers['vndirect']._request_limiter, router.request_limiters['vndirect'])
        self.assertEqual(router.request_limiters['fixture'].minimum_interval_seconds, 0)
        self.assertEqual(router.request_limiters['vndirect'].minimum_interval_seconds, 1.0)

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

    def test_dataset_routing_requires_an_exact_implemented_capability(self):
        router = ProviderRouter()
        capability_id = 'vndirect:dchart-community:candles.1d:equity:HOSE'
        route = {'candles.1d:equity:HOSE': capability_id}
        updated = router.update_policy({'datasets': route})
        self.assertEqual(updated.datasets, route)

        with self.assertRaisesRegex(ValueError, 'does not match'):
            router.update_policy({'datasets': {'candles.1d:equity:HNX': capability_id}})
        with self.assertRaisesRegex(ValueError, 'no implemented adapter'):
            router.update_policy({'datasets': {
                'instruments.details:equity:unknown': 'ssi:market-data:instruments.details:equity:unknown',
            }})
        with self.assertRaisesRegex(ValueError, 'unknown dataset capability'):
            router.update_policy({'datasets': {'candles.1d:equity:HOSE': 'ssi:missing'}})
        with self.assertRaisesRegex(ValueError, 'dataset:asset_class:venue'):
            router.update_policy({'datasets': {'candles.1d': capability_id}})
        self.assertEqual(router.policy.datasets, route)

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

    def test_ssi_market_data_ping_requests_official_access_token(self):
        provider = SsiFastConnectProvider()
        provider.configure_credentials({'consumer_id': 'private-id', 'consumer_secret': 'private-secret'})
        response = io.BytesIO(b'{"status":200,"data":{"accessToken":"short-lived-token"}}')
        with patch('kestrel_engine.providers.urllib.request.urlopen', return_value=response) as open_url:
            status = provider.ping()
        self.assertEqual(status.state, 'connected')
        self.assertTrue(status.configured)
        self.assertEqual(provider.access_token, 'short-lived-token')
        request = open_url.call_args.args[0]
        self.assertEqual(request.full_url, 'https://fc-data.ssi.com.vn/api/v2/Market/AccessToken')
        self.assertEqual(json.loads(request.data), {'consumerID': 'private-id', 'consumerSecret': 'private-secret'})
        self.assertEqual(request.get_method(), 'POST')

    def test_ssi_authenticated_read_refreshes_token_once_after_unauthorized(self):
        provider = SsiFastConnectProvider()
        credential = {'consumerID': 'private-id', 'consumerSecret': 'private-secret'}
        expired = urllib.error.HTTPError('https://fc-data.ssi.com.vn/api/v2/Market/Securities', 401, 'expired', None, None)
        responses = [
            io.BytesIO(b'{"status":200,"data":{"accessToken":"token-one"}}'),
            expired,
            io.BytesIO(b'{"status":200,"data":{"accessToken":"token-two"}}'),
            io.BytesIO(b'{"status":"Success","data":[{"Symbol":"AAA"}]}'),
        ]
        with patch('kestrel_engine.providers.urllib.request.urlopen', side_effect=responses) as open_url:
            payload = provider.get_json('Securities', {'market': 'HOSE', 'pageIndex': 1}, credential=credential)

        self.assertEqual(payload['data'], [{'Symbol': 'AAA'}])
        calls = open_url.call_args_list
        self.assertEqual(len(calls), 4)
        self.assertEqual(calls[0].args[0].full_url, 'https://fc-data.ssi.com.vn/api/v2/Market/AccessToken')
        self.assertEqual(calls[1].args[0].get_header('Authorization'), 'Bearer token-one')
        self.assertEqual(calls[2].args[0].full_url, 'https://fc-data.ssi.com.vn/api/v2/Market/AccessToken')
        self.assertEqual(calls[3].args[0].get_header('Authorization'), 'Bearer token-two')
        self.assertEqual(provider.consumer_id, '')
        self.assertEqual(provider.consumer_secret, '')

    def test_ssi_authenticated_read_reports_failed_refresh_without_secret(self):
        provider = SsiFastConnectProvider()
        credential = {'consumerID': 'private-id', 'consumerSecret': 'private-secret'}
        expired_read = urllib.error.HTTPError('https://fc-data.ssi.com.vn/api/v2/Market/Securities', 401, 'expired', None, None)
        denied_refresh = urllib.error.HTTPError('https://fc-data.ssi.com.vn/api/v2/Market/AccessToken', 401, 'denied', None, None)
        responses = [io.BytesIO(b'{"status":200,"data":{"accessToken":"token-one"}}'), expired_read, denied_refresh]
        with patch('kestrel_engine.providers.urllib.request.urlopen', side_effect=responses):
            with self.assertRaisesRegex(ValueError, 'token refresh failed') as error:
                provider.get_json('Securities', credential=credential)
        self.assertNotIn('private-secret', str(error.exception))

    def test_ssi_authenticated_read_rejects_unknown_endpoint_before_network(self):
        provider = SsiFastConnectProvider()
        with patch('kestrel_engine.providers.urllib.request.urlopen', side_effect=AssertionError('network called')):
            with self.assertRaisesRegex(ValueError, 'invalid SSI market-data endpoint'):
                provider.get_json('https://example.test', credential={'consumerID':'id','consumerSecret':'secret'})

    def test_ssi_rejected_credentials_do_not_leak_and_listing_does_not_probe(self):
        provider = SsiFastConnectProvider()
        provider.configure_credentials({'consumerID': 'private-id', 'consumerSecret': 'private-secret'})
        denied = urllib.error.HTTPError('https://fc-data.ssi.com.vn/api/v2/Market/AccessToken', 401, 'denied', None, None)
        with patch('kestrel_engine.providers.urllib.request.urlopen', side_effect=denied):
            status = provider.ping()
        self.assertEqual(status.state, 'blocked')
        self.assertNotIn('private-secret', status.error)
        router = ProviderRouter()
        router.providers['ssi'].configure_credentials({'consumerID': 'private-id', 'consumerSecret': 'private-secret'})
        with patch('kestrel_engine.providers.urllib.request.urlopen', side_effect=AssertionError('provider listing made a network request')):
            listing = router.list_statuses()
        ssi = next(item for item in listing if item.id == 'ssi')
        self.assertEqual(ssi.state, 'unknown')
        self.assertTrue(ssi.configured)

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

    def test_capability_registry_uses_unique_service_dataset_class_venue_ids(self):
        items = ProviderRouter().capabilities.list()
        ids = [item.capability_id for item in items]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(item.asset_class != 'multiple' for item in items))
        self.assertTrue(all(item.capability_id.endswith(':' + item.venue) for item in items))
        tcbs_services = {item.service for item in items if item.provider_id == 'tcbs'}
        self.assertEqual(tcbs_services, {'community', 'openapi'})
        ssi_classes = {item.asset_class for item in items if item.provider_id == 'ssi'}
        self.assertEqual(ssi_classes, {'equity', 'covered_warrant', 'derivative', 'etf', 'bond', 'fund'})

if __name__ == '__main__':
    unittest.main()
