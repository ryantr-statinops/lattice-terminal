"""SSI market-data normalization and adapter."""
"""Multi-provider abstractions for market data feeds (VNDIRECT, TCBS, DNSE, SSI, Local, Fixture)."""
from abc import ABC, abstractmethod
from datetime import date, datetime, time as daytime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import threading
import time
from typing import Any, Callable, Literal
import urllib.error
from urllib.parse import urlencode
import urllib.request
from pydantic import BaseModel, Field

from zoneinfo import ZoneInfo
from ..models import Candle, DailyIndexObservation, IndexConstituentSet, Instrument, ProviderIndexConstituent, decimal_text

from .base import BaseMarketProvider, ProviderProbe, ProviderStatus

def _normalize_ssi_security_catalogue(
    payload: dict[str, Any], venue: str, security_types: set[str], instrument_class: str,
) -> list[Instrument]:
    """Normalize one documented SSI security class and exchange combination."""
    venue = venue.strip().upper()
    if venue not in {'HOSE', 'HNX', 'UPCOM', 'HNXBOND', 'DER'}:
        raise ValueError('SSI security catalogue venue is not supported')
    status = str(payload.get('status', '')).strip().casefold()
    if status not in {'success', '200'}:
        raise ValueError('SSI returned an unsuccessful SecuritiesDetails response')
    data = payload.get('data')
    if not isinstance(data, list):
        raise ValueError('SSI SecuritiesDetails data must be a list')

    details: list[dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict):
            raise ValueError('SSI SecuritiesDetails row must be an object')
        nested = item.get('RepeatedInfo') or item.get('repeatedinfoList') or item.get('RepeatedInfoList')
        if nested is None:
            details.append(item)
        elif isinstance(nested, list):
            if any(not isinstance(value, dict) for value in nested):
                raise ValueError('SSI repeated security details must be objects')
            details.extend(nested)
        else:
            raise ValueError('SSI repeated security details must be a list')

    instruments: dict[str, Instrument] = {}
    for detail in details:
        security_type = str(detail.get('SecType') or '').strip().upper()
        if security_type not in security_types:
            continue
        exchange = str(detail.get('Exchange') or detail.get('MarketId') or detail.get('Market') or '').strip().upper()
        if exchange != venue:
            raise ValueError(f'SSI {venue} catalogue contained a security from another venue or without a venue')
        symbol = str(detail.get('Symbol') or '').strip().upper()
        if not symbol:
            kind = 'stock' if instrument_class == 'equity' else 'security'
            raise ValueError(f'SSI {venue} {kind} is missing its symbol')
        isin = str(detail.get('Isin') or '').strip().upper()
        fallback_kind = '' if instrument_class == 'equity' else f'{instrument_class.upper()}:'
        instrument_id = f'SSI:ISIN:{isin}' if isin else f'SSI:{venue}:{fallback_kind}{symbol}'
        name = str(detail.get('SymbolName') or detail.get('SymbolEngName') or symbol).strip()
        metadata_fields = (
            ('Issuer', 'issuer'), ('LotSize', 'lot_size'),
            ('IssueDate', 'issue_date'), ('FirstTradingDate', 'first_trading_date'),
            ('LastTradingDate', 'last_trading_date'), ('MaturityDate', 'maturity_date'),
            ('ContractMultiplier', 'contract_multiplier'), ('SettlMethod', 'settlement_method'),
            ('Underlying', 'underlying'), ('PutOrCall', 'put_or_call'),
            ('ExercisePrice', 'exercise_price'), ('ExerciseStyle', 'exercise_style'),
            ('ExcerciseRatio', 'exercise_ratio'), ('ListedShare', 'listed_share'),
            ('TickPrice1', 'tick_price_1'), ('TickIncrement1', 'tick_increment_1'),
            ('TickPrice2', 'tick_price_2'), ('TickIncrement2', 'tick_increment_2'),
            ('TickPrice3', 'tick_price_3'), ('TickIncrement3', 'tick_increment_3'),
            ('TickPrice4', 'tick_price_4'), ('TickIncrement4', 'tick_increment_4'),
        )
        if instrument_class == 'equity':
            metadata_fields = tuple(
                (source, key) for source, key in metadata_fields
                if source in {'Issuer', 'LotSize', 'IssueDate', 'FirstTradingDate', 'LastTradingDate', 'ListedShare'}
            )
        metadata = {key: str(detail[source]) for source, key in metadata_fields if detail.get(source) not in (None, '')}
        if isin:
            metadata['isin'] = isin
        instrument = Instrument(
            id=instrument_id, venue=venue, board='unknown', native_symbol=symbol,
            instrument_class=instrument_class, name=name, metadata=metadata,
            source_id='SSI-FC-DATA', is_synthetic=False,
        )
        previous = instruments.get(instrument.id)
        if previous is not None and previous != instrument:
            kind = 'stock' if instrument_class == 'equity' else 'security'
            raise ValueError(f'SSI {venue} catalogue has conflicting {kind} identities')
        instruments[instrument.id] = instrument
    return sorted(instruments.values(), key=lambda value: (value.native_symbol, value.id))


def normalize_ssi_equity_catalogue(payload: dict[str, Any], venue: str) -> list[Instrument]:
    return _normalize_ssi_security_catalogue(payload, venue, {'ST', 'S'}, 'equity')


def normalize_ssi_hose_covered_warrant_catalogue(payload: dict[str, Any]) -> list[Instrument]:
    return _normalize_ssi_security_catalogue(payload, 'HOSE', {'CW'}, 'covered_warrant')


