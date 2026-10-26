import json
import hashlib
from pathlib import Path
import pyarrow.parquet as pq
import pytest
from kestrel_engine.market import MarketRepository,SCHEMA_V1

FIXTURES=Path(__file__).resolve().parents[3]/'data/fixtures'

def test_replay_hash_decimal_precision_and_corruption(tmp_path):
    repo=MarketRepository(tmp_path,FIXTURES)
    a=repo.ingest_fixture(FIXTURES/'SYN01.json')
    assert repo.ingest_fixture(FIXTURES/'SYN01.json')==a
    snapshot=repo.load(a)
    assert snapshot.quality.state=='fixture'
    assert snapshot.schema_version=='2'
    assert len(snapshot.candles)==100
    assert snapshot.candles[0].open=='9880.00000000'
    assert snapshot.candles[0].currency=='unknown'
    path=repo.root/'snapshots'/a/'candles.parquet'
    path.write_bytes(path.read_bytes()+b'corruption')
    with pytest.raises(ValueError,match='checksum'): repo.load(a)

def test_legacy_v1_snapshot_keeps_identity_and_uses_v1_asset_semantics(tmp_path):
    repo=MarketRepository(tmp_path,FIXTURES)
    key=repo.ingest_fixture(FIXTURES/'SYN01.json')
    path=repo.root/'snapshots'/key
    parquet=path/'candles.parquet'
    old_table=pq.read_table(parquet).select(SCHEMA_V1.names)
    pq.write_table(old_table,parquet,compression='zstd')
    manifest_path=path/'manifest.json'
    manifest=json.loads(manifest_path.read_text())
    manifest['schema_version']='1'
    manifest['instrument'].pop('instrument_class')
    manifest['instrument'].pop('currency',None)
    manifest['parquet_sha256']=hashlib.sha256(parquet.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))

    snapshot=repo.load(key)
    assert snapshot.snapshot_id==key
    assert snapshot.schema_version=='1'
    assert snapshot.instrument.instrument_class=='equity'
    assert snapshot.candles[0].currency=='unknown'

def test_conflicting_duplicates_and_provisional_are_not_published(tmp_path):
    raw=json.loads((FIXTURES/'SYN01.json').read_text())
    raw['candles'].append(raw['candles'][0]|{'close':'9900'})
    path=tmp_path/'bad.json';path.write_text(json.dumps(raw))
    repo=MarketRepository(tmp_path,FIXTURES)
    with pytest.raises(ValueError,match='duplicate'): repo.ingest_fixture(path)
    raw['candles']=raw['candles'][:1];raw['candles'][0]['is_closed']=False
    path.write_text(json.dumps(raw))
    with pytest.raises(ValueError,match='provisional'): repo.ingest_fixture(path)
