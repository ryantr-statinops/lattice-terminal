import pytest
from kestrel_engine.programs import inspect_source

def test_inspection_does_not_execute_and_contracts_are_distinct():
    source='KESTREL_KIND="research"\nraise RuntimeError("must not run")\ndef run(context): pass'
    assert inspect_source(source,'research')['kind']=='research'
    with pytest.raises(ValueError,match='cannot run'):inspect_source(source,'backtest')
    with pytest.raises(ValueError,match='on_event'):inspect_source('KESTREL_KIND="strategy"\ndef run(context): pass','strategy')
    with pytest.raises(ValueError,match='literal'):inspect_source('KESTREL_KIND=str("research")\ndef run(context): pass','research')

def test_explicit_selection_without_declaration():
    assert inspect_source('def run(context): pass','research',selected=True)['kind']=='research'
    with pytest.raises(ValueError):inspect_source('def run(context): pass','research')