def normalize_ssi_der_derivative_catalogue(payload: dict[str, Any]) -> list[Instrument]:
    return _normalize_ssi_security_catalogue(payload, 'DER', {'FU'}, 'derivative')


def normalize_ssi_hose_etf_catalogue(payload: dict[str, Any]) -> list[Instrument]:
    return _normalize_ssi_security_catalogue(payload, 'HOSE', {'EF'}, 'etf')


def normalize_ssi_hnxbond_bond_catalogue(payload: dict[str, Any]) -> list[Instrument]:
    return _normalize_ssi_security_catalogue(payload, 'HNXBOND', {'BO'}, 'bond')


def normalize_ssi_hose_equity_catalogue(payload: dict[str, Any]) -> list[Instrument]:
    return normalize_ssi_equity_catalogue(payload, 'HOSE')


def normalize_ssi_hnx_equity_catalogue(payload: dict[str, Any]) -> list[Instrument]:
    return normalize_ssi_equity_catalogue(payload, 'HNX')


def normalize_ssi_upcom_equity_catalogue(payload: dict[str, Any]) -> list[Instrument]:
    return normalize_ssi_equity_catalogue(payload, 'UPCOM')


def normalize_ssi_index_catalogue(rows: list[dict[str, Any]], exchange: str) -> list[Instrument]:
    """Normalize an SSI IndexList page without treating indexes as equities."""
    exchange = exchange.strip().upper()
    if exchange not in {'HOSE', 'HNX'}:
        raise ValueError('SSI IndexList adapter supports only HOSE and HNX indexes')
    instruments: dict[str, Instrument] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('SSI IndexList row must be an object')
        row_exchange = str(row.get('Exchange') or '').strip().upper()
        if row_exchange != exchange:
            raise ValueError(f'SSI {exchange} IndexList contained an index from another exchange')
        code = str(row.get('IndexCode') or '').strip().upper()
        name = str(row.get('IndexName') or '').strip()
        if not code or not name:
            raise ValueError(f'SSI {exchange} IndexList index code and name are required')
        instrument = Instrument(
            id=f'SSI:INDEX:{exchange}:{code}', venue=exchange, board='unknown',
            native_symbol=code, instrument_class='index', name=name,
            metadata={'index_code': code, 'exchange': row_exchange},
            source_id='SSI-FC-DATA', is_synthetic=False,
        )
        previous = instruments.get(instrument.id)
        if previous is not None and previous != instrument:
            raise ValueError(f'SSI {exchange} IndexList contains conflicting index identities')
        instruments[instrument.id] = instrument
    return sorted(instruments.values(), key=lambda value: (value.native_symbol, value.id))


def normalize_ssi_hose_index_catalogue(rows: list[dict[str, Any]]) -> list[Instrument]:
    """Normalize the SSI HOSE index catalogue."""
    return normalize_ssi_index_catalogue(rows, 'HOSE')


def normalize_ssi_hose_index_components(
    rows: list[dict[str, Any]], index: Instrument, observed_at: datetime,
) -> IndexConstituentSet:
    """Preserve the provider's observed membership set without inferring an ISIN or effective date."""
    if index.instrument_class != 'index' or index.venue != 'HOSE':
        raise ValueError('SSI IndexComponents adapter only supports HOSE indexes')
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise ValueError('SSI IndexComponents observation time must include a timezone')
    reported_total: int | None = None
    index_name = ''
    members: dict[str, ProviderIndexConstituent] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('SSI IndexComponents row must be an object')
        code = str(row.get('IndexCode') or '').strip().upper()
        exchange = str(row.get('Exchange') or '').strip().upper()
        if code != index.native_symbol.upper() or exchange != 'HOSE':
            raise ValueError('SSI IndexComponents response does not match the requested HOSE index')
        current_total = row.get('TotalSymbolNo')
        if isinstance(current_total, bool) or not isinstance(current_total, (int, str)):
            raise ValueError('SSI IndexComponents has an invalid TotalSymbolNo')
        try:
            current_total = int(current_total)
        except (TypeError, ValueError) as error:
            raise ValueError('SSI IndexComponents has an invalid TotalSymbolNo') from error
        if current_total < 0 or (reported_total is not None and reported_total != current_total):
            raise ValueError('SSI IndexComponents TotalSymbolNo changed within the response')
        reported_total = current_total
        current_name = str(row.get('IndexName') or '').strip()
        if index_name and current_name and index_name != current_name:
            raise ValueError('SSI IndexComponents index name changed within the response')
        if current_name:
            index_name = current_name
        components = row.get('IndexComponent')
        if not isinstance(components, list) or any(not isinstance(value, dict) for value in components):
            raise ValueError('SSI IndexComponents member list is invalid')
        for component in components:
            symbol = str(component.get('StockSymbol') or '').strip().upper()
            if not symbol:
                raise ValueError('SSI IndexComponents member is missing StockSymbol')
            raw_security_id = component.get('Isin')
            provider_security_id = None if raw_security_id in (None, '') else str(raw_security_id).strip()
            if provider_security_id == '':
                provider_security_id = None
            member = ProviderIndexConstituent(
                provider_security_id=provider_security_id,
                native_symbol=symbol,
            )
            previous_member = members.get(member.native_symbol)
            if previous_member is not None and previous_member != member:
                raise ValueError('SSI IndexComponents contains conflicting identifiers for one member symbol')
            members[member.native_symbol] = member
    if reported_total is None or not index_name:
        raise ValueError('SSI IndexComponents response is empty or incomplete')
    return IndexConstituentSet(
        index_instrument_id=index.id,
        index_code=index.native_symbol,
        index_name=index_name,
        exchange='HOSE',
        reported_total_symbol_count=reported_total,
        constituents=sorted(members.values(), key=lambda value: value.native_symbol),
        source_id='SSI-FC-DATA',
        observed_at=observed_at,
    )


