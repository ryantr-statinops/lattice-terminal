
import pytest
from kestrel_engine.market import MarketRepository



def test_quant_can_select_an_explicit_local_snapshot(tmp_path, repository_paths):
    repo=MarketRepository(tmp_path,repository_paths['fixtures'])
    snapshot_id=repo.ingest_fixture(repository_paths['fixtures']/'SYN01.json')
    snapshot=repo.load_for_instrument(snapshot_id,'HOSE:REGULAR:equity:SYN01')
    assert snapshot.snapshot_id==snapshot_id


def test_quant_rejects_snapshot_for_another_instrument(tmp_path, repository_paths):
    repo=MarketRepository(tmp_path,repository_paths['fixtures'])
    snapshot_id=repo.ingest_fixture(repository_paths['fixtures']/'SYN01.json')
    with pytest.raises(ValueError,match='does not belong'):
        repo.load_for_instrument(snapshot_id,'HNX:REGULAR:equity:SYN02')
