import json
from pathlib import Path
import pytest
from kestrel_engine.market import MarketRepository

FIXTURES=Path(__file__).resolve().parents[3]/'data/fixtures'

def test_replay_hash_decimal_precision_and_corruption(tmp_path):
    repo=MarketRepository(tmp_path,FIXTURES)
    a=repo.ingest_fixture(FIXTURES/'SYN01.json')
    assert repo.ingest_fixture(FIXTURES/'SYN01.json')==a
    snapshot=repo.load(a)
    assert snapshot.quality.state=='fixture'
    assert len(snapshot.candles)==100
    assert snapshot.candles[0].open=='9880.00000000'
    path=repo.root/'snapshots'/a/'candles.parquet'
    path.write_bytes(path.read_bytes()+b'corruption')
    with pytest.raises(ValueError,match='checksum'): repo.load(a)

def test_conflicting_duplicates_and_provisional_are_not_published(tmp_path):
    raw=json.loads((FIXTURES/'SYN01.json').read_text())
    raw['candles'].append(raw['candles'][0]|{'close':'9900'})
    path=tmp_path/'bad.json';path.write_text(json.dumps(raw))
    repo=MarketRepository(tmp_path,FIXTURES)
    with pytest.raises(ValueError,match='duplicate'): repo.ingest_fixture(path)
    raw['candles']=raw['candles'][:1];raw['candles'][0]['is_closed']=False
    path.write_text(json.dumps(raw))
    with pytest.raises(ValueError,match='provisional'): repo.ingest_fixture(path)