def _normalize_ssi_daily_index_rows(
    rows: list[dict[str, Any]], index: Instrument, venue: str, start: date, end: date, observed_at: datetime,
) -> list[DailyIndexObservation]:
    """Normalize SSI DailyIndex records while retaining provider-local time without a timezone guess."""
    if venue not in {'HOSE', 'HNX'} or index.instrument_class != 'index' or index.venue != venue:
        raise ValueError(f'SSI DailyIndex adapter only supports {venue} indexes')
    if start > end:
        raise ValueError('SSI DailyIndex date range is invalid')
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise ValueError('SSI DailyIndex observation time must include a timezone')

    def get(row: dict[str, Any], *names: str) -> Any:
        fields = {''.join(char for char in key.casefold() if char.isalnum()): value for key, value in row.items()}
        for name in names:
            normalized = ''.join(char for char in name.casefold() if char.isalnum())
            if normalized in fields:
                return fields[normalized]
        return None

    def required_decimal(row: dict[str, Any], field: str, *names: str) -> str:
        value = get(row, *names)
        if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
            raise ValueError(f'SSI DailyIndex {field} must be an exact decimal value')
        result = format(value, 'f') if isinstance(value, Decimal) else str(value).strip()
        decimal_text(result)
        return result

    def optional_decimal(row: dict[str, Any], field: str, *names: str) -> str | None:
        value = get(row, *names)
        if value is None or value == '':
            return None
        return required_decimal(row, field, *names)

    def optional_text(row: dict[str, Any], field: str, *names: str) -> str | None:
        value = get(row, *names)
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError(f'SSI DailyIndex {field} must be text')
        return value.strip() or None

    observations: dict[date, DailyIndexObservation] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('SSI DailyIndex row must be an object')
        code = optional_text(row, 'index code', 'IndexId', 'IndexCode', 'Indexcode')
        if code is None or code.upper() != index.native_symbol.upper():
            raise ValueError(f'SSI DailyIndex row does not match the requested {venue} index')
        market = optional_text(row, 'market', 'Market')
        exchange = optional_text(row, 'exchange', 'Exchange')
        if (market and market.upper() != venue) or (exchange and exchange.upper() != venue):
            raise ValueError(f'SSI DailyIndex row does not match the requested {venue} venue')
        raw_date = optional_text(row, 'trading date', 'TradingDate', 'Trading Date')
        if raw_date is None:
            raise ValueError('SSI DailyIndex TradingDate must use dd/mm/yyyy')
        try:
            trading_date = datetime.strptime(raw_date, '%d/%m/%Y').date()
        except ValueError as error:
            raise ValueError('SSI DailyIndex TradingDate must use dd/mm/yyyy') from error
        if trading_date < start or trading_date > end:
            raise ValueError('SSI DailyIndex returned a row outside the requested date range')

        observation = DailyIndexObservation(
            index_instrument_id=index.id, index_code=index.native_symbol, exchange=venue,
            trading_date=trading_date, provider_time=optional_text(row, 'time', 'Time'),
            index_value=required_decimal(row, 'IndexValue', 'IndexValue'),
            change=optional_decimal(row, 'Change', 'Change'),
            ratio_change=optional_decimal(row, 'RatioChange', 'RatioChange'),
            total_trade=optional_decimal(row, 'TotalTrade', 'TotalTrade'),
            total_match_volume=optional_decimal(row, 'TotalMatchVol', 'TotalMatchVol'),
            total_match_value=optional_decimal(row, 'TotalMatchVal', 'TotalMatchVal'),
            type_index=optional_text(row, 'TypeIndex', 'TypeIndex'),
            index_name=optional_text(row, 'IndexName', 'IndexName'),
            advances=optional_decimal(row, 'Advances', 'Advances'),
            no_changes=optional_decimal(row, 'NoChanges', 'NoChanges'),
            declines=optional_decimal(row, 'Declines', 'Declines'),
            ceilings=optional_decimal(row, 'Ceilings', 'Ceilings', 'Ceiling'),
            floors=optional_decimal(row, 'Floors', 'Floors', 'Floor'),
            total_deal_volume=optional_decimal(row, 'TotalDealVol', 'TotalDealVol'),
            total_deal_value=optional_decimal(row, 'TotalDealVal', 'TotalDealVal'),
            total_volume=optional_decimal(row, 'TotalVol', 'TotalVol'),
            total_value=optional_decimal(row, 'TotalVal', 'TotalVal'),
            trading_session=optional_text(row, 'TradingSession', 'TradingSession'),
            provider_market=market,
            provider_exchange=exchange,
            field_units={
                'index_value': 'provider_native_index_value_scale',
                'change': 'provider_native_index_change_scale',
                'ratio_change': 'provider_native_ratio_scale_unverified',
                'total_trade': 'trade_count', 'total_match_volume': 'provider_native_quantity',
                'total_match_value': 'provider_native_value_currency_unverified',
                'advances': 'instrument_count', 'no_changes': 'instrument_count', 'declines': 'instrument_count',
                'ceilings': 'instrument_count', 'floors': 'instrument_count',
                'total_deal_volume': 'provider_native_quantity', 'total_deal_value': 'provider_native_value_currency_unverified',
                'total_volume': 'provider_native_quantity', 'total_value': 'provider_native_value_currency_unverified',
            },
            source_id='SSI-FC-DATA', revision='unknown',
        )
        previous = observations.get(trading_date)
        if previous is not None and previous != observation:
            raise ValueError('SSI DailyIndex contains conflicting rows for one trading date')
        observations[trading_date] = observation
    return [observations[key] for key in sorted(observations)]


