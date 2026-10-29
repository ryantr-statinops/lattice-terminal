from pathlib import Path

import pytest
from kestrel_engine.market import MarketRepository

FIXTURES=Path(__file__).resolve().parents[3]/'data/fixtures'


def test_quant_can_select_an_explicit_local_snapshot(tmp_path):
    repo=MarketRepository(tmp_path,FIXTURES)
    snapshot_id=repo.ingest_fixture(FIXTURES/'SYN01.json')
    snapshot=repo.load_for_instrument(snapshot_id,'HOSE:REGULAR:equity:SYN01')
    assert snapshot.snapshot_id==snapshot_id


def test_quant_rejects_snapshot_for_another_instrument(tmp_path):
    repo=MarketRepository(tmp_path,FIXTURES)
    snapshot_id=repo.ingest_fixture(FIXTURES/'SYN01.json')
    with pytest.raises(ValueError,match='does not belong'):
        repo.load_for_instrument(snapshot_id,'HNX:REGULAR:equity:SYN02')
