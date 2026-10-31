from pathlib import Path
from kestrel_engine.tapes import TapeRepository
from kestrel_engine.paper import PaperSession

def test_paper_callbacks_reserve_then_fill_future_quote(repository_paths):
    repo=TapeRepository(repository_paths['fixtures']);events,rules=repo.load(repo.manifest()['snapshot_id']);output=[]
    session=PaperSession('100000',rules,lambda kind,payload:output.append((kind,payload)))
    session.place(events[0],{'side':'buy','limit_price':'11000','quantity':'1'},'allocation','run')
    session.quote(events[0],True)
    assert [v[0] for v in output]==['paper_order']
    session.quote(events[1],True)
    assert [v[0] for v in output]==['paper_order','paper_fill']
    assert session.positions[events[0].instrument_id]==1