def normalize_ssi_hose_daily_index_rows(
    rows: list[dict[str, Any]], index: Instrument, start: date, end: date, observed_at: datetime,
) -> list[DailyIndexObservation]:
    return _normalize_ssi_daily_index_rows(rows, index, 'HOSE', start, end, observed_at)


def normalize_ssi_hnx_daily_index_rows(
    rows: list[dict[str, Any]], index: Instrument, start: date, end: date, observed_at: datetime,
) -> list[DailyIndexObservation]:
    return _normalize_ssi_daily_index_rows(rows, index, 'HNX', start, end, observed_at)


def normalize_ssi_equity_daily_rows(
    rows: list[dict[str, Any]], instrument: Instrument, start: date, end: date,
    available_at: datetime, venue: str,
) -> list[Candle]:
    """Normalize SSI DailyOhlc while preserving provider-native price decimals."""
    expected_venue = venue.strip().upper()
    if expected_venue not in {'HOSE', 'HNX'} or instrument.instrument_class != 'equity' or instrument.venue != expected_venue:
        raise ValueError(f'SSI DailyOhlc adapter only supports {expected_venue} equity instruments')
    if start > end:
        raise ValueError('SSI DailyOhlc date range is invalid')
    if available_at.tzinfo is None or available_at.utcoffset() is None:
        raise ValueError('SSI DailyOhlc observation time must include a timezone')

    timezone_vietnam = ZoneInfo('Asia/Ho_Chi_Minh')
    candles: dict[date, Candle] = {}

    def decimal_string(value: Any, field: str) -> str:
        if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
            raise ValueError(f'SSI DailyOhlc {field} must be an exact decimal value')
        result = str(value).strip()
        decimal_text(result)
        return result

    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('SSI DailyOhlc row must be an object')
        symbol = str(row.get('Symbol') or '').strip().upper()
        row_venue = str(row.get('Market') or '').strip().upper()
        if symbol != instrument.native_symbol.upper() or row_venue != expected_venue:
            raise ValueError(f'SSI DailyOhlc row does not match the requested {expected_venue} instrument')
        raw_date = row.get('TradingDate')
        if not isinstance(raw_date, str):
            raise ValueError('SSI DailyOhlc TradingDate must use dd/mm/yyyy')
        try:
            trading_date = datetime.strptime(raw_date, '%d/%m/%Y').date()
        except ValueError as error:
            raise ValueError('SSI DailyOhlc TradingDate must use dd/mm/yyyy') from error
        if trading_date < start or trading_date > end:
            raise ValueError('SSI DailyOhlc returned a row outside the requested date range')
        open_time = datetime.combine(trading_date, daytime.min, tzinfo=timezone_vietnam)
        close_time = datetime.combine(trading_date + timedelta(days=1), daytime.min, tzinfo=timezone_vietnam)
        candle = Candle(
            instrument_id=instrument.id, interval='1d', open_time=open_time,
            close_time=close_time, available_at=available_at, is_closed=True,
            open=decimal_string(row.get('Open'), 'Open'),
            high=decimal_string(row.get('High'), 'High'),
            low=decimal_string(row.get('Low'), 'Low'),
            close=decimal_string(row.get('Close'), 'Close'),
            volume=decimal_string(row.get('Volume'), 'Volume'),
            currency='unknown', price_unit='unknown', volume_unit='unknown',
            revision='unknown', session='daily', source_id='SSI-FC-DATA',
        )
        existing = candles.get(trading_date)
        if existing is not None and existing != candle:
            raise ValueError('SSI DailyOhlc contains conflicting rows for one trading date')
        candles[trading_date] = candle
    return sorted(candles.values(), key=lambda value: value.open_time)


def normalize_ssi_hose_equity_daily_rows(
    rows: list[dict[str, Any]], instrument: Instrument, start: date, end: date,
    available_at: datetime,
) -> list[Candle]:
    return normalize_ssi_equity_daily_rows(rows, instrument, start, end, available_at, 'HOSE')


def normalize_ssi_hnx_equity_daily_rows(
    rows: list[dict[str, Any]], instrument: Instrument, start: date, end: date,
    available_at: datetime,
) -> list[Candle]:
    return normalize_ssi_equity_daily_rows(rows, instrument, start, end, available_at, 'HNX')

