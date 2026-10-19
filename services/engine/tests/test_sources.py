import json
from datetime import datetime,timedelta,timezone
import pytest
from kestrel_engine.sources import SourceGate,SourceBlocked

def test_probe_before_production_does_not_imply_retention(tmp_path):
    gate=SourceGate(tmp_path)
    scope={'endpoints':['DailyOhlc'],'purposes':['schema-check'],'fields':['status'],'request_limit':1,'timeout_seconds':10,'terms_reference':'test-only-terms','entitlement_reference':'test-only-entitlement','expires_at':(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat()}
    gate.path.write_text(json.dumps([{'id':'SSI-FC-DATA-REST','probe_authorized':True,'probe_reference':'synthetic-authorization','probe_scope':scope}]))
    assert gate.authorize('SSI-FC-DATA-REST','schema-check','DailyOhlc',probe=True).request_limit==1
    with pytest.raises(SourceBlocked):gate.authorize('SSI-FC-DATA-REST','display','DailyOhlc')
    assert not gate.records()['SSI-FC-DATA-REST'].access_tested
    with pytest.raises(SourceBlocked):gate.authorize('SSI-FC-DATA-REST','store','DailyOhlc',probe=True)

def test_expired_and_malformed_policy_fail_closed(tmp_path):
    gate=SourceGate(tmp_path)
    with pytest.raises(SourceBlocked):gate.authorize('SSI-FC-DATA-REST','display','DailyOhlc')
    gate.path.write_text('not-json')
    assert all(v['operating_state']=='fixture-only' for v in gate.status())
