import io
import json
import urllib.error
from datetime import datetime, timezone
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from kestrel_engine.app import create_app
from kestrel_engine.providers import VndirectCommunityProvider


def response(payload):
    return io.BytesIO(json.dumps(payload).encode())


def valid_payload():
    return {'s':'ok','t':[1792800000,1792886400],'o':[1,2],'h':[2,3],'l':[0.5,1.5],'c':[1.5,2.5],'v':[100,200]}


def test_vndirect_probe_validates_recent_vnindex_daily_bars():
    provider=VndirectCommunityProvider()
    with patch('kestrel_engine.providers.urllib.request.urlopen',return_value=response(valid_payload())) as open_url:
        status=provider.ping()

    request=open_url.call_args.args[0]
    query=parse_qs(urlparse(request.full_url).query)
    assert query['symbol']==['VN:VNINDEX']
    assert query['resolution']==['D']
    assert int(query['to'][0])>datetime(2026,1,1,tzinfo=timezone.utc).timestamp()
    assert status.state=='connected'
    assert status.probe.transport=='reachable'
    assert status.probe.data=='available'
    assert status.probe.sample_count==2
    assert status.probe.first_bar_at is not None
    assert status.probe.last_bar_at is not None


def test_vndirect_probe_distinguishes_no_data_from_unreachable():
    provider=VndirectCommunityProvider()
    with patch('kestrel_engine.providers.urllib.request.urlopen',return_value=response({'s':'no_data'})):
        empty=provider.ping()
    with patch('kestrel_engine.providers.urllib.request.urlopen',side_effect=TimeoutError('timeout')):
        offline=provider.ping()

    assert empty.state=='unknown'
    assert empty.probe.transport=='reachable'
    assert empty.probe.data=='no_data'
    assert offline.state=='offline'
    assert offline.probe.transport=='unreachable'
    assert offline.probe.data=='not_checked'


def test_vndirect_probe_marks_http_response_with_invalid_payload_separately():
    provider=VndirectCommunityProvider()
    bad_payloads=[
        {'s':'error','errmsg':'invalid symbol'},
        {'s':'ok','t':[1],'o':[1],'h':[1],'l':[1],'c':[1]},
        {'s':'ok','t':[1,2],'o':[1],'h':[1,2],'l':[1,2],'c':[1,2],'v':[1,2]},
        {'s':'ok','t':[2,1],'o':[1,2],'h':[2,3],'l':[0,1],'c':[1,2],'v':[1,2]},
    ]
    for payload in bad_payloads:
        with patch('kestrel_engine.providers.urllib.request.urlopen',return_value=response(payload)):
            status=provider.ping()
        assert status.state=='unknown'
        assert status.probe.transport=='reachable'
        assert status.probe.data=='invalid'


def test_vndirect_probe_classifies_http_error_as_reachable_invalid_response():
    provider=VndirectCommunityProvider()
    error=urllib.error.HTTPError('https://dchart-api.vndirect.com.vn/dchart/history',401,'unauthorized',None,None)
    with patch('kestrel_engine.providers.urllib.request.urlopen',side_effect=error):
        status=provider.ping()

    assert status.probe.transport=='reachable'
    assert status.probe.data=='invalid'
    assert status.state=='unknown'
    assert 'HTTP 401' in status.error


def test_provider_ping_contract_includes_separate_probe_statuses():
    schema=create_app().openapi()
    response=schema['paths']['/internal/v1/providers/{id}/ping']['post']['responses']['200']['content']['application/json']['schema']
    status=schema['components']['schemas'][response['$ref'].rsplit('/',1)[-1]]
    probe_ref=status['properties']['probe']['anyOf'][0]['$ref']
    probe=schema['components']['schemas'][probe_ref.rsplit('/',1)[-1]]
    assert set(probe['properties'])=={'transport','data','symbol','resolution','sample_count','first_bar_at','last_bar_at'}
