"""Isolated fixture-only acceptance smoke. Never uses the default user data root."""
import argparse
import ctypes
import http.cookiejar
import json
import os
import re
from pathlib import Path
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
import uuid

parser=argparse.ArgumentParser()
parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
args=parser.parse_args();root=args.root.resolve();binary=root/'.cache/bin/kestrel.exe'
if os.name!='nt':raise SystemExit('This acceptance smoke requires Windows')
origin='http://127.0.0.1:8080'
def local_account(path):
    values={}
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        line=line.strip()
        if not line or line.startswith('#'):continue
        if line.startswith('export '):line=line[7:].lstrip()
        key,separator,value=line.partition('=')
        if not separator:continue
        key,value=key.strip(),value.strip()
        if value.startswith("'") and value.endswith("'"):value=value[1:-1]
        elif value.startswith('"') and value.endswith('"'):value=json.loads(value)
        else:value=value.split(' #',1)[0].strip()
        values[key]=value
    username,password=values.get('KESTREL_LOCAL_USERNAME',''),values.get('KESTREL_LOCAL_PASSWORD','')
    if not username or len(password.encode())<6:raise RuntimeError('Set a valid local account in repository .env before the Windows smoke')
    return username,password
username,password=local_account(root/'.env')
def key():return uuid.uuid4().hex
with tempfile.TemporaryDirectory(prefix='kestrel-smoke-',dir=root/'.cache') as temp:
    base=Path(temp).resolve();assert base.is_relative_to((root/'.cache').resolve());data=base/'data';process=None;jar=http.cookiejar.CookieJar()
    opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    def call(path,body=None,method=None,expected=200,authenticated=True):
        request=urllib.request.Request(origin+'/api/v1'+path,data=json.dumps(body).encode() if body is not None else None,method=method,headers={'Origin':origin,'Content-Type':'application/json'})
        try:
            response=(opener if authenticated else urllib.request.build_opener()).open(request,timeout=20)
        except urllib.error.HTTPError as error:response=error
        text=response.read().decode();assert response.code==expected,(path,response.code,text)
        try:return json.loads(text)
        except json.JSONDecodeError:return text
    def start(directory):
        global process
        jar.clear()
        process=subprocess.Popen([str(binary),'-root',str(root),'-data',str(directory)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
        end=time.monotonic()+40
        while time.monotonic()<end:
            if process.poll() is not None:raise AssertionError('Gateway exited during startup')
            try:
                call('/ready')
                state=json.loads((directory/'runtime.json').read_text())
                assert state['pid']==process.pid,'readiness belongs to another instance'
                return
            except (OSError,AssertionError):time.sleep(.1)
        raise AssertionError('Readiness timed out')
    def descendants():
        raw=subprocess.check_output(['powershell','-NoProfile','-Command','Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId | ConvertTo-Json -Compress'],text=True)
        records=json.loads(raw);known={process.pid}
        while True:
            next_ids=known|{v['ProcessId'] for v in records if v['ParentProcessId'] in known}
            if next_ids==known:return known-{process.pid}
            known=next_ids
    def assert_gone(identities):
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.OpenProcess.argtypes=[ctypes.c_uint32,ctypes.c_int,ctypes.c_uint32];kernel.OpenProcess.restype=ctypes.c_void_p
        kernel.GetExitCodeProcess.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_uint32)];kernel.CloseHandle.argtypes=[ctypes.c_void_p]
        for identity in identities:
            until=time.monotonic()+5
            while True:
                handle=kernel.OpenProcess(0x1000,False,identity)
                if not handle:break
                code=ctypes.c_uint32();ok=kernel.GetExitCodeProcess(handle,ctypes.byref(code));kernel.CloseHandle(handle)
                if ok and code.value!=259:break
                if time.monotonic()>until:raise AssertionError(f'orphan child process {identity}')
                time.sleep(.1)
    def stop(directory):
        children=descendants();assert children,'engine process missing'
        state=json.loads((directory/'runtime.json').read_text())
        assert state['pid']==process.pid,'refuse to stop another instance'
        request=urllib.request.Request(origin+'/api/v1/runtime/stop',data=b'{}',headers={'Authorization':'Bearer '+state['stop_token']},method='POST')
        urllib.request.urlopen(request,timeout=10).close();process.wait(timeout=15)
        assert not (directory/'runtime.json').exists();assert_gone(children)
    def write(kind,name,source):call('/workspaces/'+kind+'/file',{'Path':name,'Content':source,'Directory':False},'PUT')
    def run(kind,file,params):return call('/runs',{'Kind':kind,'File':file,'Params':params},expected=202)['id']
    def done(identity,status='completed'):
        end=time.monotonic()+30
        while time.monotonic()<end:
            value=call('/runs/'+identity)
            if value['status'] in ['completed','failed','cancelled','interrupted']:
                assert value['status']==status,value
                return value
            time.sleep(.1)
        raise AssertionError('Run timed out')
    try:
        start(data)
        call('/portfolio',expected=401,authenticated=False)
        try:
            urllib.request.urlopen(origin+'/..%20/..%20/..%20/package.json')
            raise AssertionError('Windows alias path accepted')
        except urllib.error.HTTPError as error:assert error.code==404
        call('/auth/login',{'username':username,'password':password},expected=204)
        for page in ['market','quant','backtest','strategies','assets','portfolio','settings']:
            with urllib.request.urlopen(origin+'/'+page) as response:
                body=response.read();assert b'Kestrel Terminal' in body,(page,response.status,response.url,body[:200])
                if page=='market':
                    for asset in re.findall(rb'(?:src|href)="(/assets/[^"]+)"',body):
                        with urllib.request.urlopen(origin+asset.decode()) as static:
                            assert static.status==200 and 'text/html' not in static.headers.get('Content-Type','')
        call('/engine/runner/unknown/events',expected=404)
        instruments=call('/engine/market/instruments');assert len(instruments)==3
        instrument=instruments[0]['id'];snapshot=call('/engine/market/candles?instrument_id='+urllib.parse.quote(instrument));assert snapshot['quality']['state']=='fixture';assert snapshot['candles'][0]['open_time'].endswith('Z')
        quant=call('/engine/quant/calculate?instrument_id='+urllib.parse.quote(instrument)+'&indicator=sma&period=5');assert quant['snapshot_id']==snapshot['snapshot_id']
        write('research','main.py','KESTREL_KIND="research"\ndef run(context):\n    context.log("smoke")\n    context.table("values",["n"],[[42]])\n')
        research=run('research','main.py',{});done(research)
        artifacts=call('/runs/'+research+'/artifacts');assert len(artifacts)==1
        tape=call('/engine/backtest/data')[0]['snapshot_id']
        write('backtest','main.py','KESTREL_KIND="backtest"\ndef run(context):\n    context.replay(lambda view,event: [])\n')
        params={'event_snapshot':tape,'capital':'1000000','stage':'train','train_start':'2026-10-01T00:00:00Z','train_end':'2026-10-01T23:59:00Z','test_start':'2026-10-02T00:00:00Z','test_end':'2026-10-02T23:59:00Z'}
        train=run('backtest','main.py',params);done(train)
        test=run('backtest','main.py',params|{'stage':'test','train_run_id':train});done(test);assert call('/runs/'+test+'/report')['report']['stage']=='test'
        write('strategy','wrong.py','KESTREL_KIND="backtest"\ndef run(context):pass\n')
        call('/runs',{'Kind':'strategy','File':'wrong.py','Params':{}},expected=400)
        fund=call('/funds',{'name':'Paper smoke','kind':'paper','capital':'1000000','request_key':key()},expected=201)['id']
        manual=call('/funds/'+fund+'/allocations',{'name':'Manual','mode':'manual','amount':'100000','request_key':key()},expected=201)['id']
        strategy=call('/funds/'+fund+'/allocations',{'name':'Strategy','mode':'strategy','amount':'100000','request_key':key()},expected=201)['id']
        call('/allocations/'+manual+'/paper/advance',{'snapshot':tape,'source':'fixture-replay','after':0})
        order_request={'snapshot':tape,'source':'fixture-replay','side':'buy','limit_price':'11000','quantity':'1','request_key':key()}
        first_order=call('/allocations/'+manual+'/paper/order',order_request,expected=201)
        assert call('/allocations/'+manual+'/paper/order',order_request,expected=201)['id']==first_order['id']
        call('/allocations/'+manual+'/paper/advance',{'snapshot':tape,'source':'fixture-replay','after':1})
        assert call('/allocations/'+manual+'/paper/order',order_request,expected=201)['id']==first_order['id']
        assert len(call('/allocations/'+manual+'/paper')['orders'])==1
        write('strategy','main.py','KESTREL_KIND="strategy"\ndef on_event(context,event):\n    return []\n')
        live=run('strategy','main.py',{'allocation_id':strategy,'paper_source':'fixture-replay','event_snapshot':tape})
        call('/auth/lock',{},expected=204);call('/portfolio',expected=401);call('/auth/login',{'username':username,'password':password},expected=204)
        time.sleep(.3);assert call('/runs/'+live)['status'] in ['queued','running','completed']
        call('/runs/'+live+'/stop',{},expected=202);done(live,'cancelled')
        # Wait for controller cleanup, then explicitly acknowledge interrupted book.
        end=time.monotonic()+5
        while time.monotonic()<end:
            book=next(a for a in call('/allocations') if a['id']==strategy)
            if book['status']=='interrupted':break
            time.sleep(.1)
        call('/allocations/'+strategy+'/reconcile',{'acknowledge_no_missing_fills_inferred':True,'request_key':key()},expected=204)
        tracking=call('/funds',{'name':'Tracking smoke','kind':'tracking','capital':'1000000','request_key':key()},expected=201)['id']
        csv='trade_id,event_time,instrument_id,side,quantity,price,fee,tax,settled\na,2026-10-01T02:00:00Z,HOSE:REGULAR:equity:SYN02,buy,1,100,0,0,true\n'
        preview=call('/portfolio/import/preview',{'fund_id':tracking,'csv':csv});assert not preview['errors']
        call('/portfolio/import/apply',{'fund_id':tracking,'csv':csv,'preview_hash':preview['hash']})
        values=call('/portfolio');assert next(f for f in values['funds'] if f['id']==tracking)['nav'] is None
        # >200 persisted events must all replay after a terminal state.
        write('research','many.py','KESTREL_KIND="research"\ndef run(context):\n    for i in range(240):context.log(str(i))\n')
        many=run('research','many.py',{});done(many)
        stream=call('/runs/'+many+'/events');assert stream.count('event: run')>=243
        write('research','slow.py','KESTREL_KIND="research"\nimport time\ndef run(context):time.sleep(60)\n')
        interrupted=run('research','slow.py',{})
        stop(data);start(data);call('/auth/login',{'username':username,'password':password},expected=204)
        assert call('/runs/'+interrupted)['status']=='interrupted'
        crashed=run('research','slow.py',{});time.sleep(.5);children=descendants();process.kill();process.wait(timeout=10);assert_gone(children)
        start(data);call('/auth/login',{'username':username,'password':password},expected=204);assert call('/runs/'+crashed)['status']=='interrupted'
        stop(data)
        archive=base/'backup.zip';restored=base/'restored'
        subprocess.run([str(binary),'-data',str(data),'-backup',str(archive)],check=True,timeout=30)
        subprocess.run([str(binary),'-data',str(restored),'-restore',str(archive)],check=True,timeout=30)
        start(restored);assert call('/auth/status')['configured']
        call('/auth/login',{'username':username,'password':password},expected=204)
        assert len(call('/portfolio')['funds'])==2
        assert len(call('/engine/market/candles?instrument_id='+urllib.parse.quote(instrument))['candles'])==100
        stop(restored)
        print('PASS Windows fixture smoke: auth, routes, market, quant, research artifacts, Train/Test, separate contracts, manual/strategy, lock, CSV, SSE replay, stop/restart, backup/restore')
    finally:
        if process and process.poll() is None:
            process.kill();process.wait(timeout=10)
