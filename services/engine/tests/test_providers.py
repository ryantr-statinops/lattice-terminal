import unittest
import urllib.error
import io
import json
from unittest.mock import patch
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo
from kestrel_engine.models import Instrument
from kestrel_engine.providers import (
    ProviderRouter,
    ProviderRequestLimiter,
    retry_read,
    VndirectCommunityProvider,
    SyntheticFixtureProvider,
    SsiFastConnectProvider,
    DnseBrokerProvider,
    TcbsCommunityProvider,
    normalize_ssi_index_catalogue,
    normalize_ssi_hose_equity_catalogue,
    normalize_ssi_hose_index_catalogue,
    normalize_ssi_hose_index_components,
)

class TestProviders(unittest.TestCase):
    def test_ssi_hose_index_components_preserve_provider_identifier_without_calling_it_isin(self):
        provider = SsiFastConnectProvider()
        index = Instrument(
            id='SSI:INDEX:HOSE:VN30', venue='HOSE', board='unknown', native_symbol='VN30',
            instrument_class='index', name='VN30', source_id='SSI-FC-DATA', is_synthetic=False,
        )
        index_row = {
            'IndexCode': 'VN30', 'IndexName': 'VN30', 'Exchange': 'HOSE', 'TotalSymbolNo': 1,
            'IndexComponent': [{'Isin': 'ACB', 'StockSymbol': 'ACB'}],
        }
        response = {'status': 'Success', 'totalRecord': 2, 'data': [index_row, index_row]}
        with patch.object(provider, 'get_json', return_value=response) as get_json:
            constituents = provider.fetch_hose_index_components(index, credential={'consumerID': 'id', 'consumerSecret': 'secret'})

        get_json.assert_called_once_with('IndexComponents', {
            'indexCode': 'VN30', 'pageIndex': 1, 'pageSize': 1000,
        }, credential={'consumerID': 'id', 'consumerSecret': 'secret'})
        self.assertEqual(constituents.index_instrument_id, index.id)
        self.assertEqual(constituents.reported_total_symbol_count, 1)
        self.assertEqual(len(constituents.constituents), 1)
        self.assertEqual(constituents.constituents[0].provider_security_id, 'ACB')
        self.assertEqual(constituents.constituents[0].native_symbol, 'ACB')
        self.assertTrue(constituents.observed_at.tzinfo)

    def test_ssi_hose_index_components_reject_another_index(self):
        index = Instrument(
            id='SSI:INDEX:HOSE:VN30', venue='HOSE', board='unknown', native_symbol='VN30',
            instrument_class='index', name='VN30', source_id='SSI-FC-DATA', is_synthetic=False,
        )
        with self.assertRaisesRegex(ValueError, 'does not match'):
            normalize_ssi_hose_index_components([{
                'IndexCode': 'VN100', 'IndexName': 'VN100', 'Exchange': 'HOSE',
                'TotalSymbolNo': 1, 'IndexComponent': [{'StockSymbol': 'ACB'}],
            }], index, datetime.now(timezone.utc))

    def test_ssi_hose_daily_index_preserves_daily_metrics_and_unzoned_provider_time(self):
        provider = SsiFastConnectProvider()
        index = Instrument(
            id='SSI:INDEX:HOSE:VN30', venue='HOSE', board='unknown', native_symbol='VN30',
            instrument_class='index', name='VN30', source_id='SSI-FC-DATA', is_synthetic=False,
        )
        row = {
            'IndexId': 'VN30', 'IndexValue': '1320.50', 'TradingDate': '02/01/2025', 'Time': None,
            'Change': '-1.25', 'RatioChange': '-0.09', 'TotalTrade': '123',
            'TotalMatchVol': '84693600', 'TotalMatchVal': '1836008470000', 'TypeIndex': None,
            'IndexName': 'VN30', 'Advances': '21', 'NoChanges': '4', 'Declines': '5',
            'Ceilings': '2', 'Floors': '0', 'TotalDealVol': '2504000', 'TotalDealVal': '60256000000',
            'TotalVol': '87197600', 'TotalVal': '1896264470000', 'TradingSession': 'C',
        }
        with patch.object(provider, 'get_json', return_value={'status': 'Success', 'totalRecord': 1, 'data': [row]}) as get_json:
            observations = provider.fetch_hose_daily_index(
                index, date(2025, 1, 2), date(2025, 1, 2), credential={'consumerID': 'id', 'consumerSecret': 'secret'},
            )

        get_json.assert_called_once_with('DailyIndex', {
            'indexId': 'VN30', 'fromDate': '02/01/2025', 'toDate': '02/01/2025',
            'pageIndex': 1, 'pageSize': 1000, 'ascending': 'true',
        }, credential={'consumerID': 'id', 'consumerSecret': 'secret'})
        observation = observations[0]
        self.assertEqual(observation.trading_date, date(2025, 1, 2))
        self.assertEqual(observation.index_value, '1320.50')
        self.assertEqual(observation.change, '-1.25')
        self.assertIsNone(observation.provider_time)
        self.assertEqual(observation.total_match_value, '1836008470000')
        self.assertEqual(observation.field_units['total_match_value'], 'provider_native_value_currency_unverified')

    def test_ssi_hose_daily_index_rejects_wrong_index_and_incomplete_time_range(self):
        provider = SsiFastConnectProvider()
        index = Instrument(
            id='SSI:INDEX:HOSE:VN30', venue='HOSE', board='unknown', native_symbol='VN30',
            instrument_class='index', name='VN30', source_id='SSI-FC-DATA', is_synthetic=False,
        )
        with self.assertRaisesRegex(ValueError, 'before the current Vietnam date'):
            provider.fetch_hose_daily_index(
                index, datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).date(),
                datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).date(), credential={},
            )
        with patch.object(provider, 'get_json', return_value={'status': 'Success', 'totalRecord': 1, 'data': [{
            'IndexId': 'HNX30', 'IndexValue': '1', 'TradingDate': '02/01/2025',
        }]}):
            with self.assertRaisesRegex(ValueError, 'does not match'):
                provider.fetch_hose_daily_index(
                    index, date(2025, 1, 2), date(2025, 1, 2), credential={},
                )

    def test_ssi_hose_index_catalogue_paginates_and_preserves_index_class(self):
        provider = SsiFastConnectProvider()
        rows = [
            {'IndexCode': f'IDX{index:04d}', 'IndexName': f'Index {index}', 'Exchange': 'HOSE'}
            for index in range(1001)
        ]
        pages = [
            {'status': 'Success', 'totalRecord': 1001, 'data': rows[:1000]},
            {'status': 'Success', 'totalRecord': 1001, 'data': rows[1000:]},
        ]
        with patch.object(provider, 'get_json', side_effect=pages) as get_json:
            instruments = provider.fetch_hose_index_catalogue(credential={'consumerID': 'id', 'consumerSecret': 'secret'})

        self.assertEqual(len(instruments), 1001)
        self.assertEqual(instruments[0].id, 'SSI:INDEX:HOSE:IDX0000')
        self.assertEqual(instruments[0].instrument_class, 'index')
        self.assertEqual(instruments[0].metadata, {'index_code': 'IDX0000', 'exchange': 'HOSE'})
        self.assertEqual(get_json.call_count, 2)
        self.assertEqual(get_json.call_args_list[0].args, ('IndexList', {
            'exchange': 'HOSE', 'pageIndex': 1, 'pageSize': 1000,
        }))
        self.assertEqual(get_json.call_args_list[1].args[1]['pageIndex'], 2)

    def test_ssi_hose_index_normalizer_rejects_other_exchange(self):
        with self.assertRaisesRegex(ValueError, 'another exchange'):
            normalize_ssi_hose_index_catalogue([{
                'IndexCode': 'HNX30', 'IndexName': 'HNX 30', 'Exchange': 'HNX',
            }])

    def test_ssi_hnx_index_catalogue_keeps_hnx_scope_and_index_identity(self):
        provider = SsiFastConnectProvider()
        rows = [
            {'IndexCode': f'HNXIDX{index:04d}', 'IndexName': f'HNX Index {index}', 'Exchange': 'HNX'}
            for index in range(1001)
        ]
        pages = [
            {'status': 'Success', 'totalRecord': 1001, 'data': rows[:1000]},
            {'status': 'Success', 'totalRecord': 1001, 'data': rows[1000:]},
        ]
        with patch.object(provider, 'get_json', side_effect=pages) as get_json:
            instruments = provider.fetch_hnx_index_catalogue(credential={'consumerID': 'id', 'consumerSecret': 'secret'})
        self.assertEqual(len(instruments), 1001)
        self.assertEqual(get_json.call_args_list[0].args, ('IndexList', {'exchange': 'HNX', 'pageIndex': 1, 'pageSize': 1000}))
        self.assertEqual(get_json.call_args_list[1].args[1]['pageIndex'], 2)
        self.assertEqual(instruments[0].id, 'SSI:INDEX:HNX:HNXIDX0000')
        self.assertEqual(instruments[0].venue, 'HNX')
        self.assertEqual(instruments[0].instrument_class, 'index')
        self.assertEqual(instruments[0].metadata, {'index_code': 'HNXIDX0000', 'exchange': 'HNX'})
        with self.assertRaisesRegex(ValueError, 'another exchange'):
            normalize_ssi_index_catalogue([{'IndexCode': 'VN30', 'IndexName': 'VN30', 'Exchange': 'HOSE'}], 'HNX')

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

    def test_ssi_hose_catalogue_reads_each_documented_page(self):
        provider = SsiFastConnectProvider()
        credential = {'consumerID': 'test-id', 'consumerSecret': 'test-secret'}
        first = {'status': 'Success', 'totalRecord': 1001, 'data': [{'SecType': 'ST', 'Symbol': 'AAA', 'Exchange': 'HOSE'}]}
        second = {'status': 'Success', 'data': [{'SecType': 'ST', 'Symbol': 'BBB', 'Exchange': 'HOSE'}]}
        with patch.object(provider, 'get_json', side_effect=[first, second]) as get_json:
            instruments = provider.fetch_hose_equity_catalogue(credential=credential)

        self.assertEqual([item.native_symbol for item in instruments], ['AAA', 'BBB'])
        self.assertEqual(get_json.call_count, 2)
        self.assertEqual(get_json.call_args_list[0].args, ('SecuritiesDetails', {
            'market': 'HOSE', 'pageIndex': 1, 'pageSize': 1000,
        }))
        self.assertEqual(get_json.call_args_list[1].args, ('SecuritiesDetails', {
            'market': 'HOSE', 'pageIndex': 2, 'pageSize': 1000,
        }))

    def test_ssi_hose_catalogue_refuses_to_exceed_ten_pages(self):
        provider = SsiFastConnectProvider()
        first = {'status': 'Success', 'totalRecord': 10001, 'data': []}
        with patch.object(provider, 'get_json', return_value=first) as get_json:
            with self.assertRaisesRegex(ValueError, '10-page limit'):
                provider.fetch_hose_equity_catalogue(credential={})
        get_json.assert_called_once()

    def test_ssi_daily_ohlc_pages_and_preserves_exact_provider_decimals(self):
        provider = SsiFastConnectProvider()
        instrument = Instrument(
            id='SSI:ISIN:VN000000AAA1', venue='HOSE', board='unknown', native_symbol='AAA',
            instrument_class='equity', name='Alpha JSC', source_id='SSI-FC-DATA', is_synthetic=False,
        )
        start = date(2022, 1, 1)
        end = datetime.now(timezone.utc).astimezone(ZoneInfo('Asia/Ho_Chi_Minh')).date() - timedelta(days=1)
        all_rows = [{
            'Symbol': 'AAA', 'Market': 'HOSE', 'TradingDate': (start + timedelta(days=index)).strftime('%d/%m/%Y'),
            'Open': '28600.0000', 'High': '28850.0000', 'Low': '28100.0000',
            'Close': '28100.0000', 'Volume': '23382100', 'Value': '663258204999.9850',
        } for index in range(1001)]
        pages = [
            {'status': 'Success', 'totalRecord': 1001, 'data': all_rows[:1000]},
            {'status': 'Success', 'totalRecord': 1001, 'data': all_rows[1000:]},
        ]
        with patch.object(provider, 'get_json', side_effect=pages) as get_json:
            candles = provider.fetch_hose_equity_daily(
                instrument, start, end, credential={'consumerID': 'id', 'consumerSecret': 'secret'},
            )

        self.assertEqual(len(candles), 1001)
        self.assertEqual(candles[0].open, '28600.0000')
        self.assertEqual(candles[0].volume, '23382100')
        self.assertEqual(candles[0].price_unit, 'unknown')
        self.assertEqual(candles[0].currency, 'unknown')
        self.assertEqual(candles[0].open_time, datetime(2021, 12, 31, 17, tzinfo=timezone.utc))
        self.assertEqual(get_json.call_count, 2)
        self.assertEqual(get_json.call_args_list[0].args, ('DailyOhlc', {
            'symbol': 'AAA', 'fromDate': '01/01/2022', 'toDate': end.strftime('%d/%m/%Y'),
            'pageIndex': 1, 'pageSize': 1000, 'ascending': 'true',
        }))
        self.assertEqual(get_json.call_args_list[1].args[1]['pageIndex'], 2)

    def test_ssi_daily_ohlc_rejects_out_of_scope_instrument_before_network(self):
        provider = SsiFastConnectProvider()
        instrument = Instrument(
            id='SSI:DER:FU1', venue='DER', board='unknown', native_symbol='FU1',
            instrument_class='derivative', name='Future', source_id='SSI-FC-DATA', is_synthetic=False,
        )
        with patch.object(provider, 'get_json') as get_json:
            with self.assertRaisesRegex(ValueError, 'only supports HOSE equity'):
                provider.fetch_hose_equity_daily(instrument, date(2025, 1, 1), date(2025, 1, 2), credential={})
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
        ssi_catalogue = {'instruments.details:equity:HOSE': 'ssi:market-data:instruments.details:equity:HOSE'}
        self.assertEqual(router.update_policy({'datasets': ssi_catalogue}).datasets, ssi_catalogue)
        with self.assertRaisesRegex(ValueError, 'unknown dataset capability'):
            router.update_policy({'datasets': {'candles.1d:equity:HOSE': 'ssi:missing'}})
        with self.assertRaisesRegex(ValueError, 'dataset:asset_class:venue'):
            router.update_policy({'datasets': {'candles.1d': capability_id}})
        self.assertEqual(router.policy.datasets, ssi_catalogue)

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

    def test_ssi_authenticated_read_parses_fractional_numbers_as_decimal(self):
        provider = SsiFastConnectProvider()
        credential = {'consumerID': 'id', 'consumerSecret': 'secret'}
        provider.configure_credentials(credential)
        provider.access_token = 'token'
        with patch('kestrel_engine.providers.urllib.request.urlopen', return_value=io.BytesIO(
            b'{"status":"Success","data":[{"Open":28600.1250}]}'
        )):
            payload = provider.get_json('DailyOhlc', credential=credential)
        self.assertEqual(payload['data'][0]['Open'], Decimal('28600.1250'))

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
        self.assertEqual(ssi_classes, {'equity', 'index', 'covered_warrant', 'derivative', 'etf', 'bond', 'fund'})

if __name__ == '__main__':
    unittest.main()