class SsiFastConnectProvider(BaseMarketProvider):
    """Official SSI FastConnect Data provider."""
    id = 'ssi'
    name = 'SSI FastConnect Data'
    category = 'broker_api'
    capabilities = ['historical_candles', 'realtime_streaming', 'level2_quotes']
    description = 'Institutional market data feed from SSI Securities. Gated by source policy.'

    def __init__(self, base_url: str = 'https://fc-data.ssi.com.vn/api/v2/Market'):
        self.base_url = base_url.rstrip('/')
        self.consumer_id = ''
        self.consumer_secret = ''
        self.configured = False
        self.access_token = ''
        self._credential_fingerprint = ''

    def configure_credentials(self, credential: dict[str, str]) -> None:
        if not isinstance(credential, dict):
            raise ValueError('SSI market-data credential document must be an object')
        consumer_id = credential.get('consumerID') or credential.get('consumer_id')
        consumer_secret = credential.get('consumerSecret') or credential.get('consumer_secret')
        if not isinstance(consumer_id, str) or not consumer_id.strip() or not isinstance(consumer_secret, str) or not consumer_secret.strip():
            raise ValueError('SSI market-data credentials require consumerID and consumerSecret')
        self.consumer_id = consumer_id
        self.consumer_secret = consumer_secret
        self._credential_fingerprint = hashlib.sha256(
            (consumer_id + '\0' + consumer_secret).encode('utf-8')
        ).hexdigest()
        self.configured = True
        self.access_token = ''

    def ping(self) -> ProviderStatus:
        consumer_id, consumer_secret = self.consumer_id, self.consumer_secret
        configured = bool(consumer_id and consumer_secret)
        self.consumer_id = ''
        self.consumer_secret = ''
        if not configured:
            return ProviderStatus(
                id=self.id, name=self.name, category=self.category, state='blocked',
                latency_ms=None, capabilities=self.capabilities, description=self.description,
                configured=False, error='Configure SSI FastConnect Data consumerID and consumerSecret before testing access',
            )
        body = json.dumps({'consumerID': consumer_id, 'consumerSecret': consumer_secret}).encode()
        request = urllib.request.Request(
            f'{self.base_url}/AccessToken',
            data=body,
            headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
            method='POST',
        )
        started = time.perf_counter()
        try:
            limiter = getattr(self, '_request_limiter', None)
            if limiter is not None:
                limiter.acquire()
            with urllib.request.urlopen(request, timeout=6.0) as response:
                payload = json.loads(response.read(1024 * 1024 + 1).decode('utf-8'))
            data = payload.get('data') if isinstance(payload, dict) else None
            token = data.get('accessToken') if isinstance(data, dict) else None
            if not isinstance(token, str) or not token:
                return ProviderStatus(
                    id=self.id, name=self.name, category=self.category, state='blocked',
                    latency_ms=round((time.perf_counter() - started) * 1000, 1),
                    capabilities=self.capabilities, description=self.description, configured=True,
                    error='SSI returned no market-data access token',
                )
            self.access_token = token
            return ProviderStatus(
                id=self.id, name=self.name, category=self.category, state='connected',
                latency_ms=round((time.perf_counter() - started) * 1000, 1),
                capabilities=self.capabilities, description=self.description, configured=True,
            )
        except urllib.error.HTTPError as error:
            state = 'blocked' if error.code in (400, 401, 403) else 'offline'
            return ProviderStatus(
                id=self.id, name=self.name, category=self.category, state=state,
                latency_ms=round((time.perf_counter() - started) * 1000, 1),
                capabilities=self.capabilities, description=self.description, configured=True,
                error=f'SSI market-data access-token request failed with HTTP {error.code}',
            )
        except Exception:
            return ProviderStatus(
                id=self.id, name=self.name, category=self.category, state='offline',
                latency_ms=round((time.perf_counter() - started) * 1000, 1),
                capabilities=self.capabilities, description=self.description, configured=True,
                error='SSI market-data access-token request failed; verify service access and network settings',
            )

    def get_json(self, endpoint: str, params: dict[str, str | int] | None = None, *, credential: dict[str, str]) -> dict:
        """Perform an authenticated GET and refresh the SSI token once on HTTP 401."""
        if endpoint not in {
            'Securities', 'SecuritiesDetails', 'IndexComponents', 'IndexList',
            'DailyOhlc', 'IntradayOhlc', 'DailyIndex', 'DailyStockPrice',
        }:
            raise ValueError('invalid SSI market-data endpoint')
        query = urlencode(params or {})
        url = f'{self.base_url}/{endpoint}' + (f'?{query}' if query else '')
        consumer_id = credential.get('consumerID') or credential.get('consumer_id')
        consumer_secret = credential.get('consumerSecret') or credential.get('consumer_secret')
        if not isinstance(consumer_id, str) or not consumer_id.strip() or not isinstance(consumer_secret, str) or not consumer_secret.strip():
            raise ValueError('SSI market-data credentials require consumerID and consumerSecret')
        fingerprint = hashlib.sha256((consumer_id + '\0' + consumer_secret).encode('utf-8')).hexdigest()

        if self._credential_fingerprint != fingerprint or not self.access_token:
            self.configure_credentials(credential)
            status = self.ping()
            if status.state != 'connected':
                raise ValueError('SSI market-data authentication failed')

        def read() -> dict:
            request = urllib.request.Request(
                url,
                headers={'Authorization': f'Bearer {self.access_token}', 'Accept': 'application/json'},
                method='GET',
            )
            with self._read(lambda: urllib.request.urlopen(request, timeout=10.0)) as response:
                body = response.read(16 * 1024 * 1024 + 1)
            if len(body) > 16 * 1024 * 1024:
                raise ValueError('SSI market-data response exceeds the size limit')
            payload = json.loads(body.decode('utf-8'), parse_float=Decimal)
            if not isinstance(payload, dict):
                raise ValueError('SSI market-data response must be an object')
            return payload

        try:
            return read()
        except urllib.error.HTTPError as error:
            if error.code != 401:
                raise
        self.configure_credentials(credential)
        status = self.ping()
        if status.state != 'connected':
            raise ValueError('SSI market-data token refresh failed')
        return read()

    def _fetch_security_catalogue_page(
        self, venue: str, page_index: int, security_types: set[str], instrument_class: str,
        *, credential: dict[str, str],
    ) -> list[Instrument]:
        venue = venue.strip().upper()
        if venue not in {'HOSE', 'HNX', 'UPCOM', 'HNXBOND', 'DER'}:
            raise ValueError('SSI security catalogue venue is not supported')
        if isinstance(page_index, bool) or page_index < 1 or page_index > 10:
            raise ValueError('SSI SecuritiesDetails page index must be between 1 and 10')
        payload = self.get_json(
            'SecuritiesDetails',
            {'market': venue, 'pageIndex': page_index, 'pageSize': 1000},
            credential=credential,
        )
        return _normalize_ssi_security_catalogue(payload, venue, security_types, instrument_class)

    def _fetch_equity_catalogue_page(self, venue: str, page_index: int, *, credential: dict[str, str]) -> list[Instrument]:
        if venue not in {'HOSE', 'HNX', 'UPCOM'}:
            raise ValueError('SSI equity catalogue supports only HOSE, HNX, and UPCOM')
        return self._fetch_security_catalogue_page(venue, page_index, {'ST', 'S'}, 'equity', credential=credential)

    def fetch_hose_equity_catalogue_page(self, page_index: int, *, credential: dict[str, str]) -> list[Instrument]:
        return self._fetch_equity_catalogue_page('HOSE', page_index, credential=credential)

    def fetch_hnx_equity_catalogue_page(self, page_index: int, *, credential: dict[str, str]) -> list[Instrument]:
        return self._fetch_equity_catalogue_page('HNX', page_index, credential=credential)

    def fetch_upcom_equity_catalogue_page(self, page_index: int, *, credential: dict[str, str]) -> list[Instrument]:
        return self._fetch_equity_catalogue_page('UPCOM', page_index, credential=credential)

    def _fetch_security_catalogue(
        self, venue: str, security_types: set[str], instrument_class: str, *, credential: dict[str, str],
    ) -> list[Instrument]:
        venue = venue.strip().upper()
        if venue not in {'HOSE', 'HNX', 'UPCOM', 'HNXBOND', 'DER'}:
            raise ValueError('SSI security catalogue venue is not supported')
        first_page = self.get_json(
            'SecuritiesDetails',
            {'market': venue, 'pageIndex': 1, 'pageSize': 1000},
            credential=credential,
        )
        total_raw = first_page.get('totalRecord')
        if isinstance(total_raw, bool) or not isinstance(total_raw, (int, str)):
            raise ValueError('SSI SecuritiesDetails response has an invalid totalRecord')
        try:
            total_records = int(total_raw)
        except (TypeError, ValueError) as error:
            raise ValueError('SSI SecuritiesDetails response has an invalid totalRecord') from error
        if total_records < 0 or total_records > 10000:
            raise ValueError(f'SSI {venue} catalogue exceeds the documented 10-page limit')
        page_count = max(1, (total_records + 999) // 1000)
        instruments = _normalize_ssi_security_catalogue(first_page, venue, security_types, instrument_class)
        for page_index in range(2, page_count + 1):
            instruments.extend(self._fetch_security_catalogue_page(
                venue, page_index, security_types, instrument_class, credential=credential,
            ))

        unique: dict[str, Instrument] = {}
        for instrument in instruments:
            previous = unique.get(instrument.id)
            if previous is not None and previous != instrument:
                kind = 'stock' if instrument_class == 'equity' else 'security'
                raise ValueError(f'SSI {venue} catalogue has conflicting {kind} identities across pages')
            unique[instrument.id] = instrument
        return sorted(unique.values(), key=lambda value: (value.native_symbol, value.id))

    def _fetch_equity_catalogue(self, venue: str, *, credential: dict[str, str]) -> list[Instrument]:
        if venue not in {'HOSE', 'HNX', 'UPCOM'}:
            raise ValueError('SSI equity catalogue supports only HOSE, HNX, and UPCOM')
        return self._fetch_security_catalogue(venue, {'ST', 'S'}, 'equity', credential=credential)

    def fetch_hose_equity_catalogue(self, *, credential: dict[str, str]) -> list[Instrument]:
        return self._fetch_equity_catalogue('HOSE', credential=credential)

    def fetch_hnx_equity_catalogue(self, *, credential: dict[str, str]) -> list[Instrument]:
        return self._fetch_equity_catalogue('HNX', credential=credential)

    def fetch_upcom_equity_catalogue(self, *, credential: dict[str, str]) -> list[Instrument]:
        return self._fetch_equity_catalogue('UPCOM', credential=credential)

    def fetch_hose_covered_warrant_catalogue_page(self, page_index: int, *, credential: dict[str, str]) -> list[Instrument]:
        return self._fetch_security_catalogue_page('HOSE', page_index, {'CW'}, 'covered_warrant', credential=credential)

    def fetch_hose_covered_warrant_catalogue(self, *, credential: dict[str, str]) -> list[Instrument]:
        return self._fetch_security_catalogue('HOSE', {'CW'}, 'covered_warrant', credential=credential)

    def fetch_der_derivative_catalogue_page(self, page_index: int, *, credential: dict[str, str]) -> list[Instrument]:
        return self._fetch_security_catalogue_page('DER', page_index, {'FU'}, 'derivative', credential=credential)

    def fetch_der_derivative_catalogue(self, *, credential: dict[str, str]) -> list[Instrument]:
        return self._fetch_security_catalogue('DER', {'FU'}, 'derivative', credential=credential)

    def fetch_hose_etf_catalogue_page(self, page_index: int, *, credential: dict[str, str]) -> list[Instrument]:
        return self._fetch_security_catalogue_page('HOSE', page_index, {'EF'}, 'etf', credential=credential)

    def fetch_hose_etf_catalogue(self, *, credential: dict[str, str]) -> list[Instrument]:
        return self._fetch_security_catalogue('HOSE', {'EF'}, 'etf', credential=credential)

    def fetch_hnxbond_bond_catalogue_page(self, page_index: int, *, credential: dict[str, str]) -> list[Instrument]:
        return self._fetch_security_catalogue_page('HNXBOND', page_index, {'BO'}, 'bond', credential=credential)

    def fetch_hnxbond_bond_catalogue(self, *, credential: dict[str, str]) -> list[Instrument]:
        return self._fetch_security_catalogue('HNXBOND', {'BO'}, 'bond', credential=credential)

    def fetch_hose_index_catalogue(self, *, credential: dict[str, str]) -> list[Instrument]:
        def checked_page(page_index: int) -> tuple[int, list[dict[str, Any]]]:
            payload = self.get_json('IndexList', {
                'exchange': 'HOSE', 'pageIndex': page_index, 'pageSize': 1000,
            }, credential=credential)
            status = str(payload.get('status', '')).strip().casefold()
            if status not in {'success', '200'}:
                raise ValueError('SSI IndexList returned an unsuccessful response')
            total_raw = payload.get('totalRecord')
            if isinstance(total_raw, bool) or not isinstance(total_raw, (int, str)):
                raise ValueError('SSI IndexList response has an invalid totalRecord')
            try:
                total = int(total_raw)
            except (TypeError, ValueError) as error:
                raise ValueError('SSI IndexList response has an invalid totalRecord') from error
            rows = payload.get('data')
            if total < 0 or not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
                raise ValueError('SSI IndexList response has invalid data')
            return total, rows

        total_records, rows = checked_page(1)
        if total_records > 10000:
            raise ValueError('SSI HOSE IndexList exceeds the documented 10-page limit')
        page_count = max(1, (total_records + 999) // 1000)
        for page_index in range(2, page_count + 1):
            page_total, page_rows = checked_page(page_index)
            if page_total != total_records:
                raise ValueError('SSI IndexList totalRecord changed during pagination')
            rows.extend(page_rows)
        if len(rows) != total_records:
            raise ValueError('SSI IndexList page set is incomplete')
        instruments = normalize_ssi_hose_index_catalogue(rows)
        if not instruments:
            raise ValueError('SSI returned no HOSE indexes')
        return instruments

    def fetch_hnx_index_catalogue(self, *, credential: dict[str, str]) -> list[Instrument]:
        def checked_page(page_index: int) -> tuple[int, list[dict[str, Any]]]:
            payload = self.get_json('IndexList', {
                'exchange': 'HNX', 'pageIndex': page_index, 'pageSize': 1000,
            }, credential=credential)
            status = str(payload.get('status', '')).strip().casefold()
            if status not in {'success', '200'}:
                raise ValueError('SSI IndexList returned an unsuccessful response')
            total_raw = payload.get('totalRecord')
            if isinstance(total_raw, bool) or not isinstance(total_raw, (int, str)):
                raise ValueError('SSI IndexList response has an invalid totalRecord')
            try:
                total = int(total_raw)
            except (TypeError, ValueError) as error:
                raise ValueError('SSI IndexList response has an invalid totalRecord') from error
            rows = payload.get('data')
            if total < 0 or not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
                raise ValueError('SSI IndexList response has invalid data')
            return total, rows

        total_records, rows = checked_page(1)
        if total_records > 10000:
            raise ValueError('SSI HNX IndexList exceeds the documented 10-page limit')
        page_count = max(1, (total_records + 999) // 1000)
        for page_index in range(2, page_count + 1):
            page_total, page_rows = checked_page(page_index)
            if page_total != total_records:
                raise ValueError('SSI IndexList totalRecord changed during pagination')
            rows.extend(page_rows)
        if len(rows) != total_records:
            raise ValueError('SSI IndexList page set is incomplete')
        instruments = normalize_ssi_index_catalogue(rows, 'HNX')
        if not instruments:
            raise ValueError('SSI returned no HNX indexes')
        return instruments

    def fetch_hose_index_components(
        self, index: Instrument, *, credential: dict[str, str],
    ) -> IndexConstituentSet:
        if index.instrument_class != 'index' or index.venue != 'HOSE':
            raise ValueError('SSI IndexComponents adapter only supports HOSE indexes')

        def checked_page(page_index: int) -> tuple[int, list[dict[str, Any]]]:
            payload = self.get_json('IndexComponents', {
                'indexCode': index.native_symbol,
                'pageIndex': page_index,
                'pageSize': 1000,
            }, credential=credential)
            status = str(payload.get('status', '')).strip().casefold()
            if status not in {'success', '200'}:
                raise ValueError('SSI IndexComponents returned an unsuccessful response')
            total_raw = payload.get('totalRecord')
            if isinstance(total_raw, bool) or not isinstance(total_raw, (int, str)):
                raise ValueError('SSI IndexComponents response has an invalid totalRecord')
            try:
                total = int(total_raw)
            except (TypeError, ValueError) as error:
                raise ValueError('SSI IndexComponents response has an invalid totalRecord') from error
            rows = payload.get('data')
            if total < 0 or not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
                raise ValueError('SSI IndexComponents response has invalid data')
            return total, rows

        total_records, rows = checked_page(1)
        if total_records > 10000:
            raise ValueError('SSI IndexComponents exceeds the documented 10-page limit')
        page_count = max(1, (total_records + 999) // 1000)
        for page_index in range(2, page_count + 1):
            page_total, page_rows = checked_page(page_index)
            if page_total != total_records:
                raise ValueError('SSI IndexComponents totalRecord changed during pagination')
            rows.extend(page_rows)
        if len(rows) != total_records:
            raise ValueError('SSI IndexComponents page set is incomplete')
        return normalize_ssi_hose_index_components(rows, index, datetime.now(timezone.utc))

    def _fetch_daily_index(
        self, index: Instrument, venue: str, start: date, end: date, *, credential: dict[str, str],
    ) -> list[DailyIndexObservation]:
        if venue not in {'HOSE', 'HNX'} or index.instrument_class != 'index' or index.venue != venue:
            raise ValueError(f'SSI DailyIndex adapter only supports {venue} indexes')
        if start > end:
            raise ValueError('SSI DailyIndex date range is invalid')
        if end >= datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).date():
            raise ValueError('SSI DailyIndex history must end before the current Vietnam date until publication timing is verified')

        def checked_page(page_index: int) -> tuple[int, list[dict[str, Any]]]:
            payload = self.get_json('DailyIndex', {
                'indexId': index.native_symbol,
                'fromDate': start.strftime('%d/%m/%Y'),
                'toDate': end.strftime('%d/%m/%Y'),
                'pageIndex': page_index,
                'pageSize': 1000,
                'ascending': 'true',
            }, credential=credential)
            status = str(payload.get('status', '')).strip().casefold()
            if status not in {'success', '200'}:
                raise ValueError('SSI DailyIndex returned an unsuccessful response')
            total_raw = payload.get('totalRecord')
            if isinstance(total_raw, bool) or not isinstance(total_raw, (int, str)):
                raise ValueError('SSI DailyIndex response has an invalid totalRecord')
            try:
                total = int(total_raw)
            except (TypeError, ValueError) as error:
                raise ValueError('SSI DailyIndex response has an invalid totalRecord') from error
            rows = payload.get('data')
            if total < 0 or not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
                raise ValueError('SSI DailyIndex response has invalid data')
            return total, rows

        total_records, rows = checked_page(1)
        if total_records > 10000:
            raise ValueError('SSI DailyIndex range exceeds the documented 10-page limit')
        page_count = max(1, (total_records + 999) // 1000)
        for page_index in range(2, page_count + 1):
            page_total, page_rows = checked_page(page_index)
            if page_total != total_records:
                raise ValueError('SSI DailyIndex totalRecord changed during pagination')
            rows.extend(page_rows)
        if len(rows) != total_records:
            raise ValueError('SSI DailyIndex page set is incomplete')
        return _normalize_ssi_daily_index_rows(rows, index, venue, start, end, datetime.now(timezone.utc))

    def fetch_hose_daily_index(
        self, index: Instrument, start: date, end: date, *, credential: dict[str, str],
    ) -> list[DailyIndexObservation]:
        return self._fetch_daily_index(index, 'HOSE', start, end, credential=credential)

    def fetch_hnx_daily_index(
        self, index: Instrument, start: date, end: date, *, credential: dict[str, str],
    ) -> list[DailyIndexObservation]:
        return self._fetch_daily_index(index, 'HNX', start, end, credential=credential)

    def _fetch_equity_daily(
        self, instrument: Instrument, venue: str, start: date, end: date, *, credential: dict[str, str],
    ) -> list[Candle]:
        venue = venue.strip().upper()
        if venue not in {'HOSE', 'HNX'} or instrument.instrument_class != 'equity' or instrument.venue != venue:
            raise ValueError(f'SSI DailyOhlc adapter only supports {venue} equity instruments')
        if start > end:
            raise ValueError('SSI DailyOhlc date range is invalid')
        if end >= datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).date():
            raise ValueError('SSI DailyOhlc history must end before the current Vietnam date until publication timing is verified')

        def checked_page(page_index: int) -> tuple[int, list[dict[str, Any]]]:
            payload = self.get_json('DailyOhlc', {
                'symbol': instrument.native_symbol,
                'fromDate': start.strftime('%d/%m/%Y'),
                'toDate': end.strftime('%d/%m/%Y'),
                'pageIndex': page_index,
                'pageSize': 1000,
                'ascending': 'true',
            }, credential=credential)
            status = str(payload.get('status', '')).strip().casefold()
            if status not in {'success', '200'}:
                raise ValueError('SSI DailyOhlc returned an unsuccessful response')
            total_raw = payload.get('totalRecord')
            if isinstance(total_raw, bool) or not isinstance(total_raw, (int, str)):
                raise ValueError('SSI DailyOhlc response has an invalid totalRecord')
            try:
                total = int(total_raw)
            except (TypeError, ValueError) as error:
                raise ValueError('SSI DailyOhlc response has an invalid totalRecord') from error
            rows = payload.get('data')
            if total < 0 or not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
                raise ValueError('SSI DailyOhlc response has invalid data')
            return total, rows

        total_records, rows = checked_page(1)
        if total_records > 10000:
            raise ValueError('SSI DailyOhlc range exceeds the documented 10-page limit')
        page_count = max(1, (total_records + 999) // 1000)
        for page_index in range(2, page_count + 1):
            page_total, page_rows = checked_page(page_index)
            if page_total != total_records:
                raise ValueError('SSI DailyOhlc totalRecord changed during pagination')
            rows.extend(page_rows)
        if len(rows) != total_records:
            raise ValueError('SSI DailyOhlc page set is incomplete')
        observed_at = datetime.now(timezone.utc)
        return normalize_ssi_equity_daily_rows(rows, instrument, start, end, observed_at, venue)

    def fetch_hose_equity_daily(
        self, instrument: Instrument, start: date, end: date, *, credential: dict[str, str],
    ) -> list[Candle]:
        return self._fetch_equity_daily(instrument, 'HOSE', start, end, credential=credential)

    def fetch_hnx_equity_daily(
        self, instrument: Instrument, start: date, end: date, *, credential: dict[str, str],
    ) -> list[Candle]:
        return self._fetch_equity_daily(instrument, 'HNX', start, end, credential=credential)

    def fetch_candles(self, symbol: str, interval: str, start: datetime, end: datetime) -> list[Candle]:
        raise ValueError('SSI source capability blocked by policy')

    def fetch_instruments(self) -> list[Instrument]:
        return []
