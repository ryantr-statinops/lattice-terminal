import hashlib
import json
import time
from pathlib import Path
from kestrel_engine.runner import RunManager
from kestrel_engine.version import engine_hash

def snapshot(root,source,identity='a'*64):
    files={'main.py':source,'helper.py':'VALUE=42\n'}
    manifest={'kind':'research','entry':'main.py','params':{},'files':files,'engine_sha256':engine_hash(),'dependency_lock':(Path(__file__).resolve().parents[2]/'services/engine/uv.lock').read_text()}
    raw=json.dumps(manifest).encode();key=hashlib.sha256(raw).hexdigest();directory=root/'code-snapshots'/key
    (directory/'files').mkdir(parents=True,exist_ok=True)
    (directory/'manifest.json').write_bytes(raw)
    for name,text in files.items():(directory/'files'/name).write_text(text,encoding='utf-8',newline='\n')
    return {'id':identity,'kind':'research','snapshot':key,'timeout_seconds':10}

def wait(manager,identity):
    until=time.monotonic()+15
    while time.monotonic()<until:
        value=manager.events(identity,0)
        if value['done']:return value['events']
        time.sleep(.05)
    raise AssertionError('worker did not finish')

def test_research_runs_frozen_helpers_and_structured_outputs(tmp_path):
    config=snapshot(tmp_path,'KESTREL_KIND="research"\nfrom helper import VALUE\ndef run(context):\n    print(VALUE)\n    context.table("values",["n"],[[VALUE]])\n    context.chart("line",[1,2],[3,4])\n')
    manager=RunManager(tmp_path);manager.start(config);events=wait(manager,config['id'])
    assert events[-1]['payload']['status']=='completed',events
    assert any(e['type']=='log' and e['payload']['message']=='42' for e in events)
    assert any(e['type']=='table' for e in events)
    assert (tmp_path/'artifacts'/config['id']/'values.parquet').exists()

def test_timeout_stops_worker_without_completing(tmp_path):
    config=snapshot(tmp_path,'KESTREL_KIND="research"\ndef run(context):\n    while True: pass\n')
    config['timeout_seconds']=1;manager=RunManager(tmp_path);manager.start(config);events=wait(manager,config['id'])
    assert events[-1]['payload']['status']=='failed'
    assert any('time limit' in e['payload'].get('message','') for e in events)

def test_engine_shutdown_cancels_running_worker(tmp_path):
    config=snapshot(tmp_path,'KESTREL_KIND="research"\ndef run(context):\n    while True: pass\n')
    manager=RunManager(tmp_path);manager.start(config)
    deadline=time.monotonic()+5
    while time.monotonic()<deadline:
        process=manager.jobs[config['id']]['process']
        if process is not None and process.stdin.closed:break
        time.sleep(.02)
    assert process is not None and process.stdin.closed
    manager.close(timeout=5)
    events=manager.events(config['id'],0)['events']
    assert manager.jobs[config['id']]['done']
    assert events[-1]['payload']['status']=='cancelled'


def test_run_event_store_deduplicates_signals_by_stable_id(tmp_path):
    identity='b'*64
    manager=RunManager(tmp_path)
    manager.jobs[identity]={'events':[],'signal_ids':set(),'done':False}
    signal={'id':'stable-signal-id','run_id':identity,'logical_key':'breakout:HPG'}
    manager.append(identity,'signal',signal)
    manager.append(identity,'signal',signal)
    manager.append(identity,'signal',signal|{'id':'another-signal-id'})
    events=manager.events(identity,0)['events']
    assert [event['seq'] for event in events]==[1,2]
    assert [event['payload']['id'] for event in events]==['stable-signal-id','another-signal-id']
